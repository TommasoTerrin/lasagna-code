# Phase state — <FEAT-NNN>

File: `.lasagna/state/<FEAT-NNN>.state.md`. **Not committed** (goes in
`.gitignore`). One per feature. It survives context compaction: it is the only
memory of the harness that does not live in the conversation.

The `key: value` lines at column zero are read and written by scripts. Do not
reorder them, do not indent them.

feature_id: FEAT-NNN
flow: official
phase: grilling
layer: domain
budget_max: 3
cycles_used: 0
active_role: none
last_test_result: none
last_test_command: none
last_test_at: none
escalation: none
skipped_phases: none
updated: YYYY-MM-DDTHH:MM:SSZ

## Criteria

One line per criterion. State: `open`, `covered <file>::<test>`, `waived <why>`.

AC-FEAT-NNN-001: open
AC-FEAT-NNN-002: open

## Open questions

Q1 (owner: <name>): ...

## Checkpoint

Written **before** the risky operation, not after. If the context is compacted or
the session dies mid-operation, this is where you restart. Free text, imperative,
addressed to an agent that has seen none of this session.

Shape (the example is indented on purpose: real checkpoint lines start at column
zero with `- [`, which is how dump-phase-state.sh finds them again).

    - [YYYY-MM-DDTHH:MM] About to <operation>. If on restart <condition>, then
      <what to do>. Otherwise <what to do>.

## Cycle log

Append-only. Written by count-cycle.sh on every SubagentStop.

| when | role | outcome |
|---|---|---|

---

## Allowed values

**phase**: `grilling`, `spec`, `gate-spec`, `domain-modeling`, `freeze-contract`,
`gate-contract`, `tdd-loop`, `adversarial-review`, `ports-adapters`, `gate-pr`,
`done`.

**flow**: `official`, `prototype`, `bugfix`, `brownfield`.

**layer**: `domain` (budget 3) or `adapter` (budget 5). Sets `budget_max`.

**active_role**: `none`, `test-writer`, `implementer`, `referee`,
`adversarial-reviewer`. Hooks read this field: if it is wrong, the test-write
block is protecting nothing.

**last_test_result**: `none`, `green`, `red-compile`, `red-assertion`,
`red-generic`, `unknown`.

**escalation**: `none`, or the reason a human is needed. While it is anything
else, no agent proceeds.

**skipped_phases**: `none`, or a comma-separated list of phases deliberately
skipped for this change, each with a reason. A skipped phase is a decision, and
this is where it is recorded so the next session knows the shape was chosen
rather than forgotten.
