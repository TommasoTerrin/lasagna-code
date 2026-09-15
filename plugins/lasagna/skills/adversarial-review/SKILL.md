---
name: adversarial-review
description: Runs the adversarial reviewer against a green suite to find the gaps it hides, then routes the findings. Use before the lasagna PR gate, or when you need to confirm the tests cover the spec and not just the happy path.
---

# adversarial-review

**Trigger**: the suite is green and every criterion looks covered. Which is
exactly the moment it becomes tempting to open the PR.

**Green is necessary, not sufficient.** A green suite proves the tests that were
written pass. It does not prove the right tests were written.

## Run it

Start the `adversarial-reviewer` subagent. It sees everything — spec, contract,
code, suite, phase state, ADRs — and it has no `Write` or `Edit`, so it can only
report. Pass it the feature id and the paths to the spec, the contract and the
phase state.

In a **bugfix** flow the question changes, and you must say so in the brief. There
are no criteria to trace; ask instead: *what could this fix have broken, and who
proves it did not?* Concretely: are all the characterization tests still green?
Does the fix touch a path shared with other use cases, and do those have tests?
Does the same bug shape exist elsewhere in the code? A bug is nearly always an
instance of a pattern, and fixing one instance leaves the others.

## Route the findings

The reviewer returns three kinds, deliberately kept apart. They go to three
different places — merging them is how work gets lost.

**Gaps** go back to `tdd-loop`: one criterion, one cycle, like any other. Do not
write the missing tests yourself in one batch — that is horizontal slicing, the
exact thing this harness exists to prevent.

**Unrequested code** either earns a new criterion in the spec, or gets deleted.
No test fixes it.

**Risks not covered by the spec** go to the human at the PR gate. They are not
bugs and no test resolves them. They are questions.

## Before moving on

No open gaps, traceability green, whole suite green. Then set
`phase: ports-adapters` (official flow) or `phase: gate-pr`.
