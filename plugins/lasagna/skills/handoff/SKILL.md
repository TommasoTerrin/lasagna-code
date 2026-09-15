---
name: handoff
description: Compresses the session into a handoff document for an agent starting from nothing. Use before ending a session, before an expected compaction, or when the user asks for a handoff or to pass work to another session.
---

# handoff

**Trigger**: the session is ending, the context is about to be compacted, or the
work is passing to someone else.

Write a document that lets an agent **who has seen nothing** resume where you
are. Save it to the OS temp directory, **not** the workspace: it is not a project
artifact.

## The phase state comes first

lasagna already has a memory that survives compaction:
`.lasagna/state/FEAT-NNN.state.md`. Update it **before** writing the handoff —
phase, cycles used, criteria covered by id, escalation, and above all the next
checkpoint.

```bash
sh "${CLAUDE_PLUGIN_ROOT}/scripts/set-state.sh" --append "- [$(date -u +%FT%RZ)] <what I was about to do and how to resume>"
```

If the phase state is current, the handoff can be short. If it is not, no amount
of handoff fixes it: at the next compaction the document is out of context while
the file on disk is still there.

## Do not duplicate

Do not copy what is written elsewhere. Spec, frozen contract, ADRs,
`CONTEXT.md`, phase state, issues, diffs and commits get cited by path or URL.

A handoff that repeats the spec is a handoff that will drift from the spec, and
the reader will not know which one is true.

## What to put in, then

Only what lives in your head alone:

- **Where I got to**: the last thing that worked, the first that does not.
- **What I tried that failed, and why.** The most valuable part and the only
  unrecoverable one: without it the next agent walks the same dead ends.
- **Hypotheses still standing**, and which observation separates them.
- **Decisions made in conversation** that never reached an ADR or the spec — and
  if one deserved an ADR, write it now instead of putting it here.
- **Traps**: the test that fails misleadingly, the command that needs a specific
  directory, the service that must be running first.
- **Skills to invoke next**, in order.

## Format

```md
# Handoff — <feature / topic> — <date>

## State
Phase: <phase>. Authoritative reference: <phase state path>.
One line on where I got to.

## Artifacts (not copied here)
- spec: <path>
- contract: <path>
- phase state: <path>
- branch / PR: <reference>

## Next concrete step
<A single action, imperative. Not a list of intentions.>

## Already tried, and why it did not work
- ...

## Open hypotheses
- <hypothesis> -> separated by observing <what>

## Traps
- ...

## Skills to invoke
1. <skill> — why
```

## Rules

- **Redact**: no API keys, passwords, personal data. If a value is needed, write
  where it lives, not what it is.
- **The next step is one.** A list of five possible things is not a handoff, it
  is a deferred decision.
- **Imperative.** "Run X, and if it fails with Y then Z" executes. "It would be
  worth considering verifying" does not.
- **Short.** Past two screens you are duplicating an artifact: delete it and put
  the path.
