# Spec — <FEAT-NNN>: <title>

File: `.lasagna/specs/<FEAT-NNN>.md`. Committed. **Ephemeral**: it moves to
`.lasagna/specs/archive/` when the feature merges. What survives is the ADRs,
the project context (`docs/context/`) and the tests.

feature_id: FEAT-NNN
flow: official | prototype | bugfix | brownfield
status: draft | approved | in-progress | archived
approved_by: <human name> on <YYYY-MM-DD>
contexts: <bounded contexts this feature touches, from docs/context/INDEX.md — comma-separated>

## Goal

What must be true when the work is done, from the point of view of whoever uses
the system. One or two sentences. Not a list of activities.

## Non-goals

What is explicitly excluded. Each entry is something a reasonable reader might
expect and we will not do, with one line of why.

- ...

## Architectural constraints and assumptions

From the grilling. Stated, never silent.

- **Asynchrony**: ...
- **Consistency**: which read can be stale, and for how long.
- **Contention**: what happens with two simultaneous actors on one entity.
- **Partial failure**: the state of the world if the second system fails after
  the first; who cleans up; is the operation idempotent?
- **Volumes**: orders of magnitude today and in a year; the worst case.
- **Technology constraints already decided**: ...

## System use cases

Jacobson format. One per meaningful interaction.

### UC-1 — <name>

- **Actor**: ...
- **Pre-conditions**: what must be true before. Verifiable.
- **Post-conditions**: what is true after, on success. Verifiable.
- **Main scenario**:
  1. ...
- **Alternative flows**:
  - 1a. <condition> → <what happens>

## Acceptance criteria

Every criterion has a unique id `AC-<FEAT-NNN>-NNN` and is Given/When/Then. No
criterion without a test, no test without a criterion:
`run.sh check-traceability` verifies both directions.

| ID | Given | When | Then |
|---|---|---|---|
| AC-FEAT-NNN-001 | ... | ... | ... |

Include criteria for the **alternative flows and the errors**, not just the main
path. One criterion per row of the error taxonomy.

## Domain invariants

Always true, at every instant, whatever happens. If one can be temporarily
false, it is not an invariant: it is a business rule.

- INV-1: ...

## Business rules

Conditional: they hold when some condition occurs.

- BR-1: when <condition>, then <consequence>.

## Error taxonomy

| Code | Cause | What the user sees | Retryable |
|---|---|---|---|
| ERR-001 | ... | ... | yes / no |

## Slices

The build order. Each slice is **vertical**: a thin path through everything a
user would touch — core logic, the shell around it, and the integration with
the outside world when the criteria need it — not a layer. A slice is done when
its criteria are green end to end.

**S1 is the tracer bullet**: the thinnest path that crosses every layer the
feature will use, from the edge of the system to storage and back. It proves the
wiring before anything is built on it; its logic can be almost trivial.

| Slice | Criteria | Touches the outside world? | Done when |
|---|---|---|---|
| S1 (tracer) | AC-FEAT-NNN-001 | yes: <which> | ... |
| S2 | AC-FEAT-NNN-002, AC-FEAT-NNN-003 | no | ... |

## Verification and rollback plan

Per slice, in build order.

| Slice | How we verify it is right | How we get back |
|---|---|---|
| S1 | ... | ... |

## Open questions

Every question has a named **owner**. A question with no owner is not open, it is
abandoned.

| # | Question | Owner | Blocking? |
|---|---|---|---|
| Q1 | ... | ... | yes / no |

## Domain model

Appended by `domain-modeling` after the spec gate. Always: the business rules
and invariants, the glossary terms, and the **module each rule lives in**.
Entities and value objects only where they earn their place. Aggregates only
where two things must change together atomically — with their boundary and
root, and cross-aggregate references by id.
