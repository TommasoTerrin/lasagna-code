# Stack profile — Python

Copy to `.lasagna/stack.md` and adjust. Key reference: `base.md`.

language: python
runtime: cpython-3.12
package_manager: uv

## Commands

test_command: uv run pytest
test_command_pattern: (pytest|uv run pytest|python -m pytest)
typecheck_command: uv run mypy src
lint_command: uv run ruff check
mutation_command: uv run mutmut run --paths-to-mutate src

## Test outcome classification

fail_compile_pattern: (ModuleNotFoundError|ImportError|SyntaxError|NameError|AttributeError: module)
fail_assert_pattern: (AssertionError|^E +assert|Failed: DID NOT RAISE)
fail_generic_pattern: ([0-9]+ failed|[0-9]+ error|FAILED|ERROR)
pass_pattern: ([0-9]+ passed|OK|no tests ran)

## Paths

test_path: tests/
test_file_pattern: (^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$|conftest\.py$

Where production code lives: the test-writer may not read it during tdd-loop.

source_path: src/

## Project layout

Change these if the project already uses these paths for something else.

adr_dir: docs/adr
context_dir: docs/context

## Budget and closing

budget_core: 3
budget_shell: 5
budget_bugfix: 5
git_host: github
issue_cli: gh
bugfix_automerge: false

## Guardrails to switch off

Empty means all active. Names: block-tests, block-test-reads, block-code-reads,
test-result, budget, precompact, session-status.

hooks_disabled:
