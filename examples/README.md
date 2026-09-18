# examples/

Progetti dimostrativi che usano il plugin `lasagna` in un contesto reale — la vetrina
del funzionamento del sistema, e allo stesso tempo un portfolio di progetti indipendenti.

## Convenzione

Ogni progetto qui dentro è un **git submodule**: un repository GitHub a sé stante,
clonabile, forkabile e linkabile indipendentemente da questo repo (utile per CV/portfolio),
agganciato qui solo come puntatore a un commit preciso. Nessuna dipendenza condivisa tra
progetti: ognuno ha il proprio stack, le proprie dipendenze, la propria history.

```bash
# clonare questo repo insieme a tutti gli examples
git clone --recurse-submodules https://github.com/TommasoTerrin/lasagna-code.git

# se hai già clonato senza, recuperali dopo
git submodule update --init --recursive
```

## Come un progetto qui dentro usa lasagna

Ogni progetto committa il proprio `.claude/settings.json` per dichiarare il plugin —
non si copia mai la cartella `plugins/lasagna/`:

```json
{
  "extraKnownMarketplaces": {
    "lasagna": {
      "source": { "source": "github", "repo": "TommasoTerrin/lasagna-code" }
    }
  },
  "enabledPlugins": { "lasagna@lasagna": true }
}
```

Poi, dentro il progetto: `claude plugin install lasagna@lasagna`, seguito da
`/lasagna-init` per generare `.lasagna/stack.md` e la struttura del harness.

## Progetti

| Progetto | Cosa testa | Stato |
|---|---|---|
| [`httpskills/`](https://github.com/TommasoTerrin/httpskills) | server MCP (fastmcp) — libreria skill centralizzata via protocollo Agent Skills | domain + adapter layer completi, 39 criteri coperti |

Ogni progetto qui dentro spedisce, quando sensato, una propria cartella di
esempio (es. `skills/` in `httpskills/`) con contenuto dimostrativo reale —
non un fixture di test isolato, ma qualcosa che il progetto stesso serve
quando lo avvii così com'è. Il README di ciascun progetto la documenta.
