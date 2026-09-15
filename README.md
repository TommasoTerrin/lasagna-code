# 🍝 lasagna

![lasagna hero](.github/assets/hero.jpg)

**Layered Spec-Driven Development for Claude Code**

[🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)

*The opposite of spaghetti code.* A Claude Code plugin that brings structure to software development through precise specifications, domain modeling, frozen contracts, and a mechanically isolated red-green loop.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://github.com/TommasoTerrin/lasagna-code)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](#stack-agnostic)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.5+-blue)](#stack-agnostic)
[![JVM](https://img.shields.io/badge/JVM-11+-red)](#stack-agnostic)
[![.NET](https://img.shields.io/badge/.NET-6+-purple)](#stack-agnostic)

---

## 🎯 What is lasagna?

Lasagna is a structured approach to software development that combines five proven disciplines:

1. **Spec-Driven Development** — precise specifications approved before code
2. **Test-Driven Development** — one test per cycle, written before implementation
3. **Domain-Driven Design** — pure domain core with clear aggregate boundaries
4. **Hexagonal/Onion Architecture** — infrastructure adapters isolated from domain
5. **Agentic Loop Engineering** — isolated agents (test-writer, implementer, referee) with mechanical guardrails

Each layer is **distinct, separated, and has a clear purpose**. You can pull one layer out, understand it in isolation, and rebuild it. Try that with spaghetti.

### Why lasagna, not spaghetti?

| Problem | Spaghetti Code | lasagna |
|---------|---|---|
| **No clear spec** | 🔴 Ambiguity breeds 3x cycles | 🟢 Spec approval gate before code |
| **Test-code coupling** | 🔴 Tests follow implementation | 🟢 Test-writer ≠ Implementer (mechanical isolation) |
| **Tangled layers** | 🔴 UI logic in domain, I/O everywhere | 🟢 Core pure, adapters isolated, hook-enforced |
| **Silent failures** | 🔴 Budget overruns, regressions | 🟢 Cycle budget + adversarial review |
| **No traceability** | 🔴 Acceptance criteria drift | 🟢 AC ↔ Test mapping verified |

---

## 🚀 Quick Start

### Installation

#### Option A: Global (Recommended for CLI users)

```bash
# Add to Claude Code marketplace
claude plugin marketplace add TommasoTerrin/lasagna-code

# Install
claude plugin install lasagna

# Restart Claude Code to load hooks
```

#### Option B: Local (For a single project)

```bash
# Clone into your project
git clone https://github.com/TommasoTerrin/lasagna-code lasagna-code

# Add to local plugins (in Claude Code settings)
# Or link via symlink:
ln -s $(pwd)/lasagna-code ~/.claude/plugins/lasagna
```

### Initialize Your Project

```bash
# In your project root
/lasagna-init

# Choose your stack: Python, TypeScript, JVM, or .NET
# Creates: .lasagna/, .lasagna/stack.md, updates .gitignore
```

**Verify installation:**
```bash
/lasagna-status
# Shows: plugin version, stack profile, readiness
```

> **Note:** All guardrails remain inactive until `.lasagna/stack.md` exists. If nothing blocks, the profile is missing — run `/lasagna-init`.

---

## 📊 Four Workflows for Different Scenarios

### 1. Official Flow → New feature (greenfield)

**When:** You have a **decided feature**, budget, and clear vision.

```bash
/lasagna official
```

**Flow:**
```
📝 Grilling (Socratic interview)
   ↓ Discover stack profile, architectural constraints
🟨 GATE 1: Spec Approval (human decision)
   ↓
🧬 Domain Modeling (aggregates from invariants)
   ↓
❄️ Freeze Contract (public signatures, error types, ports)
   ↓
🟨 GATE 2: Contract Approval (human decision)
   ↓
🔴🟢 TDD Loop (test-writer + implementer, budget 3 domain)
   ↓ Hook: Implementer cannot edit test files
   ↓ Hook: Domain core layering rules enforced
   ↓ Hook: Cycle budget counted
   ↓
⚔️ Adversarial Review (hunt gaps: missing errors, invariant stress, edges)
   ↓
🔌 Ports-Adapters (real infrastructure, budget 5 adapters)
   ↓
🟨 GATE 3: PR Review (human decision)
   ↓
✅ Merge
```

**Mechanically enforced:**
- ✅ Test-write block (implementer cannot touch test files)
- ✅ Cycle budget (3 for domain, 5 for adapters)
- ✅ Onion layering (domain stays pure)
- ✅ Traceability (AC-NNN must map to tests)

**Human-decided:**
- 👤 Spec captures real requirements
- 👤 Contract is unambiguous
- 👤 PR passes final review

---

### 2. Prototype Flow → Validate an idea

**When:** You have a **question**, not an answer. Need to validate before committing to spec.

```bash
/lasagna prototype
```

**Flow:**
```
📝 Grilling (reduced)
   ↓ Just the research question
🏗️ Build & Validate
   ↓ Walking skeleton on real infrastructure
✅ Demo works?
   ├─ YES → Re-enter Official Flow (becomes a feature)
   └─ NO  → Abandon or pivot
```

**Characteristics:**
- ⚡ No spec, no gates, fast
- 🎯 Goal: answer the question
- 📈 If validated: convert to official feature

**Typical uses:**
- "Does Postgres support our query patterns?"
- "Can we integrate with vendor X's API?"
- "Does hexagonal architecture handle our concurrency model?"

---

### 3. Bugfix Flow → Defect in working code

**When:** Production bug or defect in existing, working code.

```bash
/lasagna bugfix
```

**Flow:**
```
🔍 Characterize
   ↓ Test that PASSES with bug (current behavior)
🔴 Reproduce
   ↓ Test that FAILS with desired behavior
🟢 TDD Loop (budget 5, no spec)
   ↓ Implementer fixes the bug
   ↓
⚔️ Adversarial Review (focus on regressions)
   ↓ Did the fix break something else?
✅ Merge (auto or manual)
```

**Characteristics:**
- 💊 Higher budget (5 vs 3) — bugfixes are messier
- 📋 No spec — test and code only
- 🤖 Can auto-merge if `bugfix_automerge: true` in stack profile

**Typical uses:**
- "Users can't login with accented passwords"
- "Large table queries crash the server"
- "Token expires when it shouldn't"

---

### 4. Brownfield Flow → Legacy code without spec

**When:** Adding a feature to legacy code with no existing spec.

```bash
/lasagna brownfield
```

**Flow:**
```
🔍 Reverse-Spec-Brownfield
   ↓ Extract spec from code:
   ├─ Entry points → use cases
   ├─ Schema → entity model
   └─ Behaviors → acceptance criteria (with sources)
👤 Human Confirm
   ↓ What was intended vs bug vs dead code?
🟨 GATE 1: Approve Extracted Spec
   ↓
→ Continue as Official Flow (domain-modeling onward)
```

**Onion Baseline:** Freeze technical debt, pay it down incrementally

```bash
# On first init, capture all current violations
sh plugins/lasagna/scripts/onion-baseline.sh

# From then on, only NEW violations block
# Check progress:
sh plugins/lasagna/scripts/onion-baseline.sh --check
```

**Characteristics:**
- 📊 Defensive: violations grandfathered into baseline
- 📈 Ratchet: can only improve or stay same, never regress
- 🔄 Safe: existing code works, new code follows rules

---

## 🏗️ Architecture & Principles

### Domain-Driven Core

The domain layer is **pure**: no I/O, no clock, no randomness. All external effects happen in adapters.

```
        🌍 External World (HTTP, DB, Queue, Clock)
        ↑ ↓
    ┌───────────────────┐
    │  Adapter Layer    │  ← I/O, vendor errors, clock
    │  (Ports/Adapters) │  → translate to domain types
    └────────┬──────────┘
             ↓ ↑
    ┌───────────────────┐
    │  Domain Core      │  ← Pure: use cases, invariants
    │  (Entities,       │     Aggregates, Value Objects
    │   Aggregates)     │     No imports from infrastructure
    └───────────────────┘
```

**Why?** A pure core is testable in isolation, portable, and free of vendor lock-in.

### Test Isolation: Mechanical Separation

**Test-Writer** and **Implementer** never share code context:

```
Test-Writer sees:
  ✅ Acceptance Criterion (AC-FEAT-001)
  ✅ Frozen Contract (signatures, types, errors)
  ❌ Implementation (can't see it — hook blocks Reads)

Implementer sees:
  ✅ Test (must pass it)
  ✅ Frozen Contract (what to implement)
  ❌ Acceptance Criterion (might bias implementation)
  ❌ Test file (can't edit — hook blocks Writes)

Referee sees:
  ✅ All three: AC, Test, Code
     Decides: whose fault is disagreement?
```

**Why?** Prevents the test from being a copy-paste of the implementation.

### Fixed Budget: No Silent Overruns

Every feature gets a cycle budget per layer:

```
Domain layer:  3 attempts (red → green → refactor)
Adapter layer: 5 attempts (vendor APIs are messier)
```

When budget exhausts: automatic escalation to human. No silent failures.

### Mechanical Traceability

Every acceptance criterion `AC-FEAT-NNN` must appear in test code, and vice versa.

```bash
/lasagna-status
# Shows: AC-FEAT-001 ← ✅ test_ac_feat_001_when_user_logs_in...
#        AC-FEAT-002 ← ✅ test_ac_feat_002_when_invalid_password...
#        test_ac_feat_003... ← ❌ ORPHAN (no AC mapped)
```

---

## 💻 Implementation: Agents & Skills

### Four Agents (Roles)

Each agent has **isolated context and specific tools**:

| Agent | Sees | Can't See | Tools |
|-------|------|-----------|-------|
| **test-writer** | AC + Contract | Implementation | Read, Grep, Write (test files only) |
| **implementer** | Test + Contract | AC, Spec | Read, Write, Edit, Bash (code files only) |
| **referee** | All three | Nothing (decides disputes) | Read (all), no Write |
| **adversarial-reviewer** | All three | Implementation details for writing | Read only (hunts gaps) |

### Ten Skills (Workflows)

Each skill is a structured prompt sequence:

1. **grilling** — Socratic interview, stack profile discovery
2. **to-spec** — Jacobson use cases, acceptance criteria, error taxonomy
3. **domain-modeling** — Aggregate design from invariants, deletion tests
4. **freeze-contract** — Public API signatures, error types, required ports
5. **tdd-loop** — Orchestrates test-writer and implementer, observes red
6. **adversarial-review** — Hunts missing error paths, invariant stress, volume edges
7. **ports-adapters** — Real infrastructure, vendor error translation
8. **characterize-bugfix** — Pin current (wrong) behavior, then reproduce desired
9. **reverse-spec-brownfield** — Extract spec from legacy code
10. **handoff** — Compress session into one document before context compaction

### Five Hooks (Mechanical Guardrails)

| Hook | Trigger | Action | Can Be Disabled |
|------|---------|--------|---|
| **block-test-edits** | Edit/Write on test file by implementer | Exit 2, block write | `hooks_disabled: block-tests` |
| **check-onion** | Edit/Write on domain core | Verify no I/O/clock/infra imports | `hooks_disabled: onion` |
| **capture-test-result** | Bash exits after test run | Classify outcome (green/red/unknown) | `hooks_disabled: test-result` |
| **count-cycle** | Implementer subagent completes | Increment budget counter, escalate if spent | `hooks_disabled: budget` |
| **dump-phase-state** | Context compaction starts | Pin phase state to disk | `hooks_disabled: precompact` |

---

## 📁 Project Structure

```
your-project/
├── CONTEXT.md                    # Ubiquitous language glossary (permanent)
├── docs/
│   └── adr/NNNN-slug.md         # Architecture Decision Records (permanent)
│
└── .lasagna/                     # lasagna harness state (only root level in git)
    ├── stack.md                  # Stack profile: test runner, paths, patterns (committable)
    ├── specs/
    │   ├── FEAT-001.md          # Active spec (committable, ephemeral)
    │   ├── FEAT-002.md
    │   └── archive/
    │       └── FEAT-000-closed.md
    ├── contracts/
    │   ├── FEAT-001.md          # Frozen contract: signatures + types (committable)
    │   └── FEAT-002.md
    └── state/
        ├── FEAT-001.state.md    # Phase state: cycles, test outcomes (NOT committable, .gitignored)
        └── FEAT-002.state.md
```

**What survives the feature:**
- ✅ ADRs (permanent reference)
- ✅ CONTEXT.md (glossary, evolves)
- ✅ Tests (become regression suite)

**What doesn't:**
- ❌ Spec (archived after feature closes)
- ❌ Phase state (per-feature, local)
- ❌ Contract (lives as frozen signatures in code comments)

---

## 🛠️ Stack Profiles (Language Agnostic)

lasagna ships with profiles for **Python, TypeScript, JVM, and .NET**. Each profile declares:

```yaml
# .lasagna/stack.md
stack: python
test_command: "pytest --tb=short tests/ -v"
test_file_pattern: "tests/test_*.py"
core_path_pattern: "src/(domain|model)/"
forbidden_patterns:
  - "import requests"  # HTTP → must use adapter
  - "datetime.now()"   # Clock → must use port
  - "random\."         # Randomness → must use port
budget_domain: 3
budget_adapters: 5
bugfix_automerge: false
```

**Add your own:** Copy a profile, update patterns for your project structure and linter.

---

## 🎓 Why lasagna vs Traditional SDLC?

### Waterfall (Document Everything)

```
Spec → Design → Dev → Test → Ops
❌ Expensive to change at any stage
❌ Testing finds bugs at the end (most expensive)
❌ No feedback loop
```

### Agile/Scrum (Iterate Fast)

```
Backlog → Sprint → Demo → Backlog
✅ Fast iteration
❌ Test often skipped ("ship it")
❌ Spec drifts (spec and code diverge)
❌ No isolation: devs write tests too (tautology)
```

### lasagna (Iterate with Structure)

```
Spec (gate) → Design (gate) → TDD Loop (isolated agents, budget, hooks) → Review (gate) → Merge
✅ Fast iteration (3-5 cycles per feature)
✅ Test comes first, from third party
✅ Spec approval prevents ambiguity later
✅ Mechanical isolation: test-writer ≠ implementer (no tautology)
✅ Budget enforcement: impossible to overrun silently
✅ Traceability: requirements ↔ tests (auditable)
```

### Real-World Impact

| Scenario | Waterfall | Agile | lasagna |
|----------|-----------|-------|---------|
| **Spec ambiguity discovered** | Rework at end (10x cost) | Rework in next sprint | Gate 1: fix before code (free) |
| **Test doesn't match code** | Catches at acceptance | Won't happen (dev wrote both) | Catches immediately (isolated agent) |
| **Feature costs 5x budget** | War room | Ship tech debt | Escalation at cycle 3 (known early) |
| **Regression in production** | Hotfix fire | Hotfix + sprint debt | Adversarial review caught it (pre-merge) |
| **Onboard new developer** | Read 20-page spec | Read backlog | Read spec + frozen contract (precise) |

---

## 🔮 Roadmap & Planned Evolutions

### Phase 1: Stable Core ✅ (Current)
- [x] Four workflows (official, prototype, bugfix, brownfield)
- [x] Mechanical isolation (test-writer, implementer, referee)
- [x] Cycle budgets and traceability
- [x] Onion layering rules (with baseline for legacy)

### Phase 2: GitHub Integration (Q4 2026)

#### Auto-start from Issues
```bash
# Fetch issue, extract AC, create spec, start flow
claude plugin github issues TommasoTerrin/my-project#42
→ /lasagna official (auto-routed to bug or feature flow)
```

#### AC from Issue Comments
```
GitHub Issue #42:
  Title: User can't login with special chars
  
  /lasagna
  AC: User should login with password containing: !@#$%^&*()
  AC: Error message should be clear if password invalid
```

#### Auto-Map AC → Tests
```bash
/lasagna-status
# Shows: Issue #42 → AC-42-001,002 → test_issue_42_001...
# Checks: PR#XXX closes issue #42 if all AC covered
```

#### Inline PR Comments from Adversarial Review
```
PR Review by lasagna:
└─ adversarial-review found:
   ├─ Missing error path: "invalid charset in password" 
   │  Suggestion: add test_ac_42_001_with_emoji_password
   └─ Volume edge: 1000 failed logins → DDoS vector
      Suggestion: rate-limit by IP in adapter
```

---

### Phase 3: Multi-Agent Orchestration (Q1 2027)

- **Parallel testing**: multiple test-writers per AC (vote on coverage)
- **Reference implementation**: fourth agent writes reference code, referee compares
- **Mutation testing**: fourth agent writes mutants, tests catch them
- **Cost tracking**: estimate and track per-cycle costs in Claude API tokens

---

### Phase 4: Workspace & Team Sync (Q2 2027)

- **Shared contracts**: freeze contract, share with team
- **Async handoff**: test-writer → implementer without real-time chat
- **Workflow replay**: save and replay sessions for onboarding
- **Integration**: Slack notifications, Linear/Asana board updates, ADR sync to docs

---

## 📖 Examples & Tutorials

### Example 1: New Feature (Official Flow)

A startup wants to build "User Invites" feature. 3-person team, 5-day deadline.

```bash
# Day 1 Morning: Interview & Spec
/lasagna official
# → grilling: discovers they need invite link + email + expiry
# → to-spec: writes 3 use cases, 5 acceptance criteria
# GATE 1: Product lead approves spec

# Day 1 Afternoon: Domain & Contract
# → domain-modeling: Invite aggregate (email, token, expiresAt invariants)
# → freeze-contract: InviteService.send(), InviteNotFound error, ports for email
# GATE 2: Tech lead approves contract

# Day 2-3: TDD Loop (domain)
# Cycle 1: test-writer writes AC#1 (create invite), red
#         implementer codes Invite aggregate, green
# Cycle 2: test-writer writes AC#2 (send email), red
#         implementer codes, green
# Cycle 3: test-writer writes AC#3 (validate token), red
#         implementer codes, green
# Budget exhausted: hook escalates

# Day 3-4: Ports-Adapters (infrastructure)
# Cycle 1: real email adapter (SendGrid), 5x budget available
# Cycle 2: rate limiting + observability
# GATE 3: PR merged with full traceability

# Result: 3 AC, all covered, no silent regressions, 2 days ahead
```

### Example 2: Bugfix (Production Issue)

Customer reports: "Invites sent after 5pm never expire correctly."

```bash
/lasagna bugfix
# → characterize: test confirms bug (invite still valid after expiry)
# → reproduce: test shows desired (invite invalid after expiry)
# → tdd-loop: implementer fixes clock mock in adapter
# → adversarial-review: check for regressions in expiry flow
# ✅ Auto-merge (if configured)
# Result: bug fixed, no regressions, auditable
```

### Example 3: Prototype (Idea Validation)

Team asks: "Should we use WebSockets or polling for live updates?"

```bash
/lasagna prototype
# → grilling: reduced, just ask the question
# → build: quick walking skeleton with both approaches
# → validate: measure latency, CPU, complexity trade-offs
# If YES: becomes official feature
# If NO: abandon, no wasted spec/design effort
# Result: decision data, low risk
```

---

## 🛡️ Known Limitations

- **No auto-merge in official flow** — three gates are human decisions (by design)
- **Subagents cannot spawn subagents** — orchestration runs in main thread
- **Stack profile must exist** — all hooks silent no-op if `.lasagna/stack.md` missing
- **Test outcome classification is textual** — a test asserting on string "ModuleNotFoundError" may be misclassified

---

## 🔗 Integrations & MCP Servers

Future support for:

- **GitHub** — fetch issues, auto-create AC, PR comments from reviews
- **Linear / Asana** — sync status, update tickets, link to ADRs
- **Slack** — notify team of gates, async handoff
- **PagerDuty** — escalate when budget spent or adversarial review fails
- **Figma / Miro** — embed architecture diagrams in contracts

---

## 📚 Further Reading

### Core Concepts

- [Spec-Driven Development](https://gojko.net/books/specification-by-example/) — Gojko Adzic
- [Test-Driven Development](https://www.oreilly.com/library/view/test-driven-development/0321146530/) — Kent Beck
- [Domain-Driven Design](https://www.domainlanguage.com/ddd/) — Eric Evans
- [Hexagonal / Onion Architecture](https://alistair.cockburn.us/hexagonal-architecture/) — Alistair Cockburn

### lasagna Design

- Original SDLC harness: [sdlc-harness](https://github.com/TommasoTerrin/lasagna-code/tree/main/sdlc-harness)
- Loop engineering: [Augment Code](https://augmentcode.com/)
- Structured prompts: [mattpocock/skills](https://github.com/mattpocock/skills)

---

## 🤝 Contributing

Issues, PRs, and discussion are welcome. 

### Before you start

1. Read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
2. Check [open issues](https://github.com/TommasoTerrin/lasagna-code/issues)
3. For large changes, open a discussion first

### Development

```bash
# Clone
git clone https://github.com/TommasoTerrin/lasagna-code
cd lasagna-code

# Test the plugin locally
claude plugin validate ./lasagna-code
# or link it
ln -s $(pwd)/lasagna-code ~/.claude/plugins/lasagna

# Make changes to skills, agents, or hooks
# Restart Claude Code to reload
```

### What we're looking for

- **Bug reports** — with reproducible steps
- **Feature requests** — with use case and constraints
- **Stack profile contributions** — Go, Rust, PHP, etc.
- **Documentation improvements** — especially examples and diagrams
- **Integration PRs** — GitHub, Linear, Slack, etc.

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

**Tommaso Terrin**

- GitHub: [@TommasoTerrin](https://github.com/TommasoTerrin)
- Email: tterrin@ibc.it
- Company: [IBC S.R.L.](https://ibc.it)

---

## 🙏 Acknowledgments

lasagna draws from:

- **Spec-Driven Development** (Gojko Adzic)
- **Test-Driven Development** (Kent Beck)
- **Domain-Driven Design** (Eric Evans)
- **Hexagonal / Onion Architecture** (Alistair Cockburn)
- **Loop Engineering** (Augment Code's iterative agent orchestration)
- **Structured Prompts** (mattpocock/skills)

---

## 📞 Support

- **Issues & Bugs** → [GitHub Issues](https://github.com/TommasoTerrin/lasagna-code/issues)
- **Discussions** → [GitHub Discussions](https://github.com/TommasoTerrin/lasagna-code/discussions)
- **Security** → Email tterrin@ibc.it with `[SECURITY]` in subject

---

**Made with ❤️ for developers who love structure, not chaos.**
