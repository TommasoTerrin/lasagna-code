# GitHub Repository Setup

Questo documento guida la configurazione della repository GitHub per lasagna.

---

## 📋 Step 1: Repository Metadata

### Nella sezione **Settings → General**

#### Description (In Informazioni repository)
```
Layered Spec-Driven Harness for Claude Code — precise specs, frozen contracts, red-green loop with isolated test/implementation roles, mechanical guardrails.
```
**Lunghezza:** ~130 caratteri (GitHub mostra questo sotto il nome repo)

#### Homepage URL
```
https://github.com/TommasoTerrin/lasagna-code
```

#### About section (sidebar destro)
```
Title: lasagna
Description: Spec-driven development for Claude Code
Website: https://github.com/TommasoTerrin/lasagna-code
Topics: (vedi sotto)
```

---

## 🏷️ Step 2: Topics (Tags)

**Settings → About → Topics**

Aggiungi tutti questi (sono di ricerca):

```
- spec-driven-development
- test-driven-development
- domain-driven-design
- tdd
- ddd
- hexagonal-architecture
- onion-architecture
- claude-code
- claude-plugin
- guardrails
- loop-engineering
- python
- typescript
- jvm
- dotnet
- polyglot
```

**Massimo 30 topics.** I principali sono i primi 10.

---

## 📁 Step 3: Files to Include in Root

Assicurati che questi file siano nella root directory:

### ✅ Deve averli (già creati)
- `README.md` — guida principale
- `LICENSE` — MIT (già presente)
- `.gitignore` — esclude .lasagna/state/ (già presente)
- `CONTRIBUTING.md` — come contribuire (appena creato)
- `CODE_OF_CONDUCT.md` — codice di condotta (appena creato)

### ✅ Opzionali ma raccomandati (per repo mature)
- `CHANGELOG.md` — storia delle release
- `SECURITY.md` — come reportare vulnerabilità
- `.github/workflows/` — CI/CD (test, validate plugin)
- `FUNDING.json` — se accetti sponsorizzazioni

### ❌ NON includere
- `README_PRODUCTION.md` — rinominalo in `README.md` (vedi sotto)
- File locali (`.lasagna/state/`, IDE files, etc.) — già in `.gitignore`

---

## 🔄 Step 4: README Finalization

### Opzione A: Sostituisci il README attuale

Il file `README_PRODUCTION.md` che abbiamo creato è completo e pronto. Fai così:

```bash
cd lasagna-code
mv README.md README.old.md  # backup del vecchio
mv README_PRODUCTION.md README.md
git add README.md
git commit -m "docs: replace README with production-ready version

- Comprehensive workflow documentation
- Architecture and principles explained
- Roadmap and evolution plans
- Contributing guidelines embedded"
```

### Opzione B: Mantieni versione plurilingue

Se vuoi mantenere README.it.md, fai così:

```
README.md        ← versione inglese (production)
README.it.md     ← versione italiana (mantenere)
```

Nel README.md principale, aggiungi link in alto:

```markdown
# lasagna

[🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)

...rest of content
```

---

## 🔐 Step 5: Branch Protection (opzionale ma raccomandato)

**Settings → Branches → Branch Protection Rules**

Aggiungi una regola per `main`:

```
Branch name pattern: main

✅ Require pull request reviews before merging
   - Required number of reviews: 1
   - Require approval from code owners: yes (se usi CODEOWNERS)

✅ Require status checks to pass before merging
   - Require branches to be up to date: yes
   - (se aggiungerai CI in futuro, aggiungi qui)

✅ Require code reviews to be stale before merging
   - Dismiss stale pull request approvals: yes

✅ Require conversation resolution
   - Before merging: yes
```

Questo forza il review prima del merge, protegge da force-push accidentali.

---

## 👥 Step 6: Collaborators & Permissions (opzionale)

**Settings → Collaborators and teams**

Se stai collaborando con altri:

```
User/Team          Role              Permissions
─────────────────────────────────────────────────
maintainers         Maintain          Push, merge, manage issues
triage              Triage            Manage issues/PRs, no code push
docs-team           Maintain          Only docs/ and *.md files
```

Per ora, di solito solo il creator ha accesso.

---

## 🚀 Step 7: Releases & Versioning

Quando lanci la prima release (v0.1.0):

**Releases → Draft a new release**

```
Tag: v0.1.0
Release title: lasagna v0.1.0

Release notes:
# 🎉 First Public Release

Initial stable release of lasagna: spec-driven harness for Claude Code.

## Features
- ✅ Four workflows: official, prototype, bugfix, brownfield
- ✅ Mechanical isolation: test-writer ≠ implementer
- ✅ Cycle budgets and traceability
- ✅ Onion layering rules (with baseline for legacy)
- ✅ Hooks for Python, TypeScript, JVM, .NET

## Getting Started
See [README.md](README.md#quick-start)

## Known Limitations
See [LIMITATIONS](README.md#-known-limitations)

---

**Contributors:** @TommasoTerrin
```

---

## 📊 Step 8: GitHub Settings Summary

Copia questa checklist e verifica:

```
Repository Metadata
├── ✓ Description: "Layered Spec-Driven Harness for Claude Code..."
├── ✓ Homepage: https://github.com/TommasoTerrin/lasagna-code
├── ✓ Topics: spec-driven, tdd, ddd, claude-code, ...
├── ✓ Visibility: Public
├── ✓ Default branch: main
└── ✓ Require fork-based workflow for contributions: (your choice)

Files in Root
├── ✓ README.md (production version)
├── ✓ LICENSE (MIT)
├── ✓ .gitignore
├── ✓ CONTRIBUTING.md
├── ✓ CODE_OF_CONDUCT.md
└── ✓ CHANGELOG.md (opzionale)

Branch Protection (opzionale)
├── ✓ Require PRs before merge
├── ✓ Require at least 1 review
├── ✓ Dismiss stale reviews
└── ✓ Require resolved conversations

Labels (opzionali, vedi step 9)
├── ✓ bug (rosso)
├── ✓ enhancement (verde)
├── ✓ documentation (blu)
├── ✓ good-first-issue (viola)
└── ✓ help-wanted (arancione)
```

---

## 🏷️ Step 9: Issue Labels (opzionale ma utile)

**Issues → Labels**

Crea/modifica questi label standard:

| Label | Color | Descrizione |
|-------|-------|---|
| `bug` | #d73a4a | Qualcosa che non funziona |
| `enhancement` | #a2eeef | Richiesta di nuova feature |
| `documentation` | #0075ca | Improvements o aggiunte a docs |
| `good-first-issue` | #7057ff | Buono per chi vuole iniziare a contribuire |
| `help-wanted` | #008672 | Extra attenzione richiesta |
| `question` | #d876e3 | Domanda, non bug |
| `wontfix` | #ffffff | Decisione di non fixare |
| `duplicate` | #cccccc | Duplicate di un'altra issue |

---

## 📋 Step 10: Pre-commit Checks

Prima di pushare la prima volta:

```bash
# 1. Valida il plugin
claude plugin validate ./lasagna-code

# 2. Controlla links nel README
# (manualmente, o usa tool come https://github.com/gaurav-nelson/github-action-markdown-link-check)

# 3. Lint shell scripts
shellcheck plugins/lasagna/scripts/*.sh
# Se non hai shellcheck, installa:
# - macOS: brew install shellcheck
# - Ubuntu: apt-get install shellcheck
# - Windows: download from https://www.shellcheck.net/

# 4. Verifica .gitignore
git status  # Nessun .lasagna/state/ visibile

# 5. Test locale
ln -s $(pwd) ~/.claude/plugins/lasagna-test
# Restart Claude Code
/lasagna-init
/lasagna official
# Completa un ciclo di test
```

---

## 🎯 Summary: Cosa Aggiungere alla Repo

### File Definitivi (pronti per GitHub)

```
lasagna-code/
├── README.md                          ← Rinomina da README_PRODUCTION.md
├── README.it.md                       ← Mantieni
├── LICENSE                            ← Già presente (MIT)
├── .gitignore                         ← Già presente
├── CONTRIBUTING.md                    ← Appena creato ✨
├── CODE_OF_CONDUCT.md                 ← Appena creato ✨
├── CHANGELOG.md                       ← (opzionale, crea quando prima release)
├── SECURITY.md                        ← (opzionale, per vulns)
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md              ← Appena creato ✨
│   │   └── feature_request.md         ← Appena creato ✨
│   └── pull_request_template.md       ← Appena creato ✨
└── plugins/lasagna/
    ├── skills/
    ├── agents/
    ├── hooks/
    └── scripts/
```

### File NON da aggiungere

```
❌ README_PRODUCTION.md     (rinominato in README.md)
❌ GITHUB_SETUP.md          (questo file, solo per guida)
❌ .lasagna/state/          (gitignored, per-session)
❌ .vscode/, .idea/         (IDE files, gitignored)
❌ .claude/                 (local config, gitignored)
❌ node_modules/, __pycache__/ (language deps, gitignored)
```

---

## 🚀 GitHub Repo Metadata (da compilare)

Quando crei la repo su GitHub.com, compila così:

### Nome Repo
```
lasagna-code
```

### Descrizione Repo
```
Layered Spec-Driven Harness for Claude Code
```

### URL
```
https://github.com/TommasoTerrin/lasagna-code
```

### Visibility
```
Public ✓
```

### License
```
MIT
```

### Topics
```
spec-driven-development
test-driven-development
domain-driven-design
tdd
ddd
hexagonal-architecture
claude-code
claude-plugin
guardrails
```

### Includes (checkboxes)
```
✓ Add a README file
✓ Add .gitignore
✓ Choose a license: MIT
```

---

## 📝 Template Git Commit per Setup Repo

Quando pushes per la prima volta:

```bash
git add .
git commit -m "docs: add production documentation

- Complete production-ready README with workflows, principles, and roadmap
- Add CONTRIBUTING.md with detailed contribution guidelines
- Add CODE_OF_CONDUCT.md (Contributor Covenant v2.0)
- Add GitHub issue templates (bug, feature request)
- Add GitHub pull request template
- Document stack profiles and directory structure
- Add examples and use cases

This repo is now ready for public contributions."

git push -u origin main
```

---

## ✅ Deployment Checklist (Final)

Prima di annunciare la repo pubblicamente:

- [ ] README.md è completo e accurato
- [ ] LICENSE è MIT
- [ ] .gitignore esclude .lasagna/state/ e altri file locali
- [ ] CONTRIBUTING.md spiega come contribuire
- [ ] CODE_OF_CONDUCT.md è in place
- [ ] GitHub issue/PR templates sono configurati
- [ ] Topics (tags) sono compilati (9-15 tags)
- [ ] Branch protection rules sono ON (opzionale)
- [ ] Plugin valida localmente: `claude plugin validate`
- [ ] Primo test flow (`/lasagna official`) funziona
- [ ] Nessun hardcoded path o secret nei file

---

**Ready to launch! 🚀**
