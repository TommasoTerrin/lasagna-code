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

core_path: src/Domain/
core_path: src/Ports/

## Layering rules

core_allowed_import: .Domain
core_allowed_import: .Ports
core_allowed_import: System.Collections
core_allowed_import: System.Linq

core_forbidden_pattern: DateTime\.(Now|UtcNow)|DateTimeOffset\.(Now|UtcNow)|Stopwatch
core_forbidden_pattern: new Random|Guid\.NewGuid|RandomNumberGenerator
core_forbidden_pattern: File\.|Directory\.|Environment\.GetEnvironmentVariable
core_forbidden_pattern: HttpClient|Console\.Write

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