# Stack profile — TypeScript / Node

Copy to `.lasagna/stack.md` and adjust. Key reference: `base.md`.

language: typescript
runtime: node-22
package_manager: pnpm

## Commands

test_command: pnpm vitest run
test_command_pattern: (vitest|jest|pnpm test|npm test|yarn test)
typecheck_command: pnpm tsc --noEmit
lint_command: pnpm eslint .
mutation_command: pnpm stryker run

## Test outcome classification

fail_compile_pattern: (Cannot find module|TS[0-9]{4}|SyntaxError|ReferenceError|is not defined)
fail_assert_pattern: (AssertionError|expected .* to (be|equal)|toBe\(|toEqual\()
fail_generic_pattern: ([0-9]+ failed|FAIL |Tests +[0-9]+ failed)
pass_pattern: (Tests +[0-9]+ passed|[0-9]+ passing|✓ )

## Paths

test_path: tests/
test_path: src/
test_file_pattern: \.(test|spec)\.[jt]sx?$|(^|/)__tests__/|(^|/)tests?/

Where production code lives: the test-writer may not read it during tdd-loop.

source_path: src/

## Budget and closing

budget_core: 3
budget_shell: 5
budget_bugfix: 5
git_host: github
issue_cli: gh
bugfix_automerge: false

## Project layout

adr_dir: docs/adr
context_dir: docs/context

## Guardrails to switch off

Empty means all active. Names: block-tests, block-test-reads, block-code-reads,
test-result, budget, precompact, session-status.

hooks_disabled: