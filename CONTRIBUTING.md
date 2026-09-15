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

**Before opening:** check [GitHub Discussions](https://github.com/TommasoTerrin/lasagna-code/discussions).

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
- Test by running `/lasagna` flows end-to-end

**For hooks/scripts:**
- POSIX sh (no jq, Python, Node — must run anywhere)
- Test on macOS, Linux, Windows (Git Bash or WSL)
- Document environment variables at top of file

**For templates:**
- Keep minimal but complete
- Include examples (not just headings)
- Test that templates work with hook validation

#### 3. Run Local Validation

```bash
# Validate plugin structure
claude plugin validate ./lasagna-code

# Test a skill
/lasagna official
# Go through one flow, check for typos or logic errors

# Test hooks on your stack
export CLAUDE_PROJECT_DIR=/path/to/test/project
bash plugins/lasagna/scripts/block-test-edits.sh
bash plugins/lasagna/scripts/check-onion.sh
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
- [ ] Scripts are POSIX sh (no dependencies)
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
# - test_file_pattern: **/*_test.go
# - core_path_pattern: internal/(domain|model)/
# - forbidden_patterns: regex for I/O you want to block
```

Include test output samples so hook can classify green/red.

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
claude plugin validate ./

# Test individual hook (Unix/Linux/macOS)
bash plugins/lasagna/scripts/block-test-edits.sh

# On Windows (Git Bash)
bash plugins/lasagna/scripts/block-test-edits.sh
```

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
- [ ] **Scripts**: POSIX sh only, no external dependencies
- [ ] **Testing**: Tested on multiple stacks/OS
- [ ] **Docs**: README/comments explain new behavior
- [ ] **Commit message**: Follows format, links issues

---

## ❓ Questions?

- **General questions** → [GitHub Discussions](https://github.com/TommasoTerrin/lasagna-code/discussions)
- **Bugs** → [GitHub Issues](https://github.com/TommasoTerrin/lasagna-code/issues)
- **Security** → Email tommaso@terrin.eu with `[SECURITY]` in subject

---

## 🙏 Thank You

Thank you for contributing! Your work makes lasagna better for everyone.

---

**Questions about this file?** Open a discussion or email tommaso@terrin.eu.
