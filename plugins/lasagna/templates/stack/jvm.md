# Stack profile — Java / JVM

Copy to `.lasagna/stack.md` and adjust. Key reference: `base.md`.

language: java
runtime: jdk-21
package_manager: maven

## Commands

test_command: mvn -q test
test_command_pattern: (mvn .*test|gradle .*test|\./gradlew .*test)
typecheck_command: mvn -q compile
lint_command: mvn -q checkstyle:check
mutation_command: mvn -q org.pitest:pitest-maven:mutationCoverage

## Test outcome classification

fail_compile_pattern: (COMPILATION ERROR|cannot find symbol|package .* does not exist)
fail_assert_pattern: (AssertionFailedError|ComparisonFailure|expected: .* but was:)
fail_generic_pattern: (BUILD FAILURE|Tests run: [0-9]+, Failures: [1-9]|Errors: [1-9])
pass_pattern: (BUILD SUCCESS|Tests run: [0-9]+, Failures: 0, Errors: 0)

## Paths

test_path: src/test/
test_file_pattern: (^|/)src/test/|Test\.java$|Tests\.java$|IT\.java$

Where production code lives: the test-writer may not read it during tdd-loop.

source_path: src/main/

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