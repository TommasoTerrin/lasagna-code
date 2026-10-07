---
name: freeze-contract
description: Freezes the interface contract (signatures, error types, return shape, external dependencies and how tests control them) from the domain model before any TDD loop starts, and runs the contract approval gate. Use after domain-modeling in lasagna, or when a contract must be unfrozen because a requirement changed.
---

# freeze-contract

**Trigger**: the domain model is closed. Or: a requirement changed and the
frozen contract no longer holds.

The contract is **the only thing `test-writer` and `implementer` share**. They
never see each other — the implementer cannot even read the tests. Anything not
written here, they will each invent differently, and the loop will burn cycles
on a disagreement neither can see.

**Whoever writes the contract does not implement it.** This skill runs in the
main thread, never inside the implementer.

## Procedure

1. Read the domain model, `.lasagna/architecture.md` and `.lasagna/stack.md`
   (you need the language syntax).
2. Choose the **seams**: the public boundary the tests will live on. Prefer
   existing seams to new ones, and the highest seam possible. The fewer the
   better; one is ideal.
3. Fill `${CLAUDE_PLUGIN_ROOT}/templates/contract.md` into
   `.lasagna/contracts/FEAT-NNN.md`. The template carries the structure — follow
   it rather than restating it.
4. Check coverage: **every acceptance criterion must be expressible through at
   least one seam.** If one is not, a public operation is missing — add it now,
   not mid-loop.
5. Stop at the gate.

## Signatures on an existing codebase

The signatures follow the conventions in `architecture.md` — the project's
error style, its dependency injection, its naming — even where lasagna would
choose otherwise. If you see a better shape, write it as an entry in
`.lasagna/design-notes.md` (what, why, estimated cost, `proposed`) and freeze
the conventional one. A contract that quietly migrates the code towards another
architecture turns every feature into a refactoring nobody approved.

## The three failures that cost the most cycles

**Two return conventions in one contract.** Exception, `Result`/`Either`, tuple,
`None` — pick **one** for everything. The worst case is a contract where half the
functions raise and half return a Result: the test-writer writes tests in one
convention, the implementer writes code in the other, and the resulting red tells
nobody anything.

**Error types that do not match the spec's taxonomy.** Map them 1:1. If the spec
lists five errors and the contract has three, either the spec is wrong or the
contract is incomplete. Settle it now.

**Non-determinism with no row in the External dependencies table.** Time,
randomness, environment, storage, network: each needs a row saying how the code
reaches it and how a test controls it. Without one, the test-writer fixes the
clock one way and the implementer reads it another, and the red is about the
disagreement, not the behaviour. The usual answers, cheapest first: move the I/O
to the shell so the logic takes plain values; a parameter (`now`); a function;
a `Protocol`/interface only when the technology may really change, the test must
replace something slow or non-deterministic, or two implementations already
exist.

## Example

Weak — ambiguous convention, untyped error, implicit time:

```python
def cancel_order(order_id: str) -> bool: ...
```

`False` means "not cancellable", "not found", or "already cancelled"? The
test-writer has to guess. The "less than 24h since shipping" rule needs the
current time, which is absent — so the implementer reaches for `datetime.now()`
and the test cannot control it. And loading the order by id puts storage inside
the decision.

Strong:

```python
def cancel_order(order: Order, now: datetime) -> Result[Order, CancelError]: ...

class CancelError(Enum):
    ALREADY_CANCELLED = "already_cancelled"   # ERR-003
    SHIPPED           = "shipped"             # ERR-004
    WINDOW_EXPIRED    = "window_expired"      # ERR-005
```

One convention, errors mapped to spec codes, time passed in, and no storage at
all: the shell loads the order, calls `cancel_order`, saves the result. The test
builds an `Order`, picks a `now`, and checks the value that comes back — no
fake, no mock.

## Human gate 2 of 3 — contract approval

**Not automatable.** Present compactly: the chosen seams and why, every
signature, the single return convention, the error table, the External
dependencies table, and any design notes you raised. Ask for approval
explicitly.

When it comes: write `approved_by` and the date, set `phase: tdd-loop`,
`current_slice` to the first slice, `cycles_used: 0`, and invoke `tdd-loop`.

## Unfreezing

The contract changes only by stopping the loop: set `active_role: none`, update
the contract, re-approve with the human, reset `cycles_used` for the criterion in
flight, restart. A contract changed quietly while the loop runs produces a red
the referee cannot classify.
