"""Cycle counting and escalation, per acceptance criterion (D10).

A cycle is one implementer attempt. test-writer and referee are logged but
consume no budget. The counter belongs to this hook alone: when the implementer
finishes green the criterion is closed and the count starts again from zero;
when the budget is spent without green, escalation is set and no lasagna skill
starts another attempt until a human decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .guards import Role, resolve_role
from .profile import Profile
from .state import state_append, state_get, state_int, state_set

_COUNTED = (Role.TEST_WRITER, Role.IMPLEMENTER, Role.REFEREE)

_SPENT_MSG = """lasagna: BUDGET SPENT. {used} attempts out of {max}, last outcome "{last}".

Do not start a quiet extra attempt. Stop and bring a human:
  - the acceptance criterion the loop is stuck on;
  - the referee's verdict, if one was requested;
  - the two or three hypotheses that explain why red will not close.

The phase state now has escalation set: clear it only after a human has decided
how to proceed.
"""


@dataclass(frozen=True)
class CycleResult:
    state_text: str
    message: str


def budget_for(state_text: str, profile: Profile) -> int:
    """budget_max from the state if valid, else from flow / layer and the profile."""
    current = state_get(state_text, "budget_max") or ""
    if current.isdigit() and int(current) >= 1:
        return int(current)
    if state_get(state_text, "flow") == "bugfix":
        return profile.int_value("budget_bugfix", default=5)
    if state_get(state_text, "layer") in ("shell", "adapter"):
        return profile.int_value("budget_shell", "budget_adapter", default=5)
    return profile.int_value("budget_core", "budget_domain", default=3)


def count_cycle(
    state_text: str, agent_type: Optional[str], profile: Profile, now: str
) -> CycleResult:
    if not profile.hook_enabled("budget"):
        return CycleResult(state_text, "")
    role = resolve_role(agent_type, None)
    if role not in _COUNTED:
        return CycleResult(state_text, "")

    last = state_get(state_text, "last_test_result") or "none"
    text = state_set(state_text, "active_role", "none")
    text = state_set(text, "updated", now)

    if role is not Role.IMPLEMENTER:
        text = state_append(text, "## Cycle log", f"| {now} | {role.value} | {last} |")
        return CycleResult(text, "")

    budget = budget_for(text, profile)
    text = state_set(text, "budget_max", str(budget))
    used = state_int(text, "cycles_used") + 1

    if last == "green":
        row = f"| {now} | implementer | green (closed in {used}/{budget}) |"
        text = state_append(text, "## Cycle log", row)
        text = state_set(text, "cycles_used", "0")
        msg = (
            f"lasagna: criterion closed in {used}/{budget} implementer cycle(s); "
            "cycles_used reset to 0\n"
        )
        return CycleResult(text, msg)

    text = state_append(text, "## Cycle log", f"| {now} | implementer | {last} |")
    text = state_set(text, "cycles_used", str(used))
    msg = f"lasagna: implementer cycle {used}/{budget} (last outcome: {last})\n"
    if used >= budget:
        reason = f"budget-spent: {used}/{budget} cycles used, last outcome {last}"
        text = state_set(text, "escalation", reason)
        msg += _SPENT_MSG.format(used=used, max=budget, last=last)
    return CycleResult(text, msg)
