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
│   ├── populate_finsim.py          # Initial data population
│   ├── schema_runner.py            # Schema wipe/reset command
│   ├── test_populate.py            # Integration tests
│   └── finsim_schema.json          # Allowlist schema
├── agents/
│   ├── promotore_agent.py          # PromotoreAgent (LLM decision)
│   └── client_agent.py             # ClientAgent (fallback/batch processing)
├── metrics/
│   ├── normalizzatore.py           # Product normalization logic
│   └── __init__.py
├── llm/
│   ├── ollama_client.py            # REST client Ollama
│   └── __init__.py
├── scripts/
│   ├── migra_json_esistenti.py     # Data enrichment migration script
│   ├── carica_enriched_mongo.py    # MongoDB loader (optional)
│   └── __init__.py
├── simulation_engine.py            # Core orchestration (round execution)
├── search_finsim.py                # Database query interface
├── run_simulation.py               # Standalone simulation runner
├── advisor.py                      # Virtual Advisor API (FastAPI)
├── visualizzatore_grafici.py       # Plotly chart generation (9 types)
├── app_frontend.py                 # Frontend application
├── test_alignment.py               # Property alignment tests
├── test_agent.py                   # Agent unit tests
├── output/                         # Simulation results
│   ├── risultati_S0.json
│   ├── risultati_S1.json
│   ├── risultati_S2.json
│   ├── risultati_S3.json
│   ├── risultati_S4.json
│   └── enriched/                   # Enriched results from migration
│       ├── risultati_S0.json
│       ├── risultati_S1.json
│       └── ...
└── __init__.py
```

---

## Features Implementate

### ✅ Core Simulation Loop
- Round-by-round execution per scenario (1-20 rounds configurable)
- Multi-scenario support (S0-S4) with distinct macro parameters
- State persistence Neo4j with transaction safety
- Trust dynamics update based on product-risk adequacy

### ✅ A/B Testing
- Adaptive strategy via LLM (PromotoreAgent with context injection)
- Fixed benchmark strategy fallback (deterministic rules)
- Balanced 50/50 split across client portfolio
- Cross-scenario comparison capability with metrics

### ✅ Agent Communication
- 4-tier hierarchy: Scenario → Directive → Promoter → Client
- LLM prompts context-injected (scenario, directive, portfolio, risk profiles)
- Fallback strategies if LLM unavailable (deterministic defaults)
- Chat-based advisee agent communication (via advisor API)

### ✅ Advanced Metrics & Analytics
- **Product Normalization:** Intelligent categorization (5 types + fallback)
- **Adequacy Scoring:** Risk-product compatibility matrix (0.0-1.0 scale)
- **Directive Compliance:** Binary flag + per-promoter rate tracking
- **Acceptance Rate:** Threshold-based (≥0.5 adequacy = accepted)
- **Strategic Matrix:** Cross-tabulation of risk profiles × products
- **Round Summaries:** Aggregate metrics per simulation round
- **Scenario Summaries:** Overall compliance, mismatch, acceptance rates

### ✅ Frontend Visualizations
- 9 interactive Plotly charts with premium styling
- HEATMAP_PERFORMANCE: Risk × Wealth strategic grid
- BAR_PRODOTTI: Product satisfaction distribution
- LINEE_COMPARATIVE: Cumulative AUM evolution (20 rounds)
- WATERFALL_PATRIMONIO: Wealth composition breakdown
- SANKEY_FLUSSI: Client flow dynamics and churn
- AREA_GUADAGNI: Revenue generation over time
- SEMAFORO_ADEGUATEZZA: Adequacy compliance traffic light
- ACCETTAZIONI_PER_SCENARIO: Multi-scenario acceptance comparison
- TREND_COMPLIANCE: Regulatory adherence trends

### ✅ Virtual Advisor API
- Ollama-powered (gemma4:e4b) tactical recommendation engine
- Autonomous chart selection based on user query
- Strategic context injection (metrics + historical data)
- JSON-structured responses with detailed captions
- Italian language output with financial terminology
- Health check endpoint for service monitoring

### ✅ Data Migration & Enrichment
- Batch enrichment of existing simulation JSON files
- Neo4j cluster profile lookup integration
- Robust error handling and logging
- Output to separate `enriched/` directory (non-destructive)
- Summary reporting (total decisions, compliance rates)

### ✅ Database Integrity
- Property alignment (all expected properties on nodes)
- Allowlist-validated labels/relationships against `finsim_schema.json`
- Parameterized Cypher queries (zero injection risk)
- Unique constraints per scenario/promoter/client IDs
- Type coercion and validation at boundaries

### ✅ Performance
- Bulk node creation (optimize Neo4j writes)
- Cluster-only enumeration (avoid 5×20 blind iteration)
- Scenario completion caching (skip re-execution)
- Batch client processing via LIGHT_LLM (qwen2.5:3b)
- Efficient Neo4j querying with proper indexing hints

---

### Fase 8: Advanced Metrics & Enrichment (Commit: 7420dc2 → a1d8b8c)

**Cosa è stato fatto:**
- ✅ **Metrics Normalization Module (`normalizzatore.py`):**
  - Intelligent product name normalization (Bond_Corporate, Bond_Sovereign, Cash_Equivalents, Mixed_Funds, Altro)
  - Substring matching with case-insensitive rules
  - Fallback to "Altro" for unrecognized products

- ✅ **Migration Script (`migra_json_esistenti.py`):**
  - Batch enrichment of existing risultati JSON files (S0-S4)
  - Neo4j integration for cluster risk profile lookup
  - Computes adequacy scores per product-risk pair
  - Generates directive compliance metrics
  - Builds strategic matrix (profilo × prodotto analysis)
  - Outputs to `output/enriched/` directory
  - Robust error handling and logging

- ✅ **Round-Level Metrics:**
  - compliance_rate: % decisions matching scenario focus product
  - mismatch_rate: % products rejected (adequacy < 0.5)
  - prodotto_dominante: Most common recommended product
  - dispersione_prodotti: Product diversity count
  - compliance_per_promotore: Directive adherence per strategy

- ✅ **Decision-Level Enrichment:**
  - prodotto_suggerito_raw: Original LLM output
  - prodotto_suggerito: Normalized category
  - profilo_rischio_prevalente: Client cluster risk profile
  - conforme_direttiva: Boolean compliance flag
  - adeguatezza_score: Product-risk fit (0.0-1.0)
  - accettato: Boolean acceptance flag (≥0.5)

**Schema Integration:**
```json
{
  "decision": {
    "promotore": "P1_Fisso",
    "cluster": "(2, 3)",
    "prodotto_suggerito": "Bond_Corporate",
    "prodotto_suggerito_raw": "Obbligazioni Corporate",
    "profilo_rischio_prevalente": "Balanced",
    "conforme_direttiva": true,
    "adeguatezza_score": 0.8,
    "accettato": true
  }
}
```

---

### Fase 9: Frontend Visualizations (Commit: 185f59c → f59dbdf)

**Cosa è stato fatto:**
- ✅ **9 Interactive Plotly Visualizations:**

  1. **HEATMAP_PERFORMANCE** — Risk × Wealth strategic grid
     - Shows Adaptive vs Fixed performance by client segment
     - Color scale: Green (Adaptive wins) → Yellow (Tie) → Red (Fixed wins)
     
  2. **BAR_PRODOTTI** — Product satisfaction distribution
     - Stacked bars showing satisfaction levels per product
     - Identifies best/worst performing financial instruments
     
  3. **LINEE_COMPARATIVE** — Cumulative AUM evolution (Rounds 1-20)
     - Dual-line chart comparing Adaptive vs Fixed total collected assets
     - Shows strategy effectiveness over time
     
  4. **WATERFALL_PATRIMONIO** — Wealth composition breakdown
     - Cascading chart from Initial AUM → Inflows → Outflows → Final AUM
     - Visual decomposition of wealth changes per round
     
  5. **SANKEY_FLUSSI** — Client flow dynamics
     - Flow diagram showing client migrations between clusters
     - Flow thickness indicates migration volume
     - Identifies churn and retention patterns
     
  6. **AREA_GUADAGNI** — Cumulative revenue generation
     - Stacked area chart of earnings across rounds
     - Shows revenue by client segment/product
     
  7. **SEMAFORO_ADEGUATEZZA** — Adequacy traffic light system
     - Color-coded heatmap: Green (≥0.5) → Yellow (0.3-0.5) → Red (<0.3)
     - Grid shows product-risk mismatch hotspots
     
  8. **ACCETTAZIONI_PER_SCENARIO** — Scenario acceptance comparison
     - Bar chart comparing acceptance rates across S0-S4
     - Highlights which scenarios perform best
     
  9. **TREND_COMPLIANCE** — Regulatory compliance trends
     - Line chart of directive adherence per round
     - Compares Adaptive vs Fixed compliance trajectory

**Frontend Integration:**
- Premium Light Mode styling (Segoe UI typography, high contrast)
- Responsive hover templates with emoji indicators
- Automatic color scaling based on data ranges
- Fallback sample data for demo mode

---

### Fase 10: Virtual Advisor API (Commit: 86cc9c3 → ad9c4d1)

**Cosa è stato fatto:**
- ✅ **FastAPI-based Virtual Advisor Service (`advisor.py`):**
  - Analyzes financial metrics and provides tactical recommendations
  - Uses Ollama (gemma4:e4b) for LLM intelligence
  
- ✅ **Endpoints:**
  - `POST /api/advisor/chat` — Generate tactical advice + chart suggestions
  - `GET /health` — Service health check
  
- ✅ **Advanced Chart Selection Logic:**
  - Autonomous decision: chooses 0-4 relevant charts based on user query
  - Strict terminology matching per chart type (non confuse X/Y axes for SANKEY)
  - Rule-based routing (e.g., "patrimonio" → WATERFALL, "churn" → SANKEY)
  
- ✅ **Robust Response Handling:**
  - JSON extraction and validation from LLM output
  - Type coercion for Pydantic models
  - Fallback responses if LLM fails
  - Chart code allowlist filtering
  
- ✅ **Detailed Chart Captions:**
  - 3-part structure: COME LEGGERLO → ESEMPIO CONCRETO → COLLEGAMENTO STRATEGICO
  - Italian language with strict financial terminology
  - Visual component explanations per chart type

**System Prompt Features:**
- Framework: Assess → Identify → Recommend → Visualize
- Context injection: Performance metrics, risk profiles, sentiment
- Critical rules for chart interpretation accuracy
- Autonomous lead analyst role with independent decision-making

---

## Known Issues & Roadmap

### Fase 11 (In Progress) — Security Hardening
- [ ] CVE-2026-7059: Path traversal in simulation.py (Platform param non-sanitizzato)
- [ ] CVE-2026-7058: Command injection in services/send_command
- [ ] Parametrizzazione completa tutte query dinamiche
- [ ] API authentication (JWT bearer tokens)
- [ ] Rate limiting on advisor endpoint

### Fase 12 — Dashboard UI Integration
- [ ] Frontend dashboard with metric visualization panels
- [ ] Real-time metric computation during simulation
- [ ] Chart interaction (drill-down, filtering, export)
- [ ] Advisor chatbot widget integration
- [ ] Scenario comparison view

### Fase 13 — Production Readiness
- [ ] Export capabilities (PDF reports, CSV, Excel)
- [ ] Database optimization (indexes on frequently queried columns)
- [ ] Caching layer for metric computations
- [ ] Monitoring and alerting (performance, errors, advisor accuracy)
- [ ] Documentation and user guides

### Fase 14 — Advanced Analytics
- [ ] Predictive models for client churn
- [ ] Scenario sensitivity analysis
- [ ] A/B statistical significance testing
- [ ] Comparative benchmark reports
- [ ] Advisor feedback loop (learning from user corrections)

---

## Metriche di Stato

| Metrica | Valore | Status |
|---|---|---|
| Lines of Code (Backend) | ~6500+ | ✅ Expanding |
| Neo4j Queries | 30+ | ✅ Parameterized |
| Frontend Charts | 9 interactive visualizations | ✅ Complete |
| Metrics Dimensions | 15+ computed metrics | ✅ Complete |
| API Endpoints | 3 (advisor chat + health) | ✅ Complete |
| Test Coverage | Syntax validated | ⚠️ Need unit tests |
| Security Compliance | 8/10 | ⚠️ CVEs pending |
| Documentation | CLAUDE.md + README + progress | ✅ Complete |

---

## Come Continuare

### 1. Eseguire una simulazione:
```bash
cd backend/app/finsim
python run_simulation.py
```
Output: `backend/app/finsim/output/risultati_S0.json` (and S1-S4 if configured)

### 2. Arricchire dati simulazione con metriche:
```bash
cd backend/app/finsim/scripts
python migra_json_esistenti.py
```
Output: `backend/app/finsim/output/enriched/risultati_S0.json` (enriched with metrics)

### 3. Avviare Virtual Advisor API:
```bash
cd backend
python -m app.finsim.advisor
```
Endpoint: `http://localhost:8000/api/advisor/chat` (POST con metrics data)
Health: `http://localhost:8000/health` (GET)

### 4. Generare visualizzazioni:
```python
from backend.app.finsim.visualizzatore_grafici import *
import json

# Carica dati arricchiti
with open('backend/app/finsim/output/enriched/risultati_S0.json', 'r') as f:
    scenario_data = json.load(f)

# Genera singolo grafico
fig = genera_heatmap_performance(scenario_data['summary'])
fig.show()

# Oppure tutti i 9 grafici per uno scenario
for round_data in scenario_data['rounds']:
    fig_perf = genera_heatmap_performance(round_data)
    fig_prodotti = genera_bar_prodotti(round_data)
    # ... etc
```

### 5. Interrogare database per metriche:
```python
from backend.app.finsim.search_finsim import FinsimSearcher

searcher = FinsimSearcher(config)
scenario = searcher.get_scenario_state("s0")
directive = searcher.get_directive("s0")
print(f"Scenario: {scenario}")
print(f"Directive: {directive}")
```

### 6. Testare normalizzazione prodotti:
```bash
cd backend/app/finsim/metrics
python normalizzatore.py
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
| 91f5b9f | Add new metrics | 8 |
| 8c6149e | Normalization metrics | 8 |
| 7420dc2 | Adequacy scoring and compliance metrics | 8 |
| a1d8b8c | Add migration script to enrich JSON files | 8 |
| 185f59c | Enhance visualizations and frontend charts | 9 |
| 547191b | Log: 20 round simulation | 9 |
| db0f2b3 | Add frontend for strategic analysis | 9 |
| 86cc9c3 | Implement FINsim Virtual Advisor API | 10 |
| e33bc64 | Implement AI query flow with MongoDB integration | 10 |
| c29f64c | Change model: gemma4:e4b | 10 |
| f59dbdf | Add new visualizations (adequacy & acceptance) | 9 |
| cd21a7a | Refactor decision enrichment process | 8 |

---

**Status Attuale (Giugno 2026):**
- ✅ Fase 8-10: Metrics, visualizations, advisor API complete
- ⏳ Fase 11: Security hardening in progress (CVE remediation)
- 🔮 Fase 12+: Dashboard UI integration, production deployment

**Prossima sessione:** Continue con security audit (Fase 11) e dashboard integration (Fase 12).
