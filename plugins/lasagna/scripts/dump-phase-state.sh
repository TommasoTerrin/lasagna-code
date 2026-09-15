#!/usr/bin/env sh
# PreCompact.
#
# Before the context is compacted, pin the phase state to disk and reprint it.
# The phase state already lives in a file precisely for this: here we take a
# dated snapshot (so you can tell, later, what the agent knew at compaction
# time) and put the essentials back in front of a model that is about to
# restart with a much shorter context.
set -u

. "$(dirname "$0")/lib.sh"

lasagna_hook_enabled "precompact" || exit 0

input=$(cat 2>/dev/null || printf '{}')
reason=$(json_first "$input" "reason")
[ -n "$reason" ] || reason="unknown"

state=$(lasagna_state_path 2>/dev/null) || {
  printf 'lasagna: no active phase state in .lasagna/state/ (compaction: %s).\n' "$reason"
  exit 0
}

state_set "updated" "$(lasagna_now)"

snapshot="${state%.state.md}.precompact.md"
{
  printf '# Pre-compaction snapshot\n\n'
  printf 'when:   %s\n' "$(lasagna_now)"
  printf 'reason: %s\n\n' "$reason"
  cat "$state"
} > "$snapshot" 2>/dev/null

cat <<EOF
lasagna: phase state pinned before compaction.

  state:    $state
  snapshot: $snapshot

Resume from here, not from what you remember of the conversation:

  feature:    $(state_get feature_id 2>/dev/null)
  flow:       $(state_get flow 2>/dev/null)
  phase:      $(state_get phase 2>/dev/null)
  layer:      $(state_get layer 2>/dev/null)
  cycles:     $(state_get cycles_used 2>/dev/null)/$(state_get budget_max 2>/dev/null)
  role:       $(state_get active_role 2>/dev/null)
  last test:  $(state_get last_test_result 2>/dev/null)
  escalation: $(state_get escalation 2>/dev/null)

Criteria:
$(grep -E '^AC-[A-Za-z0-9-]+-[0-9]{3}:' "$state" 2>/dev/null || printf '  (none)')

Checkpoints:
$(grep -E '^- \[' "$state" 2>/dev/null | tail -n 5 || printf '  (none)')

Before any risky operation, write the next checkpoint into the phase state.
Before, not after.
EOF

exit 0
