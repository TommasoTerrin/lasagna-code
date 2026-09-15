#!/usr/bin/env sh
# Write a key into the active phase state.
#
#   sh scripts/set-state.sh <key> <value>
#   sh scripts/set-state.sh --append "<line>"
#
# It exists because hooks read active_role from this file. Setting it by hand
# with an Edit works right up until someone gets the indentation wrong, and at
# that point the test-write block stops protecting anything without saying so.
set -u

. "$(dirname "$0")/lib.sh"

state=$(lasagna_state_path 2>/dev/null) || {
  printf 'lasagna: no phase state in %s/.lasagna/state/.\n' "$(lasagna_project_dir)" >&2
  printf 'Run /lasagna-init, or create one from templates/phase-state.md.\n' >&2
  exit 1
}

[ "$#" -ge 2 ] || { printf 'usage: set-state.sh <key> <value> | --append <line>\n' >&2; exit 1; }

if [ "$1" = "--append" ]; then
  state_append "## Checkpoint" "$2"
  state_set "updated" "$(lasagna_now)"
  printf 'lasagna: checkpoint added to %s\n' "$state"
  exit 0
fi

state_set "$1" "$2"
state_set "updated" "$(lasagna_now)"
printf 'lasagna: %s = %s  (%s)\n' "$1" "$2" "$state"
