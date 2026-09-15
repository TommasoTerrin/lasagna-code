#!/usr/bin/env sh
# Layering rules on the core.
#
# Two modes:
#   (no args)      PostToolUse hook. Checks the file just written and blocks on
#                  NEW violations only.
#   --scan <file>  Prints this file's violation signatures, one per line. Used
#                  by onion-baseline.sh so the baseline and the hook can never
#                  disagree about what counts as a violation.
#
# Two mechanical checks:
#   1. import allowlist: inside the core you may only import what the profile
#      declares allowed. An infrastructure import is a violation.
#   2. purity: no I/O, clock, randomness or environment patterns in the core.
#
# The third layering rule ("every outside access goes through a port") has no
# check of its own: it follows from the other two. If the core cannot import
# infrastructure and cannot call the world directly, the only route left is an
# injected port. Ports are declared by the frozen contract.
#
# The ratchet: if <lasagna_dir>/onion-baseline.txt exists, violations listed
# there are grandfathered and only new ones block. That is what makes these
# rules usable on a legacy codebase, where the core already violates them and a
# hook that fires on every edit is a hook everyone learns to ignore.
set -u

. "$(dirname "$0")/lib.sh"

mode="hook"
if [ "${1:-}" = "--scan" ]; then
  mode="scan"
  target="${2:-}"
  [ -n "$target" ] || { printf 'usage: check-onion.sh --scan <file>\n' >&2; exit 2; }
fi

[ "$mode" = "scan" ] || lasagna_hook_enabled "onion" || exit 0

proj=$(lasagna_project_dir)
projn=$(lasagna_slash "$proj")

if [ "$mode" = "hook" ]; then
  input=$(cat)
  file=$(json_first "$input" "file_path")
  [ -n "$file" ] || exit 0
  norm=$(lasagna_slash "$file")
else
  norm=$(lasagna_slash "$target")
  case "$norm" in /*|?:/*) ;; *) norm="$projn/$norm" ;; esac
fi

rel=${norm#"$projn"/}

tmp="${TMPDIR:-/tmp}/lasagna-onion.$$"
mkdir -p "$tmp" 2>/dev/null || exit 0
trap 'rm -rf "$tmp"' EXIT INT TERM

# --- is the file in the core? ---------------------------------------------
in_core=0
profile_get_all "core_path" > "$tmp/core_paths" 2>/dev/null || : > "$tmp/core_paths"
while IFS= read -r cp; do
  [ -n "$cp" ] || continue
  cpn=$(lasagna_slash "$cp" | sed 's|/*$|/|')
  case "$rel/" in *"$cpn"*) in_core=1 ;; esac
done < "$tmp/core_paths"
[ "$in_core" -eq 1 ] || exit 0

# Tests are not subject to these rules, even if they live under the core.
tpat=$(profile_get "test_file_pattern" 2>/dev/null || printf '')
if [ -n "$tpat" ] && printf '%s' "$rel" | grep -qE "$tpat" 2>/dev/null; then
  exit 0
fi

[ -f "$norm" ] || exit 0

# --- scan: emit "<lineno>|<kind>|<trimmed line>" --------------------------
: > "$tmp/found"

profile_get_all "core_allowed_import" > "$tmp/allowed" 2>/dev/null || : > "$tmp/allowed"
if [ -s "$tmp/allowed" ]; then
  ipat=$(profile_get "core_import_pattern" 2>/dev/null || printf '')
  [ -n "$ipat" ] || ipat='^[[:space:]]*(from|import|use|using|#include)[[:space:]]|require[[:space:]]*\('

  grep -nE "$ipat" "$norm" > "$tmp/imports" 2>/dev/null || : > "$tmp/imports"
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    ok=0
    while IFS= read -r a; do
      [ -n "$a" ] || continue
      case "$line" in *"$a"*) ok=1; break ;; esac
    done < "$tmp/allowed"
    if [ "$ok" -eq 0 ]; then
      no=${line%%:*}
      txt=$(printf '%s' "${line#*:}" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
      printf '%s|import|%s\n' "$no" "$txt" >> "$tmp/found"
    fi
  done < "$tmp/imports"
fi

profile_get_all "core_forbidden_pattern" > "$tmp/forbidden" 2>/dev/null || : > "$tmp/forbidden"
while IFS= read -r fp; do
  [ -n "$fp" ] || continue
  grep -nE "$fp" "$norm" 2>/dev/null | while IFS= read -r line; do
    no=${line%%:*}
    txt=$(printf '%s' "${line#*:}" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    printf '%s|purity|%s\n' "$no" "$txt"
  done >> "$tmp/found"
done < "$tmp/forbidden"

sort -u "$tmp/found" -o "$tmp/found"

# --- scan mode: print signatures and stop ---------------------------------
# A signature carries no line number, so a violation that merely moves down the
# file stays grandfathered; editing the line itself makes it new again.
if [ "$mode" = "scan" ]; then
  while IFS='|' read -r no kind txt; do
    [ -n "${kind:-}" ] || continue
    printf '%s|%s|%s\n' "$rel" "$kind" "$txt"
  done < "$tmp/found"
  exit 0
fi

[ -s "$tmp/found" ] || exit 0

# --- hook mode: drop anything already in the baseline ---------------------
baseline="$(lasagna_dir)/onion-baseline.txt"
: > "$tmp/new"
grandfathered=0

while IFS='|' read -r no kind txt; do
  [ -n "${kind:-}" ] || continue
  sig="$rel|$kind|$txt"
  if [ -f "$baseline" ] && grep -Fxq "$sig" "$baseline" 2>/dev/null; then
    grandfathered=$((grandfathered + 1))
    continue
  fi
  printf '  [%s] line %s: %s\n' "$kind" "$no" "$txt" >> "$tmp/new"
done < "$tmp/found"

[ -s "$tmp/new" ] || exit 0

{
  printf 'lasagna: NEW layering violation in %s\n\n' "$rel"
  cat "$tmp/new"
  if [ "$grandfathered" -gt 0 ]; then
    printf '\n(%s pre-existing violation(s) in this file are grandfathered by the\nbaseline and were not reported.)\n' "$grandfathered"
  fi
  cat <<'EOF'

This file sits under a core_path declared in the stack profile. The core does
not import infrastructure and does not touch the world: no I/O, no clock, no
randomness, no environment.

What to do, in order of preference:

  1. If you need an outside capability, take it as a parameter or as a port the
     contract already declares. Time and IDs are the usual cases: "now" becomes
     a parameter, ID generation becomes a port.
  2. If the port is not in the contract, the contract is incomplete: stop, do
     not improvise the interface. The contract gets unfrozen and re-approved.
  3. If the code does not belong to the domain, move it to the adapter.
     Serialization, transport and persistence do not live in the core.

If a pattern is a false positive, fix core_forbidden_pattern or
core_allowed_import in the stack profile: the rule is argued in the profile, not
worked around in the code.

On a legacy codebase where the core already violates these rules, run
scripts/onion-baseline.sh once. Existing violations become the baseline and only
new ones block from then on.
EOF
} >&2
exit 2
