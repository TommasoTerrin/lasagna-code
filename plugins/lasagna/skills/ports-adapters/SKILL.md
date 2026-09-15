---
name: ports-adapters
description: Adapter phase — implements the ports against real infrastructure, separating world constraints (which belong to the domain) from vendor choices (which stay in the adapter), and closes with end-to-end tests and the PR gate. Use after adversarial-review in lasagna.
---

# ports-adapters

**Trigger**: the domain is green, traceable and has survived adversarial review.
Now you touch the world.

Budget: **5**, not 3. Real infrastructure surprises you in ways the domain does
not, and the surprise is information rather than failure.

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" layer adapter
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" budget_max 5
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" cycles_used 0
```

## The distinction that decides everything

Building the adapter you will discover constraints the domain did not know
about. Each one goes in one of two buckets, and putting it in the wrong one is
how an onion architecture rots from the outside in.

**World constraint** — would still be true with a different vendor, library or
technology. Belongs to the **domain**: go back up, update spec and contract,
re-approve.

> A payment already captured is not cancelled, it is refunded. No vendor makes
> the inverse operation true. That is a domain rule.

**Vendor choice** — true for *this* vendor, *today*. Stays in the **adapter** and
appears nowhere else.

> The field is called `customer_ref` and holds 32 characters. The domain knows
> there is a reference to the Customer; it does not know its width.

The test: **if we change vendor tomorrow, does this change?** Yes → adapter.
No → domain.

When a world constraint surfaces here, do not "enforce it in the adapter because
it is faster". A domain invariant enforced in an adapter stops holding the moment
a second adapter appears — and one always does.

## Building an adapter

1. One port at a time. Its signature is already in the frozen contract and is not
   negotiable here. If it does not survive contact with real infrastructure, you
   unfreeze the contract; you do not quietly widen the adapter.
2. Write an integration test against **real** infrastructure first (container,
   sandbox, temp file). Not a mock: a mock verifies that the adapter does what
   you believed the vendor does, which is the very assumption under test.
3. Implement the minimum. Red-green as always, `test-writer` and `implementer`
   still separate.
4. Translate vendor errors into the contract's error types. An HTTP status or a
   database constraint surfacing in the domain is a leak, and sooner or later
   someone writes a business rule on top of it.

No business rules in adapters. If you find yourself writing an `if` on a domain
value inside an adapter, that rule belongs to the domain.

## End-to-end tests

Few, high, on the path that matters. Not one per criterion — the criteria are
already covered by domain tests, and repeating them end-to-end buys slowness
without buying information.

An e2e earns its place when it verifies the **wiring**: that the whole path, from
the system edge to the database and back, is connected the way you think. That is
the only thing no domain test can tell you.

Pick one per main use case. If you need many more, something that belongs in the
domain has probably ended up in the wiring.

## Before closing

No business rules in adapters. No vendor types visible from the domain. Every
vendor error translated. World constraints surfaced here pushed back up into spec
and contract rather than frozen into the adapter. Whole suite green.

Then set `phase: gate-pr`.

## Human gate 3 of 3 — PR review

**Not automatable.** No auto-merge in the official flow.

The PR presents, in this order:

1. **The spec diff**, not just the code diff: what changed in the contract
   between approval and now, and why.
2. **The traceability table**: every criterion with the test covering it. Paste
   the output of `check-traceability.sh`.
3. **The adversarial report**, including "unrequested code" and "risks not
   covered by the spec".
4. **Cycles consumed** and any escalation along the way.

After merge: move the spec to `.lasagna/specs/archive/`, check the ADRs and
`CONTEXT.md` reflect what you learned, delete the phase state.
