"""Reading `key: value` files: the stack profile, and the phase state's keys.

Scripts read the lines that start at column zero; surrounding prose is for
humans. The first NON-EMPTY value wins: templates ship keys with empty
placeholders, and an empty line must read as "unset" rather than shadow a value
configured further down.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Pattern, Tuple

from .errors import PatternError

# Used when the profile declares no test_file_pattern (same as v1).
DEFAULT_TEST_FILE_PATTERN = (
    r"(^|/)tests?/|(^|/)test_[^/]*\.|[._-]test\.|\.spec\.|(^|/)__tests__/"
    r"|conftest\.|Test\.(java|kt|cs)$|Tests\.(java|kt|cs)$|(^|/)src/test/"
)

# v1 keys that v2 ignores or maps (docs/v2-spec.md §6.2).
LEGACY_KEYS = (
    "core_path",
    "core_allowed_import",
    "core_import_pattern",
    "core_forbidden_pattern",
    "budget_domain",
    "budget_adapter",
)

_KV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")


def parse_kv(text: str) -> Dict[str, Tuple[str, ...]]:
    """Every non-empty value of every column-zero key, in file order."""
    found: Dict[str, List[str]] = {}
    for line in text.splitlines():
        m = _KV_LINE.match(line)
        if not m:
            continue
        value = m.group(2).strip()
        if value:
            found.setdefault(m.group(1), []).append(value)
    return {k: tuple(v) for k, v in found.items()}


# POSIX bracket classes, as grep -E understands them. Profiles written for v1
# may use them; Python's re does not.
_POSIX_OUTSIDE = {
    "space": r"\s",
    "digit": r"\d",
    "alpha": r"[^\W\d_]",
    "alnum": r"[^\W_]",
    "upper": "[A-Z]",
    "lower": "[a-z]",
    "xdigit": "[0-9A-Fa-f]",
    "punct": r"[!-/:-@\[-`{-~]",
}
_POSIX_INSIDE = {
    "space": r"\s",
    "digit": r"\d",
    "alpha": "a-zA-Z",
    "alnum": "a-zA-Z0-9",
    "upper": "A-Z",
    "lower": "a-z",
    "xdigit": "0-9A-Fa-f",
    "punct": r"!-/:-@\[-`{-~",
}


def ere_to_python(ere: str) -> str:
    """Translate the POSIX classes of an ERE; leave the rest untouched."""
    out: List[str] = []
    i, n = 0, len(ere)
    while i < n:
        c = ere[i]
        if c == "\\" and i + 1 < n:
            out.append(ere[i : i + 2])
            i += 2
            continue
        if c != "[":
            out.append(c)
            i += 1
            continue
        # A bracket expression. A lone class "[[:space:]]" becomes a shorthand;
        # a mixed one "[^[:space:]x]" gets the class expanded in place.
        m = re.match(r"\[\[:([a-z]+):\]\]", ere[i:])
        if m and m.group(1) in _POSIX_OUTSIDE:
            out.append(_POSIX_OUTSIDE[m.group(1)])
            i += m.end()
            continue
        j = i + 1
        buf = ["["]
        if j < n and ere[j] == "^":
            buf.append("^")
            j += 1
        if j < n and ere[j] == "]":  # a literal ']' first in the set
            buf.append(r"\]")
            j += 1
        closed = False
        while j < n:
            m = re.match(r"\[:([a-z]+):\]", ere[j:])
            if m and m.group(1) in _POSIX_INSIDE:
                buf.append(_POSIX_INSIDE[m.group(1)])
                j += m.end()
                continue
            ch = ere[j]
            if ch == "]":
                buf.append("]")
                j += 1
                closed = True
                break
            if ch == "\\":
                buf.append(r"\\")
            elif ch == "[":
                buf.append(r"\[")
            else:
                buf.append(ch)
            j += 1
        if not closed:  # unbalanced: let re report it on the original text
            out.append(ere[i:])
            break
        out.append("".join(buf))
        i = j
    return "".join(out)


def compile_pattern(key: str, ere: str) -> Pattern[str]:
    try:
        return re.compile(ere_to_python(ere), re.MULTILINE)
    except re.error as exc:
        raise PatternError(key, ere, str(exc)) from None


@dataclass(frozen=True)
class Profile:
    values: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        vals = self.values.get(key, ())
        return vals[0] if vals else default

    def get_all(self, key: str) -> Tuple[str, ...]:
        return tuple(self.values.get(key, ()))

    def pattern(self, key: str) -> Optional[Pattern[str]]:
        ere = self.get(key)
        return None if ere is None else compile_pattern(key, ere)

    def hook_enabled(self, name: str) -> bool:
        disabled = self.get("hooks_disabled", "") or ""
        names = {part.strip() for part in disabled.split(",")}
        return name not in names

    def int_value(self, key: str, *fallback_keys: str, default: int) -> int:
        """First key (then fallbacks) holding a positive integer, else default."""
        for k in (key, *fallback_keys):
            v = self.get(k)
            if v is not None and v.isdigit() and int(v) >= 1:
                return int(v)
        return default


def parse_profile(text: str) -> Profile:
    return Profile(parse_kv(text))


def legacy_keys(profile: Profile) -> Tuple[str, ...]:
    """v1 keys present in the profile, for the "update your profile" hint."""
    found = [k for k in LEGACY_KEYS if profile.get(k) is not None]
    if profile.get("context_file") is not None and profile.get("context_dir") is None:
        found.append("context_file")
    return tuple(found)
