---
name: domain-modeling
description: Derives entities, aggregates and invariants from an approved spec, updates CONTEXT.md and writes ADRs for non-obvious aggregate boundaries. Use after the lasagna spec gate, or whenever domain terminology, CONTEXT.md or an ADR is being changed.
---

# domain-modeling

**Trigger**: spec approved at gate 1. Or: the project's vocabulary is changing
and needs recording.

Work from the **approved spec**. In greenfield, do not read existing code: it
would anchor you to a model you are deciding right now, and you would call
"entity" whatever the database calls a table. Exception: brownfield, where the
code is the source.

## What you produce

1. A **domain model** appended to `.lasagna/specs/FEAT-NNN.md`: entities, value
   objects, aggregates with their boundary and root, invariants per aggregate,
   cross-aggregate references by id.
2. `CONTEXT.md` updated **inline**, as each term resolves. Do not batch.
3. Zero or more ADRs, only for non-obvious aggregate boundaries.

## Aggregates come from invariants, not from relationships

An aggregate is the smallest set of objects that must change together to keep an
invariant true. The boundary derives from the spec's **invariants**, never from
the schema's foreign keys.

Take each `INV-n`. List what must be read and written in the same transaction to
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
an entity too many.

A value object earns its place when it carries at least one of: validation at
construction, an operation that makes no sense on the primitive, or a unit that
would otherwise be confused with another.

Weak: `CustomerName(str)` with no constraints, existing only to have a name.
Strong: `Money` with a currency, because adding euros to dollars must break.

## CONTEXT.md

A glossary of the ubiquitous language. **Glossary only** — no implementation
decisions, no spec fragments, no scratch notes.

```md
# <Context name>

<One or two sentences: what this context is and why it exists.>

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

- two actors on the same aggregate at the same instant;
- an entity deleted while another references it by id;
- a quantity at zero, negative, or at the volume limit from the grilling;
- a failure halfway between two aggregates.

If the model has no answer to one of these, it is not finished.

## Next

Move the phase state to `phase: freeze-contract` and invoke `freeze-contract`.
Ambiguity here becomes ambiguous signatures there.
