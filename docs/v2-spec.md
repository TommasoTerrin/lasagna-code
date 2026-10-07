# lasagna v2 — specifica delle modifiche

> Stato: **bozza approvata nei contenuti, non ancora implementata** (2026-10-06).
> Autore delle decisioni: Tommaso Terrin. Redazione: sessione Claude Code.

## 0. Come usare questo documento

Questo documento è **autosufficiente**: una sessione che parte da zero deve poter
implementare lasagna v2 leggendo solo questo file più il codice del repo. Contiene:

- il contesto (cos'è lasagna v1, dove sta, cosa non va);
- le decisioni prese (con il perché e le alternative scartate);
- la specifica di ogni modifica, file per file;
- i criteri di accettazione verificabili (`AC-V2-NNN`);
- l'ordine di lavoro, i punti aperti e i riferimenti esterni.

Regola per chi implementa: **le decisioni della sezione 4 sono chiuse**. Se durante
il lavoro una decisione si rivela sbagliata, ci si ferma e la si discute con il
maintainer: non la si aggira in silenzio. I punti della sezione 9 sono invece
aperti e vanno chiesti prima di essere toccati.

Lingua: questo documento è in italiano; i file del plugin (skill, agenti, template,
README principale) restano **in inglese**, come in v1. `README.it.md` è la
traduzione italiana.

---

## 1. Contesto

### 1.1 Cos'è lasagna (v1)

Plugin di Claude Code (`plugins/lasagna/`, marketplace in `.claude-plugin/`) che
impone un processo spec-driven + TDD con agenti isolati:

- **Flussi**: official (feature nuova), prototype, bugfix, brownfield — router in
  `plugins/lasagna/commands/lasagna.md`.
- **Fasi official**: grilling → to-spec (**gate 1** umano) → domain-modeling →
  freeze-contract (**gate 2**) → tdd-loop (dominio) → adversarial-review →
  ports-adapters (adapter) → **gate 3** (PR).
- **Agenti** (`plugins/lasagna/agents/`): `test-writer` (scrive UN test da un AC +
  contratto, osserva il red), `implementer` (minimo codice per farlo passare, vede
  solo contratto + test), `referee` (arbitra fallimenti ambigui),
  `adversarial-reviewer` (cerca buchi dopo il verde).
- **Hook** (`plugins/lasagna/hooks/hooks.json` → `scripts/*.sh`, POSIX sh):
  `session-status`, `block-test-edits`, `capture-test-result`, `check-onion`,
  `count-cycle`, `dump-phase-state`. Script CLI: `set-state`, `check-traceability`,
  `init`, `onion-baseline`, più `lib.sh` condivisa.
- **Stato**: `.lasagna/stack.md` (profilo, committato), `.lasagna/specs/`,
  `.lasagna/contracts/`, `.lasagna/state/*.state.md` (gitignored), `CONTEXT.md`
  (glossario), `docs/adr/`.
- **Architettura imposta**: DDD + onion/esagonale. Il core è un `core_path`
  controllato da `check-onion.sh` (allowlist di import + pattern vietati).

### 1.2 Repo e stato git

- Repo: `TommasoTerrin/lasagna-code`, MIT, versione plugin `0.1.0`.
- Branch: `main` (release) e `develop` (lavoro). **Attenzione**: al 2026-10-06
  `main` ha un commit in più di `develop` (`b88cac0 docs: fix leftover merge
  markers, curate roadmap`). Prima di creare il branch `v2` va riallineato
  `develop` con `main` (o si parte da `main`).
- CI: `.github/workflows/lint.yml` (shellcheck sugli script), `validate.yml`
  (`claude plugin validate`), `links.yml`.
- `note.md` è privato (gitignored).
- Utente attuale: **un solo sviluppatore** (il maintainer). Il supporto team è un
  punto aperto (§9).

---

## 2. Obiettivi e non-obiettivi

### Obiettivi v2

1. **Separare il motore di processo dallo stile architetturale.** Il processo (gate,
   isolamento test-writer/implementer, red osservato, budget, tracciabilità) resta
   rigoroso. L'architettura non è più imposta.
2. **Un principio architetturale preferito, non obbligatorio**: *functional core,
   imperative shell* (FCIS), proporzionato al progetto (§5).
3. **Progetti esistenti: adattarsi**, non convertire. Le proposte di modifica al
   design si scrivono e si discutono, non si applicano.
4. **Hook deterministici solo dove serve una verità meccanica**: esito dei test,
   isolamento tra agenti, budget, salvataggio dello stato. Tutto il resto è
   giudizio del modello.
5. **Hook e script in Python** (solo libreria standard), più leggibili e testabili.
6. **Costruzione per fette verticali** invece che per strati orizzontali.
7. **Contesto di progetto modulare**, caricato per la sola parte che serve.
8. **Una suite di eval** per misurare se ogni modifica al plugin migliora o
   peggiora il comportamento.

### Non-obiettivi v2

- Supporto team (ID condivisi, stato condiviso, gate legati alle review PR): §9.
- Integrazione GitHub issue → spec (roadmap Fase 2): invariata, non in v2.
- Varianti per altri strumenti oltre Claude Code (roadmap Fase 7).
- Migrare il progetto di esempio `examples/httpskills` (submodule): resta un
  esempio v1 finché non si decide altrimenti (§9).

---

## 3. Problemi di v1 che motivano la v2

| # | Problema | Dove |
|---|---|---|
| P1 | DDD + esagonale cablati ovunque: aggregati obbligatori, sezioni "Required ports" e "Determinism" fisse nel contratto, fase intera `ports-adapters`, hook `check-onion` che conosce solo il "core puro". Su CRUD, pipeline, CLI, frontend, progetti Django/FastAPI esistenti lasagna può solo *spegnere* pezzi, non adattarsi. | `skills/domain-modeling`, `templates/contract.md`, `skills/ports-adapters`, `scripts/check-onion.sh` |
| P2 | Nel brownfield il contratto descrive "le firme che vuoi, non quelle che esistono": ogni feature diventa una migrazione verso l'esagono. | `skills/reverse-spec-brownfield/SKILL.md` §6 |
| P3 | Processo orizzontale tra le fasi: prima tutto il dominio per tutti gli AC, poi tutti gli adapter. Il core viene testato contro un'integrazione immaginata. (Dentro il tdd-loop invece è già verticale: un test → un'implementazione.) | `skills/tdd-loop`, `skills/ports-adapters` |
| P4 | Il blocco in lettura del codice per il test-writer è promesso dal README ("hook blocks Reads") ma **non esiste**: è solo un'istruzione nel prompt. | `README.md`, `agents/test-writer.md` |
| P5 | Gli hook estraggono campi dal JSON con `grep`/`sed` (nessun parser); sh è poco leggibile per il maintainer e non testato. | `scripts/lib.sh` (`json_values`) |
| P6 | Budget ambiguo: `cycles_used` cresce su tutti i criteri di un layer e si azzera solo al cambio layer o allo sblocco del contratto. Dopo 3 criteri verdi al primo colpo, il primo rosso del 4° criterio fa scattare subito l'escalation. Il README presenta "budget esaurito dopo 3 criteri" come normale. | `scripts/count-cycle.sh`, `skills/tdd-loop` §Budget, README esempio 1 |
| P7 | `CONTEXT.md` unico, caricato per intero; inoltre alcune skill scrivono `CONTEXT.md` a mano invece di rispettare la chiave `context_file` del profilo. | `skills/to-spec:16`, `skills/domain-modeling`, `skills/reverse-spec-brownfield`, `skills/handoff`, `agents/adversarial-reviewer` |
| P8 | Nessun modo di misurare se una modifica al plugin lo migliora. | — |

---

## 4. Decisioni

Ogni decisione: **cosa**, **perché**, **alternative scartate**.

### D1 — Motore di processo separato dall'architettura
- **Cosa**: i meccanismi di processo restano rigidi e indipendenti dal design del
  codice. Tutto ciò che riguarda l'architettura diventa linea guida per il modello
  e giudizio dell'adversarial-reviewer.
- **Perché**: la rigidità sul processo è il valore del prodotto; la rigidità
  sull'architettura è ciò che impedisce di usarlo su progetti diversi (P1).

### D2 — Principio architetturale: FCIS proporzionato
- **Cosa**: il principio preferito è *functional core, imperative shell*, espresso
  come 5 regole e 3 livelli di separazione (§5). Il livello lo propone il grilling
  e lo decide l'umano.
- **Perché**: dà codice leggibile anche da un agente senza conoscenze specifiche
  degli strumenti, unit test senza mock né E2E obbligatori, migrazioni
  tecnologiche localizzate — senza la cerimonia del DDD completo.
- **Scartato**: un catalogo fisso di architetture (layered, pipeline, modular
  monolith…): si insegna *come decidere quanto separare*, non *da cosa scegliere*.

### D3 — Brownfield: adottare le convenzioni esistenti
- **Cosa**: `reverse-spec-brownfield` estrae le convenzioni di design esistenti e
  le scrive in `.lasagna/architecture.md`. Contratto e codice nuovo si conformano a
  quelle. Le proposte di miglioramento vanno in `.lasagna/design-notes.md` e **non
  si applicano** senza discussione. In caso di spaghetti-code grave: domanda
  esplicita al maintainer umano, mai refactoring di iniziativa.
- **Perché**: P2.

### D4 — Hook solo per verità sui test, isolamento, budget, stato
- **Cosa**: restano/nascono questi hook:
  - `block-test-edits`: l'implementer non scrive file di test (esiste);
  - `block-test-reads` (**nuovo**): l'implementer non legge file di test;
  - `block-code-reads` (**nuovo**): il test-writer non legge il codice di
    produzione durante la fase `tdd-loop`;
  - `capture-test-result`: classificazione red/green dall'output reale;
  - `count-cycle`: budget;
  - `dump-phase-state` e `session-status`: conservazione e visibilità dello stato
    (non prendono decisioni al posto del modello).
- **Escono**: `check-onion.sh` e `onion-baseline.sh`, con tutte le chiavi
  `core_*` del profilo.
- **Perché**: i modelli attuali sono affidabili su linguaggio, librerie e
  architettura; vincoli meccanici lì ricreano rumore e rigidità. Coerente con il
  pattern "deterministic core, agentic shell": il nucleo deterministico è piccolo
  e protegge solo ciò che non si negozia.
- **Scartato**: generalizzare `check-onion` in "regole di confine" configurabili
  (proposta intermedia della discussione) — superata da questa decisione.

### D5 — Implementer cieco sui test (lettura e scrittura)
- **Cosa**: l'implementer non può né scrivere né **leggere** i file di test. Lavora
  da: contratto congelato, nome del test, righe di fallimento rilevanti passate
  dal coordinatore (come già in v1), comando di test.
- **Perché**: impedisce di "cucire" il codice sui letterali attesi del test; il
  comportamento deve venire dal contratto.
- **Rischio noto**: più cicli per criterio quando il fallimento non è
  autoesplicativo. Mitigazioni: il coordinatore passa le righe di fallimento
  complete (pytest mostra la riga dell'assert e i valori atteso/ottenuto); il
  referee resta disponibile; una eval misura i cicli medi (§6.9).
- **Nota**: l'output di pytest mostra comunque la riga di assert che fallisce:
  è accettato, è informazione sul *fallimento*, non accesso al file.

### D6 — Hook e script in Python, solo stdlib
- **Cosa**: tutti gli script `.sh` diventano Python ≥ 3.9, solo libreria standard
  (niente `pip install`). Resta **un solo** script sh: il launcher `run.sh` che
  trova l'interprete (§6.1).
- **Perché**: leggibilità per il maintainer, parsing JSON reale (`json`) invece di
  `grep` (P5), test con pytest.
- **Costo accettato**: Python diventa requisito dichiarato per gli utenti.
- **Vincoli**: su Windows `python3` può essere il collegamento fittizio del
  Microsoft Store; su macOS/Linux `python` può non esistere. Il launcher deve
  gestirli. Se Python manca in un progetto lasagna, i guardrail bloccanti
  **falliscono chiusi** (exit 2 con messaggio), perché un hook che non parte esce
  con codice ≠ 2 e Claude Code lo tratta come errore non bloccante: il guardrail
  sparirebbe in silenzio.

### D7 — Contratto riformulato: "dipendenze esterne" al posto di ports/determinismo
- **Cosa**: le sezioni "Required ports" e "Determinism" del template contratto
  diventano un'unica tabella **Dipendenze esterne** (§6.7).
- **Perché**: il bisogno reale è che test-writer e implementer concordino *come i
  test controllano tutto ciò che è esterno o non deterministico*; i port sono solo
  uno dei modi.

### D8 — domain-modeling senza aggregati obbligatori
- **Cosa**: output obbligatorio = invarianti (regole di business) + termini del
  glossario + **modulo in cui vive ogni regola**. Aggregati solo quando due cose
  devono cambiare insieme in modo atomico (emerge dagli assi contention / partial
  failure del grilling).
- **Perché**: P1; su CRUD e pipeline gli aggregati sono cerimonia.

### D9 — Fette verticali: tdd-loop e ports-adapters fusi
- **Cosa**: la skill `ports-adapters` viene eliminata. Il `tdd-loop` lavora **per
  fetta**: per ogni AC (o piccolo gruppo coerente) prima i test del core, poi la
  shell e un test di integrazione se l'AC tocca il mondo esterno. La **prima
  fetta è un tracer bullet end-to-end**. Grilling, spec e contratto restano a
  monte. L'adversarial review resta dopo tutte le fette. Il gate 3 (PR) passa a una
  nuova skill `pr-gate`.
- **Perché**: P3; allineato al vertical slicing / tracer bullet di Matt Pocock.
- **Scartato**: mettere il gate 3 dentro `adversarial-review` — si preferisce una
  skill per responsabilità (roadmap Fase 5, fasi evolvibili indipendentemente).
- **Da conservare** da `ports-adapters`: il test "se cambiamo fornitore domani,
  questo cambia?" (sì → shell, no → core); test di integrazione su infrastruttura
  reale, non mock; traduzione degli errori del fornitore negli errori del
  contratto; nessuna regola di business nella shell; pochi E2E che verificano il
  cablaggio.

### D10 — Budget per criterio
- **Cosa**: `cycles_used` si azzera **a ogni criterio chiuso** (e allo sblocco del
  contratto). `budget_max` dipende dal tipo di test della fetta in corso: `core`
  → `budget_core` (default 3), `shell` → `budget_shell` (default 5); flusso bugfix
  → `budget_bugfix` (default 5).
- **Perché**: P6.

### D11 — Contesto di progetto: cartella normale con indice
- **Cosa**: `docs/context/` con `INDEX.md` + un file per bounded context + un
  file `structure.md` separato. Percorso nel profilo (`context_dir`). Una riga in
  `CLAUDE.md` del progetto lo segnala alle sessioni fuori da lasagna. La spec
  dichiara quali contesti tocca la feature; le fasi successive caricano solo
  quelli.
- **Perché**: P7; un glossario per bounded context è anche più fedele al DDD.
- **Scartato**: impacchettarlo come skill di progetto. Dentro lasagna non dà
  vantaggi (lasagna legge un percorso in entrambi i casi, e "invoca la skill X"
  non è più deterministico di "leggi il file X"); fuori da lasagna la riga in
  `CLAUDE.md` (sempre caricato) è più affidabile dell'attivazione di una skill.
  Una skill avrebbe senso solo per riuso tra progetti, che qui non c'è.

### D12 — Principi di testing espliciti
- **Cosa**: test-writer e adversarial-reviewer incorporano (riformulati, con
  citazione della fonte) i principi di *Testing on the Toilet*: gerarchia dei
  test double reale → fake → stub → mock; niente mock di tipi di terze parti
  (si incapsula e si sostituisce il wrapper); niente test che ricalcano la
  struttura del codice (change-detector); test ermetici e deterministici. Il
  reviewer aggiunge la checklist FCIS (logica impura, shell grasse, effetti
  collaterali nascosti come logging od orologio dentro funzioni "pure").
- **Prima di copiare testo** dal repo `testing-on-the-toilet` verificarne la
  licenza; in ogni caso riformulare, non incollare.

### D13 — Eval con `claude plugin eval`
- **Cosa**: una suite di eval nel plugin, eseguita prima di ogni release e
  confrontata con la versione precedente (§6.9).

### D14 — Niente lasagna su lasagna (rivista il 2026-10-07)
- **Cosa**: la v2 si implementa **direttamente** da questo documento, senza
  applicare il flusso di lasagna al repo del plugin (niente `.lasagna/`, gate o
  agenti test-writer/implementer qui). Gli hook Python hanno normali test pytest;
  le skill si verificano con la suite di eval (§6.9).
- **Perché**: lasagna è un plugin (skill in markdown + pochi script), non
  un'applicazione: il suo processo applicato a sé stesso è cerimonia.
- **Scartato**: sviluppare con la v1 installata e il flusso official (versione
  originale di D14), provata fino al gate 2 e abbandonata.
- Le decisioni D1–D14 possono essere registrate come ADR in `docs/adr/` del repo
  (facoltativo, da chiedere).

---

## 5. Il principio architetturale (testo di riferimento)

Questa sezione è la fonte da cui scrivere le linee guida nelle skill (grilling,
domain-modeling, freeze-contract, implementer, adversarial-reviewer).

### 5.1 Functional core, imperative shell

- **Core**: funzioni (o classi semplici) che ricevono dati e restituiscono dati
  applicando le regole di business. Niente I/O, niente orologio, niente casualità,
  niente variabili d'ambiente.
- **Shell**: endpoint, CLI, job, accesso a DB/file/rete. Raccoglie i dati, chiama
  il core, applica ciò che il core ha deciso. Sottile, con pochi `if`.

Effetto atteso: il core si testa passando valori, **senza mock**; i fake servono
solo dove c'è un'astrazione (regola 3); gli E2E sono pochi e verificano il
cablaggio.

### 5.2 Le 5 regole

1. **La logica sta in moduli "poveri"**: libreria standard + poche librerie
   fondamentali dichiarate in `.lasagna/architecture.md` (es. `pydantic`).
   Linea guida, **non** controllo meccanico (D4).
2. **L'I/O sta ai bordi.** La logica riceve valori: `now` è un parametro, la
   configurazione è un oggetto.
3. **Un'astrazione (`Protocol`/interface) solo quando conviene**: la tecnologia
   potrebbe cambiare davvero, oppure il test deve sostituire qualcosa di lento o
   non deterministico, oppure esistono già due implementazioni. Altrimenti si
   passa un valore o una funzione. (È il *deletion test* applicato alle
   astrazioni.)
4. **I tipi dei fornitori non entrano nella logica**: errori HTTP, modelli ORM,
   oggetti SDK si traducono al bordo. È ciò che rende possibili le migrazioni.
5. **Organizzazione per funzionalità**, non per livello tecnico (`billing/`,
   `auth/` invece di `domain/`, `adapters/`, `infrastructure/`). Nomi di file che
   dicono il comportamento (`decide_registration`), non il ruolo (`service`).
   In un progetto piccolo bastano `logic.py` + `app.py`.

### 5.3 Livelli di separazione (decisi nel grilling)

| Livello | Quando | Forma |
|---|---|---|
| **minimo** | poca logica di business, script, CRUD semplici | un modulo di logica pura + i bordi |
| **modulare** (default consigliato) | logica non banale, qualche dipendenza esterna | moduli per funzionalità, core puro per modulo, `Protocol` solo sulle dipendenze esterne che lo meritano |
| **esagonale completo** | dominio complesso, più adapter reali per la stessa porta, vincoli di consistenza forti | ports & adapters espliciti, aggregati |

Il grilling presenta la domanda con una raccomandazione motivata; la risposta
finisce in `.lasagna/architecture.md`.

### 5.4 `Protocol`: quando sì e quando no

`typing.Protocol` (PEP 544) è il modo Python di dichiarare "mi serve qualcosa con
questi metodi" senza ereditarietà (tipizzazione strutturale). Equivalenti:
`interface` in TypeScript e Go (strutturali), in Java/C# (nominali, con
`implements`); in Python l'alternativa nominale è `abc.ABC`.

Sì — la logica deve interrogare una dipendenza *mentre* decide:

```python
class PaymentGateway(Protocol):
    def charge(self, customer_id: str, cents: int) -> ChargeResult: ...

def checkout(cart: Cart, gateway: PaymentGateway) -> Order: ...
# test: FakeGateway che risponde "rifiutato", senza ereditare nulla
```

No:
- ora corrente → parametro `now: datetime`;
- una sola operazione → un `Callable`;
- configurazione → un oggetto `Settings`;
- **caso più frequente**: si porta l'I/O nella shell. Invece di
  `cancel(store, order_id)` si scrive `cancel(order, now) -> Order` (puro); la
  shell fa `get` → `cancel` → `save`. Nessuna dipendenza, nessun fake.

### 5.5 Progetti esistenti

- Prima si **rilevano** le convenzioni (dove sta la logica, convenzione degli
  errori, stile di dependency injection, stile dei test, struttura delle
  cartelle) e si scrivono in `.lasagna/architecture.md`, confermate dall'umano.
- Il codice nuovo segue quelle convenzioni anche se diverse da §5.2.
- Le proposte (anche "applica FCIS a questo modulo") vanno in
  `.lasagna/design-notes.md`, con motivazione e costo stimato.
- Spaghetti-code grave che impedisce di lavorare: domanda esplicita al
  maintainer, con opzioni.

---

## 6. Specifica delle modifiche

Percorsi relativi a `plugins/lasagna/` salvo diversa indicazione.

### 6.1 Hook e script in Python

#### Struttura

```
scripts/
  run.sh                  # unico sh: trova Python ed esegue lasagna.py
  lasagna.py              # entrypoint: dispatch dei sottocomandi
  lasagna_lib/
    core/                 # funzioni PURE (FCIS): testo/dict in → decisione out
      profile.py          # parse delle righe "key: value" del profilo
      state.py            # lettura/aggiornamento del phase state (str → str)
      classify.py         # classificazione esito test
      guards.py           # decisioni di blocco (scrittura/lettura)
      budget.py           # conteggio cicli ed escalation
      traceability.py     # mappa AC ↔ test
    shell/                # I/O: stdin JSON, file, stderr, exit code
      hooks.py            # un handler per hook
      cli.py              # set-state, check-traceability, init, status
tests/                    # pytest, alla RADICE del repo: test del progetto, non
                          # parte del plugin installato (deciso 2026-10-06)
```

Gli hook diventano la dimostrazione del metodo: `decide(payload, profile, state)
-> Verdict` puro, testato senza mock; la shell legge stdin, chiama, scrive
stderr/exit code.

#### Launcher `run.sh`

Comportamento:
1. Se non esiste `${LASAGNA_DIR:-$CLAUDE_PROJECT_DIR/.lasagna}/stack.md` → `exit 0`
   silenzioso (progetto che non usa lasagna; stesso comportamento di v1).
2. Usa l'interprete **salvato** in `${CLAUDE_PLUGIN_DATA}/python-path` (cartella
   dati persistente del plugin: per macchina, sopravvive agli aggiornamenti;
   ripiego `<plugin root>/.python-path` se la variabile manca). Python si cerca
   quindi **una volta sola**, al primo uso, non a ogni chiamata (deciso
   2026-10-06: `block-reads` gira su ogni Read/Grep/Glob/Bash).
3. Se il file manca o punta a un file che non esiste più, cerca un interprete
   *funzionante* in quest'ordine: `python3`, `python`, `py -3`. "Funzionante" =
   `<cmd> -c "<verifica ≥ 3.9 e stampa sys.executable>"` riesce (scarta lo stub
   del Microsoft Store e versioni vecchie); il percorso assoluto si salva.
   Poi `exec <python> <scripts>/lasagna.py "$@"`.
   `run.sh python` mostra il percorso in uso, `run.sh python --reset` lo
   ricerca da capo, `run.sh python <percorso>` lo imposta; `session-status`
   riporta a inizio sessione quale Python è in uso.
4. Non trovato → per i guardrail bloccanti (`block-test-edits`,
   `block-test-reads`, `block-code-reads`) `exit 2` con messaggio "lasagna
   richiede Python ≥ 3.9: installalo o disattiva lasagna in questo progetto";
   per gli altri `exit 0` con avviso su stderr; `session-status` stampa un avviso
   evidente.

Da verificare in implementazione: che su Windows Claude Code esegua i comandi
degli hook tramite Git Bash (in v1 funzionava con `sh`).

#### `hooks.json` v2

| Evento | Matcher | Comando |
|---|---|---|
| SessionStart | `*` | `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" hook session-status` |
| PreToolUse | `^(Edit\|Write\|MultiEdit\|NotebookEdit)$` | `… hook block-test-edits` |
| PreToolUse | `^(Read\|Grep\|Glob\|Bash\|NotebookRead)$` | `… hook block-reads` (gestisce sia test-reads sia code-reads) |
| PostToolUse | `^Bash$` | `… hook capture-test-result` |
| SubagentStop | `^plugin:lasagna:(test-writer\|implementer\|referee)$` | `… hook count-cycle` |
| PreCompact | `*` | `… hook dump-phase-state` |

Rimosso: PostToolUse `check-onion`.

#### Comportamento dei guardrail

Identificazione dell'agente (come v1): campo `agent_type` del payload se presente
(autorevole dentro un subagent), altrimenti `active_role` del phase state.

- **block-test-edits** (`hooks_disabled: block-tests`): agente implementer +
  percorso che corrisponde a `test_file_pattern` → exit 2 con il messaggio di v1
  (riformulato se serve). Percorsi presi da `tool_input.file_path` /
  `tool_input.notebook_path` con parsing JSON reale.
- **block-test-reads** (`hooks_disabled: block-test-reads`): agente implementer +
  Read/Grep/Glob su percorso di test, o Bash il cui comando contiene un percorso
  di test e **non** corrisponde a `test_command_pattern` → exit 2. Eseguire la
  suite è sempre permesso.
- **block-code-reads** (`hooks_disabled: block-code-reads`): agente test-writer +
  `phase: tdd-loop` + Read/Grep/Glob su un percorso sotto un `source_path` che
  **non** corrisponde a `test_file_pattern`, o Bash che cita un tale percorso
  senza essere il comando di test → exit 2. **Non** si applica in
  `phase: characterize` (bugfix/brownfield, dove leggere il codice è
  necessario). Sempre leggibili: test, `.lasagna/`, `docs/`, contesto.
- **Limite dichiarato**: il filtro su Bash è euristico (un comando creativo può
  aggirarlo). È un ostacolo, non un muro; va scritto così nel README.
- Grep/Glob senza `path` (= tutto il repo): per gli agenti bloccati si nega con
  il messaggio "restringi la ricerca ai test / al contratto".

#### Comportamento degli altri hook

- **capture-test-result**: se il comando Bash corrisponde a
  `test_command_pattern`, classifica l'output (`tool_response`) nell'ordine
  `fail_compile` → `fail_assert` → `fail_generic` → `pass` → `unknown` e scrive
  `last_test_result`, `last_test_command`, `last_test_at`. Stessa semantica di v1.
  L'hook non conosce nessun runner: decide solo dai pattern del profilo del
  progetto. I golden file (output **reali**, mai trascritti) servono a
  verificare i pattern delle varianti di stack distribuite, per i runner
  disponibili sulla macchina di sviluppo/CI. Dove v1 sbagliava perché applicava
  le regex al JSON grezzo su una riga (es. `^E +assert`), la deviazione è
  accettata e documentata nel golden file (deciso 2026-10-06).
- **count-cycle**: come v1 (log nel `## Cycle log`, `active_role: none`,
  incrementa `cycles_used` solo per l'implementer, escalation quando
  `cycles_used >= budget_max` e l'ultimo esito non è `green`), più D10: se
  `budget_max` manca lo ricava da `layer` (`core`/`shell`) o da `flow: bugfix`.
  Il contatore è **solo dell'hook** (deciso 2026-10-06): quando l'implementer
  chiude in `green` il criterio è chiuso e l'hook azzera `cycles_used`; la skill
  non lo tocca.
- **dump-phase-state**, **session-status**: porting 1:1 del comportamento v1;
  session-status aggiunge l'avviso su Python mancante (fatto dal launcher) e
  segnala profili v1 (presenza di chiavi `core_*`, vedi §6.2).

#### Script CLI

Tutti diventano sottocomandi: `sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" <cmd>`.

| v1 | v2 |
|---|---|
| `set-state.sh <key> <value>` / `--append` | `set-state` (stessi argomenti) |
| `check-traceability.sh [FEAT]` | `check-traceability` |
| `init.sh` | `init` |
| `session-status.sh` | `hook session-status` / `status` |
| `check-onion.sh`, `onion-baseline.sh` | **eliminati** |
| `lib.sh` | `lasagna_lib/` |

Tutti i riferimenti a `scripts/*.sh` in skill, comandi e agenti vanno
aggiornati (oggi ~30 file li citano).

#### CI

- `lint.yml`: sostituire shellcheck-su-tutto con: `ruff check` + `pytest` su
  matrice Python 3.9 e 3.12 × ubuntu e windows; shellcheck solo su `run.sh`.
- `validate.yml`: invariato.

### 6.2 Profilo `.lasagna/stack.md`

| Chiave | Stato v2 |
|---|---|
| `language`, `runtime`, `package_manager` | invariate |
| `test_command`, `test_command_pattern`, `fail_*_pattern`, `pass_pattern` | invariate |
| `test_path`, `test_file_pattern` | invariate |
| `source_path` | **nuova**, ripetibile: dove sta il codice di produzione (per `block-code-reads`) |
| `core_path`, `core_allowed_import`, `core_import_pattern`, `core_forbidden_pattern` | **rimosse** |
| `typecheck_command`, `lint_command`, `mutation_command` | invariate (aggiornare i path d'esempio che citano `src/domain`) |
| `budget_domain`, `budget_adapter` | **rinominate** `budget_core` (3), `budget_shell` (5); **nuova** `budget_bugfix` (5) |
| `git_host`, `issue_cli`, `bugfix_automerge`, `adr_dir` | invariate |
| `context_file` | **sostituita** da `context_dir` (default `docs/context`) |
| `hooks_disabled` | nomi validi: `block-tests`, `block-test-reads`, `block-code-reads`, `test-result`, `budget`, `precompact`, `session-status` (`onion` rimosso) |

Compatibilità: se il profilo contiene chiavi `core_*` o `budget_domain`/`budget_adapter`,
gli script le ignorano/mappano (`budget_domain`→`budget_core`,
`budget_adapter`→`budget_shell`) e `session-status` suggerisce di aggiornare il
profilo. Se c'è `context_file` e non `context_dir`, il file indicato vale come
unico contesto.

File da aggiornare: `templates/stack/base.md`, `python.md`, `typescript.md`,
`jvm.md`, `dotnet.md` (togliere la sezione "Layering rules", aggiungere
`source_path`).

### 6.3 Nuovi file di progetto

- **`.lasagna/architecture.md`** (committato, nuovo template
  `templates/architecture.md`): livello di separazione scelto (§5.3); dove stanno
  core e shell; librerie ammesse nel core; convenzioni (errori, DI, test,
  struttura); uso dei `Protocol`. Scritto dal grilling (greenfield) o da
  reverse-spec (brownfield), confermato dall'umano. Letto da domain-modeling,
  freeze-contract, implementer, adversarial-reviewer. **Nessun hook lo legge.**
- **`.lasagna/design-notes.md`** (committato, template
  `templates/design-notes.md`): proposte di miglioramento del design non
  applicate. Per voce: cosa, perché, costo stimato, stato (`proposta`,
  `accettata`, `rifiutata`).

### 6.4 Phase state (`templates/phase-state.md`)

- `layer`: valori `core` | `shell` (al posto di `domain` | `adapter`).
- `phase`: valori `grilling`, `spec`, `gate-spec`, `domain-modeling`,
  `freeze-contract`, `gate-contract`, `characterize`, `tdd-loop`,
  `adversarial-review`, `gate-pr`, `done` (rimosso `ports-adapters`, aggiunto
  `characterize`).
- Nuovo campo `current_slice`: id della fetta in corso (es. `S1: AC-…-001,
  AC-…-002`).
- Nuovo campo `contexts`: contesti caricati per la feature (copiati dalla spec).
- Documentare D10: `cycles_used` si azzera alla chiusura di ogni criterio.

### 6.5 Router e comandi

- `commands/lasagna.md`: tabella di dimensionamento delle fasi senza
  `ports-adapters`; nuova riga `pr-gate` (mai saltata); i budget citati diventano
  core 3 / shell 5 / bugfix 5.
- `commands/lasagna-init.md` + `init`: crea `.lasagna/stack.md`,
  `.lasagna/architecture.md` (vuoto da compilare), `docs/context/INDEX.md` se
  manca; **propone** la riga per `CLAUDE.md` e la aggiunge solo con conferma;
  verifica la presenza di Python ≥ 3.9 e lo riporta.
- `commands/lasagna-status.md`: mostra livello architetturale, fetta corrente,
  contesti caricati, budget per criterio.

### 6.6 Skill

| Skill | Modifiche |
|---|---|
| `grilling` | Round 0: anche `source_path`. Nuova domanda obbligatoria (greenfield): **livello di separazione** con raccomandazione motivata (§5.3) e librerie ammesse nel core → `.lasagna/architecture.md`. Nuova domanda: **quali contesti** tocca la feature (dall'`INDEX.md`). Togliere le domande su core paths/import allowlist/forbidden patterns. In brownfield il livello non si chiede: si rileva (reverse-spec). |
| `to-spec` | Leggere il contesto da `context_dir` (non `CONTEXT.md` fisso); la spec dichiara `contexts:`. Proporre la **suddivisione in fette** verticali (ordine: prima fetta = tracer bullet end-to-end). |
| `domain-modeling` | D8: output obbligatorio = invarianti + glossario + modulo di appartenenza di ogni regola; aggregati solo se servono, con la regola "aggregati dagli invarianti" conservata per quel caso. Aggiorna i file in `context_dir` (solo i contesti della feature). Mantiene deletion test e stress test. |
| `freeze-contract` | Template nuovo (§6.7). Le "tre failure costose" restano, la terza diventa "non determinismo senza riga nella tabella Dipendenze esterne". Togliere il riferimento a `check-onion.sh`. Brownfield: le firme seguono le convenzioni di `architecture.md`; firme "ideali" diverse vanno in `design-notes.md`. |
| `tdd-loop` | D9 + D10: loop per fetta (core → shell → integrazione se serve); prima fetta tracer bullet; imposta `layer` e `budget_max` per test; azzera `cycles_used` a ogni criterio chiuso. Incorpora le regole di `ports-adapters` elencate in D9. Comandi script aggiornati. |
| `ports-adapters` | **Eliminata.** |
| `pr-gate` | **Nuova.** Contenuto del gate 3 di v1: diff della spec, tabella di tracciabilità, report adversarial, cicli consumati; dopo il merge archivia la spec, verifica ADR e contesto, cancella il phase state. Nessun auto-merge nel flusso official. |
| `adversarial-review` | Aggiunge la checklist FCIS (§D12) come *giudizio*, e la verifica delle convenzioni di `architecture.md`. Dopo: `pr-gate`. |
| `reverse-spec-brownfield` | D3: nuovo passo "rileva le convenzioni" → `architecture.md`; §6 "contratto con le firme che vuoi" sostituito da "firme conformi alle convenzioni; le alternative in `design-notes.md`"; niente più `core_path`/`core_allowed_import` "as they are" (chiavi rimosse). Contesto in `context_dir`. |
| `characterize-bugfix` | Imposta `phase: characterize` durante la caratterizzazione (lettura del codice permessa al test-writer), poi `tdd-loop`; budget `budget_bugfix`. |
| `handoff` | Riferimenti a contesto e script aggiornati. |

### 6.7 Template

- **`contract.md`**: sezioni Seams, Signatures, Data types, Error types, Return
  shape, *What is NOT frozen* invariate. Sezioni "Required ports" e
  "Determinism" sostituite da:

  ```md
  ## External dependencies

  Every source of I/O or non-determinism the code under test needs, and how the
  tests control it. One row each — a missing row is two agents inventing two
  different answers.

  | Dependency | How the code reaches it | How tests control it |
  |---|---|---|
  | Current time | parameter `now: datetime` | fixed value |
  | Order storage | `OrderRepo` (Protocol) | in-memory fake |
  | Email | `notifications.send_email()` | monkeypatch (existing convention) |
  | Config | `Settings` (pydantic) | instance built in the test |
  ```

  Default greenfield: parametro se basta, `Protocol` solo per §5.2 regola 3.
  Brownfield: il meccanismo già usato dal progetto.
- **`spec.md`**: campo `contexts:`; sezione "Slices" (fette con i loro AC).
- **`architecture.md`**, **`design-notes.md`**: nuovi (§6.3).
- **`context/INDEX.md`**, **`context/<name>.md`**, **`context/structure.md`**:
  nuovi template (§6.8).
- `adr.md`, `phase-state.md`: aggiornamenti minori (§6.4).

### 6.8 Contesto di progetto

```
docs/context/
  INDEX.md          # una riga per contesto: nome, una frase, file
  billing.md        # glossario del bounded context (formato CONTEXT.md di v1)
  auth.md
  structure.md      # mappa minimale del codice, separata: invecchia, il glossario no
```

- Regole del glossario (solo termini di dominio, `_Avoid_`, definizioni di 1–2
  frasi) restano nella skill `domain-modeling` (generiche, di lasagna).
- Convenzioni specifiche del progetto → `.lasagna/architecture.md`, non nel
  glossario.
- Riga suggerita per `CLAUDE.md` del progetto:
  `Project context (domain glossary per bounded context, code map) lives in docs/context/ — start from INDEX.md.`
- Tutte le skill/agenti che oggi citano `CONTEXT.md` leggono `INDEX.md` + i soli
  contesti in `contexts:` della spec.

### 6.9 Suite di eval

Strumento: `claude plugin eval` (verificato su Claude Code 2.1.276 con `--help`):

- casi in `plugins/lasagna/evals/<case>/` come `prompt.md` + `graders/*.md`,
  oppure `case.yaml` con `scaffold_script` per partire da un **repo di prova**
  (richiede `--scaffold`);
- ogni caso gira più volte (default 3) in sessione isolata; risultati in
  `evals/results/<timestamp>/aggregate-result.json` + report HTML;
- braccio di confronto **senza plugin** automatico (`--ablation with-without`);
- `claude plugin eval init` crea casi tramite intervista; `--max-cost-usd`,
  `--json`, `--threshold`, `--trust-plugin` per CI.
- Grader (dalla documentazione interna, **da verificare** con `init` o un caso di
  prova): regex, `tool_used` (con min/max, anche "mai usato"), `tool_order`,
  `file_exists`, giudice LLM con rubrica (default haiku).
- **Da verificare con un primo caso**: che gli hook del plugin si attivino dentro
  le run di eval.

**Confronto tra versioni** (non è automatico): stessa suite su due checkout (tag
precedente in un `git worktree` + branch nuovo), poi uno script
(`tools/compare_evals.py`, fuori dal plugin) confronta i due
`aggregate-result.json` per caso: percentuale di successo su ≥ 5 run, delta,
costo.

**Casi iniziali** (suite veloce, a ogni modifica):

| Famiglia | Caso | Verifica |
|---|---|---|
| Routing | richiesta di bug → bugfix; feature decisa → official; codice senza spec → brownfield | skill invocata |
| Gate | richiesta di feature → si ferma alla spec | nessun `Write` sotto `src/`, ultimo messaggio chiede approvazione |
| Isolamento | scaffold in `phase: tdd-loop` | implementer non scrive/legge test; test-writer non legge `src/` |
| Proporzionalità | modifica minuscola | fasi saltate e dichiarate |
| Adattamento | repo FastAPI di prova con convenzioni proprie | nessuna cartella `ports/`/`adapters/` creata; convenzioni seguite (giudice LLM) |
| Architettura greenfield | feature nuova | grilling propone il livello con motivazione; `architecture.md` scritto |

**Suite costosa** (prima di ogni release): esecuzione end-to-end di una feature
piccola su repo di prova partendo da uno stato `.lasagna/` predefinito; esito:
suite verde, tracciabilità ok, cicli consumati. Con `--max-cost-usd`.

### 6.10 Documentazione e metadati

- `README.md` / `README.it.md`: le "cinque discipline" diventano processo (spec,
  TDD, agenti isolati) + principio FCIS proporzionato; rimuovere "Hexagonal/Onion"
  come obbligo; aggiornare tabelle hook (5→6, senza onion, con i blocchi in
  lettura **reali** e il limite su Bash); requisito Python ≥ 3.9; sezione
  "Onion Baseline" eliminata; struttura progetto con `docs/context/`,
  `architecture.md`, `design-notes.md`; esempio budget corretto (D10); roadmap
  Fase 3 segnata come in corso/fatta.
- `CONTRIBUTING.md`: come eseguire pytest e la suite di eval.
- `plugin.json`: versione (vedi §9), descrizione, keywords: togliere
  `domain-driven-design`, `hexagonal-architecture`; aggiungere
  `functional-core-imperative-shell`, `vertical-slices`.

---

## 7. Criteri di accettazione v2

| ID | Criterio |
|---|---|
| AC-V2-001 | Sotto `scripts/` l'unico file `.sh` è `run.sh`. |
| AC-V2-002 | In un progetto senza `.lasagna/stack.md` ogni hook esce 0 senza output. |
| AC-V2-003 | Implementer + Edit/Write/MultiEdit/NotebookEdit su un file che corrisponde a `test_file_pattern` → exit 2 con messaggio. |
| AC-V2-004 | Implementer + Read/Grep/Glob su file di test → exit 2; implementer + Bash che esegue `test_command` → consentito. |
| AC-V2-005 | Test-writer + `phase: tdd-loop` + Read su file sotto `source_path` non di test → exit 2; stessa azione con `phase: characterize` → exit 0. |
| AC-V2-006 | Test-writer + Bash `cat <source_path>/x.py` in `tdd-loop` → exit 2; test-writer + Bash che esegue il comando di test → consentito. |
| AC-V2-007 | `capture-test-result` dà lo stesso esito di v1 sui golden file di output reali dei runner disponibili, salvo le deviazioni documentate (§6.1). |
| AC-V2-008 | `cycles_used` si azzera a ogni criterio chiuso; escalation quando `cycles_used >= budget_max` e ultimo esito ≠ `green`; `budget_max` da `budget_core`/`budget_shell`/`budget_bugfix`. |
| AC-V2-009 | Python assente in un progetto lasagna → i guardrail bloccanti escono 2 con istruzioni; gli altri escono 0 con avviso; `session-status` avvisa. |
| AC-V2-010 | Il payload degli hook è letto con `json`; i percorsi vengono da `tool_input`. |
| AC-V2-011 | Le funzioni di `lasagna_lib/core/` hanno unit test senza mock; pytest verde su Python 3.9 e 3.12, Linux e Windows (CI). |
| AC-V2-012 | Nessun riferimento a `check-onion`, `onion-baseline`, `core_path`, `core_allowed_import`, `core_forbidden_pattern` nel plugin (grep vuoto). |
| AC-V2-013 | Nessuna skill/agente/template impone ports, adapter o aggregati come obbligatori; la skill `ports-adapters` non esiste; esiste `pr-gate`. |
| AC-V2-014 | Il grilling (greenfield) pone la domanda sul livello di separazione con raccomandazione e scrive `.lasagna/architecture.md`. |
| AC-V2-015 | Il reverse-spec scrive le convenzioni rilevate in `architecture.md` e le proposte in `design-notes.md`, senza applicarle. |
| AC-V2-016 | Il template contratto ha la sezione "External dependencies" e non ha "Required ports" né "Determinism". |
| AC-V2-017 | Il tdd-loop descrive il ciclo per fetta (core → shell → integrazione) con prima fetta tracer bullet; `ports-adapters` assente dai valori di `phase`. |
| AC-V2-018 | Chiave `context_dir`; le skill leggono `INDEX.md` + i contesti della spec; nessun `CONTEXT.md` scritto a mano nelle skill. |
| AC-V2-019 | Profili v1 (chiavi `core_*`, `budget_domain`, `context_file`) funzionano con mappatura e avviso. |
| AC-V2-020 | Esiste una suite di eval con almeno i casi della suite veloce (§6.9) eseguibile con `claude plugin eval`; risultati di riferimento salvati per v1 e v2. |
| AC-V2-021 | README e README.it descrivono la v2 (niente esagonale obbligatorio, blocchi in lettura reali con il limite su Bash, requisito Python). |

---

## 8. Ordine di lavoro

0. Riallineare `develop` con `main`, creare il branch `v2`. (Commit e push solo
   su richiesta del maintainer.)
1. **Hook in Python** (§6.1) con test pytest, implementati direttamente (D14).
   Prima i moduli `core/`, poi `shell/`, poi `hooks.json` e launcher.
   AC-V2-001…011.
2. **Profilo** e template stack (§6.2), con compatibilità v1. AC-V2-012, 019.
3. **Skill, agenti, template** (§6.4–6.7). AC-V2-013…018.
4. **Contesto di progetto** (§6.8). AC-V2-018.
5. **Suite di eval** piccola (§6.9) + risultati di riferimento v1 e v2. AC-V2-020.
6. **Documentazione e metadati** (§6.10), CI (§6.1). AC-V2-021.

Ogni passo si chiude con la suite pytest verde e, dal passo 5 in poi, con la
suite di eval veloce.

---

## 9. Punti aperti

- **Team** (rimandato, oggi un solo utente):
  - collisione di `FEAT-NNN` tra branch (to-spec assegna "il prossimo numero
    libero") → usare il numero della issue (roadmap Fase 2);
  - phase state locale e gitignored → nessun passaggio di consegne se non via
    `handoff`;
  - `approved_by` testo libero → gate legati alle approvazioni reali (review PR,
    CODEOWNERS);
  - convenzioni di team iniettabili senza fork (roadmap Fase 5), notifiche ai gate.
- **Versione**: proposta `0.2.0` (cambi incompatibili in fase pre-1.0); da
  confermare.
- **ADR per D1–D14** nel repo: da confermare (D14).
- **`examples/httpskills`**: resta v1 o va migrato a v2?
- **Licenza di `testing-on-the-toilet`**: da verificare prima di riusarne testo.
- **Sostenibilità di D5** (implementer cieco sui test): da rivalutare con i dati
  della suite di eval (cicli medi per criterio).

Emersi durante l'implementazione (2026-10-07):

- **AC-V2-012 vs AC-V2-019**: il grep "nessun `core_path`…" non può essere vuoto
  se i profili v1 devono funzionare con mappatura. Interpretazione adottata:
  le chiavi v1 compaiono solo nello strato di compatibilità
  (`core/profile.py`, `core/budget.py`, `templates/stack/base.md`), escluso dal
  controllo in `tests/test_repo.py`.
- **Baseline delle eval (AC-V2-020) non ancora prodotte**: le run di
  `claude plugin eval` sono processi `claude` figli che non ereditano il login
  dell'app desktop; vanno lanciate da un terminale autenticato. Su Windows il
  runner rifiuta di concedere Bash senza sandbox: i casi veloci non lo usano, il
  caso `e2e-small-feature` va eseguito su Linux/macOS o in CI. Resta da
  verificare che gli hook del plugin scattino dentro le run (casi `isolation-*`).
- **Golden file**: solo pytest (unico runner presente sulla macchina di
  sviluppo); TypeScript, JVM e .NET risultano "non verificati" finché qualcuno
  non cattura output reali con `tools/capture_golden.py`.
- **Python 3.9**: verificato solo in CI (localmente 3.11 e 3.13).

---

## 10. Riferimenti esterni

Functional core, imperative shell:
- Gary Bernhardt, *Boundaries* (2012) — origine del pattern: https://www.destroyallsoftware.com/talks/boundaries
- Kenneth Lange, *The Functional Core, Imperative Shell Pattern*: https://kennethlange.com/functional-core-imperative-shell/
- Rico Fritzsche, *Functional Core / Imperative Shell for Agentic Coding* — il repo insegna la struttura all'agente; cartelle per funzionalità, nomi di comportamento, skill di progetto: https://ricofritzsche.me/functional-core-imperative-shell-for-agentic-coding/
- davemo, *Deterministic Core, Agentic Shell* (2026) — nucleo deterministico, LLM come shell: https://blog.davemo.com/posts/2026-02-14-deterministic-core-agentic-shell.html
- sbrudz/agent-skills — skill FCIS come checklist di review (logica impura, shell grasse, effetti nascosti): https://github.com/sbrudz/agent-skills
- ed3d-plugins, skill FCIS — include quando non applicarla (prototipi, retrofit senza beneficio): https://claudemarketplaces.com/skills/ed3dai/ed3d-plugins/functional-core-imperative-shell

Vertical slicing / TDD:
- Matt Pocock, skill `tdd` (vertical slice, tracer bullet, test sulle interfacce pubbliche): https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md
- Breaking PRDs into Vertical Slices: https://deepwiki.com/mattpocock/skills/3.2-breaking-prds-into-vertical-slices

Testing:
- shamashel, *testing-on-the-toilet* skill (sintesi della serie Google Testing on the Toilet): https://github.com/shamashel/testing-on-the-toilet/blob/main/skills/testing-on-the-toilet/SKILL.md

Python:
- PEP 544 — Protocols (structural subtyping): https://peps.python.org/pep-0544/

Eval:
- `claude plugin eval --help` (Claude Code ≥ 2.1.276) — riferimento primario.
- Skill Benchmark Harness (metodologia con braccio di controllo): https://mcpmarket.com/tools/skills/skill-benchmark-harness
