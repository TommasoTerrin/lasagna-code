---
name: tdd-loop
description: Builds the feature slice by slice — core tests, then the shell and an integration test when the slice touches the world — one criterion at a time, isolating whoever writes the test from whoever writes the code, with observed red and a per-criterion cycle budget. Use after the lasagna contract gate, or when a characterization test is ready in a bugfix flow.
---

# tdd-loop

**Trigger**: contract frozen and approved (gate 2). Or: a reproducing test is
ready in a bugfix flow.

This skill **orchestrates**. Do not write the test yourself, do not write the
code yourself: the isolation between the two roles is the mechanism, and it
collapses the moment one context does both.

All state changes go through the script, never by editing the file:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state <key> <value>
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state --append "- [<UTC time>] <checkpoint>"
```

## The shape: slices, not layers

Work through the spec's **Slices** in order. Each slice is built end to end
before the next one starts:

1. **Core** — for each criterion of the slice, the logic: pure functions tested
   by passing values. `layer: core`.
2. **Shell** — the code around it: endpoint, CLI, job, storage, network. Thin:
   it gathers data, calls the core, applies what the core decided. `layer: shell`.
3. **Integration** — if the slice touches the outside world, one test against
   **real** infrastructure (a container, a sandbox, a temp file, an in-memory
   database the project really uses). Not a mock: a mock checks that the shell
   does what you believe the vendor does, which is the very assumption under
   test. `layer: shell`.

**S1 is the tracer bullet**: the thinnest path through every layer, from the
system's edge to storage and back. Its logic may be trivial. Its job is to prove
the wiring while changing it is still cheap — so do not start S2 until S1 runs
end to end.

A slice with no contact with the outside world is core only. Never build all the
core for every slice first: the logic would be tested against an integration
that does not exist yet.

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state current_slice "S1: AC-FEAT-042-001"
```

## Before every cycle

Read `.lasagna/state/FEAT-NNN.state.md`. If `escalation` is not `none`, **stop**
and bring it to the human.

Pick **one** criterion still `open` in the current slice. Prefer the simplest of
those that unblock others: every cycle teaches the next one something.

Set the kind of test, and leave the budget to the hook:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state layer core     # or shell
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state budget_max ""
```

With `budget_max` empty, the count-cycle hook derives it: `budget_core` (3) for
core, `budget_shell` (5) for shell and integration, `budget_bugfix` (5) in the
bugfix flow.

Write the checkpoint **before** starting, not after:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state --append "- [<UTC time>] S1: starting AC-FEAT-042-003 (core)"
```

## Red phase

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state active_role test-writer
```

Start the `test-writer` subagent with **only**: the current criterion and its id,
the kind of test (`core` / `shell` / integration), the path to the frozen
contract, the path to the stack profile. Not the whole spec, not future
criteria, not your reasoning. During `tdd-loop` a hook denies it reading the
production code.

When it returns, read `last_test_result` from the phase state — a hook wrote it
from the actual run, not from the agent's account of it.

**Red is observed.** If the state does not say `red-*`, the cycle does not start.

| outcome | what to do |
|---|---|
| `red-compile` | Legitimate starting red: the symbol does not exist. Proceed. |
| `red-assertion` | Legitimate and better: the behaviour is wrong. Proceed. |
| `green` | The test passes with no implementation. Either the criterion is already covered (mark it `covered`, move on) or the test is too permissive: send it back to the `test-writer` to tighten. **Do not proceed.** |
| `red-generic` / `unknown` | You do not know what happened. Look at the output before spending a cycle, and fix the patterns in `.lasagna/stack.md` if the classification was wrong. |

## Green phase

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state active_role implementer
```

Start the `implementer` subagent with **only**: the path to the frozen contract,
the **name** of the current test, the **complete failure lines** from the
test-writer's answer (the assertion with expected and actual values, or the
missing symbol), the test command, the kind of test. **Never** the test-writer's
reasoning, never the spec, never future criteria — and not the test file: the
implementer cannot read tests, a hook denies it. The failure lines are all it
has besides the contract, so pass them whole.

When it returns, read `last_test_result` again.

If the implementer reports `noticed:` a design improvement, add it to
`.lasagna/design-notes.md` as `proposed`. Do not apply it.

## Rules for the shell and the integration tests

These come from building against the real world, where most surprises are
information rather than failure:

- **World constraint or vendor choice?** Ask: *if we changed vendor tomorrow,
  would this change?* Yes → it stays in the shell and appears nowhere else (the
  field is called `customer_ref` and holds 32 characters). No → it is a rule of
  the domain (a captured payment is refunded, not cancelled): stop, take it back
  to the spec and the contract, re-approve. A business rule enforced only in the
  shell stops holding the day a second shell appears.
- **Translate vendor errors** into the contract's error types. An HTTP status or
  a database constraint reaching the logic is a leak, and sooner or later
  someone writes a business rule on top of it.
- **No business rules in the shell.** An `if` on a domain value inside an
  endpoint or adapter is a rule in the wrong place.
- **Few end-to-end tests.** The criteria are covered by core tests; an e2e earns
  its place when it checks the **wiring** of a main use case — that the path
  from the edge to storage and back is connected the way you think. One per main
  use case; if you need many more, logic has leaked into the wiring.

## When to call the referee

Only on an **ambiguous assertion failure**: the test asserts one thing, the code
does another, and both look defensible against the contract. Typically when the
implementer attaches an objection.

Not on a compile error (there is nothing to arbitrate) and not when the answer is
obvious.

Start `referee` with: the criterion text, the test, the failure output, the
implementer's objection, the contract. Not the implementation. The verdict is one
of three: test wrong, code wrong, criterion ambiguous. The last one is not yours
to resolve — it is human escalation.

## Closing a criterion

Green: the count-cycle hook has already reset `cycles_used` to 0 for the next
criterion — do not touch it. Clear the role, run the **whole** suite (a local
green says nothing about regressions), mark the criterion:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state active_role none
```

Update the criterion line from `open` to `covered <file>::<test>`.

When every criterion of the slice is covered and the whole suite is green, move
`current_slice` to the next slice.

## Budget

Per criterion: 3 implementer attempts on core tests, 5 on shell and integration
tests and in bugfixes. A hook counts them on every `SubagentStop` and resets the
count when a criterion closes green. When the budget is spent the phase state
gets `escalation` and **the loop stops**.

There is no quiet extra attempt. When you escalate, bring the human: the
criterion the loop is stuck on, the referee's verdict if there was one, and the
two or three hypotheses that explain why red will not close — not a summary of
the attempts.

If the reason is that the contract is insufficient, the answer is not another
cycle: unfreeze the contract (`freeze-contract`), re-approve, reset
`cycles_used`, restart.

## When the loop is done

Every slice is done, every criterion `covered`, the whole suite green. Green is
not enough:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" check-traceability FEAT-NNN
```

Then set `phase: adversarial-review` and invoke `adversarial-review`.
