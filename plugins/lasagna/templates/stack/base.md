# Stack profile — key reference

The profile lives at `.lasagna/stack.md` in the target project and is committed.
Copy the variant for your language from this directory (`python.md`,
`typescript.md`, `jvm.md`, `dotnet.md`) and adjust the values.

Scripts read the `key: value` lines that start at column zero. Surrounding prose
is for humans and is ignored. Repeatable keys (`core_path`, `core_allowed_import`,
`core_forbidden_pattern`, `test_path`) may appear many times; each occurrence adds
a value.

**Without this file the hooks degrade to silent no-ops.** The harness looks armed
and blocks nothing. `/lasagna-init` creates it.

## Keys

| Key | What it does |
|---|---|
| `language`, `runtime`, `package_manager` | documentation only; helps agents pick idioms |
| `test_command` | how to run the whole suite |
| `test_command_pattern` | regex identifying a test run in a Bash command, so the PostToolUse hook knows to classify the outcome |
| `fail_compile_pattern` | regex marking a compile/import failure — checked first |
| `fail_assert_pattern` | regex marking an assertion failure |
| `fail_generic_pattern` | regex marking any other failure |
| `pass_pattern` | regex marking success — checked last |
| `test_path` | repeatable; where tests live, for traceability scanning |
| `test_file_pattern` | regex identifying a test file, used by the write block |
| `core_path` | repeatable; the domain core, where layering rules apply |
| `core_allowed_import` | repeatable; import prefixes allowed inside the core. Everything else is a violation |
| `core_import_pattern` | regex identifying an import line; has a sensible default |
| `core_forbidden_pattern` | repeatable; patterns that make the core impure — I/O, clock, randomness, environment |
| `typecheck_command`, `lint_command` | optional |
| `mutation_command` | optional; if absent, adversarial-review reports an explicit TODO instead of staying silent |
| `budget_domain`, `budget_adapter` | implementer attempts before escalation |
| `git_host`, `issue_cli` | optional; `gh` is used when present, never required |
| `bugfix_automerge` | `false` by default. With `true`, a fully green bugfix within budget may close without a human gate. Turning it on is a human decision taken once per project |
| `adr_dir` | where ADRs live; default `docs/adr`. Change it when the project already uses that path for something else |
| `context_file` | the ubiquitous-language glossary; default `CONTEXT.md` |
| `hooks_disabled` | comma-separated guardrails to switch off: `block-tests`, `onion`, `test-result`, `budget`, `precompact`, `session-status`. Empty by default |

## Fitting an existing project

Three things adapt the harness to a repo that already has its own conventions:

**`adr_dir` and `context_file`** are the only paths that can realistically
collide with an existing layout. `.lasagna/` itself is fixed — a dotdir does not
clash with anything. For a monorepo where the harness should live under one
package instead of the repo root, set the `LASAGNA_DIR` environment variable.

**`hooks_disabled`** turns individual guardrails off. A project can keep
traceability and the cycle budget while switching off the layering check, for
instance, if it has no layered core to speak of.

**`onion-baseline.txt`**, written by `scripts/onion-baseline.sh`, grandfathers
the layering violations that already exist so only new ones block. Run it once
when adopting lasagna on a legacy codebase; without it, the check fires on every
edit and becomes noise everyone ignores.

## Classification order

`fail_compile` → `fail_assert` → `fail_generic` → `pass` → `unknown`.

The regexes are applied to the whole hook payload, not to an isolated output
stream, so a test asserting on a string like `ModuleNotFoundError` can be
misclassified. The result is a hint for the referee, never a verdict.
