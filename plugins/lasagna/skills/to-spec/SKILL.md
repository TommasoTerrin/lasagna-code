---
name: to-spec
description: Turns a finished grilling into a lasagna spec (Jacobson use cases, criteria with ids, invariants, error taxonomy, vertical slices, rollback plan) and runs the spec approval gate. Use after grilling closes, or when a requirement changes while work is open.
---

# to-spec

**Trigger**: grilling is closed and the user confirmed alignment. Or: a spec
exists and a requirement changed while the work is open.

**Do not interview.** If you find an answer missing, go back to `grilling`. This
skill synthesises, it does not discover.

## Procedure

1. Read the project context: `docs/context/INDEX.md` (the profile's
   `context_dir`), then **only** the contexts the grilling settled on. Use their
   vocabulary throughout. A term you need that is not there is a signal for
   `domain-modeling`, not a licence to invent a synonym.
   (A v1 profile with `context_file` and no `context_dir`: that one file is the
   whole context.)
2. Read the ADRs in `docs/adr/` touching the area. The spec cannot contradict
   one silently; if it must, that ADR is being superseded and the spec says so.
3. Assign `FEAT-NNN`, the next free number in `.lasagna/specs/`.
4. Fill `${CLAUDE_PLUGIN_ROOT}/templates/spec.md` into `.lasagna/specs/FEAT-NNN.md`,
   with `contexts:` set. The template carries the format — follow it.
5. **Cut the work into vertical slices** (template section "Slices"). See below.
6. Create the phase state from `templates/phase-state.md` at
   `.lasagna/state/FEAT-NNN.state.md`, `phase: gate-spec`, `contexts:` copied
   from the spec.
7. Stop at the gate.

## Slices

A slice is a thin path through **everything** a user would touch — the logic,
the code around it, and the outside world when its criteria need it — not a
layer. Never "all the logic first, then all the integration": the logic would be
tested against an integration nobody has built yet.

- **S1 is the tracer bullet**: the thinnest end-to-end path through every layer
  the feature will use — from the system's edge to storage and back. Its logic
  can be almost trivial; its job is to prove the wiring early, while changing it
  is still cheap.
- Each later slice adds one criterion or a small coherent group, and is
  demoable on its own.
- Mark the slices that touch the outside world: they need an integration test
  against real infrastructure.

## The three things that actually go wrong here

**Criteria that only cover the happy path.** Every row of the error taxonomy and
every alternative flow needs its own criterion with its own id. The main path is
the easy part, and the adversarial reviewer will go looking for precisely what
you skipped.

**Invariants that are really business rules.** An invariant is true at every
instant, unconditionally: "an order's total is the sum of its lines". A business
rule is conditional: "premium customers get 10% off". If a supposed invariant can
be temporarily false mid-transaction, it is not an invariant.

**A rollback plan per feature instead of per slice.** "Revert the commit" is not
a plan. The plan says what happens to data already written and to effects that
already left the system.

## Living spec

While work is open the spec is a contract that gets updated. If a requirement
changes mid-loop:

1. Give new criteria **new** ids. Never reuse an id and never change what an
   existing one means — tests point at them.
2. Mark stale criteria `superseded` rather than deleting them, and align the
   phase state.
3. If the change touches signatures, the contract must be **unfrozen**: stop the
   loop, return to `freeze-contract`, re-approve. Do not let the implementer
   discover the change on its own.

## Human gate 1 of 3 — spec approval

**Not automatable.** No agent clears it on a human's behalf, no flow skips it
because it "looks obvious".

Present compactly: goal and non-goals; the four architectural assumptions
(consistency, contention, partial failure, volumes) in one line each; the
contexts touched; the slices in order, with their criterion ids and titles;
blocking open questions.

Then ask for approval explicitly. When it comes: write `approved_by` and the
date into the spec, move the phase state to `phase: domain-modeling`, and invoke
`domain-modeling`.

If it does not come, stay at `phase: gate-spec`. Do not start modelling "in the
meantime".

## Example

Weak — no id, not verifiable, happy path only:

> - The user must be able to cancel the order.

Strong:

> | AC-FEAT-042-003 | an Order in `confirmed`, shipped less than 24h ago | the Customer requests cancellation | the Order moves to `cancelled` and `OrderCancelled` is emitted |
> | AC-FEAT-042-004 | an Order in `shipped` | the Customer requests cancellation | the request is refused with `OrderNotCancellable` and the Order stays `shipped` |
