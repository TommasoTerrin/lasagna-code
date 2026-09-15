#!/usr/bin/env sh
# SubagentStop on test-writer, implementer, referee.
#
# Logs the subagent outcome and counts cycles. A cycle is one implementer
# attempt: test-writer and referee are recorded but consume no budget. Once the
# budget is spent it writes escalation into the phase state, and from then on
# no lasagna skill starts another attempt.
set -u

. "$(dirname "$0")/lib.sh"

lasagna_hook_enabled "budget" || exit 0

input=$(cat)
agent=$(json_first "$input" "agent_type")

case "$agent" in
  *test-writer*)  role="test-writer"  ;;
  *implementer*)  role="implementer"  ;;
  *referee*)      role="referee"      ;;
  *)              exit 0              ;;
esac

lasagna_state_path >/dev/null 2>&1 || exit 0

last=$(state_get "last_test_result" 2>/dev/null || printf 'none')
state_append "## Cycle log" "| $(lasagna_now) | $role | $last |"
state_set "active_role" "none"
state_set "updated" "$(lasagna_now)"

[ "$role" = "implementer" ] || exit 0

used=$(state_get "cycles_used" 2>/dev/null || printf '0')
max=$(state_get "budget_max"  2>/dev/null || printf '')

case "$used" in ''|*[!0-9]*) used=0 ;; esac

if [ -z "$max" ] || [ -n "$(printf '%s' "$max" | tr -d '0-9')" ]; then
  layer=$(state_get "layer" 2>/dev/null || printf 'domain')
  if [ "$layer" = "domain" ]; then
    max=$(profile_get "budget_domain"  2>/dev/null || printf '3')
  else
    max=$(profile_get "budget_adapter" 2>/dev/null || printf '5')
  fi
  case "$max" in ''|*[!0-9]*) max=3 ;; esac
  state_set "budget_max" "$max"
fi

used=$((used + 1))
state_set "cycles_used" "$used"

printf 'lasagna: implementer cycle %s/%s (last outcome: %s)\n' "$used" "$max" "$last"

if [ "$used" -ge "$max" ] && [ "$last" != "green" ]; then
  state_set "escalation" "budget-spent: $used/$max cycles used, last outcome $last"
  cat <<EOF
lasagna: BUDGET SPENT. $used attempts out of $max, last outcome "$last".

Do not start a quiet fourth attempt. Stop and bring a human:
  - the acceptance criterion the loop is stuck on;
  - the referee's verdict, if one was requested;
  - the two or three hypotheses that explain why red will not close.

The phase state now has escalation set: clear it only after a human has decided
how to proceed.
EOF
fi

exit 0
