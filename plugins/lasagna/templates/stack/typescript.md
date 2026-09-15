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

core_path: src/domain/
core_path: src/ports/

## Layering rules

core_allowed_import: @/domain
core_allowed_import: ./domain
core_allowed_import: ../domain
core_allowed_import: @/ports
core_allowed_import: ./ports
core_allowed_import: ../ports
core_allowed_import: type

core_forbidden_pattern: Date\.now|new Date\(\)|performance\.now
core_forbidden_pattern: Math\.random|crypto\.randomUUID|randomBytes
core_forbidden_pattern: fetch\(|axios\.|\bfs\.|readFile|writeFile
core_forbidden_pattern: process\.env|console\.(log|error|warn)

## Budget and closing

budget_domain: 3
budget_adapter: 5
git_host: github
issue_cli: gh
bugfix_automerge: false

## Project layout

adr_dir: docs/adr
context_file: CONTEXT.md

## Guardrails to switch off

Empty means all active. Names: block-tests, onion, test-result, budget,
precompact, session-status.

hooks_disabled: