---
name: tdd-loop
description: Runs the red-green loop one criterion at a time, isolating whoever writes the test from whoever writes the code, with observed red and a fixed cycle budget. Use after the lasagna contract gate, or when a characterization test is ready in a bugfix flow.
---

# tdd-loop

**Trigger**: contract frozen and approved (gate 2). Or: a characterization test
is ready in a bugfix flow.

This skill **orchestrates**. Do not write the test yourself, do not write the
code yourself: the isolation between the two roles is the mechanism, and it
collapses the moment one context does both.

## Before every cycle

Read `.lasagna/state/FEAT-NNN.state.md`. If `escalation` is not `none`, **stop**
and bring it to the human. Same if `cycles_used >= budget_max`.

Pick **one** criterion still `open`. Prefer the simplest of those that unblock
others: every cycle teaches the next one something, and starting from the hardest
wastes that.

Write the checkpoint **before** starting, not after:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" --append "- [$(date -u +%FT%RZ)] starting cycle on AC-FEAT-042-003"
```

## Red phase

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" active_role test-writer
```

Start the `test-writer` subagent with **only**: the current criterion and its id,
the path to the frozen contract, the path to the stack profile. Not the whole
spec, not future criteria, not your reasoning.

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
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" active_role implementer
```

Start the `implementer` subagent with **only**: the path to the frozen contract,
the path and name of the current test, the failure lines that matter, the test
command. **Never** the test-writer's full answer, never the spec, never future
criteria.

A hook denies it writes to test files. If it tries and gets blocked you will see
it in the output: do not loosen the constraint, that is the point.

When it returns, read `last_test_result` again.

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

## Closing a cycle

Green: mark the criterion, clear the role, run the **whole** suite — a local
green says nothing about regressions — then move to the next criterion.

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" active_role none
```

Update the criterion line from `open` to `covered <file>::<test>`.

## Budget

3 implementer attempts on the domain, 5 on ports and adapters. A hook counts
them on every `SubagentStop`. When the budget is spent the phase state gets
`escalation` and **the loop stops**.

There is no quiet fourth attempt. When you escalate, bring the human: the
criterion the loop is stuck on, the referee's verdict if there was one, and the
two or three hypotheses that explain why red will not close — not a summary of
the attempts.

If the reason is that the contract is insufficient, the answer is not another
cycle: unfreeze the contract (`freeze-contract`), re-approve, reset
`cycles_used`, restart.

## When the loop is done

Every criterion in the layer is `covered` and the whole suite is green. Green is
not enough:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-traceability.sh" FEAT-NNN
```

Then set `phase: adversarial-review` and invoke `adversarial-review`.
