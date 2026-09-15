#!/usr/bin/env sh
# PreToolUse on Edit|Write|MultiEdit|NotebookEdit.
#
# Denies writes to test files while the running agent is the implementer. This
# is the mechanical half of context isolation: without it, "do not touch the
# tests" is a request, and a request is something an agent under pressure can
# talk itself out of.
#
# stdin: hook JSON. Exit 0 to allow, exit 2 with the reason on stderr to deny.
set -u

. "$(dirname "$0")/lib.sh"

lasagna_hook_enabled "block-tests" || exit 0

input=$(cat)

# --- is the running agent the implementer? --------------------------------
# agent_type is present only inside a subagent and is authoritative there.
# Outside one, fall back to active_role in the phase state.
agent=$(json_first "$input" "agent_type")

if [ -n "$agent" ]; then
  case "$agent" in
    *implementer*) ;;
    *) exit 0 ;;
  esac
else
  role=$(state_get "active_role" 2>/dev/null || printf 'none')
  [ "$role" = "implementer" ] || exit 0
fi

# --- is the path a test file? ---------------------------------------------
pattern=$(profile_get "test_file_pattern" 2>/dev/null || printf '')
if [ -z "$pattern" ]; then
  # Used when .lasagna/stack.md is missing or declares no pattern.
  pattern='(^|/)tests?/|(^|/)test_[^/]*\.|[._-]test\.|\.spec\.|(^|/)__tests__/|conftest\.|Test\.(java|kt|cs)$|Tests\.(java|kt|cs)$|(^|/)src/test/'
fi

paths=$(
  {
    json_values "$input" "file_path"
    json_values "$input" "notebook_path"
  } | sed 's|\\\\|/|g; s|\\|/|g'
)

[ -n "$paths" ] || exit 0

hit=$(printf '%s\n' "$paths" | grep -E "$pattern" 2>/dev/null | head -n 1)
[ -n "$hit" ] || exit 0

# --- deny -----------------------------------------------------------------
cat >&2 <<EOF
lasagna: write to a test file denied.

  file:  $hit
  agent: ${agent:-implementer (from active_role)}

The implementer cannot modify tests. The current test is the contract you have
to satisfy, not the obstacle to remove: changing it destroys the separation
between whoever specifies the behaviour and whoever implements it.

If you believe the test is wrong, you have two legitimate moves:

  1. If the code can pass the test as written, write that code. The minimum
     that turns it green, nothing more.
  2. If you believe the test contradicts the frozen contract, stop and say so
     in your final answer, quoting the contract line you think it violates.
     The referee decides between you and the test.

Do not route around this by renaming files, adding a parallel test, or putting
production code inside the test directory.
EOF
exit 2
