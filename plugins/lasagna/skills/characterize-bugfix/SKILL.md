---
name: characterize-bugfix
description: Bugfix flow with no spec — pin current behaviour with characterization tests, reproduce the bug with a red test, then run the tdd-loop. Use when a bug or a regression is reported.
---

# characterize-bugfix

**Trigger**: a reported bug. No spec needed: a system already behaves one way,
and there is a way it should behave.

**No production code before the tests.** Faced with a bug you understand in
thirty seconds, the temptation is to fix it in twenty. The problem is not the
fix: it is that without tests you do not know whether the bug you fixed is the
one reported, and you do not know what you broke fixing it.

## 1. Reproduce, do not interpret

Reproduce with the data and steps from the report, not with what you believe is
equivalent. If you cannot reproduce it, you do not have a bug, you have a report:
go back and ask for the exact state.

Note the **observed** and **expected** behaviour, one line each. If the expected
one is not obvious, this is not a bug: it is a missing feature, and it goes to
the official flow.

## 2. Safety net: characterization tests

Before touching anything, pin the **current** behaviour around the bug. These
tests **pass now**: they do not describe what the system should do, they describe
what it does.

They exist for one reason: to tell you if the fix changed something that should
not have changed. Code containing a bug is almost always code someone
misunderstood, and whoever fixes it tends to misunderstand it in turn.

Write enough to cover the paths running through the area you will touch. No
criterion ids — there is no spec. Mark them as characterization in the name or a
comment, so a future reader knows they are **not** requirements: they are
photographs, and they can be deleted when behaviour changes on purpose.

Run them. They must be **green**. A red characterization test means you described
the current behaviour wrong, not that the system is broken.

## 3. The reproducing test

One. Red. It asserts the **expected** behaviour, so it fails now.

The `test-writer` subagent writes it, as in any other loop. Pass it: the report,
the observed and expected behaviour, and the real signatures of the functions
involved — there is no frozen contract here, so signatures are read from the code
and quoted in the brief.

Watch the red. An assertion failure is the right red: the path is correct and the
value is wrong. An import error means you are testing in the wrong place.

## 4. tdd-loop

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" flow bugfix
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" layer adapter
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" budget_max 5
```

Invoke `tdd-loop`. The implementer sees the reproducing test and the signatures,
not the report. The test-write block applies identically: if it could touch the
characterization tests, the safety net would vanish exactly when it is needed.

## 5. Adversarial review, aimed at regressions

Invoke `adversarial-review` and state in the brief that this is a bugfix flow —
the question changes from "is every criterion covered" to "what could this have
broken, and who proves it did not".

## 6. Closing

If everything is green within budget, the bugfix flow may close itself — **only**
if `.lasagna/stack.md` declares `bugfix_automerge: true`. The default is `false`,
and turning it on is a human decision taken once per project: a merge is
irreversible outward, and it is not a decision an agent takes on someone's behalf.

With the default, prepare the PR and stop. It carries the report, the reproducing
test, the characterization tests added, and the regression report.

If the budget runs out, or the review finds an uncovered path: **escalate**, in
both cases. A bug that will not close in five cycles is not the bug that was
reported.

## Never

- Fix first, test after. A test written afterwards always passes.
- Delete a characterization test that turns red after the fix. That red is the
  only useful thing produced today: either the fix is wrong, or that behaviour
  needed changing and nobody said so.
- Tidy the surrounding code. A bugfix diff must be readable in thirty seconds.
