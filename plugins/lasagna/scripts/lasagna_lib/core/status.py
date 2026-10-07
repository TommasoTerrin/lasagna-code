"""Text shown at session start and before compaction.

These hooks take no decisions for the model: they keep the phase state visible,
because the worst thing a guardrail system can do is look armed while
protecting nothing.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .profile import legacy_keys, parse_profile
from .state import state_get

_INACTIVE = """lasagna: {dir}/ exists but there is no stack profile at {dir}/stack.md.

Every guardrail is INACTIVE right now — test-file blocking, test-outcome capture
and the cycle budget all read that file and exit quietly without it. The harness
looks armed and blocks nothing.

Run /lasagna-init to create it.
"""


def _v(state: str, key: str) -> str:
    return state_get(state, key) or ""


def render_session_status(
    lasagna_dir: str,
    profile_text: Optional[str],
    state_text: Optional[str],
    state_path: Optional[str],
    snapshot_newer: bool,
    python_path: Optional[str],
) -> str:
    if profile_text is None:
        return _INACTIVE.format(dir=lasagna_dir)

    profile = parse_profile(profile_text)
    lines: List[str] = []
    if python_path:
        lines.append(
            f"lasagna: python {python_path} "
            "(change: run.sh python <path> | run.sh python --reset)"
        )

    if state_text is None:
        lang = profile.get("language", "profile loaded")
        lines.append(f"lasagna: ready ({lang}). No feature in progress — /lasagna to start one.")
    else:
        s = state_text
        lines.append(
            f"lasagna: {_v(s, 'feature_id')} | phase {_v(s, 'phase')} | "
            f"cycles {_v(s, 'cycles_used')}/{_v(s, 'budget_max')} | "
            f"last test {_v(s, 'last_test_result')}"
        )
        esc = _v(s, "escalation")
        if esc and esc != "none":
            lines.append(f"  ESCALATION PENDING: {esc}")
            lines.append("  No agent proceeds until a human decides. /lasagna-status for detail.")
        role = _v(s, "active_role")
        if role and role != "none":
            lines.append(
                f'  active_role is "{role}" with no subagent running — state left dirty by an'
            )
            lines.append(
                "  interrupted session. Clear it: "
                'sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state active_role none'
            )
        if snapshot_newer and state_path:
            snap = re.sub(r"\.state\.md$", ".precompact.md", state_path)
            lines.append(f"  A compaction snapshot is newer than the state: read {snap} first.")

    legacy = legacy_keys(profile)
    if legacy:
        lines.append(
            f"lasagna: v1 profile keys found ({', '.join(legacy)}): they are mapped or "
            "ignored. Update .lasagna/stack.md from templates/stack/ when convenient."
        )
    return "\n".join(lines) + "\n"


def render_snapshot(state_text: str, reason: str, now: str) -> str:
    return f"# Pre-compaction snapshot\n\nwhen:   {now}\nreason: {reason}\n\n{state_text}"


_CRITERION = re.compile(r"^AC-[A-Za-z0-9-]+-[0-9]{3}:")


def render_precompact(
    state_text: Optional[str],
    state_path: Optional[str],
    snapshot_path: Optional[str],
    reason: str,
) -> str:
    if state_text is None:
        return f"lasagna: no active phase state in .lasagna/state/ (compaction: {reason}).\n"
    s = state_text
    criteria = [ln for ln in s.splitlines() if _CRITERION.match(ln)]
    checkpoints = [ln for ln in s.splitlines() if ln.startswith("- [")][-5:]
    return f"""lasagna: phase state pinned before compaction.

  state:    {state_path}
  snapshot: {snapshot_path}

Resume from here, not from what you remember of the conversation:

  feature:    {_v(s, 'feature_id')}
  flow:       {_v(s, 'flow')}
  phase:      {_v(s, 'phase')}
  layer:      {_v(s, 'layer')}
  slice:      {_v(s, 'current_slice')}
  cycles:     {_v(s, 'cycles_used')}/{_v(s, 'budget_max')}
  role:       {_v(s, 'active_role')}
  last test:  {_v(s, 'last_test_result')}
  escalation: {_v(s, 'escalation')}

Criteria:
{chr(10).join(criteria) if criteria else '  (none)'}

Checkpoints:
{chr(10).join(checkpoints) if checkpoints else '  (none)'}

Before any risky operation, write the next checkpoint into the phase state.
Before, not after.
"""
