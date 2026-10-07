# 🍝 lasagna — Harness Layered Spec-Driven per Claude Code

![lasagna hero](.github/assets/hero.png)

[🇬🇧 English version](README.md) | [🇮🇹 Italiano](README.it.md)

> **Nota:** Questa è una versione semplificata. Per documentazione completa, roadmap e diagrammi, vedi la [versione inglese](README.md).

**L'opposto dello spaghetti code.** Un plugin per Claude Code che porta struttura allo sviluppo software attraverso specifiche precise, contratti congelati e un ciclo rosso-verde in cui **chi scrive il test e chi scrive il codice sono separati meccanicamente**.

lasagna è **rigido sul processo e flessibile sull'architettura**.

- **Spec-driven**: si parte da una spec precisa approvata da un umano. Il contratto si congela prima di qualunque codice.
- **Test-driven, per fette verticali**: un test per ciclo, rosso osservato prima del verde. Ogni fetta attraversa tutto (logica, shell, integrazione); la prima è un *tracer bullet* end-to-end.
- **Agenti isolati davvero**: il test-writer non può leggere il codice di produzione, l'implementer non può né leggere né scrivere i test. Lo impediscono degli hook.
- **Architettura in proporzione**: il principio preferito è *functional core, imperative shell* (logica pura al centro, I/O ai bordi), applicato nel livello che il progetto richiede — *minimo*, *modulare*, *esagonale completo*. Sui progetti esistenti lasagna **adotta le convenzioni che trova** invece di convertirle.
- **Protetto**: tre gate umani, budget di cicli per criterio, tracciabilità dai criteri di accettazione ai test.
- **Stack-agnostico**: Python/TypeScript/JVM/.NET. Progetti nuovi e codebase esistenti.

---

## Requisiti

- Claude Code con supporto ai plugin.
- **Python ≥ 3.9** sulla macchina, solo libreria standard (niente `pip install`): gli hook sono in Python. lasagna cerca `python3`, `python`, `py -3` la prima volta e ricorda quello trovato (`run.sh python` lo mostra, `run.sh python --reset` lo ricerca, `run.sh python <percorso>` lo imposta). Senza Python, in un progetto lasagna i guardrail bloccanti **falliscono chiusi**, e l'avvio di sessione lo segnala.

---

## Il flusso

I quattro flussi principali:

1. **Ufficiale** (feature decisa): intervista → spec con le fette → modello di dominio → contratto congelato → loop rosso-verde fetta per fetta (core budget 3, shell budget 5) → revisione avversariale → gate PR → merge.
2. **Prototipo** (idea incerta): intervista ridotta → prototipo → validazione → se sì, rientra come brownfield.
3. **Bugfix** (difetto in codice che funziona): caratterizza il comportamento attuale → test che riproduce il bug (rosso) → loop (budget 5) → revisione → merge.
4. **Brownfield** (codice esistente senza spec): rileva le convenzioni del progetto → ricostruisci la spec dal codice → l'umano conferma cosa è voluto vs bug vs codice morto → si prosegue come ufficiale, seguendo le convenzioni rilevate.

Ogni flusso ha un **gate finale obbligatorio** (revisione PR), salvo il bugfix che può fare auto-merge se configurato.

---

## Cosa è applicato, cosa no

### Meccanico (hook, sempre attivo salvo disattivazione)

Solo dove serve una verità meccanica:

- **Blocco scrittura test**: l'implementer non può modificare file di test.
- **Blocco lettura test**: l'implementer non può leggere i file di test (Read/Grep/Glob e comandi Bash che li citano). Eseguire la suite è sempre permesso: l'output del fallimento è informazione, non accesso al file.
- **Blocco lettura codice**: durante `tdd-loop` il test-writer non può leggere il codice di produzione (`source_path`). Non vale in `characterize` (bugfix, brownfield), dove leggere il codice è il lavoro.
- **Cattura dell'esito test**: ogni esecuzione è classificata (verde / rosso-compile / rosso-assertion / rosso-generico / sconosciuto) dall'output reale.
- **Budget per criterio**: 3 tentativi sui test del core, 5 su shell, integrazione e bugfix. Il conteggio si azzera quando un criterio diventa verde; esaurito il budget, escalation a un umano.
- **Stato della fase**: salvato prima della compattazione, mostrato all'avvio di sessione.
- **Tracciabilità**: ogni `AC-<feature>-NNN` deve comparire nei test, e viceversa (`run.sh check-traceability`).

**Limite dichiarato:** il filtro sui comandi Bash è euristico — un comando creativo può aggirarlo. È un ostacolo, non un muro.

### Giudizio (skill e agenti, non controllato da hook)

- **Architettura**: livello di separazione, dove stanno core e shell, convenzioni. Scritto in `.lasagna/architecture.md`, letto da contratto, implementer e reviewer. Nessun hook lo legge.
- **Proporzionalità**: ogni fase passa il *deletion test* — se saltandola la sua complessità ricompare altrove, la si esegue; altrimenti la si salta e lo si dichiara.
- **Test di qualità**: gerarchia dei test double (reale → fake → stub → mock), niente mock di tipi di terze parti, niente test che ricalcano la struttura del codice, test ermetici (dai principi di *Testing on the Toilet* di Google).

---

## Installazione

### Claude Code CLI

```bash
claude plugin marketplace add TommasoTerrin/lasagna-code
claude plugin install lasagna
```

### Poi inizializza

Nel tuo progetto:

```bash
/lasagna-init
```

Verifica Python, rileva lo stack, crea `.lasagna/` (profilo, `architecture.md` vuoto), `docs/context/INDEX.md`, aggiorna `.gitignore` e riporta tutto quello che ha aggiunto. Propone una riga per `CLAUDE.md` e la aggiunge solo con il tuo consenso.

**Ogni guardrail rimane inattivo finché non esiste il profilo dello stack.** Se `init` dice "NOT ready", il profilo manca — scrivilo prima di fare affidamento su qualunque hook.

---

## Utilizzo

```bash
/lasagna official
/lasagna prototype
/lasagna bugfix
/lasagna brownfield
/lasagna-status
```

L'harness instrada verso il flusso corretto in base allo stato in `.lasagna/state/FEAT-NNN.state.md`. `/lasagna-status` mostra fase, fetta corrente, livello architetturale, contesti caricati, cicli sul criterio in corso, criteri coperti ed eventuali escalation.

---

## File chiave nell'harness

### Skill (10)

- **grilling**: intervista socratica: profilo dello stack, livello di separazione (una volta per progetto, con raccomandazione), contesti toccati, i quattro assi architetturali.
- **to-spec**: use case Jacobson, criteri con id, tassonomia degli errori, **fette verticali** (la prima è un tracer bullet).
- **domain-modeling**: regole, invarianti e modulo in cui vive ciascuna; aggregati solo quando serve consistenza atomica; aggiorna i glossari in `docs/context/`.
- **freeze-contract**: firme, tipi di errore, convenzione di ritorno, **dipendenze esterne** e come i test le controllano.
- **tdd-loop**: fetta per fetta, core → shell → integrazione; test-writer e implementer isolati, rosso osservato, budget per criterio.
- **adversarial-review**: buchi nei test, codice non richiesto, deriva dal design, rischi non coperti dalla spec.
- **pr-gate**: gate 3: diff della spec, tracciabilità, report, cicli; dopo il merge archivia la spec.
- **characterize-bugfix**: fissa il comportamento attuale, riproduci il bug, poi tdd-loop.
- **reverse-spec-brownfield**: rileva le convenzioni (→ `architecture.md`), ricostruisce la spec dal codice; le proposte vanno in `design-notes.md`, non applicate.
- **handoff**: comprime la sessione in un documento prima della compattazione.

### Agenti (4)

- **test-writer**: un test per ciclo da un criterio e dal contratto, senza vedere il codice. Osserva il rosso.
- **implementer**: il minimo per far passare il test, partendo da contratto e output del fallimento; non può leggere né scrivere i test.
- **referee**: risolve una disputa su un'asserzione: test sbagliato, codice sbagliato, o criterio ambiguo (→ umano).
- **adversarial-reviewer**: vede tutto, non scrive nulla; cerca buchi e deriva dal design.

### Hook (6, disattivabili)

`hooks_disabled:` nel profilo. Nomi: `block-tests`, `block-test-reads`, `block-code-reads`, `test-result`, `budget`, `precompact`, `session-status`.

---

## Percorsi del progetto (configurabili)

- Spec: `.lasagna/specs/` · Contratti: `.lasagna/contracts/` · Stato: `.lasagna/state/` (gitignored)
- Architettura e proposte: `.lasagna/architecture.md`, `.lasagna/design-notes.md`
- ADR: `docs/adr/`
- Contesto di progetto: `docs/context/` — `INDEX.md`, un glossario per bounded context, `structure.md`

Cambia `adr_dir` e `context_dir` nel profilo se entrano in collisione con il tuo layout. Per monorepo, `LASAGNA_DIR` punta l'harness a un package diverso. I profili v1 continuano a funzionare: le chiavi vecchie sono mappate o ignorate, e l'avvio di sessione suggerisce di aggiornarle.

---

## Valutare il plugin

`plugins/lasagna/evals/` contiene una suite per `claude plugin eval` (instradamento, gate, isolamento, proporzionalità, adattamento al codice esistente, livello di separazione, un caso end-to-end). Ogni caso gira anche **senza** plugin, così ogni punteggio ha il suo delta. Vedi [plugins/lasagna/evals/README.md](plugins/lasagna/evals/README.md).

---

## Limiti noti

- **Nessun auto-merge nel flusso ufficiale** (i 3 gate sono decisioni umane).
- **I subagent non possono avviare altri subagent**: l'orchestrazione gira nel thread principale.
- **Senza profilo dello stack** ogni hook è un'operazione silenziosa (l'avvio di sessione lo segnala).
- **Serve Python ≥ 3.9**.
- **Il filtro Bash è euristico**.
- **La classificazione dell'esito è testuale**: un test che asserisce sulla stringa "ModuleNotFoundError" può essere classificato male. È un suggerimento per l'arbitro, mai un verdetto.
- **Un solo sviluppatore**: id delle feature e stato non sono ancora pensati per i team.

---

## Licenza

MIT. Vedi [LICENSE](LICENSE).

---

## Derivato da

- **Spec-Driven Development**: l'approccio specification-first di Gojko Adzic.
- **Test-Driven Development**: la disciplina rosso-verde-refactor di Kent Beck.
- **Functional Core, Imperative Shell**: Gary Bernhardt, *Boundaries*.
- **Hexagonal Architecture** (Alistair Cockburn) e **Domain-Driven Design** (Eric Evans).
- **Testing on the Toilet**: i consigli di testing di Google.
- **Loop Engineering**: orchestrazione iterativa di agenti di Augment Code.

---

## Il nome

Lasagna è l'opposto dello spaghetti code. Ogni layer è distinto, separato, e ha uno scopo chiaro. Puoi estrarre un layer, capirlo in isolamento, e ricostruirlo. Prova a farlo con lo spaghetti.
