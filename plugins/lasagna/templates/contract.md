# Frozen interface contract — <FEAT-NNN>

File: `.lasagna/contracts/<FEAT-NNN>.md`. Committed.

frozen_on: YYYY-MM-DD
approved_by: <human name>
derives_from: .lasagna/specs/<FEAT-NNN>.md

> This document is the **only** thing `test-writer` and `implementer` share. If
> it is ambiguous, the two agents diverge and the loop burns cycles. To change
> it: stop the loop, edit here, re-approve.

## Seams under test

The public boundary the tests live on. Fewer is better; one is ideal.

| Seam | Why here | Criteria that pass through |
|---|---|---|
| `<module.function>` | ... | AC-...-001, AC-...-002 |

## Signatures

One line per public function or method, in the real syntax of the profile's
language. No bodies, no `TODO`, no explanatory comments inside the block —
anything that needs explaining goes below.

```
<signature 1>
```

## Data types

The types appearing in the signatures. Value objects, entities, DTOs. For each:
fields, types, validity constraints.

```
<type 1>
```

**Proportionate ceremony**: before creating a value object, apply the *deletion
test*. Delete the type, put the primitive back. If the complexity it held does
not reappear anywhere else, it was a pass-through. Do not create it. The same
test applies to abstractions: an interface with one implementation and no test
that needs to replace it is a pass-through too.

## Error types

Every error the seam can produce. Maps 1:1 to the spec's error taxonomy. Vendor
errors (HTTP statuses, database constraints, SDK exceptions) never appear here:
the shell translates them into these.

| Error | When | Fields | Spec code |
|---|---|---|---|
| `...` | ... | ... | ERR-001 |

## Return shape

How success is distinguished from failure: exception, `Result`/`Either`, tuple,
`None`. **One convention for the whole contract.**

Chosen convention: ...

Per signature, what exactly the successful return contains:

- `<signature 1>` → ...

## External dependencies

Every source of I/O or non-determinism the code under test needs, and how the
tests control it. One row each — a missing row is two agents inventing two
different answers.

| Dependency | How the code reaches it | How tests control it |
|---|---|---|
| Current time | parameter `now: datetime` | fixed value |
| Order storage | `OrderRepo` (Protocol) | in-memory fake |
| Email | `notifications.send_email()` | monkeypatch (existing convention) |
| Config | `Settings` (pydantic) | instance built in the test |

How to choose the second column (`.lasagna/architecture.md` has the project's
answer):

- **Greenfield**: a parameter when a value is enough (`now`, configuration); a
  plain function when one operation is enough; a `Protocol`/interface only when
  the technology may really change, the test must replace something slow or
  non-deterministic, or two implementations already exist. The most frequent
  answer is none of these: move the I/O to the shell — `cancel(order, now) ->
  Order` is pure, and the shell does load → cancel → save.
- **Existing code**: the mechanism the project already uses, even if it is not
  the one you would pick. A better one goes to `.lasagna/design-notes.md`.

"How tests control it" must be something the test-writer can do without reading
the implementation.

## What is NOT frozen

Everything the implementer may decide alone without coming back here: internal
data structures, private functions, operation order, algorithms.

This section is not pedantry: it is what tells the `referee`, in a dispute, that
a test depending on these things is a wrong test.
