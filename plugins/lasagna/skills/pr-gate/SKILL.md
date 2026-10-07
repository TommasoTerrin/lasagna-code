---
name: pr-gate
description: Human gate 3 of 3 — prepares the pull request with the spec diff, the traceability table, the adversarial report and the cycles consumed, waits for a human to merge, then archives the spec, checks ADRs and project context, and deletes the phase state. Use after adversarial-review in lasagna, in every flow.
---

# pr-gate

**Trigger**: adversarial review done, no open gaps, traceability and the whole
suite green. Phase state at `phase: gate-pr`.

**Never skipped, in any flow.** Skipping `to-spec` or `freeze-contract` folds
their gates into this one; nothing folds this one away. The single exception is
the bugfix flow with `bugfix_automerge: true` in the profile — a decision a
human took once for the whole project.

## Before opening the PR

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" check-traceability FEAT-NNN
<test_command from .lasagna/stack.md>
```

Both clean, or you are not at this gate: go back to `tdd-loop`.

## The PR presents, in this order

1. **The spec diff**, not just the code diff: what changed in the spec and the
   contract between approval and now, and why. A reviewer who only sees code
   cannot tell an intended change from a drift.
2. **The traceability table**: every criterion with the test covering it —
   paste the output of `run.sh check-traceability`.
3. **The adversarial report**: unrequested code and how it was resolved, design
   drift and the design notes it produced, and the **risks not covered by the
   spec** — these are questions for the reviewer, not findings to bury.
4. **Cycles consumed** per slice, and every escalation along the way with how a
   human resolved it.
5. **Design notes raised** during this feature (`.lasagna/design-notes.md`
   entries with status `proposed`): not part of this change, listed so a human
   can decide on them.

## Human gate 3 of 3 — PR review

**Not automatable.** No auto-merge in the official flow. Ask for the review
explicitly and stop. A merge is irreversible outward; it is not a decision an
agent takes on someone's behalf.

## After the merge

1. Move the spec to `.lasagna/specs/archive/`.
2. Check the ADRs reflect the hard-to-reverse decisions taken along the way; if
   one is missing, write it now (`${CLAUDE_PLUGIN_ROOT}/templates/adr.md`).
3. Check the project context: the glossaries of the contexts in `contexts:`
   use the language the code now uses, and `structure.md` still matches where
   things are.
4. Delete the phase state and its `.precompact.md` snapshot, if any.

The spec was ephemeral. What survives the feature is the tests, the ADRs and
the project context.
