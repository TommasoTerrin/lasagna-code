---
description: Show the lasagna state of the current project - stack profile, phase, cycles used, criteria covered, traceability.
argument-hint: "[FEAT-NNN]"
---

Report the harness state. Change nothing, start no phase.

Feature (empty = the active one): $ARGUMENTS

## Collect

```bash
echo "--- profile"
head -40 .lasagna/stack.md 2>/dev/null || echo "MISSING: hooks are no-ops until .lasagna/stack.md exists — run /lasagna-init"
echo "--- specs"
ls -1 .lasagna/specs/*.md 2>/dev/null || echo "no active spec"
echo "--- contracts"
ls -1 .lasagna/contracts/*.md 2>/dev/null || echo "no frozen contract"
echo "--- phase state"
cat .lasagna/state/*.state.md 2>/dev/null || echo "no phase state"
echo "--- git"
git status --short 2>/dev/null; git branch --show-current 2>/dev/null
```

Then traceability, if a spec exists:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-traceability.sh" $ARGUMENTS
```

## Report

```
feature:  FEAT-NNN — <title>
flow:     <flow>        phase: <phase>        layer: <layer>
cycles:   <used>/<budget>
role:     <active_role>  last test: <last_test_result>

criteria:  <n covered> / <n total>
uncovered: <ids, or "none">
orphans:   <ids, or "none">

blocks:   <escalation / gate waiting / profile missing, or "none">
next:     <the next concrete action, one line>
```

Two things worth calling out when you see them:

**`active_role` is not `none` while no subagent is running.** State left dirty by
an interrupted session. Until it is cleared, the test-write block applies outside
the loop too:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" active_role none
```

**A `.precompact.md` newer than its `.state.md`.** A compaction happened; read the
checkpoint before resuming.
