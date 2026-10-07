---
name: reverse-spec-brownfield
description: Reconstructs spec, domain model and contract from existing code and records the project's own design conventions so new code follows them, to bring a legacy project or a validated prototype into the lasagna format. Use on brownfield codebases, before modifying code no spec describes.
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

If `.lasagna/stack.md` does not exist, fill it now from the real code: test
command, where tests live, where production code lives (`source_path`).

Then set the perimeter: which modules are in the spec, which are the boundary,
which are out. Write it before reading, or you will read everything.

Set `phase: characterize` while you read: in that phase the test-writer may read
the code too, which characterization tests need.

## 2. Detect the conventions — and adopt them

**lasagna adapts to the project; it does not convert it.** Before the first
line of new code, find out how this codebase already does things, and write it
down in `.lasagna/architecture.md` (from
`${CLAUDE_PLUGIN_ROOT}/templates/architecture.md`, `origin: detected`):

- **where the logic lives**: in models, in services, in views, in plain
  functions? Is any of it pure, or does it all reach the database?
- **the separation level** that best describes what exists (minimal, modular,
  full-hexagonal) — described, not prescribed;
- **error convention**: exceptions, result types, error codes, HTTP errors
  thrown from deep inside?
- **dependency injection style**: parameters, constructors, a container, module
  globals, framework magic;
- **test style**: framework, fixtures, layout, which test doubles are used;
- **folder structure and naming**.

Cite a file and line for each. Then **confirm with the human** and record their
name in `confirmed_by`. From here on, the contract and all new code follow these
conventions, even where they differ from *functional core, imperative shell*.

What you would do differently goes into `.lasagna/design-notes.md` (from
`${CLAUDE_PLUGIN_ROOT}/templates/design-notes.md`): what, why, estimated cost,
status `proposed`. **Nothing there is applied without a discussion.** "Apply
functional core / imperative shell to this module" is a proposal like any other.

If the code is so tangled that the feature cannot be built without restructuring
it first, do not refactor on your own initiative. Stop and ask the human
explicitly, with options: build on top of it as it is; a bounded refactoring as
its own feature, with its own spec, first; or narrow the feature.

## 3. Use cases from the code

Start from the **entry points** — HTTP endpoints, CLI commands, queue consumers,
scheduled jobs — not from the classes. A use case is something someone *asks of
the system*, and entry points are the only place that is visible.

For each, rebuild the Jacobson shape: actor, pre-conditions (the checks done
before acting: authentication, validation, state guards), post-conditions (what
ends up written and emitted), main scenario, alternative flows (every error
branch and every early return).

Error branches are not a detail to defer: in legacy they are half the real
behaviour, and the half nobody ever documented.

## 4. Domain model from the schema, with suspicion

The database schema is the starting point, not the answer. Take tables and
relations, then correct with what the code actually does:

- A table is not an entity. Join tables, config tables and audit tables are not
  domain entities.
- **Aggregate boundaries are not in the schema**: they are in the code, where
  transactions open and close. Look there.
- A constraint the database does not enforce but the code does is still an
  invariant — probably a fragile one, and worth saying so.
- A field used for three things is three concepts waiting for a name.

Update the project context (`docs/context/`, the profile's `context_dir`: the
`INDEX.md` and one glossary per bounded context in the perimeter) with the
**real language of the business**, not table names.
If the code calls `t_cust_ord` what everyone calls an Order, the glossary says
Order and records `t_cust_ord` as the technical name. A glossary that mirrors
technical names doubles the legacy instead of escaping it.

## 5. Criteria, with a truth column

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

## 6. Human gate

The same gate 1 as the official flow, plus one question per "to confirm" row:
**is this behaviour intended?** Three possible answers: it is a requirement (it
becomes a criterion), it is a bug (it becomes a separate bugfix flow), it is no
longer needed (it becomes code to delete, not to specify).

While unconfirmed rows remain, the spec is not approved.

## 7. Back to the normal flow

With the spec approved: `domain-modeling` on the slice, then `freeze-contract` —
where the signatures **follow the conventions** recorded in `architecture.md`.
If a different signature would be better, freeze the conventional one and write
the better one as a design note. A contract that quietly migrates the code
towards another architecture turns every feature into a refactoring nobody
approved.

From there it is the official flow. The difference is that domain modelling may
read the existing code: here the code is a source, not a contaminant.

## Promoted prototype

A validated prototype enters here, not through the official flow. The perimeter
is known and small, the "suspected bugs" are nearly always deliberate shortcuts,
and the reconstructed spec becomes the project's first official feature. You do
not carry the prototype's code forward — you carry what it taught you.
