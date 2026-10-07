---
name: domain-modeling
description: Derives the business rules, invariants and the module each one lives in from an approved spec, updates the project's context glossaries, and introduces aggregates only where atomic consistency demands them. Use after the lasagna spec gate, or whenever domain terminology, the docs/context glossaries or an ADR is being changed.
---

# domain-modeling

**Trigger**: spec approved at gate 1. Or: the project's vocabulary is changing
and needs recording.

Work from the **approved spec** and `.lasagna/architecture.md`. In greenfield, do
not read existing code: it would anchor you to a model you are deciding right
now, and you would call "entity" whatever the database calls a table. Exception:
brownfield, where the code is the source.

## What you produce

Appended to `.lasagna/specs/FEAT-NNN.md`, section "Domain model":

1. **Rules and invariants** — every business rule and invariant of the spec, in
   the project's language.
2. **Where each rule lives** — the module (by feature: `billing/`,
   `registration/`; file names that say the behaviour, `decide_refund`, not the
   role, `service`). In a small project `logic.py` + `app.py` can be the whole
   answer. Follow the separation level and conventions in `architecture.md`.
3. **Glossary terms** — written into the context files (below), inline as each
   term resolves. Do not batch.
4. **Entities, value objects, aggregates — only where they earn their place.**
   On CRUD and data pipelines they are usually ceremony. See below.
5. Zero or more ADRs, only when the three conditions hold.

## Aggregates: only when two things must change together

An aggregate is the smallest set of objects that must change together, in one
atomic step, to keep an invariant true. You need one only when the grilling's
**contention** or **partial failure** answers say so: two actors on the same
data at once, or a change that must never be half-applied. No such pressure, no
aggregate — a function over plain data does the job.

When you do need them, they come from **invariants, not relationships**. Take
each `INV-n`. List what must be read and written in the same transaction to
guarantee it. That set is a candidate aggregate. Merge overlapping candidates.
Whatever falls outside is referenced **by id**, never by direct reference.

If an invariant crosses two aggregates you have three options and must pick one
explicitly: merge them, weaken the invariant to eventual consistency, or move the
rule into a reconciling process. **This choice is always an ADR** — it is hard to
reverse and surprising without context.

## Proportionate ceremony

Before creating a value object, apply the **deletion test**: delete it, put the
primitive back. If the complexity it held does not reappear anywhere, it was a
pass-through and should not exist.

Apply the same test one level up, to entities: delete the entity, inline its
fields into its neighbour. If no invariant or state transition reappears, it was
an entity too many. And to abstractions: an interface with one implementation
that no test needs to replace is a pass-through.

A value object earns its place when it carries at least one of: validation at
construction, an operation that makes no sense on the primitive, or a unit that
would otherwise be confused with another.

Weak: `CustomerName(str)` with no constraints, existing only to have a name.
Strong: `Money` with a currency, because adding euros to dollars must break.

## The project context

Lives in `context_dir` from the profile (default `docs/context/`):

```
docs/context/
  INDEX.md        one line per bounded context: name, one sentence, file
  billing.md      the glossary of one bounded context
  structure.md    a minimal code map, kept apart: it ages, the glossary does not
```

Update **only the contexts in the spec's `contexts:`**. A new context gets its
file from `${CLAUDE_PLUGIN_ROOT}/templates/context/context.md` and a line in
`INDEX.md`. If code moved, update `structure.md` (template in the same folder).
A v1 project with `context_file` and no `context_dir`: that single file is the
glossary.

A glossary file is **glossary only** — no implementation decisions, no spec
fragments, no scratch notes. Project conventions belong in
`.lasagna/architecture.md`, not here.

```md
# Ordering

Placing and changing orders, from the cart to confirmation.

## Language

**Order**:
A purchase request confirmed by a Customer.
_Avoid_: purchase, transaction

**Customer**:
A person or organisation that places Orders.
_Avoid_: user, account
```

Be prescriptive: when several words exist for one concept, pick one and list the
rest under `_Avoid_`. Definitions of one or two sentences, saying what a thing
**is**, not what it does. Only terms specific to **this** domain — timeouts,
retries and caches do not belong even if the project is full of them.

When the user uses a term that conflicts with the glossary, stop them
immediately: "the glossary says *cancellation* is X, but you seem to mean Y —
which is it?"

## ADRs

Write one only if **all three** hold: hard to reverse, surprising without
context, the result of a real trade-off with alternatives weighed. If one is
missing, skip it. Format: `${CLAUDE_PLUGIN_ROOT}/templates/adr.md`.

At this stage the usual qualifiers are: an aggregate boundary chosen against the
schema's intuition, an invariant deliberately weakened to eventual consistency,
the decision not to model something as an entity.

## Stress test before closing

Try the model against concrete edge scenarios. Invent them yourself:

- two actors on the same data at the same instant;
- something deleted while another thing references it by id;
- a quantity at zero, negative, or at the volume limit from the grilling;
- a failure halfway between two writes.

If the model has no answer to one of these, it is not finished.

## Next

Move the phase state to `phase: freeze-contract` and invoke `freeze-contract`.
Ambiguity here becomes ambiguous signatures there.
