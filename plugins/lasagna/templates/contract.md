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
not reappear anywhere else, it was a pass-through. Do not create it.

## Error types

Every error the seam can produce. Maps 1:1 to the spec's error taxonomy.

| Error | When | Fields | Spec code |
|---|---|---|---|
| `...` | ... | ... | ERR-001 |

## Return shape

How success is distinguished from failure: exception, `Result`/`Either`, tuple,
`None`. **One convention for the whole contract.**

Chosen convention: ...

Per signature, what exactly the successful return contains:

- `<signature 1>` → ...

## Required ports

Every access to the outside world, as an abstract interface. The domain depends
on these, never on the adapters.

| Port | Signature | Why it is needed | Planned adapter |
|---|---|---|---|
| `...` | `...` | ... | ... |

## Determinism

The core is pure. Every source of non-determinism the domain needs enters as a
parameter or as a port, never as a direct call.

| Source | How it enters the domain |
|---|---|
| Current time | parameter `now: Instant` / port `Clock` |
| Randomness, ids | port `IdGenerator` |
| Environment | configuration parameter resolved at the edge |

## What is NOT frozen

Everything the implementer may decide alone without coming back here: internal
data structures, private functions, operation order, algorithms.

This section is not pedantry: it is what tells the `referee`, in a dispute, that
a test depending on these things is a wrong test.
