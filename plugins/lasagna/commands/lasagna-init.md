---
description: Set lasagna up in the current project - check Python, detect the stack, write the profile, create the directories and the project context, and report exactly what was added.
argument-hint: "[python|typescript|jvm|dotnet]"
---

Bootstrap the harness here. Idempotent: safe to run again, never overwrites an
existing file.

Stack hint from the user (may be empty): $ARGUMENTS

## 1. Python first

The hooks are Python (standard library only, ≥ 3.9). Check which interpreter
they will use:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" python
```

It prints the path, found once and saved for this machine. If it fails, stop
and tell the user plainly: **without Python ≥ 3.9 every guardrail is inactive**,
and the blocking ones deny everything in a lasagna project. They can install
Python, or point lasagna at an existing one with
`run.sh python <path-to-python>`.

## 2. Detect the project

Look before you ask:

```bash
ls -la
cat pyproject.toml package.json pom.xml build.gradle* *.csproj 2>/dev/null | head -60
ls -d tests test src app lib docs 2>/dev/null
cat .gitignore 2>/dev/null | head -20
git log --oneline -5 2>/dev/null
```

Decide: language, test runner, package manager, where tests live, where
production code lives. If `$ARGUMENTS` names a stack, that wins.

**Is this greenfield or brownfield?** Existing source files with no `.lasagna/`
means brownfield, and step 5 matters.

## 3. Create the structure

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" init "${CLAUDE_PLUGIN_ROOT}/templates/stack/<detected>.md"
```

It prints `CREATED` / `EXISTS` / `SKIPPED` / `MISSING` / `SUGGEST` per item. Read
that output — it is what you report back, not a summary you invent. It creates
`.lasagna/` (profile, an empty `architecture.md`, `specs/`, `contracts/`,
`state/`), the `.gitignore` entry, and `docs/context/INDEX.md`.

## 4. Correct the profile against reality

The template is a starting point with plausible defaults, not the truth about
this project. Open `.lasagna/stack.md` and fix, at minimum:

- `test_command` — run it once and confirm it works.
- `test_path`, `test_file_pattern` — match the real layout. The implementer can
  neither write nor read what this pattern matches.
- `source_path` — where production code really lives. The test-writer cannot
  read it during the loop. A path that does not exist silently turns that block
  off; a path too wide (`.`) blocks the docs and the contract too.

Then verify the outcome patterns really match this runner:

```bash
<test_command> 2>&1 | tail -20
```

If the output does not match `pass_pattern`, fix the pattern now. A profile whose
patterns never match makes every red look like `unknown`, and `tdd-loop` refuses
to start the implementer on `unknown`.

## 5. Architecture: leave it for later, or detect it

`.lasagna/architecture.md` is created empty. Do not fill it here:

- **greenfield**: `grilling` asks the separation level on the first feature;
- **brownfield**: `reverse-spec-brownfield` detects the existing conventions
  and the human confirms them. lasagna follows them — it does not convert the
  project.

Say which of the two applies.

## 6. CLAUDE.md, only with consent

`init` prints a `SUGGEST` line for the project's `CLAUDE.md`, so that sessions
outside lasagna also know where the project context is. **Ask the user** before
adding it; add it only if they say yes.

## 7. Report

```
lasagna initialised in <project>

python:    <path> (<version>)
created:   <only what init actually created>
existing:  <what was already there>
profile:   <language> / <test runner> / <package manager>
code:      <source_path entries>    tests: <test_path entries>
arch:      to be decided by grilling | to be detected by reverse-spec
CLAUDE.md: line added | declined | already there

verify:    <test_command> runs clean
next:      /lasagna <what you want to build>
```

If the profile could not be written, say plainly that **every guardrail is
inactive** until it exists. That is the one failure mode of this harness that is
invisible from the inside, and it is worth being blunt about.

## Notes

- Restart Claude Code after the first init: hooks load at session start.
- `.lasagna/state/` goes in `.gitignore` (`init` does it); everything else
  under `.lasagna/` is committed.
- To turn a guardrail off, add it to `hooks_disabled:` in the profile. Names:
  `block-tests`, `block-test-reads`, `block-code-reads`, `test-result`,
  `budget`, `precompact`, `session-status`.
- For a monorepo where the harness should live under one package rather than the
  repo root, set `LASAGNA_DIR` to that package's `.lasagna` path.
