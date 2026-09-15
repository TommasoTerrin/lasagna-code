---
description: Set lasagna up in the current project - detect the stack, write the profile, create the directories, and report exactly what was added.
argument-hint: "[python|typescript|jvm|dotnet]"
---

Bootstrap the harness here. Idempotent: safe to run again, never overwrites an
existing file.

Stack hint from the user (may be empty): $ARGUMENTS

## 1. Detect the project

Look before you ask:

```bash
ls -la
cat pyproject.toml package.json pom.xml build.gradle* *.csproj 2>/dev/null | head -60
ls -d tests test src app lib 2>/dev/null
cat .gitignore 2>/dev/null | head -20
git log --oneline -5 2>/dev/null
```

Decide: language, test runner, package manager, where tests live, where the
domain core lives (or should live). If `$ARGUMENTS` names a stack, that wins.

**Is this greenfield or brownfield?** Existing source files with no `.lasagna/`
means brownfield, and step 4 matters.

## 2. Create the structure

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/init.sh" "${CLAUDE_PLUGIN_ROOT}/templates/stack/<detected>.md"
```

It prints `CREATED` / `EXISTS` / `SKIPPED` per item. Read that output — it is
what you report back, not a summary you invent.

## 3. Correct the profile against reality

The template is a starting point with plausible defaults, not the truth about
this project. Open `.lasagna/stack.md` and fix, at minimum:

- `test_command` — run it once and confirm it works.
- `core_path` — where the domain actually lives here. If the project has no
  layering yet, say so to the user and propose one rather than inventing a path
  that does not exist.
- `core_allowed_import` — add the project's own module prefixes and any pure
  third-party dependency you accept in the core.
- `test_path`, `test_file_pattern` — match the real layout.

Then verify the outcome patterns really match this runner:

```bash
<test_command> 2>&1 | tail -20
```

If the output does not match `pass_pattern`, fix the pattern now. A profile whose
patterns never match makes every red look like `unknown`, and `tdd-loop` refuses
to start the implementer on `unknown`.

## 4. Brownfield only — freeze the existing debt

On an existing codebase the core almost certainly violates the layering rules
already. Without a baseline the hook fires on every edit and becomes noise
everyone learns to ignore.

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/onion-baseline.sh"
```

Existing violations are grandfathered; only new ones block from then on. Commit
the baseline file: its diff is how a reviewer sees debt being added instead of
paid down.

Tell the user how many violations were recorded. That number is the honest size
of the layering debt, and it is worth saying out loud once.

## 5. Report

```
lasagna initialised in <project>

created:   <only what init.sh actually created>
existing:  <what was already there>
profile:   <language> / <test runner> / <package manager>
core:      <core_path entries>
baseline:  <n violations grandfathered>  |  not needed (greenfield)

verify:    <test_command> runs clean
next:      /lasagna <what you want to build>
```

If the profile could not be written, say plainly that **every guardrail is
inactive** until it exists. That is the one failure mode of this harness that is
invisible from the inside, and it is worth being blunt about.

## Notes

- Restart Claude Code after the first init: hooks load at session start.
- `.lasagna/state/` goes in `.gitignore` (init.sh does it); everything else
  under `.lasagna/` is committed.
- To turn a guardrail off, add `hooks_disabled: onion` to the profile. Names:
  `block-tests`, `onion`, `test-result`, `budget`, `precompact`,
  `session-status`.
- For a monorepo where the harness should live under one package rather than the
  repo root, set `LASAGNA_DIR` to that package's `.lasagna` path.
