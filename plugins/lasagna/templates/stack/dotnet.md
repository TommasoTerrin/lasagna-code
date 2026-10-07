# Stack profile — C# / .NET

Copy to `.lasagna/stack.md` and adjust. Key reference: `base.md`.

language: csharp
runtime: dotnet-8
package_manager: dotnet

## Commands

test_command: dotnet test
test_command_pattern: (dotnet test|dotnet .*vstest)
typecheck_command: dotnet build --no-restore
lint_command: dotnet format --verify-no-changes
mutation_command: dotnet stryker

## Test outcome classification

fail_compile_pattern: (error CS[0-9]{4}|Build FAILED)
fail_assert_pattern: (Assert\.|Expected:.*Actual:|ShouldBeEquivalentTo)
fail_generic_pattern: (Failed! *-|Failed: *[1-9]|error MSB)
pass_pattern: (Passed! *-|Failed: *0)

## Paths

test_path: tests/
test_file_pattern: \.Tests?/|Tests?\.cs$|Spec\.cs$

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