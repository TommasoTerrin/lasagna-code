# lasagna eval suite

Measures whether a change to the plugin makes Claude follow the process better
or worse. Built on `claude plugin eval` (Claude Code ≥ 2.1.276).

Each case scaffolds a tiny throwaway project (`fixture.sh`, sharing
`_lib/project.sh`), gives Claude one prompt, and grades the run: deterministic
graders where possible (which skill fired, which files were written, what the
hooks said), an LLM judge with a rubric where only judgement works.

## Cases

| Case | Tags | What it checks |
|---|---|---|
| `routing-bugfix` | fast | a defect report goes to `characterize-bugfix`; no fix before a test |
| `routing-official` | fast | a decided feature goes to `grilling` |
| `routing-brownfield` | fast | code with no spec goes to `reverse-spec-brownfield` |
| `gate-spec` | fast | a feature request stops at a human gate; no production code written |
| `isolation-implementer` | fast | with `active_role: implementer`, reading a test file is denied by the hook |
| `isolation-test-writer` | fast | with `active_role: test-writer` in `tdd-loop`, reading production code is denied |
| `proportionality` | fast | a trivial rename skips phases and says which |
| `adaptation-brownfield` | fast | on a FastAPI-style project: no `ports/`/`adapters/` created; existing conventions recorded in `architecture.md` |
| `architecture-greenfield` | fast | a new project gets the separation-level question, with a recommendation |
| `e2e-small-feature` | slow, release | an approved feature runs the whole loop to the PR gate |

## Running

From a terminal where `claude` is logged in (the eval runs are child `claude`
processes on your own credentials — they do not inherit a desktop-app session):

```bash
cd plugins/lasagna
claude plugin eval . --tag fast --scaffold --allow-tools Write Edit --no-publish
```

- `--scaffold` runs the cases' `fixture.sh`: these are this repo's own scripts.
- The default `--ablation with-without` adds a no-plugin arm, so every score
  comes with a delta: how much of the behaviour is the plugin's doing.
- `--runs 5` or more before comparing versions: with 3 runs a single flaky run
  moves a case by a third.
- `--max-cost-usd` sets a hard ceiling.

The slow suite needs `Bash` (it runs the tests). On Windows the eval runner
refuses to grant shells without an OS sandbox, so run it on Linux or macOS:

```bash
claude plugin eval . --tag release --scaffold --allow-tools Write Edit Bash Agent --max-cost-usd 10 --no-publish
```

## Comparing two versions

`claude plugin eval` compares the plugin against no plugin, not two versions of
it. To compare, run the same suite on both checkouts and diff the results:

```bash
git worktree add ../lasagna-prev <previous tag or branch>
cp -r plugins/lasagna/evals ../lasagna-prev/plugins/lasagna/   # v1 has no suite of its own
(cd ../lasagna-prev/plugins/lasagna && claude plugin eval . --tag fast --runs 5 --scaffold --allow-tools Write Edit --no-publish --json ../../prev.json)
(cd plugins/lasagna && claude plugin eval . --tag fast --runs 5 --scaffold --allow-tools Write Edit --no-publish --json ../../new.json)
python tools/compare_evals.py ../lasagna-prev/prev.json new.json
```

Keep the reference results of each release in `baselines/` (`v0.1.0.json`,
`v0.2.0.json`, …): they are what the next release is compared against. Some
cases test behaviour v1 never had (isolation of reads, separation level,
adaptation): v1 scoring low there is the point, not a bug in the case.

## Writing a case

`case.yaml` (`schema_version: "1.1"`), the prompt under `execution.prompt`, a
`fixture.sh` that sources `../_lib/project.sh`. Prefer graders that do not need
a judge: `tool_used` on `Skill` with `input_match` for routing, `tool_used` with
`max: 0` for "never wrote production code", `regex` on `target: trace` for what a
hook printed, `file_exists` for files that must not appear.
