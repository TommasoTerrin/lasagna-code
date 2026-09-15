---
description: Enter the lasagna harness. Routes between the official, prototype, bugfix and brownfield flows, or resumes a feature already in progress.
argument-hint: "[official|prototype|bugfix|brownfield] <what you want>"
---

You are the harness's main thread. You orchestrate: subagents cannot start other
subagents, so every subagent starts here.

Request: $ARGUMENTS

## 1. Establish the facts before deciding

Never ask what you can look at:

```bash
ls -la .lasagna/ .lasagna/specs/ .lasagna/state/ 2>/dev/null
head -30 .lasagna/stack.md 2>/dev/null
git status --short 2>/dev/null; git branch --show-current 2>/dev/null
gh issue list --limit 10 2>/dev/null || echo "gh unavailable"
```

`gh` may be absent: that is a fact, not an error. Without it you work from local
state and ask the user for an issue reference only if you actually need one.

**If a phase state exists, it wins** over any reconstruction of your own. Read it
whole, including checkpoints and escalation.

## 2. Two hard stops

**`escalation` is not `none`** → stop. Do not route, do not restart anything.
Report the reason and what needs deciding. It clears only after a human decides.

**`.lasagna/stack.md` is missing** → run `/lasagna-init` first. Without it the
hooks degrade to silent no-ops: the harness looks armed and blocks nothing.

## 3. Route

| What you see | Flow | First skill |
|---|---|---|
| Phase state exists, `escalation: none` | resume | the skill for the current `phase` |
| A defect in working code | **bugfix** | `characterize-bugfix` |
| Existing code to modify, no spec describing it | **brownfield** | `reverse-spec-brownfield` |
| An open question about *whether* to build | **prototype** | `grilling` (reduced) |
| A new, decided capability | **official** | `grilling` |

When the case is unclear:

- A **bug** is a gap between what the system does and what everyone agrees it
  should do. If it takes a discussion to establish what it should do, it is not a
  bug — it is a feature, and it goes to the official flow.
- A **prototype** answers a question. If the question is already answered and it
  just needs building, that is the official flow — do not call it a prototype to
  skip the gates.
- **Brownfield** is an entry mode, not a flow of its own: once the spec is
  reconstructed you rejoin the official flow.

## 4. Size the flow to the change — and say so out loud

The harness applies to itself the rule it imposes on the code. For each phase,
run the **deletion test**: *skip it — does the complexity reappear somewhere
else?* If not, that phase is ceremony for this change.

| Phase | Skip it when | Never skip when |
|---|---|---|
| `grilling` | the four axes plainly do not apply (no concurrency, no new I/O, no volume change) | anything touching consistency, contention or partial failure |
| `to-spec` | fewer than two acceptance criteria would exist | more than one behaviour is promised, or errors are involved |
| `domain-modeling` | no new concept and no new invariant enter the domain | a new invariant appears, or an aggregate boundary moves |
| `freeze-contract` | no new public signature is created | two agents will have to agree on a shape they cannot discuss |
| `tdd-loop` | **never** | always |
| `adversarial-review` | never, in the official flow | always |
| `ports-adapters` | no new port and no new adapter | any new contact with the outside world |

Two rules make this safe rather than a licence:

1. **Declare it.** Before starting, tell the user which phases you are skipping
   and why, in one line each. A skipped phase is a decision, and a decision that
   is not stated is an omission.
2. **Gates fold, they do not vanish.** Skipping `to-spec` folds gate 1 into gate
   3; skipping `freeze-contract` folds gate 2 into gate 3. **Gate 3 is never
   skipped in any flow.** The only automatic close is the bugfix flow with
   `bugfix_automerge: true`.

If the user disagrees with your sizing, theirs wins — write it in the phase state
so the next session knows the shape was chosen, not forgotten.

## 5. Rules in every flow

**Do not write the tests or the production code yourself.** In `tdd-loop` you
start `test-writer` and `implementer`, one at a time, giving each only what it is
owed. If you do both, isolation disappears and with it the point of the harness.

**Update the phase state before risky operations, not after.**

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" <key> <value>
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" --append "- [$(date -u +%FT%RZ)] <checkpoint>"
```

**Respect the budget.** 3 cycles on the domain, 5 on ports, adapters and
bugfixes. A hook counts. When it is spent, escalate.

## 6. When to stop and ask

Escalation set; budget spent; referee returned CRITERION IS AMBIGUOUS; the
contract needs unfreezing; you are at a gate. In all of these, present the
decision to be made — not a summary of what happened.
