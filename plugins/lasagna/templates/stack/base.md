# Stack profile — key reference

The profile lives at `.lasagna/stack.md` in the target project and is committed.
Copy the variant for your language from this directory (`python.md`,
`typescript.md`, `jvm.md`, `dotnet.md`) and adjust the values.

Scripts read the `key: value` lines that start at column zero. Surrounding prose
is for humans and is ignored. Repeatable keys (`test_path`, `source_path`) may
appear many times; each occurrence adds a value. The first non-empty value of a
key wins, so an empty placeholder never shadows a value set further down.

**Without this file the hooks degrade to silent no-ops.** The harness looks armed
and blocks nothing. `/lasagna-init` creates it.

The profile describes how the project **runs**. How its code is **organised** —
separation level, where core and shell live, conventions — is in
`.lasagna/architecture.md`, which no hook reads.

## Keys

| Key | What it does |
|---|---|
| `language`, `runtime`, `package_manager` | documentation only; helps agents pick idioms |
| `test_command` | how to run the whole suite |
| `test_command_pattern` | regex identifying a test run in a Bash command. A matching command is always allowed, and its outcome is classified |
| `fail_compile_pattern` | regex marking a compile/import failure — checked first |
| `fail_assert_pattern` | regex marking an assertion failure |
| `fail_generic_pattern` | regex marking any other failure |
| `pass_pattern` | regex marking success — checked last |
| `test_path` | repeatable; where tests live, for traceability scanning |
| `test_file_pattern` | regex identifying a test file: the implementer may neither write nor read one |
| `source_path` | repeatable; where production code lives: the test-writer may not read it during `tdd-loop`. Without it that block is off |
| `typecheck_command`, `lint_command` | optional |
| `mutation_command` | optional; if absent, adversarial-review reports an explicit TODO instead of staying silent |
| `budget_core` | implementer attempts per criterion on core tests before escalation; default 3 |
| `budget_shell` | the same for shell and integration tests; default 5 |
| `budget_bugfix` | the same in the bugfix flow; default 5 |
| `git_host`, `issue_cli` | optional; `gh` is used when present, never required |
| `bugfix_automerge` | `false` by default. With `true`, a fully green bugfix within budget may close without a human gate. Turning it on is a human decision taken once per project |
| `adr_dir` | where ADRs live; default `docs/adr`. Change it when the project already uses that path for something else |
| `context_dir` | project context: `INDEX.md`, one glossary per bounded context, `structure.md`; default `docs/context` |
| `hooks_disabled` | comma-separated guardrails to switch off: `block-tests`, `block-test-reads`, `block-code-reads`, `test-result`, `budget`, `precompact`, `session-status`. Empty by default |

Patterns are POSIX extended regexes, as `grep -E` reads them; classes like
`[[:space:]]` work. They are applied line by line (`^` and `$` match at each line).

## v1 profiles

A v1 profile keeps working: `budget_domain` and `budget_adapter` are read as
`budget_core` and `budget_shell`; `core_path`, `core_allowed_import`,
`core_import_pattern` and `core_forbidden_pattern` are ignored (layering is no
longer checked mechanically); `context_file` without `context_dir` is used as
the only context file. The session-start line suggests updating the profile.

## Fitting an existing project

**`adr_dir` and `context_dir`** are the only paths that can realistically
collide with an existing layout. `.lasagna/` itself is fixed — a dotdir does not
clash with anything. For a monorepo where the harness should live under one
package instead of the repo root, set the `LASAGNA_DIR` environment variable.

**`hooks_disabled`** turns individual guardrails off: a project whose tests are
co-located with the code in a way `test_file_pattern` cannot express might turn
off `block-code-reads`, for instance, and keep everything else.

## Classification order

`fail_compile` → `fail_assert` → `fail_generic` → `pass` → `unknown`.

The regexes are applied to the command's output, so a test asserting on a string
like `ModuleNotFoundError` can still be misclassified. The result is a hint for
the referee, never a verdict.
