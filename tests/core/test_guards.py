"""Guardrail decisions (AC-V2-003…006, 010). Values in, Verdict out, no mocks."""

import json

import pytest

from lasagna_lib.core.errors import PayloadError
from lasagna_lib.core.guards import (
    Role,
    ToolCall,
    decide_read,
    decide_test_edit,
    decide_unreadable,
    normalize_path,
    parse_payload,
    resolve_role,
)
from lasagna_lib.core.profile import parse_profile

PROFILE = parse_profile(
    "test_command_pattern: (pytest|python -m pytest)\n"
    r"test_file_pattern: (^|/)tests?/|(^|/)test_[^/]*\.py$|conftest\.py$" "\n"
    "test_path: tests/\n"
    "source_path: src/\n"
)
ROOT = "C:/proj"
IMPL = "implementer"
TW = "test-writer"


def state(role="none", phase="tdd-loop"):
    return f"active_role: {role}\nphase: {phase}\n"


def call(tool, agent=None, **inp):
    return ToolCall(tool_name=tool, tool_input=inp, agent_type=agent)


# --- payload and roles --------------------------------------------------------


def test_payload_paths_come_from_tool_input_only():
    raw = json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/x.py", "content": '"file_path": "tests/test_x.py"'},
        }
    )
    c = parse_payload(raw)
    assert decide_test_edit(c, PROFILE, state(IMPL), ROOT).allowed


@pytest.mark.parametrize("raw", ["not json", "[1, 2]", ""])
def test_unparseable_payload_raises(raw):
    with pytest.raises(PayloadError):
        parse_payload(raw)


def test_response_is_flattened_stdout_first():
    c = parse_payload(json.dumps({"tool_name": "Bash", "tool_response": {"stderr": "E", "stdout": "O"}}))
    assert c.response_text == "O\nE"


@pytest.mark.parametrize(
    "agent,active,expected",
    [
        ("plugin:lasagna:implementer", "none", Role.IMPLEMENTER),
        ("lasagna:test-writer", "implementer", Role.TEST_WRITER),
        ("lasagna:adversarial-reviewer", None, Role.REVIEWER),
        ("general-purpose", "implementer", Role.NONE),
        (None, "implementer", Role.IMPLEMENTER),
        (None, None, Role.NONE),
    ],
)
def test_agent_type_wins_over_active_role(agent, active, expected):
    assert resolve_role(agent, active) is expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (r"C:\proj\tests\test_x.py", "tests/test_x.py"),
        ("c:/PROJ/src/a.py", "src/a.py"),
        ("/c/proj/src/a.py", "src/a.py"),
        ("./src/a.py", "src/a.py"),
        ("C:/proj", ""),
        (".", ""),
        ("D:/other/x.py", "D:/other/x.py"),
    ],
)
def test_paths_are_normalised_relative_to_the_project(path, expected):
    assert normalize_path(path, r"C:\proj") == expected


# --- block-test-edits ----------------------------------------------------------


@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit"])
def test_implementer_cannot_write_tests(tool):
    v = decide_test_edit(call(tool, file_path=r"C:\proj\tests\test_x.py"), PROFILE, state(IMPL), ROOT)
    assert not v.allowed
    assert "tests/test_x.py" in v.message


def test_implementer_cannot_edit_test_notebook():
    v = decide_test_edit(call("NotebookEdit", IMPL, notebook_path="tests/test_n.ipynb"), PROFILE, None, ROOT)
    assert not v.allowed


def test_implementer_can_write_code_and_others_can_write_tests():
    assert decide_test_edit(call("Write", file_path="src/x.py"), PROFILE, state(IMPL), ROOT).allowed
    assert decide_test_edit(call("Write", TW, file_path="tests/test_x.py"), PROFILE, state(IMPL), ROOT).allowed


def test_default_test_pattern_without_profile_key():
    v = decide_test_edit(call("Write", IMPL, file_path="tests/test_x.py"), parse_profile(""), None, ROOT)
    assert not v.allowed


def test_block_tests_can_be_disabled():
    p = parse_profile("hooks_disabled: block-tests\n")
    assert decide_test_edit(call("Write", IMPL, file_path="tests/test_x.py"), p, None, ROOT).allowed


# --- block-reads: implementer ---------------------------------------------------


@pytest.mark.parametrize(
    "c",
    [
        call("Read", IMPL, file_path="C:/proj/tests/test_x.py"),
        call("Grep", IMPL, pattern="assert", path="tests/"),
        call("Glob", IMPL, pattern="**/test_*.py", path="src"),
        call("Glob", IMPL, pattern="*.py", path="tests"),
        call("Bash", IMPL, command="cat tests/test_x.py"),
        call("Bash", IMPL, command="ls -la src && head -5 tests/test_x.py"),
        call("Bash", IMPL, command=r"type C:\proj\tests\test_x.py"),
    ],
)
def test_implementer_cannot_read_tests(c):
    v = decide_read(c, PROFILE, None, ROOT)
    assert not v.allowed
    assert v.message.startswith("lasagna:")


@pytest.mark.parametrize("tool", ["Grep", "Glob"])
@pytest.mark.parametrize("path", [None, "", ".", "C:/proj"])
def test_whole_repo_search_is_denied_to_blocked_agents(tool, path):
    inp = {"pattern": "x"} if path is None else {"pattern": "x", "path": path}
    v = decide_read(ToolCall(tool, inp, IMPL), PROFILE, None, ROOT)
    assert not v.allowed
    assert "narrow the search" in v.message


@pytest.mark.parametrize(
    "c",
    [
        call("Bash", IMPL, command="python -m pytest tests/test_x.py -x"),
        call("Read", IMPL, file_path="src/x.py"),
        call("Read", IMPL, file_path=".lasagna/contracts/FEAT-001.md"),
        call("Grep", IMPL, pattern="def ", path="src"),
    ],
)
def test_implementer_may_run_tests_and_read_code_and_contract(c):
    assert decide_read(c, PROFILE, None, ROOT).allowed


def test_block_test_reads_can_be_disabled():
    p = parse_profile(PROFILE_TEXT + "hooks_disabled: block-test-reads\n")
    assert decide_read(call("Read", IMPL, file_path="tests/test_x.py"), p, None, ROOT).allowed


PROFILE_TEXT = (
    "test_command_pattern: (pytest|python -m pytest)\n"
    "test_file_pattern: (^|/)tests?/\n"
    "source_path: src/\n"
)


# --- block-reads: test-writer ---------------------------------------------------


@pytest.mark.parametrize(
    "c",
    [
        call("Read", TW, file_path="src/app/logic.py"),
        call("Bash", TW, command="cat src/app/logic.py"),
        call("Grep", TW, pattern="def", path="src"),
        call("Glob", TW, pattern="src/**/*.py", path="tests"),
        call("Grep", TW, pattern="def"),
    ],
)
def test_test_writer_cannot_read_code_in_tdd_loop(c):
    assert not decide_read(c, PROFILE, state(phase="tdd-loop"), ROOT).allowed


def test_test_writer_may_read_code_while_characterizing():
    c = call("Read", TW, file_path="src/app/logic.py")
    assert decide_read(c, PROFILE, state(phase="characterize"), ROOT).allowed


@pytest.mark.parametrize(
    "path", ["tests/test_x.py", "src/tests/test_y.py", ".lasagna/contracts/F.md", "docs/context/INDEX.md"]
)
def test_test_writer_may_read_tests_contract_and_docs(path):
    assert decide_read(call("Read", TW, file_path=path), PROFILE, state(), ROOT).allowed


def test_test_writer_may_run_the_suite():
    c = call("Bash", TW, command="python -m pytest tests/test_x.py")
    assert decide_read(c, PROFILE, state(), ROOT).allowed


def test_code_read_block_needs_source_path():
    p = parse_profile("test_file_pattern: (^|/)tests/\n")
    assert decide_read(call("Read", TW, file_path="src/x.py"), p, state(), ROOT).allowed
    assert decide_read(call("Grep", TW, pattern="x"), p, state(), ROOT).allowed


def test_block_code_reads_can_be_disabled():
    p = parse_profile(PROFILE_TEXT + "hooks_disabled: block-code-reads\n")
    assert decide_read(call("Read", TW, file_path="src/x.py"), p, state(), ROOT).allowed


@pytest.mark.parametrize("agent", ["lasagna:referee", "lasagna:adversarial-reviewer"])
def test_other_agents_read_freely(agent):
    for c in (call("Read", agent, file_path="tests/test_x.py"), call("Read", agent, file_path="src/x.py")):
        assert decide_read(c, PROFILE, state(), ROOT).allowed


def test_main_thread_with_no_role_reads_freely():
    assert decide_read(call("Grep", pattern="x"), PROFILE, state("none"), ROOT).allowed


# --- unreadable payload (BR-5) --------------------------------------------------


def test_unreadable_payload_denied_only_for_blocked_roles():
    v = decide_unreadable("block-test-edits", PROFILE, state(IMPL))
    assert not v.allowed and "payload" in v.message
    assert not decide_unreadable("block-reads", PROFILE, state(TW, "tdd-loop")).allowed
    assert decide_unreadable("block-reads", PROFILE, state(TW, "characterize")).allowed
    assert decide_unreadable("block-test-edits", PROFILE, state("none")).allowed
    assert decide_unreadable("block-reads", PROFILE, None).allowed
