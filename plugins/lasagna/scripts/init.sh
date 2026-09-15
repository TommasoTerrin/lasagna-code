#!/usr/bin/env sh
# Idempotent bootstrap of the harness inside a target project.
#
#   sh scripts/init.sh [<stack-template>]
#
# Creates only what is missing and reports every action as CREATED or EXISTS, so
# running it twice is safe and running it on an existing project tells you
# exactly what it touched. It never overwrites a file that is already there.
#
# <stack-template> is a path to one of templates/stack/*.md. If omitted, the
# stack profile is left for the caller to write — /lasagna-init picks the right
# template after detecting the project.
set -u

. "$(dirname "$0")/lib.sh"

proj=$(lasagna_project_dir)
dir=$(lasagna_dir)
tpl="${1:-}"

report() { printf '  %-8s %s\n' "$1" "$2"; }

printf 'lasagna: initialising in %s\n' "$proj"

for d in "$dir" "$dir/specs" "$dir/specs/archive" "$dir/contracts" "$dir/state"; do
  if [ -d "$d" ]; then
    report "EXISTS" "${d#"$proj"/}/"
  else
    mkdir -p "$d" && report "CREATED" "${d#"$proj"/}/"
  fi
done

# --- stack profile ---------------------------------------------------------
profile=$(lasagna_profile_path)
if [ -f "$profile" ]; then
  report "EXISTS" "${profile#"$proj"/}"
elif [ -n "$tpl" ] && [ -f "$tpl" ]; then
  cp "$tpl" "$profile" && report "CREATED" "${profile#"$proj"/}  (from $(basename "$tpl"))"
  printf '           review every value before trusting the guardrails\n'
else
  report "MISSING" "${profile#"$proj"/}  <-- guardrails stay INACTIVE until this exists"
fi

# --- gitignore -------------------------------------------------------------
gi="$proj/.gitignore"
entry="$(basename "$dir")/state/"
if [ -f "$gi" ] && grep -Fxq "$entry" "$gi" 2>/dev/null; then
  report "EXISTS" ".gitignore entry $entry"
else
  if [ -f "$gi" ] && [ -n "$(tail -c 1 "$gi" 2>/dev/null)" ]; then printf '\n' >> "$gi"; fi
  {
    printf '\n# lasagna phase state: local, per-feature, changes every cycle\n'
    printf '%s\n' "$entry"
  } >> "$gi"
  report "CREATED" ".gitignore entry $entry"
fi

# --- context file ----------------------------------------------------------
ctx=$(lasagna_context_file)
if [ -f "$ctx" ]; then
  report "EXISTS" "${ctx#"$proj"/}"
else
  report "SKIPPED" "${ctx#"$proj"/}  (domain-modeling creates it with the first term)"
fi

adr=$(lasagna_adr_dir)
if [ -d "$adr" ]; then
  report "EXISTS" "${adr#"$proj"/}/"
else
  report "SKIPPED" "${adr#"$proj"/}/  (created with the first ADR)"
fi

# --- verdict ---------------------------------------------------------------
printf '\n'
if [ -f "$profile" ]; then
  printf 'lasagna: ready. Guardrails active. Start with /lasagna <what you want>.\n'
  core=$(profile_get_all "core_path" 2>/dev/null | tr '\n' ' ')
  if [ -n "$core" ]; then
    printf '  core paths under layering rules: %s\n' "$core"
    printf '  on an existing codebase, run scripts/onion-baseline.sh once to\n'
    printf '  grandfather the violations that are already there.\n'
  fi
else
  printf 'lasagna: NOT ready. Write the stack profile before relying on anything.\n'
  exit 1
fi
