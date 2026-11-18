# Resuming From an Existing Ledger

Part of superpowers:subagent-driven-development. This plan's workspace
already has a ledger at `<workspace>/progress.md`.

If the ledger's first line names your plan file, tasks with a `Task <N>:
complete` line are DONE — do not re-dispatch them; resume at the first
task without one. Tasks with a `Task <N>: BLOCKED` line stay blocked — do
not re-dispatch them either. A task whose last line is a `suite red, retry`
line is mid-verification: resume it at step 3 with the retries it has left.
A ledger whose first line names a
different plan file — or a stray ledger at the old flat path
`.superpowers/sdd/progress.md` — is another plan's progress: leave it in
place and start your own, fresh.
