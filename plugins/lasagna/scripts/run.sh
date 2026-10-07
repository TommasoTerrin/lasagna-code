#!/usr/bin/env sh
# The one shell script left in lasagna: find Python and hand over to lasagna.py.
#
#   run.sh hook <name>            a Claude Code hook (payload on stdin)
#   run.sh <command> [args]       set-state, check-traceability, init, status
#   run.sh python [--reset|<path>]  show, re-discover or set the interpreter
#
# Python is searched ONCE and its path saved (per machine, in the plugin's data
# directory, which survives plugin updates). block-reads runs on every
# Read/Grep/Glob/Bash call: probing for an interpreter each time would double
# the cost of every one of them.
#
# If no Python >= 3.9 exists, the guardrails that block FAIL CLOSED (exit 2).
# A hook that cannot start exits with some other code, which Claude Code treats
# as a non-blocking error — the guardrail would vanish without a word.
#
# On the hook path this script runs no external command except the Python
# candidates: no dirname, no cat. Only sh builtins.
set -u

case "$0" in
  */*) here=${0%/*} ;;
  *\\*) here=${0%\\*} ;;
  *) here=. ;;
esac
root=${CLAUDE_PLUGIN_ROOT:-$here/..}
ldir=${LASAGNA_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}/.lasagna}
cr=$(printf '\r')

# Projects that do not use lasagna: every hook stays silent. session-status
# still speaks when .lasagna/ exists without a profile — that state looks armed
# and blocks nothing, and someone has to say so.
if [ "${1:-}" = hook ] && [ ! -f "$ldir/stack.md" ]; then
  if [ "${2:-}" != session-status ] || [ ! -d "$ldir" ]; then
    exit 0
  fi
fi

if [ -n "${CLAUDE_PLUGIN_DATA:-}" ]; then
  saved="$CLAUDE_PLUGIN_DATA/python-path"
else
  saved="$root/.python-path"
fi

check='import sys; sys.exit(1) if sys.version_info < (3, 9) else print(sys.executable.replace(chr(92), "/"))'

# probe <command...>: prints the interpreter's absolute path if it is >= 3.9.
# The Microsoft Store stub and old versions print nothing or fail.
probe() {
  _out=$("$@" -c "$check" 2>/dev/null) || return 1
  _out=${_out%"$cr"}
  [ -n "$_out" ] || return 1
  printf '%s' "$_out"
}

save() {
  _d=${saved%/*}
  [ -d "$_d" ] || mkdir -p "$_d" 2>/dev/null
  printf '%s\n' "$py" > "$saved" 2>/dev/null || :
}

discover() {
  for _c in python3 python "py -3"; do
    # shellcheck disable=SC2086  # "py -3" must split into two words
    if py=$(probe $_c); then
      save
      return 0
    fi
  done
  py=
  return 1
}

missing() {
  _m='lasagna requires Python >= 3.9 (tried python3, python, py -3). Install it, or point lasagna at one with: run.sh python <path>, or disable lasagna in this project.'
  case "${1:-} ${2:-}" in
    "hook block-test-edits" | "hook block-reads")
      printf 'lasagna: %s\n' "$_m" >&2
      exit 2 ;;
    "hook session-status")
      printf 'lasagna: WARNING, every guardrail is INACTIVE. %s\n' "$_m"
      exit 0 ;;
    hook\ *)
      printf 'lasagna: %s\n' "$_m" >&2
      exit 0 ;;
    *)
      printf 'lasagna: %s\n' "$_m" >&2
      exit 1 ;;
  esac
}

py=
if [ -f "$saved" ]; then
  IFS= read -r py < "$saved" || :
  py=${py%"$cr"}
fi

if [ "${1:-}" = python ]; then
  case "${2:-}" in
    --reset)
      : > "$saved" 2>/dev/null || :
      discover || missing python ;;
    "")
      if [ -z "$py" ] || [ ! -f "$py" ]; then discover || missing python; fi ;;
    *)
      if ! py=$(probe "$2"); then
        printf 'lasagna: %s is not a working Python >= 3.9; nothing changed.\n' "$2" >&2
        exit 1
      fi
      save ;;
  esac
  printf '%s\n' "$py"
  exit 0
fi

if [ -z "$py" ] || [ ! -f "$py" ]; then
  discover || missing "$@"
fi

exec "$py" "$here/lasagna.py" "$@"
