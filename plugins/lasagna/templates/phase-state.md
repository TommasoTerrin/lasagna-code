# Phase state — <FEAT-NNN>

File: `.lasagna/state/<FEAT-NNN>.state.md`. **Not committed** (goes in
`.gitignore`). One per feature. It survives context compaction: it is the only
memory of the harness that does not live in the conversation.

The `key: value` lines at column zero are read and written by scripts. Do not
reorder them, do not indent them.

feature_id: FEAT-NNN
flow: official
phase: grilling
layer: core
current_slice: none
contexts: none
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
zero with `- [`, which is how the pre-compaction hook finds them again).

    - [YYYY-MM-DDTHH:MM] About to <operation>. If on restart <condition>, then
      <what to do>. Otherwise <what to do>.

## Cycle log

Append-only. Written by the count-cycle hook on every SubagentStop.

| when | role | outcome |
|---|---|---|

---

## Allowed values

**phase**: `grilling`, `spec`, `gate-spec`, `domain-modeling`, `freeze-contract`,
`gate-contract`, `characterize`, `tdd-loop`, `adversarial-review`, `gate-pr`,
`done`. In `characterize` (bugfix, brownfield) the test-writer may read the code;
in `tdd-loop` it may not.

**flow**: `official`, `prototype`, `bugfix`, `brownfield`.

**layer**: the kind of test in flight — `core` (budget 3: pure logic, tested by
passing values) or `shell` (budget 5: I/O, wiring, integration with real
infrastructure). Leave `budget_max` empty and the count-cycle hook derives it from
`layer`, or from `flow: bugfix` (budget 5); profile keys `budget_core`,
`budget_shell`, `budget_bugfix`.

**cycles_used**: implementer attempts on the criterion in flight. **Owned by the
count-cycle hook**: it resets to 0 when a criterion closes green, and sets
`escalation` when it reaches `budget_max` without green. Do not edit it by hand,
except when unfreezing the contract.

**current_slice**: the slice in flight, e.g. `S2: AC-FEAT-042-003, AC-FEAT-042-004`.

**contexts**: the bounded contexts loaded for this feature, copied from the
spec's `contexts:`. Later phases read only these files from `docs/context/`.

**active_role**: `none`, `test-writer`, `implementer`, `referee`,
`adversarial-reviewer`. Hooks read this field when a tool call does not say which
agent made it: if it is wrong, the isolation blocks protect nothing. Set it with
`sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" set-state active_role <role>`.

**last_test_result**: `none`, `green`, `red-compile`, `red-assertion`,
`red-generic`, `unknown`.

**escalation**: `none`, or the reason a human is needed. While it is anything
else, no agent proceeds.

**skipped_phases**: `none`, or a comma-separated list of phases deliberately
skipped for this change, each with a reason. A skipped phase is a decision, and
this is where it is recorded so the next session knows the shape was chosen
rather than forgotten.
