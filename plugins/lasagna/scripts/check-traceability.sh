#!/usr/bin/env sh
# Traceability by ID, in both directions:
#   - no acceptance criterion without a test referencing it;
#   - no reference in the tests to a criterion the spec does not contain.
#
# Not a hook: called by hand, by adversarial-review, and at the PR gate.
#
#   sh scripts/check-traceability.sh [FEAT-NNN]
#
# With no argument it uses the most recent spec in .lasagna/specs/.
# Exit 0 if everything lines up, 1 if something is missing, 2 if no spec.
set -u

. "$(dirname "$0")/lib.sh"

proj=$(lasagna_project_dir)
specs="$proj/.lasagna/specs"

if [ "$#" -ge 1 ] && [ -n "${1:-}" ]; then
  spec="$specs/$1.md"
else
  spec=$(ls -1t "$specs"/*.md 2>/dev/null | head -n 1)
fi

if [ -z "${spec:-}" ] || [ ! -f "$spec" ]; then
  printf 'lasagna: spec not found (looked in %s).\n' "$specs" >&2
  exit 2
fi

ID_RE='AC-[A-Za-z0-9][A-Za-z0-9-]*-[0-9][0-9][0-9]'

tmp="${TMPDIR:-/tmp}/lasagna-trace.$$"
mkdir -p "$tmp" || exit 2
trap 'rm -rf "$tmp"' EXIT INT TERM

grep -oE "$ID_RE" "$spec" 2>/dev/null | sort -u > "$tmp/spec.ids"

paths=$(profile_get_all "test_path" 2>/dev/null || printf '')
[ -n "$paths" ] || paths="tests"

: > "$tmp/test.ids"
found_dir=0
for p in $paths; do
  d="$proj/${p%/}"
  [ -d "$d" ] || continue
  found_dir=1
  grep -rhoE "$ID_RE" "$d" 2>/dev/null >> "$tmp/test.ids"
done
sort -u "$tmp/test.ids" -o "$tmp/test.ids"

comm -23 "$tmp/spec.ids" "$tmp/test.ids" > "$tmp/missing"
comm -13 "$tmp/spec.ids" "$tmp/test.ids" > "$tmp/orphan"

n_spec=$(wc -l < "$tmp/spec.ids" | tr -d ' ')
n_miss=$(wc -l < "$tmp/missing"  | tr -d ' ')
n_orph=$(wc -l < "$tmp/orphan"   | tr -d ' ')

printf 'lasagna: traceability of %s\n' "$(basename "$spec")"
printf '  criteria in the spec:     %s\n' "$n_spec"
printf '  criteria covered by test: %s\n' "$((n_spec - n_miss))"

if [ "$found_dir" -eq 0 ]; then
  printf '  WARNING: none of the profile test_path entries exist (%s).\n' "$paths" >&2
fi

rc=0

if [ "$n_miss" -gt 0 ]; then
  rc=1
  printf '\nCriteria with NO test (%s):\n' "$n_miss" >&2
  sed 's/^/  - /' "$tmp/missing" >&2
  printf '\nEach line above is behaviour the spec promises and nobody verifies.\n' >&2
  printf 'Send them back to the test-writer, one at a time.\n' >&2
fi

if [ "$n_orph" -gt 0 ]; then
  rc=1
  printf '\nORPHAN references in tests (%s):\n' "$n_orph" >&2
  sed 's/^/  - /' "$tmp/orphan" >&2
  printf '\nThese IDs appear in tests but not in the spec: either the criterion\n' >&2
  printf 'was renamed (align the test) or the test verifies something nobody\n' >&2
  printf 'asked for (delete it, or add the criterion to the spec).\n' >&2
fi

if [ "$n_spec" -eq 0 ]; then
  rc=1
  printf '\nThe spec contains no IDs in the AC-<feature>-NNN format.\n' >&2
  printf 'Without IDs there is no traceability: re-read the spec template.\n' >&2
fi

[ "$rc" -eq 0 ] && printf '  OK: no uncovered criteria, no orphan tests.\n'
exit "$rc"
