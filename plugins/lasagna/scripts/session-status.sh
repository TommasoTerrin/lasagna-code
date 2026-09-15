#!/usr/bin/env sh
# SessionStart.
#
# Prints one line about the harness. It exists for a single failure mode: the
# worst thing a guardrail system can do is look armed while protecting nothing.
# Without the stack profile every hook exits silently, and nothing anywhere says
# so. This makes that state impossible to miss.
#
# Silent in projects that do not use lasagna: no .lasagna/ directory, no output.
# A hook that nags in unrelated projects gets uninstalled.
set -u

. "$(dirname "$0")/lib.sh"

lasagna_hook_enabled "session-status" || exit 0

dir=$(lasagna_dir)
[ -d "$dir" ] || exit 0

profile=$(lasagna_profile_path)
if [ ! -f "$profile" ]; then
  cat <<EOF
lasagna: $dir/ exists but there is no stack profile at $profile.

Every guardrail is INACTIVE right now — test-write blocking, layering checks,
test-outcome capture and the cycle budget all read that file and exit quietly
without it. The harness looks armed and blocks nothing.

Run /lasagna-init to create it.
EOF
  exit 0
fi

state=$(lasagna_state_path 2>/dev/null) || {
  printf 'lasagna: ready (%s). No feature in progress — /lasagna to start one.\n' "$(profile_get language 2>/dev/null || printf 'profile loaded')"
  exit 0
}

esc=$(state_get escalation 2>/dev/null || printf 'none')
role=$(state_get active_role 2>/dev/null || printf 'none')

printf 'lasagna: %s | phase %s | cycles %s/%s | last test %s\n' \
  "$(state_get feature_id 2>/dev/null)" \
  "$(state_get phase 2>/dev/null)" \
  "$(state_get cycles_used 2>/dev/null)" \
  "$(state_get budget_max 2>/dev/null)" \
  "$(state_get last_test_result 2>/dev/null)"

if [ -n "$esc" ] && [ "$esc" != "none" ]; then
  printf '  ESCALATION PENDING: %s\n' "$esc"
  printf '  No agent proceeds until a human decides. /lasagna-status for detail.\n'
fi

if [ -n "$role" ] && [ "$role" != "none" ]; then
  printf '  active_role is "%s" with no subagent running — state left dirty by an\n' "$role"
  printf '  interrupted session. Clear it: sh scripts/set-state.sh active_role none\n'
fi

snap="${state%.state.md}.precompact.md"
if [ -f "$snap" ] && [ "$snap" -nt "$state" ]; then
  printf '  A compaction snapshot is newer than the state: read %s first.\n' "$snap"
fi

exit 0
