"""Budget per criterion (AC-V2-008), outcome classification, traceability, status text."""

import pytest

from lasagna_lib.core.budget import count_cycle
from lasagna_lib.core.classify import Outcome, classify_output, is_test_command, record_outcome
from lasagna_lib.core.profile import parse_profile
from lasagna_lib.core.state import state_get
from lasagna_lib.core.status import render_precompact, render_session_status, render_snapshot
from lasagna_lib.core.traceability import render_trace, trace

NOW = "2026-10-07T10:00:00Z"
IMPL = "plugin:lasagna:implementer"


def make_state(**kv):
    base = {
        "feature_id": "FEAT-001",
        "flow": "official",
        "phase": "tdd-loop",
        "layer": "core",
        "budget_max": "3",
        "cycles_used": "0",
        "active_role": "implementer",
        "last_test_result": "red-assertion",
        "escalation": "none",
    }
    base.update(kv)
    head = "".join(f"{k}: {v}\n" for k, v in base.items())
    return head + "\n## Checkpoint\n\n## Cycle log\n\n| when | role | outcome |\n|---|---|---|\n"


EMPTY = parse_profile("")


# --- budget -------------------------------------------------------------------


def test_red_cycle_increments_without_escalation():
    r = count_cycle(make_state(cycles_used="1"), IMPL, EMPTY, NOW)
    assert state_get(r.state_text, "cycles_used") == "2"
    assert state_get(r.state_text, "escalation") == "none"
    assert state_get(r.state_text, "active_role") == "none"
    assert f"| {NOW} | implementer | red-assertion |" in r.state_text
    assert r.message == "lasagna: implementer cycle 2/3 (last outcome: red-assertion)\n"


def test_spent_budget_escalates():
    r = count_cycle(make_state(cycles_used="2"), IMPL, EMPTY, NOW)
    assert state_get(r.state_text, "cycles_used") == "3"
    assert state_get(r.state_text, "escalation") == (
        "budget-spent: 3/3 cycles used, last outcome red-assertion"
    )
    assert "BUDGET SPENT" in r.message


def test_green_closes_the_criterion_and_resets_the_count():
    r = count_cycle(make_state(cycles_used="2", last_test_result="green"), IMPL, EMPTY, NOW)
    assert state_get(r.state_text, "cycles_used") == "0"
    assert state_get(r.state_text, "escalation") == "none"
    assert "| implementer | green (closed in 3/3) |" in r.state_text
    assert "criterion closed" in r.message


def test_closing_three_criteria_never_escalates_the_fourth_first_red():
    # v1 bug (P6): the count grew across criteria, so this red escalated at once.
    s = make_state(last_test_result="green")
    for _ in range(3):
        s = count_cycle(s, IMPL, EMPTY, NOW).state_text
    s = s.replace("last_test_result: green", "last_test_result: red-assertion")
    r = count_cycle(s, IMPL, EMPTY, NOW)
    assert state_get(r.state_text, "cycles_used") == "1"
    assert state_get(r.state_text, "escalation") == "none"


@pytest.mark.parametrize(
    "state_kv,profile,expected",
    [
        ({"layer": "core"}, "", "3"),
        ({"layer": "shell"}, "", "5"),
        ({"layer": "domain"}, "budget_domain: 4\n", "4"),
        ({"layer": "adapter"}, "budget_adapter: 6\n", "6"),
        ({"layer": "core"}, "budget_core: 2\nbudget_domain: 9\n", "2"),
        ({"flow": "bugfix", "layer": "core"}, "budget_bugfix: 7\n", "7"),
        ({"layer": "core", "budget_max": "0"}, "", "3"),
    ],
)
def test_missing_budget_is_derived(state_kv, profile, expected):
    s = make_state(budget_max="", **{k: v for k, v in state_kv.items() if k != "budget_max"})
    if "budget_max" in state_kv:
        s = s.replace("budget_max: \n", f"budget_max: {state_kv['budget_max']}\n")
    r = count_cycle(s, IMPL, parse_profile(profile), NOW)
    assert state_get(r.state_text, "budget_max") == expected


@pytest.mark.parametrize("agent", ["lasagna:test-writer", "lasagna:referee"])
def test_other_agents_are_logged_but_cost_nothing(agent):
    r = count_cycle(make_state(cycles_used="1"), agent, EMPTY, NOW)
    assert state_get(r.state_text, "cycles_used") == "1"
    assert f"| {agent.split(':')[1]} | red-assertion |" in r.state_text
    assert r.message == ""


def test_unrelated_agent_or_disabled_budget_changes_nothing():
    s = make_state()
    assert count_cycle(s, "general-purpose", EMPTY, NOW).state_text == s
    assert count_cycle(s, IMPL, parse_profile("hooks_disabled: budget\n"), NOW).state_text == s


# --- classification --------------------------------------------------------------

PY = parse_profile(
    "test_command_pattern: (pytest|python -m pytest)\n"
    "fail_compile_pattern: (ModuleNotFoundError|ImportError)\n"
    "fail_assert_pattern: (AssertionError|^E +assert)\n"
    "fail_generic_pattern: ([0-9]+ failed|ERROR)\n"
    "pass_pattern: ([0-9]+ passed)\n"
)


@pytest.mark.parametrize(
    "output,expected",
    [
        ("E   ModuleNotFoundError: x\n1 failed", Outcome.RED_COMPILE),
        ("E       assert 1 == 2\n1 failed", Outcome.RED_ASSERTION),
        ("1 failed, 2 passed", Outcome.RED_GENERIC),
        ("3 passed in 0.1s", Outcome.GREEN),
        ("nothing useful", Outcome.UNKNOWN),
    ],
)
def test_classification_order(output, expected):
    assert classify_output(output, PY) is expected


def test_test_command_recognition():
    assert is_test_command("python -m pytest -x", PY)
    assert not is_test_command("cat x", PY)
    assert not is_test_command("pytest", EMPTY)


def test_record_outcome_writes_four_keys():
    text, out = record_outcome("a: 1\n", Outcome.UNKNOWN, "pytest", NOW)
    assert state_get(text, "last_test_result") == "unknown"
    assert state_get(text, "last_test_command") == "pytest"
    assert state_get(text, "last_test_at") == NOW
    assert state_get(text, "updated") == NOW
    assert out.startswith("lasagna: test outcome = unknown (command: pytest)\n")
    assert "pass_/fail_ patterns" in out


# --- traceability -----------------------------------------------------------------


def test_trace_both_directions():
    spec = "AC-FEAT-001-001 AC-FEAT-001-002"
    r = trace(spec, ["# AC-FEAT-001-001", "# AC-FEAT-001-009"])
    assert r.missing == ("AC-FEAT-001-002",)
    assert r.orphans == ("AC-FEAT-001-009",)
    out = render_trace(r, "FEAT-001.md", ["tests/"], True)
    assert out.exit_code == 1
    assert "Criteria with NO test (1):" in out.stderr
    assert "ORPHAN references in tests (1):" in out.stderr


def test_trace_ok_and_no_ids():
    ok = render_trace(trace("AC-X-001", ["AC-X-001"]), "F.md", ["tests/"], True)
    assert ok.exit_code == 0 and "OK: no uncovered criteria" in ok.stdout
    none = render_trace(trace("no ids", []), "F.md", ["tests/"], False)
    assert none.exit_code == 1 and "WARNING" in none.stderr and "no IDs" in none.stderr


# --- status text --------------------------------------------------------------------


def test_status_without_profile_says_inactive_only():
    out = render_session_status(".lasagna", None, None, None, False, "/usr/bin/python3")
    assert "INACTIVE" in out and "/lasagna-init" in out
    assert "python" not in out.split("INACTIVE")[0].lower().replace("lasagna", "")


def test_status_lines():
    s = make_state(escalation="budget-spent: 3/3", active_role="implementer")
    out = render_session_status(
        ".lasagna", "core_path: src/\n", s, ".lasagna/state/FEAT-001.state.md", True, "/py"
    )
    assert "lasagna: python /py" in out
    assert "lasagna: FEAT-001 | phase tdd-loop | cycles 0/3 | last test red-assertion" in out
    assert "ESCALATION PENDING" in out
    assert "run.sh\" set-state active_role none" in out
    assert "FEAT-001.precompact.md" in out
    assert "v1 profile" in out and "core_path" in out


def test_status_ready_without_state():
    out = render_session_status(".lasagna", "language: python\n", None, None, False, None)
    assert out == "lasagna: ready (python). No feature in progress — /lasagna to start one.\n"


def test_precompact_texts():
    s = make_state() + "AC-FEAT-001-001: open\n- [t] cp\n"
    assert render_snapshot(s, "auto", NOW).startswith(f"# Pre-compaction snapshot\n\nwhen:   {NOW}\nreason: auto\n\n")
    out = render_precompact(s, "st", "snap", "auto")
    assert "phase:      tdd-loop" in out and "AC-FEAT-001-001: open" in out and "- [t] cp" in out
    assert render_precompact(None, None, None, "manual").startswith("lasagna: no active phase state")
