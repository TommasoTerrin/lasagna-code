# Contributing to lasagna

Thank you for considering contributing to lasagna! This document provides guidelines and instructions.

---

## 🎯 Code of Conduct

Please read and follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 🚀 How to Contribute

### Reporting Bugs

Before opening an issue, **check existing issues** (closed and open).

**When you open a bug report, include:**

1. **Title** — concise, what's broken
2. **Environment** — OS, Claude Code version, stack (Python/TS/JVM/.NET)
3. **Reproduction steps** — exact commands to trigger
4. **Expected vs actual** — what should happen, what happens
5. **Stack trace or logs** — if applicable
6. **Screenshots** — if UI-related

**Example:**
```
Title: Hook block-test-edits silently fails on Windows

Environment:
- OS: Windows 11 Pro
- Claude Code: 0.1.42
- Stack: Python

Steps:
1. Initialize lasagna: /lasagna-init
2. Try to edit test_*.py as implementer
3. Hook does not block (should block with exit 2)

Expected: Edit blocked, error message
Actual: Edit succeeds, no hook output

Logs:
[stderr] hook: PostToolUse on Edit returned undefined
```

---

### Suggesting Enhancements

**Before opening:** check existing issues and PRs for related work.

**When you suggest a feature, include:**

1. **Use case** — why is this needed? Who needs it?
2. **Current behavior** — what does lasagna do now?
3. **Proposed behavior** — what should it do?
4. **Alternatives considered** — other solutions you've thought of
5. **Additional context** — links, examples, proof-of-concept

**Example:**
```
Title: GitHub Issues integration for auto-AC-extraction

Use case:
Teams using GitHub Issues want lasagna to auto-extract acceptance 
criteria from issue comments, bypassing /lasagna-init grilling.

Current behavior:
User manually types AC in /lasagna official → to-spec flow.

Proposed behavior:
/lasagna github myteam/myrepo#42
→ Fetch issue, parse comments for "AC: ..." lines
→ Auto-populate spec with those AC
→ Start tdd-loop (skipping to-spec)

Alternatives:
- Manual AC entry (current, tedious at scale)
- GitHub Action to sync issues → .lasagna/specs/ (could work, but async)

Related issues:
- #15 (GitHub integration discussion)
```

---

### Submitting Changes

#### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/lasagna-code.git
cd lasagna-code
git checkout -b feature/what-you-are-adding
```

#### 2. Make Changes

**For skills/agents:**
- Edit `.md` files in `plugins/lasagna/skills/` or `plugins/lasagna/agents/`
- Keep prompts concise and unambiguous
- Prove the change with the eval suite: a case that fails before and passes after
  (`plugins/lasagna/evals/`)

**For hooks/scripts:**
- Python ≥ 3.9, **standard library only** — users never `pip install` anything
- Decisions go in `scripts/lasagna_lib/core/` as **pure functions** (text and
  dicts in, a decision out), tested by passing values, no mocks; I/O goes in
  `scripts/lasagna_lib/shell/`
- `scripts/run.sh` is the only shell script: it finds Python and nothing else
- A blocking hook exits 0 or 2, never anything else: any other code is a
  non-blocking error to Claude Code, and the guardrail would vanish silently
- Hooks only where a mechanical truth is needed (test outcome, isolation,
  budget, state). Architecture and style are the model's judgement

**For templates:**
- Keep minimal but complete
- Include examples (not just headings)
- Test that templates work with hook validation

#### 3. Run Local Validation

```bash
# Validate plugin structure
claude plugin validate .

# Hooks: lint and tests (pytest and ruff are dev tools, not plugin dependencies)
ruff check plugins/lasagna/scripts tests tools
python -m pytest

# Try a hook by hand
export CLAUDE_PROJECT_DIR=/path/to/test/project
echo '{"tool_name":"Read","agent_type":"lasagna:implementer","tool_input":{"file_path":"tests/test_x.py"}}' \
  | sh plugins/lasagna/scripts/run.sh hook block-reads; echo "exit $?"

# Skills and agents: the fast eval suite (from a terminal where claude is logged in)
cd plugins/lasagna && claude plugin eval . --tag fast --scaffold --allow-tools Write Edit --no-publish
```

#### 4. Commit & Push

```bash
git add .
git commit -m "feat(skills): add mutation-testing skill

- New skill for adversarial review: mutate implementation, verify tests catch mutations
- Supports Python pytest, TypeScript jest, JVM pitest
- Integrates with adversarial-review skill
- Fixes #189"

git push origin feature/what-you-are-adding
```

**Commit message format:**
```
type(scope): subject

body (optional)

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
Scope: `skills`, `agents`, `hooks`, `templates`, `scripts`, `docs`

#### 5. Open Pull Request

**Title:** Same as commit message (short)

**Description:**
```markdown
## What

Brief summary of what this PR does.

## Why

Why is this change needed? What problem does it solve?

## How

How does it work? Any new dependencies, breaking changes?

## Testing

How did you test it? Include steps to reproduce.

- [ ] Ran /lasagna official flow
- [ ] Ran /lasagna bugfix flow
- [ ] Tested on [macOS/Linux/Windows]
- [ ] No new warnings/errors

## Checklist

- [ ] Commit message follows format
- [ ] No breaking changes (or documented in PR)
- [ ] Skills/agents are concise and unambiguous
- [ ] Hook code: Python stdlib only, decisions in `core/` with tests, `pytest` green
- [ ] Skill/agent changes: fast eval suite run, no case regressed
- [ ] New templates include examples
- [ ] Changes tested on target stack (Python/TS/JVM/.NET)

## Related

Fixes #123, relates to #456
```

---

## 📋 Contribution Types

### 1. Bug Fixes

**Level:** Easy → Hard  
**Expected time:** 1–8 hours

```
Identify bug → Create test case → Fix → PR
```

**Good first issues:** Check [GitHub Issues labeled `good-first-issue`](https://github.com/TommasoTerrin/lasagna-code/issues?q=label%3Agood-first-issue)

### 2. Documentation

**Level:** Easy  
**Expected time:** 1–4 hours

- Typos, clarity improvements
- Add examples to README or skills
- Write tutorial for new use case
- Translate README to new language

### 3. Stack Profile Contributions

**Level:** Medium  
**Expected time:** 2–4 hours

lasagna ships with Python/TypeScript/JVM/.NET profiles. Add yours:

```bash
# Example: Go stack profile
cp plugins/lasagna/templates/stack/typescript.md plugins/lasagna/templates/stack/go.md

# Edit:
# - test_command: go test ./...
# - test_command_pattern, fail_*_pattern, pass_pattern: for the runner's output
# - test_file_pattern: _test\.go$
# - source_path: where production code lives
```

Add real runner output to `tools/capture_golden.py` (it runs the runner on tiny
projects and records the outcome) so `tests/core/test_golden.py` verifies your
patterns. Never transcribe output by hand.

**Submit as:** PR with new stack profile + documentation

### 4. Skills & Agents

**Level:** Hard  
**Expected time:** 8–40 hours

New skills integrate with the existing flow. Examples:

- **Mutation Testing skill** — fourth agent writes code mutations, verify tests catch them
- **Schema Analysis skill** — extract entity model from database schema, compare with domain model
- **Cost Estimator skill** — estimate Claude API token spend per cycle, track over time

**Before starting:**
1. Open a discussion: explain what and why
2. Get feedback from maintainers
3. Design the integration: which flow does it fit? What does it need from the harness?
4. Write skill definition (structured prompts)
5. Create tests/examples

### 5. Integrations

**Level:** Hard  
**Expected time:** 8–80 hours (depending on scope)

Future integrations:

- **GitHub Issues** — fetch issues, auto-extract AC, PR comments
- **Linear / Asana** — sync tickets, update status
- **Slack** — notifications, async handoff
- **VS Code Extension** — run /lasagna inside editor
- **CI/CD** — GitHub Actions, GitLab CI to run adversarial review on PR

**Before starting:** Open a discussion, get design feedback.

---

## 🛠️ Development Setup

### Clone & Install

```bash
git clone https://github.com/TommasoTerrin/lasagna-code
cd lasagna-code

# Link as local plugin
ln -s $(pwd) ~/.claude/plugins/lasagna-dev

# Or via settings.json
# Add to .claude/settings.json:
# "plugins": ["./path/to/lasagna-code"]

# Restart Claude Code
```

### Run Tests

```bash
# Validate plugin
claude plugin validate .

# Hook tests: core (pure, fast) and shell (runs run.sh end to end)
python -m pytest
python -m pytest tests/core        # only the pure ones

# Regenerate golden runner outputs (needs the runners installed)
python tools/capture_golden.py

# Eval suite, and comparing two versions of the plugin
# see plugins/lasagna/evals/README.md
```

CI runs ruff and pytest on Python 3.9 and 3.12, on Ubuntu and Windows, and
shellcheck on `run.sh`.

### Iterate

1. Make changes to `.md` files or scripts
2. Restart Claude Code (or reload plugin)
3. Run `/lasagna-init` in test project
4. Start a flow (`/lasagna official`)
5. Check output, logs, hook behavior

---

## 📊 Reviewer Checklist

When reviewing a PR, check:

- [ ] **Clarity**: Prompts are clear, unambiguous, no jargon
- [ ] **Completeness**: No half-finished implementations
- [ ] **Compatibility**: Works across Python/TypeScript/JVM/.NET stacks
- [ ] **Backward compat**: No breaking changes without documentation
- [ ] **Hooks**: Python stdlib only, pure decisions in `core/` with tests, exit codes 0/2 only
- [ ] **Testing**: Tested on multiple stacks/OS
- [ ] **Docs**: README/comments explain new behavior
- [ ] **Commit message**: Follows format, links issues

---

## ❓ Questions?

- **Bugs** → [GitHub Issues](https://github.com/TommasoTerrin/lasagna-code/issues)
- **Security** → Email tommaso@terrin.eu with `[SECURITY]` in subject

---

## 🙏 Thank You

Thank you for contributing! Your work makes lasagna better for everyone.

---

**Questions about this file?** Open a discussion or email tommaso@terrin.eu.
