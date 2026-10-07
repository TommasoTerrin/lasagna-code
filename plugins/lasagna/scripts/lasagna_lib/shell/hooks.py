"""One handler per hook. Each reads stdin, calls the core, and returns 0 or 2.

Exit code 2 is the only one Claude Code treats as "deny". Anything else from a
guardrail is a non-blocking error, and the guardrail would vanish silently —
so the blocking hooks turn every failure into 2 (fail closed) and the others
turn every failure into 0 with a warning.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Callable, Dict, Optional, TextIO

from ..core.budget import count_cycle
from ..core.classify import classify_output, is_test_command, record_outcome
from ..core.errors import PatternError, PayloadError
from ..core.guards import Verdict, decide_read, decide_test_edit, decide_unreadable, parse_payload
from ..core.state import state_set
from ..core.status import render_precompact, render_session_status, render_snapshot
from .files import (
    Env,
    active_state_path,
    lasagna_dir,
    load_profile,
    now,
    profile_path,
    project_dir,
    read_text,
    write_atomic,
)

BLOCKING = frozenset({"block-test-edits", "block-reads"})


class Streams:
    def __init__(self, out: TextIO, err: TextIO) -> None:
        self.out = out
        self.err = err


def _state(env: Env):
    path = active_state_path(env)
    return path, (read_text(path) if path else None)


def _guard(
    hook: str,
    decide: Callable[..., Verdict],
    stdin: str,
    env: Env,
    io: Streams,
) -> int:
    profile = load_profile(env)
    if profile is None:
        return 0
    _, state = _state(env)
    try:
        verdict = decide(parse_payload(stdin), profile, state, project_dir(env))
    except PayloadError as exc:
        verdict = decide_unreadable(hook, profile, state, exc.detail)
    except PatternError as exc:
        io.err.write(
            f"lasagna: invalid regex in .lasagna/stack.md, key {exc.key}: {exc.detail}\n"
            f"  pattern: {exc.pattern}\nFix the key; until then this guardrail denies.\n"
        )
        return 2
    if verdict.allowed:
        return 0
    io.err.write(verdict.message)
    return 2


def block_test_edits(stdin: str, env: Env, io: Streams) -> int:
    return _guard("block-test-edits", decide_test_edit, stdin, env, io)


def block_reads(stdin: str, env: Env, io: Streams) -> int:
    return _guard("block-reads", decide_read, stdin, env, io)


def capture_test_result(stdin: str, env: Env, io: Streams) -> int:
    profile = load_profile(env)
    if profile is None or not profile.hook_enabled("test-result"):
        return 0
    call = parse_payload(stdin)
    command = call.tool_input.get("command")
    if not isinstance(command, str) or not is_test_command(command, profile):
        return 0
    path, state = _state(env)
    if path is None or state is None:
        return 0
    outcome = classify_output(call.response_text, profile)
    text, out = record_outcome(state, outcome, command, now())
    if write_atomic(path, text):
        io.out.write(out)
    return 0


def count_cycle_hook(stdin: str, env: Env, io: Streams) -> int:
    profile = load_profile(env)
    if profile is None:
        return 0
    call = parse_payload(stdin)
    path, state = _state(env)
    if path is None or state is None:
        return 0
    result = count_cycle(state, call.agent_type, profile, now())
    if result.state_text != state and write_atomic(path, result.state_text):
        io.out.write(result.message)
    return 0


def dump_phase_state(stdin: str, env: Env, io: Streams) -> int:
    profile = load_profile(env)
    if profile is None or not profile.hook_enabled("precompact"):
        return 0
    reason = "unknown"
    try:
        call_data = json.loads(stdin) if stdin.strip() else {}
        if isinstance(call_data, dict):
            for key in ("trigger", "reason"):
                if isinstance(call_data.get(key), str) and call_data[key]:
                    reason = call_data[key]
                    break
    except ValueError:
        pass
    path, state = _state(env)
    if path is None or state is None:
        io.out.write(render_precompact(None, None, None, reason))
        return 0
    stamp = now()
    state = state_set(state, "updated", stamp)
    write_atomic(path, state)
    snapshot = re.sub(r"\.state\.md$", ".precompact.md", path)
    write_atomic(snapshot, render_snapshot(state, reason, stamp), must_exist=False)
    io.out.write(render_precompact(state, path, snapshot, reason))
    return 0


def session_status(stdin: str, env: Env, io: Streams) -> int:
    ldir = lasagna_dir(env)
    if not os.path.isdir(ldir):
        return 0
    profile_text = read_text(profile_path(env))
    if profile_text is not None and not load_profile(env).hook_enabled("session-status"):
        return 0
    path, state = _state(env)
    snapshot_newer = False
    if path:
        snap = re.sub(r"\.state\.md$", ".precompact.md", path)
        snapshot_newer = os.path.isfile(snap) and os.path.getmtime(snap) > os.path.getmtime(path)
    io.out.write(
        render_session_status(ldir, profile_text, state, path, snapshot_newer, sys.executable)
    )
    return 0


HOOKS: Dict[str, Callable[[str, Env, Streams], int]] = {
    "session-status": session_status,
    "block-test-edits": block_test_edits,
    "block-reads": block_reads,
    "capture-test-result": capture_test_result,
    "count-cycle": count_cycle_hook,
    "dump-phase-state": dump_phase_state,
}


def run_hook(name: str, stdin: str, env: Env, io: Optional[Streams] = None) -> int:
    io = io or Streams(sys.stdout, sys.stderr)
    handler = HOOKS.get(name)
    if handler is None:
        io.err.write(f"lasagna: unknown hook {name!r}\n")
        return 2 if name in BLOCKING else 0
    blocking = name in BLOCKING
    # Without a profile the project does not use lasagna: stay silent.
    if name != "session-status" and not os.path.isfile(profile_path(env)):
        return 0
    try:
        code = handler(stdin, env, io)
    except Exception as exc:  # noqa: BLE001 — INV-1: never exit with anything but 0/2
        line = f"lasagna: internal error in {name}: {type(exc).__name__}: {exc}\n"
        io.err.write(line)
        return 2 if blocking else 0
    return code if code in (0, 2) else (2 if blocking else 0)
