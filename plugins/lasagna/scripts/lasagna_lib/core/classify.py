"""Test outcome classification.

The hook knows no test runner: it applies the project's profile patterns, in a
fixed order, to the output of the command. A test that asserts on a string like
"ModuleNotFoundError" can still be misclassified — the result is a hint for the
referee, never a verdict.
"""

from __future__ import annotations

from enum import Enum
from typing import Tuple

from .profile import Profile
from .state import state_set


class Outcome(str, Enum):
    GREEN = "green"
    RED_COMPILE = "red-compile"
    RED_ASSERTION = "red-assertion"
    RED_GENERIC = "red-generic"
    UNKNOWN = "unknown"


_ORDER = (
    ("fail_compile_pattern", Outcome.RED_COMPILE),
    ("fail_assert_pattern", Outcome.RED_ASSERTION),
    ("fail_generic_pattern", Outcome.RED_GENERIC),
    ("pass_pattern", Outcome.GREEN),
)


def is_test_command(command: str, profile: Profile) -> bool:
    pattern = profile.pattern("test_command_pattern")
    return bool(pattern and pattern.search(command))


def classify_output(output: str, profile: Profile) -> Outcome:
    for key, outcome in _ORDER:
        pattern = profile.pattern(key)
        if pattern and pattern.search(output):
            return outcome
    return Outcome.UNKNOWN


def record_outcome(state_text: str, outcome: Outcome, command: str, now: str) -> Tuple[str, str]:
    """New state text and the line to print."""
    text = state_set(state_text, "last_test_result", outcome.value)
    text = state_set(text, "last_test_command", command)
    text = state_set(text, "last_test_at", now)
    text = state_set(text, "updated", now)
    out = f"lasagna: test outcome = {outcome.value} (command: {command})\n"
    if outcome is Outcome.UNKNOWN:
        out += (
            "lasagna: could not classify the outcome. Check the pass_/fail_ patterns "
            "in .lasagna/stack.md before trusting this state.\n"
        )
    return text, out
