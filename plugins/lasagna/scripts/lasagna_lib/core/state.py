"""The phase state as text: str in, str out.

The state stays text on purpose. Hooks only touch the `key: value` lines at
column zero and the sections they append to; every other line — notes,
criteria, checkpoints — comes back byte for byte, in the same order.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .profile import parse_kv

_SECTION_END = re.compile(r"^(## |---\s*$)")


def state_get(text: str, key: str) -> Optional[str]:
    vals = parse_kv(text).get(key, ())
    return vals[0] if vals else None


def _lines(text: str) -> List[str]:
    return text.splitlines()


def _join(lines: List[str]) -> str:
    return "\n".join(lines) + "\n" if lines else ""


def state_set(text: str, key: str, value: str) -> str:
    """Replace the first `key:` line, or append one at the end."""
    lines = _lines(text)
    prefix = key + ":"
    new = f"{key}: {value}"
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = new
            return _join(lines)
    lines.append(new)
    return _join(lines)


def state_append(text: str, section: str, line: str) -> str:
    """Insert `line` at the end of `section`, before the next section.

    Appending at end of file would bury checkpoints and cycle logs inside the
    reference notes that close the template, where nobody reads them again.
    """
    lines = _lines(text)
    try:
        start = lines.index(section)
    except ValueError:
        return _join(lines + [section, line])
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if _SECTION_END.match(lines[i]):
            end = i
            break
    # Right after the section's last non-blank line: a table row must touch
    # the table, and the blank line before the next heading stays.
    at = end
    while at > start + 1 and not lines[at - 1].strip():
        at -= 1
    return _join(lines[:at] + [line] + lines[at:])


def state_int(text: str, key: str) -> int:
    """A counter: non-numeric or negative reads as 0."""
    v = state_get(text, key) or ""
    return int(v) if v.isdigit() else 0
