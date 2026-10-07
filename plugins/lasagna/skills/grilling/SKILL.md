---
name: grilling
description: Socratic interview in rounds that settles the stack profile, the architecture's separation level, the scope and the architectural constraints before any spec is written. Use at the start of a lasagna feature, when a request arrives with no spec, or when an idea needs stress-testing before it gets built.
---

# grilling

**Trigger**: the start of a feature, before `to-spec`. No code is written here
and no spec is written here — this round produces answers only.

## The rule that shapes everything

**Facts are your job. Decisions are the user's.** Never ask what you can look
up: filesystem, dependencies, existing code, CI config. Never decide what the
user has to live with.

## Mechanics: a decision tree, worked in rounds

Every decision branches into the decisions that hang off it. The **frontier** is
the set of decisions whose prerequisites are already settled. Ask the whole
frontier in one round, then wait.

```
Q1 — <title>: <body, options if useful>
-> <your recommended answer>

---

Q2 — <title>: <body>
-> <your recommended answer>
```

A question whose answer depends on another question still open belongs to a
**later** round. If a frontier question needs a fact from the environment, go
get it: the questions downstream wait, the rest of the frontier is asked now.

The session ends when the frontier is empty. Do not move to `to-spec` until the
user confirms you are aligned.

## Round 0 — Stack profile (always first)

If `.lasagna/stack.md` does not exist, this is the first round. Detect what you
can first (`pyproject.toml`, `package.json`, `pom.xml`, `*.csproj`, existing CI)
and offer the detected values as your recommendation.

Fields to close: language and runtime, test runner and test command, package
manager, where tests live and how a test file is recognised, **where production
code lives** (`source_path`: the test-writer may not read it during the loop),
mutation testing command (or an explicit "none"), type checker and linter
commands.

Write the result to `.lasagna/stack.md` from
`${CLAUDE_PLUGIN_ROOT}/templates/stack/base.md` plus the variant for the
language (`templates/stack/python.md`, `typescript.md`, `jvm.md`, `dotnet.md`).
Load only the variant you need.

**Do not continue without this file**: the hooks read it, and without it they
degrade to silent no-ops. For Python, unless told otherwise, propose `uv` and
`uv run pytest`.

## Round 0b — How much to separate (greenfield, once per project)

If `.lasagna/architecture.md` is missing or still the empty template, and the
project is **new**, ask how far to separate logic from I/O. lasagna's preferred
principle is *functional core, imperative shell*: logic that receives values and
returns values, I/O at the edges. How much of it to apply depends on the
project, so the question is a level, not a yes/no:

| Level | When | Shape |
|---|---|---|
| **minimal** | little business logic: scripts, simple CRUD | one pure logic module + the edges |
| **modular** (usual default) | non-trivial logic, some external dependencies | modules per feature, a pure core per module, a `Protocol`/interface only on the dependencies that earn one |
| **full-hexagonal** | complex domain, several real adapters for the same port, strong consistency constraints | explicit ports and adapters, aggregates |

Recommend one **with a reason drawn from what you know of this project** — the
amount of business logic, the external systems, how likely a technology change
is. Ask in the same round which libraries are acceptable inside the logic
besides the standard library (e.g. `pydantic`).

Write the answers into `.lasagna/architecture.md` from
`${CLAUDE_PLUGIN_ROOT}/templates/architecture.md`, with `origin: greenfield` and
the user's name in `confirmed_by`.

**On an existing codebase do not ask this.** The level and the conventions are
detected from the code by `reverse-spec-brownfield`, not chosen.

## Round 0c — Which contexts does this touch

Read `docs/context/INDEX.md` (the profile's `context_dir`). Ask which bounded
contexts the feature touches, recommending from the request. Only those files
are loaded from here on; the answer goes into the spec's `contexts:`. A context
that does not exist yet is fine — `domain-modeling` creates it.

## Round 1+ — The four questions nobody asks unprompted

Beyond the feature's own questions, these four axes must be closed
**explicitly**. If the user does not raise them, you do. If they say "not a
problem", that becomes a stated assumption in the spec, not silence.

**Consistency**: which read can be stale, and for how long? Can two users
legitimately see different values at different moments?

**Contention**: what happens when two actors touch the same entity at the same
instant? Last wins, first wins, explicit error, merge? Does that need a lock, a
version, a uniqueness constraint?

**Partial failure**: the operation spans several systems. If the second fails
after the first succeeded, what state is the world left in? Who cleans up? Is
the operation safely retryable?

**Volumes**: how many records today, how many in a year? What is the worst case
for the heaviest query? At what point does the proposed design stop working?

Contention and partial failure are also where real aggregates come from: two
things that must change together atomically. Note them — `domain-modeling`
needs them.

## Example

Weak — hides a decision nobody has made:

> Q1 — Should the order be saved before or after payment?

Strong — the decision is explicit, the alternative is weighed, partial failure
is named:

> Q1 — Order and payment, write ordering: saving the order first means a crash
> in between leaves an unpaid order someone must reconcile. Charging first means
> a crash leaves a payment with no order, which is worse because it reaches the
> customer. Third option: order created `pending`, transitioned to `confirmed`
> after payment, with a job expiring `pending` past 15 minutes.
> -> I recommend the third: it is the only one where neither crash leaves an
> ambiguous state.

## Prototype mode

Skip the four architectural axes and the separation level. Close only: Round 0,
what the prototype must demonstrate, which real infrastructure it must cross,
and which question counts as answered at the end. Two rounds maximum, then build.

## Next

When the frontier is empty and the user has confirmed, invoke `to-spec`.
