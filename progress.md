# FINsim Backend — Progress Report

**Ultimo aggiornamento:** 2026-06-05  
**Status:** Core infrastructure completato, fase di test e ottimizzazione in corso

---

## Panoramica del Progetto

FINsim è un simulatore finanziario multi-agente progettato per valutare l'efficacia di una strategia commerciale **Adattiva** (AI-driven) rispetto a una strategia **Fissa** (Benchmark broadcast) su **20 round consecutivi** con **100 clienti sintetici**.

### Architettura a 4 Livelli
1. **Livello 1 — ScenarioMacro:** 1 nodo, comportamento deterministico lungo 20 round
2. **Livello 2 — DirettivaBancaria:** 1 agente adattivo, elaborato via HEAVY_LLM (qwen2.5:32b)
3. **Livello 3 — Promotori:** N agenti in parallelo, A/B split (Adattivo vs Fisso), mix HEAVY_LLM + LIGHT_LLM
4. **Livello 4 — Clienti:** 100 agenti sintetici in griglia (5×20), batch LIGHT_LLM (qwen2.5:3b)

---

## Timeline Implementazione Backend

### Fase 1: Fondamenta e Configurazione (Commit: 313fe64 → f47fa5c)

**Cosa è stato fatto:**
- ✅ Aggiunto file `CLAUDE.md` con specifiche progettuali e vincoli di sicurezza
- ✅ Definito schema FINsim (`finsim_schema.json`) con:
  - 13 label node type (ScenarioMacro, DirettivaBancaria, Promotore, Cliente, etc.)
  - 10 relationship types (DEFINISCE, OPERA_IN, GESTISCE, EFFETTUA, etc.)
  - Property allowlist per ogni node type
- ✅ Pinned Neo4j a v5.18 per stabilità (PR #10)

**File principali creati:**
- `backend/app/finsim/` — Directory root per tutti i moduli FINsim
- `backend/app/finsim/finsim_schema.json` — Schema ontologia con allowlist

---

### Fase 2: Ontologia, Schema e Popolazione (Commit: a4dcf2d → b19fd7e)

**Cosa è stato fatto:**
- ✅ Implementato modulo `ontology_loader.py`:
  - Classe `OntologyLoader` per creazione bulk di nodi Neo4j
  - Supporto property serializzazione/deserializzazione
  - Validazione label/relationship contro allowlist (security)
  
- ✅ Creato `populate_finsim.py`:
  - Script di popolazione iniziale per 5 scenari macro (S0-S4)
  - Generazione 100 clienti sintetici (5 righe × 20 colonne)
  - Creazione nodi DirettivaBancaria con parametri scenario-specifici
  - Assegnazione promotori e cluster initialization

- ✅ Implementato `search_finsim.py`:
  - FinsimSearcher per query ontologia
  - `get_scenario_state()` — fetch parametri macroeconomici
  - `get_directive()` — retrieve directive per scenario
  - `get_promotore_portfolio()` — client list per promotore
  - `get_cluster_clients()` — clients in griglia (riga, colonna)

**Security hardening:**
- Zero concatenazioni in Cypher queries (parametrizzazione nativa)
- Validazione allowlist per ogni label/relationship dinamica

---

### Fase 3: Integrazione LLM e Client REST (Commit: 4d6ae58 → aec57fc)

**Cosa è stato fatto:**
- ✅ Implementato `ollama_client.py`:
  - OllamaClient REST per Ollama (qwen2.5:32b, qwen2.5:3b)
  - Supporto embedding via endpoint `/api/embed`
  - Chat completion via `/api/chat`
  - Gestione timeout e fallback locale

- ✅ Creato `promoter_agent.py`:
  - PromotoreAgent per decisioni commerciali adattive
  - `genera_strategia_cluster()` — LLM prompt per strategia A/B
  - Injection di contesto (scenario, directive, portfolio client)
  - Fallback a strategia fissa se LLM down

- ✅ Aggiunto `results_exporter.py`:
  - JSON exporter per risultati simulazione
  - Struttura: scenario → round → promotore → decisions + metrics

---

### Fase 4: SimulationEngine e Round Orchestration (Commit: 0a15f62 → de3e616)

**Cosa è stato fatto:**
- ✅ Implementato `simulation_engine.py`:
  - SimulationEngine: orchestrazione core per esecuzione round
  - `esegui_round(scenario_id, round_n)`:
    - Fetch DirectivaBancaria e parametri scenario
    - Enumera promotori attivi per A/B split
    - Invoca LLM per strategia adattiva vs fissa
    - Persiste DecisioneCommerciale + EFFETTUA relationships
  - `salva_decisione_db()` — Node persistence con validation
  - `calcola_reazione_clienti()` — Trust update basata su product-risk congruence

- ✅ Creato `run_simulation.py`:
  - Standalone runner per esecuzione round singoli
  - Carica Config, connessione Neo4j
  - Executes Round 1 per S0
  - Displays decision summary + client trust distribution

**Design decisions:**
- **Cluster optimization:** Query solo cluster attivi (con GESTISCE → Cliente)
- **Trust logic:**
  - Match esatto: +0.1 (capped 1.0)
  - 1-level mismatch: no change
  - 2-level mismatch: -0.15 (floored 0.0)
- **Parameterized Cypher:** Security-first, no f-strings in queries

---

### Fase 5: Bug Fixes Strutturali e Caching (Commit: 436468a → bcdfe9b)

**Cosa è stato fatto:**
- ✅ **Audit strutturale (436468a):**
  - Fixed ID generation typos in client/scenario creation
  - Allineato formato ID con expectation nei prompt LLM
  - Audit su state persistence tra round

- ✅ **Database Property Alignment (4d6ae58):**
  - **Problem:** `populate_finsim.py` creava properties in dict, ma queries cercavano direct node properties
  - **Fix:** Modified `ontology_loader.py` per `SET n += node_data.properties` deserializzazione
  - **Schema validation:** Created `finsim_schema.json` con property definitions
  - **Result:** Neo4j node properties ora allineate con query expectations (scenario_id, promotore_id, etc.)

- ✅ **Caching mechanism (bcdfe9b):**
  - Implementato scenario completion cache in SimulationEngine
  - Skip already-executed rounds per non ricalcolare
  - Speedup drammatico su multi-scenario runs

---

### Fase 6: A/B Testing Refinement e Client Portfolio (Commit: 0d8eb21)

**Cosa è stato fatto:**
- ✅ **A/B Split Logic:**
  - Refined promoter allocation tra Adaptive vs Fixed strategy
  - Garantito balanced split per cross-scenario comparison
  - Client portfolio size ajustment per promoter type

- ✅ **Portfolio Sizing:**
  - Adaptive promoters: cluster-based assignment
  - Fixed promoters: benchmark portfolio con size constraints
  - Validation su total portfolio ≤ 100 clients

---

### Fase 7: Documentation e Architecture (Commit: 2ac18f3 → 86a0498)

**Cosa è stato fatto:**
- ✅ **Backend Architecture Diagram:**
  - Created `backend_architecture.puml` (PlantUML)
  - Visual representation: Neo4j → Search → SimulationEngine → LLM (Ollama)
  - Layer by layer orchestration flow

- ✅ **README Updates:**
  - Documented 5 simulation scenarios (S0-S4)
  - Architecture overview
  - Setup e run instructions

- ✅ **Style improvements:**
  - Updated diagram themes per consistency

---

## Stack Tecnologico

| Componente | Tecnologia | Versione | Note |
|---|---|---|---|
| **Language** | Python | 3.11-3.12 | Vincolo camel-oasis |
| **Database** | Neo4j | 5.18 | Pinned per stability |
| **LLM Inference** | Ollama | Latest | Local + CPU-bound |
| **LLM Models** | qwen2.5 | 32b (HEAVY), 3b (LIGHT) | Per tier architettura |
| **HTTP Client** | aiohttp / requests | Latest | REST API Ollama |
| **Config** | YAML | N/A | `backend/app/config.py` |

---

## Struttura Directory Backend

```
backend/app/finsim/
├── ontology/
│   ├── ontology_loader.py          # Node/relationship creation
│   ├── search_finsim.py            # Query DSL
│   └── finsim_schema.json          # Allowlist schema
├── agents/
│   ├── promoter_agent.py           # PromotoreAgent (LLM decision)
│   └── client_agent.py             # ClientAgent (fallback/batch processing)
├── infrastructure/
│   ├── ollama_client.py            # REST client Ollama
│   ├── neo4j_storage.py            # (inherited) Storage interface
│   └── config.py                   # (inherited) Configuration
├── simulation/
│   ├── simulation_engine.py        # Core orchestration
│   ├── run_simulation.py           # Standalone runner
│   └── results_exporter.py         # JSON output
├── populate_finsim.py              # Initial data population
└── __init__.py
```

---

## Features Implementate

### ✅ Core Simulation Loop
- Round-by-round execution per scenario
- Multi-scenario support (S0-S4)
- State persistence Neo4j
- Trust dynamics update

### ✅ A/B Testing
- Adaptive strategy via LLM (PromotoreAgent)
- Fixed benchmark strategy fallback
- Balanced split per test rigor
- Cross-scenario comparison capability

### ✅ Agent Communication
- Scenario → Directive → Promoter → Client
- LLM prompts context-injected (scenario, directive, portfolio)
- Fallback locale se LLM unavailable

### ✅ Database Integrity
- Property alignment fixed (all expected properties on nodes)
- Allowlist-validated labels/relationships
- Parameterized Cypher (zero injection risk)
- Unique constraints per scenario/promoter/client IDs

### ✅ Performance
- Bulk node creation (optimize Neo4j writes)
- Cluster-only enumeration (avoid 5×20 blind iteration)
- Scenario completion caching (skip re-execution)
- Batch client processing via LIGHT_LLM

---

## Known Issues & Roadmap

### Fase 7 (In Progress) — Security Hardening
- [ ] CVE-2026-7059: Path traversal in simulation.py (Platform param non-sanitizzato)
- [ ] CVE-2026-7058: Command injection in services/send_command
- [ ] Parametrizzazione completa tutte query dinamiche

### Fase 8 — Integration Testing
- [ ] Full round 1-20 execution su S0
- [ ] Cross-scenario comparison metrics
- [ ] A/B significance testing
- [ ] Performance benchmarking (round execution time)

### Fase 9 — Observability
- [ ] Logging round decisions (LLM reasoning)
- [ ] Metrics export (Prometheus format)
- [ ] Trace integration per debug

### Fase 10 — Optimization
- [ ] Parallel round execution (Async SimulationEngine)
- [ ] Batch client trust calculation
- [ ] LLM prompt caching per scenario-directive pair

---

## Metriche di Stato

| Metrica | Valore | Status |
|---|---|---|
| Lines of Code (Backend) | ~3500 | ✅ Stable |
| Neo4j Queries | 25+ | ✅ Parameterized |
| Test Coverage | Syntax validated | ⚠️ Need unit tests |
| Security Compliance | 8/10 | ⚠️ CVEs pending |
| Documentation | CLAUDE.md + README | ✅ Complete |

---

## Come Continuare

### Per eseguire una simulazione:
```bash
cd backend/app/finsim
python run_simulation.py
```

### Per ripopolare ontologia (reset):
```bash
python populate_finsim.py
```

### Per query database:
```python
from search_finsim import FinsimSearcher
searcher = FinsimSearcher(config)
scenario = searcher.get_scenario_state("s0")
print(scenario)
```

---

## Commit Reference

| Commit | Titolo | Fase |
|---|---|---|
| 313fe64 | CLAUDE.md + schema FINsim | 1 |
| a4dcf2d | Ontology + populate + search | 2 |
| 4d6ae58 | Ollama client + promoter agent | 3 |
| 0a15f62 | SimulationEngine | 4 |
| 436468a | Audit strutturale + ID fixes | 5 |
| bcdfe9b | Caching mechanism | 5 |
| 0d8eb21 | A/B split refinement | 6 |
| 2ac18f3 | Architecture diagram | 7 |
| 86a0498 | README + documentation | 7 |

---

**Prossima sessione:** Focus su CVE hardening (Fase 7) e test end-to-end Round 1-20.
