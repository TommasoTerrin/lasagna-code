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

core_path: src/main/java/**/domain/
core_path: src/main/java/**/ports/

## Layering rules

core_allowed_import: .domain.
core_allowed_import: .ports.
core_allowed_import: java.util
core_allowed_import: java.math
core_allowed_import: java.time.Instant
core_allowed_import: java.time.Duration

core_forbidden_pattern: LocalDate(Time)?\.now|Instant\.now|System\.currentTimeMillis
core_forbidden_pattern: new Random|UUID\.randomUUID|SecureRandom
core_forbidden_pattern: System\.getenv|System\.getProperty|Files\.|new File\(
core_forbidden_pattern: HttpClient|RestTemplate|System\.out\.print

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