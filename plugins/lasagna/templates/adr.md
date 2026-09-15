# ADR-NNNN — <title of the decision>

File: `docs/adr/NNNN-slug.md`. Sequential numbering: scan `docs/adr/`, take the
highest, increment. Create the directory only when the first ADR is needed.

status: proposed | accepted | superseded-by-ADR-NNNN
date: YYYY-MM-DD
origin_feature: FEAT-NNN

## Context

What the situation was and what pressure made a decision necessary. Facts, not
opinions. Two to five sentences.

## Decision

What we decided, in the present tense: "the write model is event-sourced", not
"we decided it would be better to...".

## Alternatives rejected

At least one, with the specific reason it was rejected. If there were no
plausible alternatives, **this ADR should not be written**.

- **<alternative>**: rejected because ...

## Consequences

What gets easier and what gets harder. Include the non-obvious effects: the
obvious ones help nobody in two years.

---

## When to write an ADR

All three, or no ADR:

1. **Hard to reverse**: changing your mind later costs meaningfully.
2. **Surprising without context**: a future reader will look at the code and ask
   "why this way?".
3. **The result of a real trade-off**: there were genuine alternatives and we
   picked one for specific reasons.

If one is missing, the decision lives in the code and the tests, not here.

**Qualifies**: architectural shape, integration between contexts, technology with
lock-in, non-obvious aggregate boundaries, deliberate deviations from the obvious
path, constraints not visible in the code.

**Does not qualify**: library choices replaceable in an afternoon, naming
conventions, anything the linter already enforces.
