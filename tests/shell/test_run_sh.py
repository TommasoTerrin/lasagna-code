"""run.sh end to end: launcher, Python discovery, every hook and CLI command.

AC-V2-002, 003, 004, 005, 006, 009 through the real process.
"""

import os

import pytest

from conftest import REAL_PYTHON

HOOKS = [
    "session-status",
    "block-test-edits",
    "block-reads",
    "capture-test-result",
    "count-cycle",
    "dump-phase-state",
]
WRITE_TEST = {"tool_name": "Write", "tool_input": {"file_path": "tests/test_x.py", "content": "x"}}


def implementer(project):
    project.state_file.write_text(
        project.state().replace("active_role: none", "active_role: implementer"), encoding="utf-8"
    )


# --- projects without lasagna --------------------------------------------------


@pytest.mark.parametrize("hook", HOOKS)
def test_hooks_are_silent_without_a_profile(project, hook):
    r = project.run("hook", hook, stdin=WRITE_TEST)
    assert (r.code, r.out, r.err) == (0, "", "")
    assert list(project.root.iterdir()) == []
    assert project.saved_python() is None  # did not even look for Python


def test_session_status_warns_when_lasagna_dir_has_no_profile(project):
    project.lasagna.mkdir()
    project.save_python()
    r = project.run("hook", "session-status")
    assert r.code == 0 and "INACTIVE" in r.out


# --- guardrails through the process ----------------------------------------------


def test_implementer_write_to_test_is_denied(project):
    project.init()
    project.save_python()
    implementer(project)
    r = project.run("hook", "block-test-edits", stdin=WRITE_TEST)
    assert r.code == 2
    assert "tests/test_x.py" in r.err


def test_implementer_read_of_test_denied_but_running_suite_allowed(project):
    project.init()
    project.save_python()
    implementer(project)
    read = {"tool_name": "Read", "tool_input": {"file_path": str(project.root / "tests" / "test_x.py")}}
    assert project.run("hook", "block-reads", stdin=read).code == 2
    run = {"tool_name": "Bash", "tool_input": {"command": "python -m pytest tests -x"}}
    assert project.run("hook", "block-reads", stdin=run).code == 0


def test_test_writer_code_read_depends_on_phase(project):
    project.init()
    project.save_python()
    read = {"tool_name": "Read", "agent_type": "lasagna:test-writer", "tool_input": {"file_path": "src/a.py"}}
    assert project.run("hook", "block-reads", stdin=read).code == 2
    project.state_file.write_text(
        project.state().replace("phase: tdd-loop", "phase: characterize"), encoding="utf-8"
    )
    assert project.run("hook", "block-reads", stdin=read).code == 0


def test_unreadable_payload_fails_closed_for_active_implementer(project):
    project.init()
    project.save_python()
    implementer(project)
    r = project.run("hook", "block-test-edits", stdin="{not json")
    assert r.code == 2 and "payload" in r.err


def test_invalid_regex_denies_in_blocking_hook_and_warns_in_others(project):
    project.init(profile="test_file_pattern: (unclosed\ntest_command_pattern: (pytest\n")
    project.save_python()
    implementer(project)
    r = project.run("hook", "block-test-edits", stdin=WRITE_TEST)
    assert r.code == 2 and "test_file_pattern" in r.err
    bash = {"tool_name": "Bash", "tool_input": {"command": "pytest"}, "tool_response": "1 passed"}
    r = project.run("hook", "capture-test-result", stdin=bash)
    assert r.code == 0 and "internal error" in r.err


# --- state hooks -------------------------------------------------------------------


def test_capture_test_result_records_the_outcome(project):
    project.init()
    project.save_python()
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "python -m pytest tests"},
        "tool_response": {"stdout": "E       assert 1 == 2\n1 failed in 0.1s", "stderr": ""},
    }
    r = project.run("hook", "capture-test-result", stdin=payload)
    assert r.code == 0
    assert "lasagna: test outcome = red-assertion" in r.out
    assert "last_test_result: red-assertion" in project.state()
    assert "last_test_command: python -m pytest tests" in project.state()


def test_capture_ignores_other_commands(project):
    project.init()
    project.save_python()
    before = project.state()
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": "1 failed"}
    assert project.run("hook", "capture-test-result", stdin=payload).out == ""
    assert project.state() == before


def test_count_cycle_updates_the_state(project):
    project.init()
    project.save_python()
    project.state_file.write_text(
        project.state().replace("last_test_result: none", "last_test_result: red-generic"),
        encoding="utf-8",
    )
    r = project.run("hook", "count-cycle", stdin={"agent_type": "plugin:lasagna:implementer"})
    assert r.code == 0 and "cycle 1/3" in r.out
    assert "cycles_used: 1" in project.state()
    assert "| implementer | red-generic |" in project.state()


def test_dump_phase_state_writes_a_snapshot(project):
    project.init()
    project.save_python()
    r = project.run("hook", "dump-phase-state", stdin={"trigger": "auto"})
    assert r.code == 0 and "pinned before compaction" in r.out
    snap = project.lasagna / "state" / "FEAT-001.precompact.md"
    assert "reason: auto" in snap.read_text(encoding="utf-8")


def test_state_file_override_and_latest_state(project):
    project.init()
    project.save_python()
    other = project.lasagna / "state" / "FEAT-002.state.md"
    other.write_text(project.state().replace("FEAT-001", "FEAT-002"), encoding="utf-8")
    os.utime(project.state_file, (1, 1))
    assert "FEAT-002" in project.run("status").out
    r = project.run("status", env={"LASAGNA_STATE_FILE": str(project.state_file)})
    assert "FEAT-001" in r.out


# --- Python discovery ---------------------------------------------------------------


def test_first_use_skips_store_stub_and_saves_the_interpreter(project):
    project.init()
    project.fake("python3", 'echo "Python was not found; run without arguments to install" >&2\nexit 49')
    project.fake("python", f'exec "{REAL_PYTHON}" "$@"')
    r = project.run("hook", "session-status", isolated_path=True)
    assert r.code == 0
    assert project.saved_python() == REAL_PYTHON
    assert "lasagna: python" in r.out


def test_saved_interpreter_is_used_without_searching(project):
    project.init()
    project.save_python()
    # Empty PATH: no candidate and no external command available at all.
    r = project.run("hook", "session-status", isolated_path=True)
    assert r.code == 0 and "lasagna: FEAT-001" in r.out


def test_saved_interpreter_gone_triggers_a_new_search(project):
    project.init()
    project.save_python("C:/nowhere/python.exe")
    project.fake("python", f'exec "{REAL_PYTHON}" "$@"')
    r = project.run("hook", "session-status", isolated_path=True)
    assert r.code == 0
    assert project.saved_python() == REAL_PYTHON


@pytest.mark.parametrize(
    "args,code,stream",
    [
        (("hook", "block-test-edits"), 2, "err"),
        (("hook", "block-reads"), 2, "err"),
        (("hook", "capture-test-result"), 0, "err"),
        (("hook", "count-cycle"), 0, "err"),
        (("hook", "session-status"), 0, "out"),
        (("set-state", "a", "b"), 1, "err"),
    ],
)
def test_no_python_blocking_hooks_fail_closed(project, args, code, stream):
    project.init()
    project.fake("python3", "exit 49")
    project.fake("python", "exit 1")
    r = project.run(*args, isolated_path=True)
    assert r.code == code
    assert "Python >= 3.9" in getattr(r, stream)


def test_python_command_shows_sets_and_resets(project):
    project.fake("python", f'exec "{REAL_PYTHON}" "$@"')
    r = project.run("python", isolated_path=True)
    assert r.code == 0 and r.out.strip() == REAL_PYTHON

    bad = project.run("python", "C:/nowhere/python.exe", isolated_path=True)
    assert bad.code == 1 and project.saved_python() == REAL_PYTHON

    project.save_python("C:/stale/python.exe")
    r = project.run("python", "--reset", isolated_path=True)
    assert r.code == 0 and project.saved_python() == REAL_PYTHON

    project.save_python("C:/stale/python.exe")
    r = project.run("python", REAL_PYTHON)
    assert r.code == 0 and project.saved_python() == REAL_PYTHON


# --- CLI ---------------------------------------------------------------------------------


def test_set_state_and_append(project):
    project.init()
    project.save_python()
    assert project.run("set-state", "active_role", "implementer").code == 0
    assert "active_role: implementer" in project.state()
    assert project.run("set-state", "--append", "- [t] next").code == 0
    assert "- [2026-10-07T09:00] about to start\n- [t] next\n\n## Cycle log" in project.state()
    assert project.run("set-state", "only-one-arg").code == 1


def test_set_state_without_state_fails(project):
    project.init(state=None)
    project.save_python()
    r = project.run("set-state", "a", "b")
    assert r.code == 1 and "no phase state" in r.err


def test_check_traceability(project):
    project.init()
    project.save_python()
    specs = project.lasagna / "specs"
    specs.mkdir()
    (specs / "FEAT-001.md").write_text("AC-FEAT-001-001 AC-FEAT-001-002", encoding="utf-8")
    tests = project.root / "tests"
    tests.mkdir()
    (tests / "test_a.py").write_text("# AC-FEAT-001-001\n", encoding="utf-8")
    r = project.run("check-traceability", "FEAT-001")
    assert r.code == 1 and "AC-FEAT-001-002" in r.err
    (tests / "test_b.py").write_text("# AC-FEAT-001-002\n", encoding="utf-8")
    assert project.run("check-traceability").code == 0
    assert project.run("check-traceability", "FEAT-404").code == 2


def test_init_is_idempotent(project):
    project.save_python()
    tpl = str(project.root.parent / "tpl.md")
    with open(tpl, "w", encoding="utf-8") as fh:
        fh.write("language: python\n")
    first = project.run("init", tpl)
    assert first.code == 0, first.out + first.err
    assert "CREATED  .lasagna/stack.md" in first.out
    assert "CREATED  .lasagna/architecture.md" in first.out
    assert "CREATED  docs/context/INDEX.md" in first.out
    assert "SUGGEST" in first.out and "PYTHON" in first.out
    assert ".lasagna/state/" in (project.root / ".gitignore").read_text(encoding="utf-8")
    second = project.run("init", tpl)
    assert "CREATED" not in second.out
    assert (project.root / ".gitignore").read_text(encoding="utf-8").count(".lasagna/state/") == 1


def test_init_without_profile_is_not_ready(project):
    project.save_python()
    r = project.run("init")
    assert r.code == 1 and "NOT ready" in r.out
