"""Profile and phase-state text handling: values in, values out, no mocks."""

import re

import pytest

from lasagna_lib.core.errors import PatternError
from lasagna_lib.core.profile import ere_to_python, legacy_keys, parse_kv, parse_profile
from lasagna_lib.core.state import state_append, state_get, state_int, state_set


def test_first_non_empty_value_wins():
    p = parse_profile("budget_core:\nbudget_core: 4\nbudget_core: 9\n")
    assert p.get("budget_core") == "4"
    assert p.get_all("budget_core") == ("4", "9")


def test_only_column_zero_keys_are_read_and_crlf_is_stripped():
    kv = parse_kv("  indented: no\nkey: value  \r\nprose line\n")
    assert kv == {"key": ("value",)}


def test_missing_key_gives_default():
    assert parse_profile("").get("x", "d") == "d"
    assert parse_profile("").get_all("x") == ()


def test_hooks_disabled_ignores_whitespace():
    p = parse_profile("hooks_disabled: block-tests , budget\n")
    assert not p.hook_enabled("block-tests")
    assert not p.hook_enabled("budget")
    assert p.hook_enabled("test-result")


def test_int_value_falls_back_to_legacy_key_then_default():
    assert parse_profile("budget_domain: 4\n").int_value("budget_core", "budget_domain", default=3) == 4
    assert parse_profile("budget_core: x\n").int_value("budget_core", default=3) == 3
    assert parse_profile("budget_core: 0\n").int_value("budget_core", default=3) == 3


@pytest.mark.parametrize(
    "ere,text,matches",
    [
        (r"^[[:space:]]*import", "   import os", True),
        (r"[[:digit:]]+ passed", "12 passed", True),
        (r"[^[:space:]x]y", " y", False),
        (r"[^[:space:]x]y", "ay", True),
        (r"[[:alpha:]]_", "a_", True),
        (r"[[:alnum:]]$", "_", False),
        (r"[]a]", "]", True),
    ],
)
def test_posix_classes_behave_like_grep_e(ere, text, matches):
    assert bool(re.search(ere_to_python(ere), text)) is matches


def test_invalid_regex_raises_pattern_error_naming_the_key():
    with pytest.raises(PatternError) as err:
        parse_profile("pass_pattern: (unclosed\n").pattern("pass_pattern")
    assert err.value.key == "pass_pattern"


def test_patterns_are_multiline():
    p = parse_profile("fail_assert_pattern: ^E +assert\n")
    assert p.pattern("fail_assert_pattern").search("first\nE   assert 1 == 2\n")


def test_legacy_keys_are_reported():
    p = parse_profile("core_path: src/domain/\nbudget_adapter: 5\ncontext_file: CONTEXT.md\n")
    assert legacy_keys(p) == ("core_path", "budget_adapter", "context_file")
    assert legacy_keys(parse_profile("context_file: C.md\ncontext_dir: docs/context\n")) == ()


STATE = """# Phase state

feature_id: FEAT-001
phase: tdd-loop
cycles_used: 2

## Checkpoint

- [t1] first

## Cycle log

| when | role | outcome |
|---|---|---|

---

## Allowed values
"""


def test_state_set_replaces_in_place_and_keeps_everything_else():
    out = state_set(STATE, "phase", "gate-pr")
    assert out == STATE.replace("phase: tdd-loop", "phase: gate-pr")


def test_state_set_appends_missing_key_at_the_end():
    out = state_set("a: 1", "b", "2")
    assert out == "a: 1\nb: 2\n"


def test_state_append_goes_before_the_next_section():
    out = state_append(STATE, "## Checkpoint", "- [t2] second")
    assert "- [t1] first\n- [t2] second\n\n## Cycle log" in out


def test_state_append_keeps_table_rows_contiguous_before_a_rule_line():
    out = state_append(STATE, "## Cycle log", "| t | implementer | green |")
    assert "|---|---|---|\n| t | implementer | green |\n\n---" in out


def test_state_append_into_empty_section():
    out = state_append("## Checkpoint\n\n## Next\n", "## Checkpoint", "- [t] a")
    assert out == "## Checkpoint\n- [t] a\n\n## Next\n"


def test_state_append_creates_missing_section():
    assert state_append("a: 1\n", "## Cycle log", "row") == "a: 1\n## Cycle log\nrow\n"


def test_state_get_and_int():
    assert state_get(STATE, "feature_id") == "FEAT-001"
    assert state_int(STATE, "cycles_used") == 2
    assert state_int("cycles_used: -1\n", "cycles_used") == 0
    assert state_int("cycles_used: x\n", "cycles_used") == 0
