---
name: reverse-spec-brownfield
description: Reconstructs spec, domain model and contract from existing code, to bring a legacy project or a validated prototype into the lasagna format. Use on brownfield codebases, before modifying code no spec describes.
---

# reverse-spec-brownfield

**Trigger**: you have to modify code that no spec describes. A legacy system, a
validated prototype, an inherited project.

**Do not reconstruct the whole system.** Reconstruct the spec of the **slice you
are about to touch**, plus the boundaries around it. A spec of the entire legacy
is a project in itself, takes months, and will be stale before it is finished.

## The rule that makes this useful

**The code says what the system does. It does not say what it should do.** A
behaviour in the code may be a requirement, a bug nobody noticed, or the residue
of a requirement that died three years ago.

You produce the first column. A human fills the second. Do not collapse them: the
urge to write "the system rounds down" as though it were a requirement is exactly
how a bug becomes a specification.

## 1. Profile and perimeter

If `.lasagna/stack.md` does not exist, fill it now from the real code. Here
`core_path` and `core_allowed_import` go in **as they are**, not as you wish they
were: if the current core imports infrastructure, the layering hook would fire on
every write and become noise to ignore. Record the gap as future work.

Then set the perimeter: which modules are in the spec, which are the boundary,
which are out. Write it before reading, or you will read everything.

## 2. Use cases from the code

Start from the **entry points** — HTTP endpoints, CLI commands, queue consumers,
scheduled jobs — not from the classes. A use case is something someone *asks of
the system*, and entry points are the only place that is visible.

For each, rebuild the Jacobson shape: actor, pre-conditions (the checks done
before acting: authentication, validation, state guards), post-conditions (what
ends up written and emitted), main scenario, alternative flows (every error
branch and every early return).

Error branches are not a detail to defer: in legacy they are half the real
behaviour, and the half nobody ever documented.

## 3. Domain model from the schema, with suspicion

The database schema is the starting point, not the answer. Take tables and
relations, then correct with what the code actually does:

- A table is not an entity. Join tables, config tables and audit tables are not
  domain entities.
- **Aggregate boundaries are not in the schema**: they are in the code, where
  transactions open and close. Look there.
- A constraint the database does not enforce but the code does is still an
  invariant — probably a fragile one, and worth saying so.
- A field used for three things is three concepts waiting for a name.

Update `CONTEXT.md` with the **real language of the business**, not table names.
If the code calls `t_cust_ord` what everyone calls an Order, the glossary says
Order and records `t_cust_ord` as the technical name. A glossary that mirrors
technical names doubles the legacy instead of escaping it.

## 4. Criteria, with a truth column

Write criteria in Given/When/Then with normal `AC-<feature>-NNN` ids, and add two
columns:

| ID | Given/When/Then | Origin | Confirmed? |
|---|---|---|---|
| AC-...-001 | ... | code: `orders.py:88` | to confirm |
| AC-...-002 | ... | existing test: `test_x.py::test_y` | yes |
| AC-...-003 | ... | code: `orders.py:104` | **suspected bug** |

**Origin** says where you read the behaviour. **Confirmed** says whether a human
recognised it as intended. A "to confirm" criterion does not enter the TDD loop:
it would freeze into a test a behaviour nobody chose.

Flag explicitly: behaviours that look like bugs, dead code, contradictions
between two paths, dependencies on execution order.

## 5. Human gate

The same gate 1 as the official flow, plus one question per "to confirm" row:
**is this behaviour intended?** Three possible answers: it is a requirement (it
becomes a criterion), it is a bug (it becomes a separate bugfix flow), it is no
longer needed (it becomes code to delete, not to specify).

While unconfirmed rows remain, the spec is not approved.

## 6. Back to the normal flow

With the spec approved: `domain-modeling` on the slice, then `freeze-contract` —
where the contract describes the signatures **you want**, not the ones that exist.
The gap between the two is the refactoring work, and it is good that it is
visible.

From there it is the official flow. The difference is that domain modelling may
read the existing code: here the code is a source, not a contaminant.

## Promoted prototype

A validated prototype enters here, not through the official flow. The perimeter
is known and small, the "suspected bugs" are nearly always deliberate shortcuts,
and the reconstructed spec becomes the project's first official feature. You do
not carry the prototype's code forward — you carry what it taught you.
