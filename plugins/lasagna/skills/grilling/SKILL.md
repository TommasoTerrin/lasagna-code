---
name: grilling
description: Socratic interview in rounds that settles the stack profile, the scope and the architectural constraints before any spec is written. Use at the start of a lasagna feature, when a request arrives with no spec, or when an idea needs stress-testing before it gets built.
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
manager, domain core paths, imports allowed inside the core, patterns that make
the core impure, mutation testing command (or an explicit "none"), type checker
and linter commands.

Write the result to `.lasagna/stack.md` from
`${CLAUDE_PLUGIN_ROOT}/templates/stack/base.md` plus the variant for the
language (`templates/stack/python.md`, `typescript.md`, `jvm.md`, `dotnet.md`).
Load only the variant you need.

**Do not continue without this file**: the hooks read it, and without it they
degrade to silent no-ops. For Python, unless told otherwise, propose `uv` and
`uv run pytest`.

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

Skip the four architectural axes. Close only: Round 0, what the prototype must
demonstrate, which real infrastructure it must cross, and which question counts
as answered at the end. Two rounds maximum, then build.

## Next

When the frontier is empty and the user has confirmed, invoke `to-spec`.
