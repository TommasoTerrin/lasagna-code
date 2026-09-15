---
name: freeze-contract
description: Freezes the interface contract (signatures, error types, return shape, ports) from the domain model before any TDD loop starts, and runs the contract approval gate. Use after domain-modeling in lasagna, or when a contract must be unfrozen because a requirement changed.
---

# freeze-contract

**Trigger**: the domain model is closed. Or: a requirement changed and the
frozen contract no longer holds.

The contract is **the only thing `test-writer` and `implementer` share**. They
never see each other. Anything not written here, they will each invent
differently, and the loop will burn cycles on a disagreement neither can see.

**Whoever writes the contract does not implement it.** This skill runs in the
main thread, never inside the implementer.

## Procedure

1. Read the domain model and `.lasagna/stack.md` (you need the language syntax).
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

## The three failures that cost the most cycles

**Two return conventions in one contract.** Exception, `Result`/`Either`, tuple,
`None` — pick **one** for everything. The worst case is a contract where half the
functions raise and half return a Result: the test-writer writes tests in one
convention, the implementer writes code in the other, and the resulting red tells
nobody anything.

**Error types that do not match the spec's taxonomy.** Map them 1:1. If the spec
lists five errors and the contract has three, either the spec is wrong or the
contract is incomplete. Settle it now.

**Non-determinism not declared as a port.** Time, randomness and environment
enter as a parameter or as a port, never as a direct call inside the core.
`check-onion.sh` enforces this mechanically on every write: if the contract does
not declare the port, the hook will block the implementer on a violation that was
predictable here.

## Example

Weak — ambiguous convention, untyped error, implicit time:

```python
def cancel_order(order_id: str) -> bool: ...
```

`False` means "not cancellable", "not found", or "already cancelled"? The
test-writer has to guess. And the "less than 24h since shipping" rule needs the
current time, which is absent — so the implementer will reach for
`datetime.now()` inside the domain and the hook will stop it.

Strong:

```python
def cancel_order(order: Order, now: Instant) -> Result[Order, CancelError]: ...

class CancelError(Enum):
    ALREADY_CANCELLED = "already_cancelled"   # ERR-003
    SHIPPED           = "shipped"             # ERR-004
    WINDOW_EXPIRED    = "window_expired"      # ERR-005
```

One convention, errors mapped to spec codes, time injected.

## Human gate 2 of 3 — contract approval

**Not automatable.** Present compactly: the chosen seams and why, every
signature, the single return convention, the error table, the required ports.
Ask for approval explicitly.

When it comes: write `approved_by` and the date, set `phase: tdd-loop`,
`layer: domain`, `budget_max` from the profile's `budget_domain`,
`cycles_used: 0`, and invoke `tdd-loop`.

## Unfreezing

The contract changes only by stopping the loop: set `active_role: none`, update
the contract, re-approve with the human, reset `cycles_used` for the criterion in
flight, restart. A contract changed quietly while the loop runs produces a red
the referee cannot classify.
