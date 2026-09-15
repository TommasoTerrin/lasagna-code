#!/usr/bin/env sh
# Records the layering violations that already exist in the core, so that from
# now on only new ones block. The ratchet: the debt is frozen, not forgiven.
#
#   sh scripts/onion-baseline.sh          # write the baseline
#   sh scripts/onion-baseline.sh --check  # report drift, write nothing
#
# Run it once when adopting lasagna on an existing codebase. Re-run it only
# after deliberately paying down debt — re-running it to silence a violation you
# just introduced defeats the entire point, and the diff on the baseline file
# makes that visible in review.
set -u

. "$(dirname "$0")/lib.sh"

check_only=0
[ "${1:-}" = "--check" ] && check_only=1

proj=$(lasagna_project_dir)
baseline="$(lasagna_dir)/onion-baseline.txt"
scanner="$(dirname "$0")/check-onion.sh"

[ -f "$(lasagna_profile_path)" ] || {
  printf 'lasagna: no stack profile at %s. Run /lasagna-init first.\n' "$(lasagna_profile_path)" >&2
  exit 2
}

core_paths=$(profile_get_all "core_path" 2>/dev/null || printf '')
[ -n "$core_paths" ] || {
  printf 'lasagna: the profile declares no core_path. Nothing to scan.\n' >&2
  exit 2
}

tmp="${TMPDIR:-/tmp}/lasagna-baseline.$$"
mkdir -p "$tmp" || exit 2
trap 'rm -rf "$tmp"' EXIT INT TERM

: > "$tmp/files"
for cp in $core_paths; do
  d="$proj/${cp%/}"
  [ -d "$d" ] || continue
  find "$d" -type f >> "$tmp/files" 2>/dev/null
done

if [ ! -s "$tmp/files" ]; then
  printf 'lasagna: no files found under the declared core_path entries (%s).\n' "$core_paths" >&2
  exit 2
fi

: > "$tmp/sigs"
scanned=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  scanned=$((scanned + 1))
  sh "$scanner" --scan "$f" >> "$tmp/sigs" 2>/dev/null
done < "$tmp/files"
sort -u "$tmp/sigs" -o "$tmp/sigs"

found=$(wc -l < "$tmp/sigs" | tr -d ' ')

# The baseline carries a comment header; comm needs signatures only, sorted.
if [ -f "$baseline" ]; then
  grep -v '^#' "$baseline" 2>/dev/null | grep -v '^[[:space:]]*$' | sort -u > "$tmp/base"
else
  : > "$tmp/base"
fi

if [ "$check_only" -eq 1 ]; then
  if [ ! -f "$baseline" ]; then
    printf 'lasagna: no baseline yet. %s violation(s) across %s file(s) would be recorded.\n' "$found" "$scanned"
    exit 1
  fi
  added=$(comm -23 "$tmp/sigs" "$tmp/base" | wc -l | tr -d ' ')
  fixed=$(comm -13 "$tmp/sigs" "$tmp/base" | wc -l | tr -d ' ')
  printf 'lasagna: baseline drift — %s new, %s fixed (%s recorded).\n' "$added" "$fixed" "$(wc -l < "$tmp/base" | tr -d ' ')"
  if [ "$fixed" -gt 0 ]; then
    printf '\nFixed since the baseline was written — re-run without --check to bank them:\n'
    comm -13 "$tmp/sigs" "$tmp/base" | sed 's/^/  - /'
  fi
  if [ "$added" -gt 0 ]; then
    printf '\nNew since the baseline:\n' >&2
    comm -23 "$tmp/sigs" "$tmp/base" | sed 's/^/  + /' >&2
    exit 1
  fi
  exit 0
fi

if [ -f "$baseline" ]; then
  previous=$(wc -l < "$tmp/base" | tr -d ' ')
  added=$(comm -23 "$tmp/sigs" "$tmp/base" | wc -l | tr -d ' ')
  fixed=$(comm -13 "$tmp/sigs" "$tmp/base" | wc -l | tr -d ' ')
  printf 'lasagna: baseline updated — was %s, now %s (%s new, %s fixed).\n' "$previous" "$found" "$added" "$fixed"
  if [ "$added" -gt 0 ]; then
    printf '\nWARNING: %s violation(s) are being newly grandfathered. If you did not\nmean to bank fresh debt, revert this file and fix them instead.\n' "$added" >&2
  fi
else
  printf 'lasagna: baseline created — %s violation(s) across %s file(s).\n' "$found" "$scanned"
fi

mkdir -p "$(dirname "$baseline")" 2>/dev/null
{
  printf '# lasagna layering baseline — pre-existing violations, grandfathered.\n'
  printf '# One signature per line: <path>|<kind>|<offending line, trimmed>.\n'
  printf '# Line numbers are deliberately absent: moving code does not un-grandfather\n'
  printf '# it, editing the offending line does. Commit this file.\n'
} > "$baseline.hdr"
grep -v '^#' "$tmp/sigs" > "$baseline.body" 2>/dev/null || : > "$baseline.body"
cat "$baseline.hdr" "$baseline.body" > "$baseline"
rm -f "$baseline.hdr" "$baseline.body"

printf '  written to %s\n' "$baseline"
printf '  commit it: it is the debt you agreed to freeze, and its diff is how\n'
printf '  reviewers see debt being added instead of paid down.\n'
