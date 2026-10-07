"""Guardrail decisions: who may write or read what.

Three blocks, all about isolation between the agents:

- the implementer may not WRITE test files (block-tests);
- the implementer may not READ test files (block-test-reads);
- the test-writer may not READ production code while in tdd-loop
  (block-code-reads). Not in `characterize`, where reading the code is the job.

Running the test suite is always allowed to everyone. The Bash filter is a
heuristic — a creative command can get past it. It is an obstacle, not a wall.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, List, Mapping, Optional, Pattern, Tuple

from .classify import is_test_command
from .errors import PayloadError
from .profile import DEFAULT_TEST_FILE_PATTERN, Profile, compile_pattern
from .state import state_get


class Role(str, Enum):
    IMPLEMENTER = "implementer"
    TEST_WRITER = "test-writer"
    REFEREE = "referee"
    REVIEWER = "adversarial-reviewer"
    NONE = "none"


# adversarial-reviewer first: the most specific name wins.
_ROLE_ORDER = (Role.REVIEWER, Role.TEST_WRITER, Role.IMPLEMENTER, Role.REFEREE)


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    tool_input: Mapping[str, Any] = field(default_factory=dict)
    agent_type: Optional[str] = None
    response_text: str = ""


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    message: str = ""


ALLOW = Verdict(True)


def _flatten_response(resp: Any) -> str:
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, Mapping):
        parts: List[str] = []
        for key in ("stdout", "stderr"):
            if isinstance(resp.get(key), str):
                parts.append(resp[key])
        for key in sorted(k for k in resp if k not in ("stdout", "stderr")):
            if isinstance(resp[key], str):
                parts.append(resp[key])
        return "\n".join(parts)
    return json.dumps(resp)


def parse_payload(raw: str) -> ToolCall:
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise PayloadError(f"not JSON: {exc}") from None
    if not isinstance(data, dict):
        raise PayloadError("not a JSON object")
    tool_input = data.get("tool_input")
    agent = data.get("agent_type")
    return ToolCall(
        tool_name=data.get("tool_name") if isinstance(data.get("tool_name"), str) else "",
        tool_input=tool_input if isinstance(tool_input, dict) else {},
        agent_type=agent if isinstance(agent, str) and agent else None,
        response_text=_flatten_response(data.get("tool_response")),
    )


def resolve_role(agent_type: Optional[str], active_role: Optional[str]) -> Role:
    """agent_type is authoritative inside a subagent; active_role otherwise."""
    if agent_type is not None:
        for role in _ROLE_ORDER:
            if role.value in agent_type:
                return role
        return Role.NONE
    for role in _ROLE_ORDER:
        if role.value == active_role:
            return role
    return Role.NONE


# --- paths -----------------------------------------------------------------

_MSYS_DRIVE = re.compile(r"^/([A-Za-z])/")
_DRIVE = re.compile(r"^[A-Za-z]:/")


def _slashes(path: str) -> str:
    p = path.replace("\\", "/")
    p = _MSYS_DRIVE.sub(lambda m: m.group(1).upper() + ":/", p)
    while "//" in p[1:]:
        p = p[0] + p[1:].replace("//", "/")
    return p


def normalize_path(path: str, project_dir: str) -> str:
    """Slash-separated, relative to the project when it is inside it."""
    p = _slashes(path.strip())
    root = _slashes(project_dir).rstrip("/")
    if root:
        if _DRIVE.match(p) or _DRIVE.match(root):
            if p.lower() == root.lower():
                return ""
            if p.lower().startswith(root.lower() + "/"):
                p = p[len(root) + 1 :]
        elif p == root:
            return ""
        elif p.startswith(root + "/"):
            p = p[len(root) + 1 :]
    while p.startswith("./"):
        p = p[2:]
    return "" if p == "." else p


def _test_pattern(profile: Profile) -> Pattern[str]:
    return profile.pattern("test_file_pattern") or compile_pattern(
        "test_file_pattern", DEFAULT_TEST_FILE_PATTERN
    )


def _dirs(values: Iterable[str]) -> Tuple[str, ...]:
    out = []
    for v in values:
        d = normalize_path(v, "").rstrip("/")
        out.append(d + "/" if d else "")
    return tuple(out)


# --- messages ----------------------------------------------------------------

_TEST_EDIT_MSG = """lasagna: write to a test file denied.

  file:  {path}
  agent: {agent}

The implementer cannot modify tests. The current test is the contract you have
to satisfy, not the obstacle to remove: changing it destroys the separation
between whoever specifies the behaviour and whoever implements it.

If you believe the test is wrong, you have two legitimate moves:

  1. If the code can pass the test as written, write that code. The minimum
     that turns it green, nothing more.
  2. If you believe the test contradicts the frozen contract, stop and say so
     in your final answer, quoting the contract line you think it violates.
     The referee decides between you and the test.

Do not route around this by renaming files, adding a parallel test, or putting
production code inside the test directory.
"""

_TEST_READ_MSG = """lasagna: the implementer cannot read test files.

  target: {target}

You work from the frozen contract, the name of the failing test and the failure
lines the coordinator passed you. Reading the test lets the code be shaped
around its literal expected values instead of the contract — that is what this
block prevents.

Running the test suite is always allowed: its failure output tells you what the
test expects. If that is not enough to know what to build, the contract is
ambiguous: say so in your final answer, quoting the contract line.
"""

_CODE_READ_MSG = """lasagna: the test-writer cannot read production code during tdd-loop.

  target: {target}

The test comes from the acceptance criterion and the frozen contract, not from
the implementation: a test written after reading the code checks what the code
does, not what it should do.

You can read test files, the contract and spec under .lasagna/, and docs/.
Running the test suite is always allowed.
"""

_NARROW_MSG = """lasagna: {tool} without a path searches the whole repository, including
files the {role} must not read.

Pass a path to narrow the search: the tests directory, or .lasagna/ for the
contract.
"""

_PAYLOAD_MSG = """lasagna: the hook payload could not be read ({detail}) and active_role is
{role}. A guardrail that cannot decide fails closed: denied.
"""


# --- decisions -----------------------------------------------------------------

_EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")


def decide_test_edit(
    call: ToolCall, profile: Profile, state_text: Optional[str], project_dir: str
) -> Verdict:
    if call.tool_name not in _EDIT_TOOLS or not profile.hook_enabled("block-tests"):
        return ALLOW
    role = resolve_role(call.agent_type, state_get(state_text or "", "active_role"))
    if role is not Role.IMPLEMENTER:
        return ALLOW
    pattern = _test_pattern(profile)
    for key in ("file_path", "notebook_path"):
        raw = call.tool_input.get(key)
        if isinstance(raw, str) and raw:
            path = normalize_path(raw, project_dir)
            if pattern.search(path):
                agent = call.agent_type or "implementer (from active_role)"
                return Verdict(False, _TEST_EDIT_MSG.format(path=path, agent=agent))
    return ALLOW


@dataclass(frozen=True)
class _Target:
    """What one blocked agent may not read."""

    role: Role
    test_pattern: Pattern[str]
    test_dirs: Tuple[str, ...]
    source_dirs: Tuple[str, ...]

    def hit(self, path: str) -> bool:
        if self.role is Role.IMPLEMENTER:
            if self.test_pattern.search(path):
                return True
            return path.rstrip("/") + "/" in self.test_dirs
        # test-writer: production code under a source_path
        if self.test_pattern.search(path):
            return False
        if path.startswith((".lasagna/", "docs/")) or path in (".lasagna", "docs"):
            return False
        as_dir = path.rstrip("/") + "/"
        for src in self.source_dirs:
            if src == "" or path.startswith(src) or as_dir == src:
                return True
        return False

    def message(self, target: str) -> str:
        tpl = _TEST_READ_MSG if self.role is Role.IMPLEMENTER else _CODE_READ_MSG
        return tpl.format(target=target)


def _read_target(
    call: ToolCall, profile: Profile, state_text: Optional[str]
) -> Optional[_Target]:
    state = state_text or ""
    role = resolve_role(call.agent_type, state_get(state, "active_role"))
    pattern = _test_pattern(profile)
    if role is Role.IMPLEMENTER and profile.hook_enabled("block-test-reads"):
        return _Target(role, pattern, _dirs(profile.get_all("test_path")), ())
    if (
        role is Role.TEST_WRITER
        and profile.hook_enabled("block-code-reads")
        and state_get(state, "phase") == "tdd-loop"
        and profile.get_all("source_path")
    ):
        return _Target(role, pattern, (), _dirs(profile.get_all("source_path")))
    return None


_PUNCT = "<>|;&()"


def _command_tokens(command: str) -> List[str]:
    text = command.replace("\\", "/")
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        raw = list(lex)
    except ValueError:
        raw = text.split()
    tokens: List[str] = []
    for tok in raw:
        tok = tok.strip(_PUNCT + "'\"")
        if not tok:
            continue
        tokens.append(tok)
        if "=" in tok:  # --file=tests/x.py
            tokens.append(tok.split("=", 1)[1])
    return tokens


def decide_read(
    call: ToolCall, profile: Profile, state_text: Optional[str], project_dir: str
) -> Verdict:
    tool = call.tool_name
    if tool not in ("Read", "NotebookRead", "Grep", "Glob", "Bash"):
        return ALLOW
    target = _read_target(call, profile, state_text)
    if target is None:
        return ALLOW
    inp = call.tool_input

    def value(key: str) -> Optional[str]:
        v = inp.get(key)
        return v if isinstance(v, str) else None

    if tool == "Bash":
        command = value("command") or ""
        if is_test_command(command, profile):
            return ALLOW
        for tok in _command_tokens(command):
            if target.hit(normalize_path(tok, project_dir)):
                return Verdict(False, target.message(command))
        return ALLOW

    if tool in ("Grep", "Glob"):
        path = value("path")
        if path is None or normalize_path(path, project_dir) == "":
            return Verdict(False, _NARROW_MSG.format(tool=tool, role=target.role.value))
        candidates = [path] + ([value("pattern") or ""] if tool == "Glob" else [])
    else:
        candidates = [value("file_path") or "", value("notebook_path") or ""]

    for raw in candidates:
        if raw:
            path = normalize_path(raw, project_dir)
            if target.hit(path):
                return Verdict(False, target.message(path))
    return ALLOW


def decide_unreadable(
    hook: str, profile: Profile, state_text: Optional[str], detail: str = "invalid JSON"
) -> Verdict:
    """BR-5: unreadable payload. Deny only when a blocked agent is active."""
    state = state_text or ""
    role = state_get(state, "active_role") or "none"
    deny = False
    if hook == "block-test-edits":
        deny = role == "implementer" and profile.hook_enabled("block-tests")
    elif hook == "block-reads":
        deny = (role == "implementer" and profile.hook_enabled("block-test-reads")) or (
            role == "test-writer"
            and state_get(state, "phase") == "tdd-loop"
            and profile.hook_enabled("block-code-reads")
        )
    if deny:
        return Verdict(False, _PAYLOAD_MSG.format(detail=detail, role=role))
    return ALLOW
