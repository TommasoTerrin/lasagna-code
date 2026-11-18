# Third-Party Notices

## Superpowers

The skills in this directory are a vendored, modified subset of Superpowers.

- **Source:** https://github.com/obra/superpowers
- **Version:** tag `v7.0.2` (commit `22f0b463e7a5e579904dd6211a520321035526f7`)
- **License:** MIT

```
MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Skills copied

Copied from `skills/` with all their supporting files:

- `using-superpowers`
- `brainstorming`
- `writing-plans`
- `subagent-driven-development`
- `test-driven-development`
- `verification-before-completion`
- `using-git-worktrees`
- `finishing-a-development-branch`

No other upstream skill is included.

### Modifications

**subagent-driven-development**

- Removed the per-task review, the final whole-branch review, and the review
  fix loop.
- Deleted `task-reviewer-prompt.md`, `re-review-prompt.md`,
  `references/fix-loop.md`, `references/final-review.md`,
  `references/cannot-verify.md` (only handled task-reviewer verdicts), and
  `scripts/review-package`.
- `SKILL.md` rewritten around a controller-run verification step: after the
  implementer reports DONE, the controller checks that the task's commit
  exists and runs the entire test suite itself; a red suite resumes the same
  implementer with the failure output, at most 2 times; a task still red is
  marked BLOCKED in the ledger with its reason, tasks that depend on it stay
  blocked, and independent tasks continue. At the end of the plan the
  controller runs the entire suite once more, writes a summary (completed
  tasks, blocked tasks, decisions) to the ledger, and moves to
  `finishing-a-development-branch`. Setup now records the suite command, a
  baseline run, and per-task dependencies in the ledger. The workspace is
  kept at the end, since the ledger holds the summary. Removed the inline
  execution branch of "When to Use" and the comparison with it.
  Unchanged: a fresh subagent per task, continuous execution without pauses,
  the four stop conditions, the ledger, and resuming after compaction.
- `implementer-prompt.md`: removed references to the controller-dispatched
  reviewer; the "After Review Findings" section became "If the Controller's
  Suite Run Fails". TDD, self-review, and reporting test commands with their
  output are unchanged.
- `references/handling-reports.md`, `references/preflight.md`,
  `references/batching.md`, `references/resuming.md`: review wording replaced
  with verification wording; resuming covers BLOCKED tasks and red-suite
  retries.
- `scripts/sdd-workspace`, `scripts/sdd-repo`: comments only (no more
  mentions of the deleted script or of skills outside this subset). No
  behavior change.

**writing-plans**

- The plan header and the execution handoff name `subagent-driven-development`
  as the only execution method (the inline / "Native" option was removed).

**using-superpowers**

- Skill Priority: the debugging skill (not included) replaced with
  `test-driven-development` (a bug starts from a failing test that reproduces
  it).
- `references/codex-tools.md`, `references/gemini-tools.md`,
  `references/muse-tools.md`, `references/claude-code-tools.md`: removed
  mentions of skills and prompt templates not included in this subset, and of
  SDD reviewers.

**test-driven-development**

- `writing-good-tests.md`: removed a reference to a skill not included in
  this subset.

All other files are unmodified copies of the upstream v7.0.2 sources.
