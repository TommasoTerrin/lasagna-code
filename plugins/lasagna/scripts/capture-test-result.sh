#!/usr/bin/env sh
# PostToolUse on Bash.
#
# If the command was the project's test runner, classify the outcome and write
# it to the phase state. Two things depend on this: tdd-loop refuses to start
# the implementer until the state says red was actually observed, and the
# referee gets a classified failure instead of having to infer one.
#
# Stated approximation: classification applies the profile's regexes to the
# whole hook payload, not to an isolated output stream. A test asserting on a
# string like "ModuleNotFoundError" can be misclassified. This is a hint for
# the referee, never a verdict.
set -u

. "$(dirname "$0")/lib.sh"

lasagna_hook_enabled "test-result" || exit 0

input=$(cat)

cmd=$(json_first "$input" "command")
[ -n "$cmd" ] || exit 0

pattern=$(profile_get "test_command_pattern" 2>/dev/null || printf '')
[ -n "$pattern" ] || exit 0

printf '%s' "$cmd" | grep -qE "$pattern" 2>/dev/null || exit 0

lasagna_state_path >/dev/null 2>&1 || exit 0

matches() {
  _p=$(profile_get "$1" 2>/dev/null || printf '')
  [ -n "$_p" ] || return 1
  printf '%s' "$input" | grep -qE "$_p" 2>/dev/null
}

if   matches "fail_compile_pattern"; then result="red-compile"
elif matches "fail_assert_pattern";  then result="red-assertion"
elif matches "fail_generic_pattern"; then result="red-generic"
elif matches "pass_pattern";         then result="green"
else                                      result="unknown"
fi

state_set "last_test_result"  "$result"
state_set "last_test_command" "$cmd"
state_set "last_test_at"      "$(lasagna_now)"
state_set "updated"           "$(lasagna_now)"

printf 'lasagna: test outcome = %s (command: %s)\n' "$result" "$cmd"

if [ "$result" = "unknown" ]; then
  printf 'lasagna: could not classify the outcome. Check the pass_/fail_ patterns in .lasagna/stack.md before trusting this state.\n'
fi

exit 0
