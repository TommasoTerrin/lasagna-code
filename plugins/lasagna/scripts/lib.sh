#!/usr/bin/env sh
# Shared helpers for lasagna hooks.
#
# No business logic here: only reading and writing "key: value" text files, and
# pulling string fields out of the JSON that hooks receive on stdin.
# POSIX sh plus grep/sed/awk — no jq, no interpreter. A guardrail that fails to
# start is not a guardrail, and at least one of jq/python/node is missing on
# most developer machines.

# --- paths ----------------------------------------------------------------

lasagna_project_dir() {
  printf '%s' "${CLAUDE_PROJECT_DIR:-$PWD}"
}

# The harness directory. Fixed at .lasagna/ because a dotdir cannot realistically
# collide with an existing project; LASAGNA_DIR overrides it for monorepos where
# the harness should live under one package instead of the repo root.
lasagna_dir() {
  if [ -n "${LASAGNA_DIR:-}" ]; then
    printf '%s' "${LASAGNA_DIR}"
  else
    printf '%s/.lasagna' "$(lasagna_project_dir)"
  fi
}

lasagna_profile_path() { printf '%s/stack.md' "$(lasagna_dir)"; }

# Project layout that CAN collide with an existing repo, so it is configurable.
lasagna_adr_dir() {
  _v=$(profile_get "adr_dir" 2>/dev/null || printf '')
  printf '%s/%s' "$(lasagna_project_dir)" "${_v:-docs/adr}"
}

lasagna_context_file() {
  _v=$(profile_get "context_file" 2>/dev/null || printf '')
  printf '%s/%s' "$(lasagna_project_dir)" "${_v:-CONTEXT.md}"
}

# The active phase state: LASAGNA_STATE_FILE if set, otherwise the most
# recently modified .state.md in <lasagna_dir>/state/.
lasagna_state_path() {
  if [ -n "${LASAGNA_STATE_FILE:-}" ] && [ -f "${LASAGNA_STATE_FILE}" ]; then
    printf '%s' "${LASAGNA_STATE_FILE}"
    return 0
  fi
  _d="$(lasagna_dir)/state"
  [ -d "$_d" ] || return 1
  _f=$(ls -1t "$_d"/*.state.md 2>/dev/null | head -n 1)
  [ -n "$_f" ] || return 1
  printf '%s' "$_f"
}

# --- reading key: value files ---------------------------------------------

# First NON-EMPTY value. Templates ship keys with empty placeholders, and an
# empty line reads as "unset" rather than as a value that shadows a later one —
# otherwise a leftover placeholder silently disarms whatever you configured
# below it.
kv_get() {
  [ -f "$1" ] || return 1
  sed -n "s/^$2:[[:space:]]*//p" "$1" | grep -v '^[[:space:]]*$' | head -n 1
}

kv_get_all() {
  [ -f "$1" ] || return 1
  sed -n "s/^$2:[[:space:]]*//p" "$1" | grep -v '^[[:space:]]*$'
}

profile_get()     { kv_get     "$(lasagna_profile_path)" "$1"; }
profile_get_all() { kv_get_all "$(lasagna_profile_path)" "$1"; }
state_get()       { _s=$(lasagna_state_path) || return 1; kv_get "$_s" "$1"; }

# --- hook switches --------------------------------------------------------

# A project can turn individual guardrails off in the profile:
#   hooks_disabled: onion, test-result
# Known names: block-tests, onion, test-result, budget, precompact,
# session-status. Returns 0 when the named hook should run.
lasagna_hook_enabled() {
  _d=$(profile_get "hooks_disabled" 2>/dev/null || printf '')
  [ -n "$_d" ] || return 0
  _d=$(printf '%s' "$_d" | tr -d '[:space:]')
  case ",$_d," in
    *",$1,"*) return 1 ;;
  esac
  return 0
}

# --- writing phase state --------------------------------------------------

# state_set <key> <value>: replaces the line if present, appends it if not.
state_set() {
  _s=$(lasagna_state_path) || return 1
  _t="$_s.tmp.$$"
  awk -v k="$1" -v v="$2" '
    BEGIN { done = 0 }
    !done && index($0, k ":") == 1 { print k ": " v; done = 1; next }
    { print }
    END { if (!done) print k ": " v }
  ' "$_s" > "$_t" && mv "$_t" "$_s"
}

# state_append <section> <line>: appends inside the named section (e.g.
# "## Checkpoint"), right before the next section. Appending at end of file
# would bury checkpoints and cycle logs inside the reference notes that close
# the template, where nobody reads them again.
state_append() {
  _s=$(lasagna_state_path) || return 1
  _t="$_s.tmp.$$"
  awk -v sec="$1" -v line="$2" '
    BEGIN { in_sec = 0; done = 0 }
    {
      if (!done && in_sec && ($0 ~ /^## / || $0 ~ /^---[[:space:]]*$/)) {
        print line
        done = 1
        in_sec = 0
      }
      print
      if (!done && $0 == sec) in_sec = 1
    }
    END { if (!done) { if (!in_sec) print sec; print line } }
  ' "$_s" > "$_t" && mv "$_t" "$_s"
}

lasagna_now() {
  date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date 2>/dev/null || printf 'unknown'
}

# Normalise a path: JSON-extracted paths carry doubled backslashes from JSON
# escaping, environment paths carry single ones.
lasagna_slash() {
  printf '%s' "$1" | sed 's|\\\\|/|g; s|\\|/|g'
}

# --- pulling fields out of the stdin JSON ---------------------------------

# json_values <blob> <key> -> EVERY string value for that key.
# Deliberately exhaustive rather than first-match: a forged "file_path" inside
# a file's content cannot hide the real one, because a hook decides on any
# occurrence. Errors therefore fall towards refusing, never towards allowing.
# Textual extraction, not a parser — see NOTE-parsing in the README.
json_values() {
  printf '%s' "$1" \
    | grep -o "\"$2\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" 2>/dev/null \
    | sed "s/^\"$2\"[[:space:]]*:[[:space:]]*\"//; s/\"$//"
}

json_first() {
  json_values "$1" "$2" | head -n 1
}
