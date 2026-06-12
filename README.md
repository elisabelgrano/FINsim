<div align="center">

<img src="./static/image/mirofish-offline-banner.png" alt="MiroFish Offline" width="100%"/>

# MiroFish-Offline

**Fully local fork of [MiroFish](https://github.com/666ghj/MiroFish) — no cloud APIs required. English UI.**

*A multi-agent swarm intelligence engine that simulates public opinion, market sentiment, and social dynamics. Entirely on your hardware.*

[![GitHub Stars](https://img.shields.io/github/stars/nikmcfly/MiroFish-Offline?style=flat-square&color=DAA520)](https://github.com/nikmcfly/MiroFish-Offline/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/nikmcfly/MiroFish-Offline?style=flat-square)](https://github.com/nikmcfly/MiroFish-Offline/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](./LICENSE)

</div>

## What is this?

MiroFish is a multi-agent simulation engine: upload any document (press release, policy draft, financial report), and it generates hundreds of AI agents with unique personalities that simulate the public reaction on social media. Posts, arguments, opinion shifts — hour by hour.

The [original MiroFish](https://github.com/666ghj/MiroFish) was built for the Chinese market (Chinese UI, Zep Cloud for knowledge graphs, DashScope API). This fork makes it **fully local and fully English**:

| Original MiroFish | MiroFish-Offline |
|---|---|
| Chinese UI | **English UI** (1,000+ strings translated) |
| Zep Cloud (graph memory) | **Neo4j Community Edition 5.15** |
| DashScope / OpenAI API (LLM) | **Ollama** (qwen2.5, llama3, etc.) |
| Zep Cloud embeddings | **nomic-embed-text** via Ollama |
| Cloud API keys required | **Zero cloud dependencies** |

## Workflow

1. **Graph Build** — Extracts entities (people, companies, events) and relationships from your document. Builds a knowledge graph with individual and group memory via Neo4j.
2. **Env Setup** — Generates hundreds of agent personas, each with unique personality, opinion bias, reaction speed, influence level, and memory of past events.
3. **Simulation** — Agents interact on simulated social platforms: posting, replying, arguing, shifting opinions. The system tracks sentiment evolution, topic propagation, and influence dynamics in real time.
4. **Report** — A ReportAgent analyzes the post-simulation environment, interviews a focus group of agents, searches the knowledge graph for evidence, and generates a structured analysis.
5. **Interaction** — Chat with any agent from the simulated world. Ask them why they posted what they posted. Full memory and personality persists.

## Screenshot

<div align="center">
<img src="./static/image/mirofish-offline-screenshot.jpg" alt="MiroFish Offline — English UI" width="100%"/>
</div>

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended), **or**
- Python 3.11+, Node.js 18+, Neo4j 5.15+, Ollama

### Option A: Docker (easiest)

```bash
git clone https://github.com/nikmcfly/MiroFish-Offline.git
cd MiroFish-Offline
cp .env.example .env

# Start all services (Neo4j, Ollama, MiroFish)
docker compose up -d

# Pull the required models into Ollama
docker exec mirofish-ollama ollama pull qwen2.5:32b
docker exec mirofish-ollama ollama pull nomic-embed-text
```

Open `http://localhost:3000` — that's it.

### Option B: Manual

**1. Start Neo4j**

```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/mirofish \
  neo4j:5.15-community
```

**2. Start Ollama & pull models**

```bash
ollama serve &
ollama pull qwen2.5:32b      # LLM (or qwen2.5:14b for less VRAM)
ollama pull nomic-embed-text  # Embeddings (768d)
```

**3. Configure & run backend**

```bash
cp .env.example .env
# Edit .env if your Neo4j/Ollama are on non-default ports

cd backend
pip install -r requirements.txt
python run.py
```

**4. Run frontend**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Configuration

All settings are in `.env` (copy from `.env.example`):

```bash
# LLM — points to local Ollama (OpenAI-compatible API)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:32b

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mirofish

# Embeddings
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

Works with any OpenAI-compatible API — swap Ollama for Claude, GPT, or any other provider by changing `LLM_BASE_URL` and `LLM_API_KEY`.

## Architecture

This fork introduces a clean abstraction layer between the application and the graph database:

```
┌─────────────────────────────────────────┐
│              Flask API                   │
│  graph.py  simulation.py  report.py     │
└──────────────┬──────────────────────────┘
               │ app.extensions['neo4j_storage']
┌──────────────▼──────────────────────────┐
│           Service Layer                  │
│  EntityReader  GraphToolsService         │
│  GraphMemoryUpdater  ReportAgent         │
└──────────────┬──────────────────────────┘
               │ storage: GraphStorage
┌──────────────▼──────────────────────────┐
│         GraphStorage (abstract)          │
│              │                            │
│    ┌─────────▼─────────┐                │
│    │   Neo4jStorage     │                │
│    │  ┌───────────────┐ │                │
│    │  │ EmbeddingService│ ← Ollama       │
│    │  │ NERExtractor   │ ← Ollama LLM   │
│    │  │ SearchService  │ ← Hybrid search │
│    │  └───────────────┘ │                │
│    └───────────────────┘                │
└─────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │  Neo4j CE   │
        │  5.15       │
        └─────────────┘
```

**Key design decisions:**

- `GraphStorage` is an abstract interface — swap Neo4j for any other graph DB by implementing one class
- Dependency injection via Flask `app.extensions` — no global singletons
- Hybrid search: 0.7 × vector similarity + 0.3 × BM25 keyword search
- Synchronous NER/RE extraction via local LLM (replaces Zep's async episodes)
- All original dataclasses and LLM tools (InsightForge, Panorama, Agent Interviews) preserved

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 32 GB |
| VRAM (GPU) | 10 GB (14b model) | 24 GB (32b model) |
| Disk | 20 GB | 50 GB |
| CPU | 4 cores | 8+ cores |

CPU-only mode works but is significantly slower for LLM inference. For lighter setups, use `qwen2.5:14b` or `qwen2.5:7b`.

## Use Cases

- **PR crisis testing** — simulate the public reaction to a press release before publishing
- **Trading signal generation** — feed financial news and observe simulated market sentiment
- **Policy impact analysis** — test draft regulations against simulated public response
- **Creative experiments** — someone fed it a classical Chinese novel with a lost ending; the agents wrote a narratively consistent conclusion

## License

AGPL-3.0 — same as the original MiroFish project. See [LICENSE](./LICENSE).

---

## FINsim — Financial Promotion Simulator (MVP)

FINsim is a specialized fork of MiroFish-Offline designed to simulate financial product promotion scenarios with **A/B testing** across 5 macroeconomic scenarios and 20 consecutive rounds. The system compares adaptive (AI-driven) vs. fixed (benchmark) promotional strategies across 100 synthetic clients using swarm intelligence.

### FINsim Architecture (4-Level Hierarchy)

```
Level 1: ScenarioMacro (1 deterministic node)
         ├─ S0: Baseline Neutral (2.0% rate, geopolitical tension)
         ├─ S1: Rate Shock / Spike (2.5% rate, equity crash)
         ├─ S2: Acute Crisis / Liquidity (3.0% rate, flight to quality)
         ├─ S3: Opportunity / Regulatory Pressure (1.8% rate, compliance boost)
         └─ S4: Dynamic Bifurcation (S0 until R10, then pivot)

Level 2: DirettivaBancaria (1 adaptive agent, HEAVY_LLM: qwen2.5:32b)
         └─ Generates bank policy & product focus per round

Level 3: Promotori (N agents in parallel)
         ├─ 50 clients → Fixed Strategy (benchmark broadcast)
         └─ 50 clients → Adaptive Strategy (LLM-driven, LIGHT_LLM: qwen2.5:3b)

Level 4: Clienti (100 synthetic agents, LIGHT_LLM batch processing)
         └─ React to promoter strategies, update trust & satisfaction
```

### Quick Start — FINsim

#### Prerequisites

- **Neo4j 5.15+** (running, bolt://localhost:7687)
- **Ollama** with models pre-pulled:
  ```bash
  ollama pull qwen2.5:32b    # Bank Directive generation (HEAVY_LLM)
  ollama pull qwen2.5:3b     # Promoter & Client strategies (LIGHT_LLM)
  ```
- **Python 3.11+**

#### 1. Wipe and Populate the Database

Clean the Neo4j database and populate with FINsim schema, scenarios, and 100 synthetic clients:

```bash
cd backend/app/finsim/ontology
python schema_runner.py wipe    # Delete all nodes/relationships
python populate_finsim.py       # Create S0-S4 scenarios, bank directives, promoters, 100 clients
```

**What happens:**
- Creates 5 `ScenarioMacro` nodes (S0–S4) with macroeconomic parameters
- Creates 1 `DirettivaBancaria` node (bank policy per scenario)
- Creates 2 `Promotore` nodes: Fixed (ID=1) and Adaptive (ID=2)
- Creates 100 `Cliente` nodes arranged in a 10×10 grid with diverse trust profiles
- Initializes client satisfaction, risk tolerance, and decision history

#### 2. Run the Simulation

Execute all 5 scenarios with 1 round each (or customize in code):

```bash
cd backend/app/finsim
python run_simulation.py
```

**What happens:**
1. For each scenario (S0–S4):
   - **Reset** client trust to initial values and clear previous decisions
   - **Run** 1 round (configurable: change `num_rounds=1` to `num_rounds=20` for full 20-round cycles)
   - **Export** scenario results to `output/risultati_SX.json`
2. Each round:
   - Queries Neo4j for active client clusters per promoter
   - Generates adaptive strategy via PromotoreAgent (LLM)
   - Executes fixed benchmark strategy in parallel (50/50 A/B split)
   - Calculates client reactions based on product–risk congruence
   - Persists decisions to DB as `DecisioneCommerciale` nodes
   - Updates client trust and satisfaction metrics

#### 3. Caching & Skip Logic

The simulation implements a **file-based cache** to avoid re-running completed scenarios:

- **Cache files location:** `backend/app/finsim/output/risultati_SX.json`
- **Skip behavior:** If `risultati_S0.json` exists, scenario S0 is skipped with a log message
- **Force recalculation:** Delete the JSON file(s) to force a re-run:
  ```bash
  rm backend/app/finsim/output/risultati_*.json
  python run_simulation.py
  ```

### Output Structure

After a complete run, the `output/` directory contains:

```
backend/app/finsim/output/
├─ risultati_S0.json      # Baseline scenario: rounds, decisions, trust metrics
├─ risultati_S1.json      # Rate shock scenario
├─ risultati_S2.json      # Acute crisis scenario
├─ risultati_S3.json      # Opportunity scenario
└─ risultati_S4.json      # Bifurcation scenario
```

**Each JSON structure:**
```json
{
  "scenario_id": "S0",
  "timestamp": "2026-06-05T14:23:45.123456",
  "rounds": [
    {
      "round": 1,
      "decisions_count": 100,
      "decisions": [
        {
          "promotore": "P1_Fisso",
          "cluster": "(0, 0)",
          "strategia": "Cautious Income",
          "approccio_comunicativo": "Risk-aware education",
          "prodotto_suggerito": "Government Bonds"
        },
        ...
      ]
    }
  ],
  "summary": {
    "total_rounds": 1,
    "total_decisions": 100,
    "total_clients_updated": 100,
    "total_errors": 0
  }
}
```

### FINsim Code Structure

```
backend/app/finsim/
├─ run_simulation.py              # Entry point: orchestrates scenario cycles & caching
├─ simulation_engine.py           # Core loop: round execution, state management
├─ search_finsim.py              # Secure Neo4j queries (parameterized, allowlist validation)
├─ agents/
│  └─ promotore_agent.py          # Promoter strategy generation (LLM)
├─ llm/
│  └─ ollama_client.py            # Ollama REST client with retry & timeout
└─ ontology/
   ├─ populate_finsim.py          # Scenario & client population
   ├─ schema_runner.py            # Schema wipe command
   ├─ ontology_loader.py          # Neo4j node/relationship loader
   ├─ finsim_schema.json          # Allowed labels & relationships (security allowlist)
   └─ test_populate.py            # Integration tests
```

### Configuration (`.env`)

FINsim uses the same `.env` as MiroFish-Offline. Key settings:

```bash
# Ollama (local models)
EMBEDDING_BASE_URL=http://localhost:11434
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:32b

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mirofish
```

### Security Rules (FINsim-Specific)

**Critical Neo4j Security:**
- ✅ All queries use **parameterized driver calls** — never f-strings
- ✅ Labels & relationships validated against `finsim_schema.json` allowlist before execution
- ⚠️ Known CVE-2026-7059: path traversal in simulation.py (Platform param) — fixed in Phase 7
- ⚠️ Known CVE-2026-7058: command injection in services/send_command — fixed in Phase 7

**Untouchable Files:**
- `backend/app/config.py` — central configuration
- `backend/app/storage/neo4j_storage.py` — Neo4j interface
- `docker-compose.yml` — container orchestration

### Advanced Metrics & Analytics

FINsim now includes comprehensive metrics calculation and enrichment:

#### Computed Metrics

- **Adequacy Scores** — Product-risk alignment assessment (0.0–1.0) based on client risk profile
- **Directive Compliance** — Whether recommended product matches scenario focus product
- **Acceptance Rate** — Percentage of products accepted by clients (>= 0.5 adequacy threshold)
- **Mismatch Rate** — Percentage of product recommendations rejected by clients
- **Compliance Per Promoter** — Directive adherence rate by Adaptive vs Fixed strategies
- **Product Distribution** — Normalized product categories (Bond_Corporate, Bond_Sovereign, Cash_Equivalents, Mixed_Funds, Altro)
- **Strategic Matrix** — Cross-tabulation of risk profiles × products with performance metrics

#### Data Enrichment Pipeline

Run the migration script to enrich existing simulation JSON files with computed metrics:

```bash
cd backend/app/finsim/scripts
python migra_json_esistenti.py
```

**What happens:**
- Reads raw decision data from `backend/app/finsim/output/risultati_SX.json`
- Normalizes product names using intelligent heuristics
- Computes adequacy scores from risk-product compatibility matrix
- Calculates directive compliance and acceptance rates per round
- Generates strategic matrix (profilo × prodotto combinations)
- Outputs enriched data to `backend/app/finsim/output/enriched/risultati_SX.json`

### Frontend Visualizations

FINsim includes 9 interactive Plotly-based visualizations:

#### 1. **HEATMAP_PERFORMANCE** — Strategic Advantage Map
- **What:** Risk level (Y-axis) × Wealth level (X-axis) performance grid
- **Interpretation:** Green = Adaptive wins, Red = Fixed wins, Yellow = Tie
- **Use case:** Identify which client segments respond better to adaptive strategies

#### 2. **BAR_PRODOTTI** — Product Satisfaction Distribution  
- **What:** Satisfaction levels across recommended financial products
- **Interpretation:** Taller bars = higher client satisfaction with that product
- **Use case:** Product portfolio optimization per scenario

#### 3. **LINEE_COMPARATIVE** — Cumulative AUM Evolution
- **What:** Comparative line chart of Total Collected Assets (round 1-20)
- **Interpretation:** Adaptive (blue) vs Fixed (red) trajectory over time
- **Use case:** Long-term strategy effectiveness assessment

#### 4. **WATERFALL_PATRIMONIO** — Wealth Composition Breakdown
- **What:** Stacked waterfall from Initial AUM → Inflows → Outflows → Final AUM
- **Interpretation:** Visual decomposition of wealth changes per round
- **Use case:** Identify sources of growth or attrition

#### 5. **SANKEY_FLUSSI** — Client Flow Dynamics
- **What:** Client migrations between risk clusters and churn destinations
- **Interpretation:** Flow thickness = volume of clients; colors = direction
- **Use case:** Detect client exodus patterns and retention risk zones

#### 6. **AREA_GUADAGNI** — Revenue Generation Over Time
- **What:** Stacked area chart of cumulative earnings (round 1-20)
- **Interpretation:** Height = total revenue; colored bands = revenue by segment
- **Use case:** Profitability trend analysis and commission forecasting

#### 7. **SEMAFORO_ADEGUATEZZA** — Adequacy Traffic Light System
- **What:** Color-coded grid (Green=Adequate ≥0.5, Yellow=Borderline 0.3-0.5, Red=Mismatch <0.3)
- **Interpretation:** Bright cells = good matches; dark cells = product-risk conflicts
- **Use case:** Compliance monitoring and product suitability audits

#### 8. **ACCETTAZIONI_PER_SCENARIO** — Scenario Comparison Acceptance Rates
- **What:** Side-by-side comparison of acceptance rates across S0-S4
- **Interpretation:** Taller bars = better scenario performance
- **Use case:** Macro scenario impact analysis

#### 9. **TREND_COMPLIANCE** — Directive Adherence Trends
- **What:** Line chart of compliance rate per round (Adaptive vs Fixed)
- **Interpretation:** Higher line = better regulatory alignment
- **Use case:** Regulatory risk assessment and strategy audit

### Virtual Advisor API

FINsim includes an **on-demand Virtual Advisor** service powered by Ollama (gemma4:e4b):

```bash
python -m backend.app.finsim.advisor
```

**Endpoints:**

- `POST /api/advisor/chat` — Get tactical advice based on financial metrics
  - Input: metrics data + optional user question
  - Output: Structured response with strategic recommendation + suggested visualizations
  
- `GET /health` — Service health check

**Features:**
- Autonomous chart selection (chooses relevant visualizations based on query)
- Strategic context injection (scenario, directive, portfolio analysis)
- Detailed captions with visual interpretation guides
- Italian language output
- Fallback mechanisms for robustness

### Next Steps

- **Phase 9:** Dashboard UI integration for interactive metric exploration
- **Phase 10:** Real-time metrics computation during simulation runs
- **Phase 11:** Export capabilities (PDF reports, CSV downloads, API integrations)
- **Phase 12:** Deploy to production with monitoring

---

## Credits & Attribution

This is a modified fork of [MiroFish](https://github.com/666ghj/MiroFish) by [666ghj](https://github.com/666ghj), originally supported by [Shanda Group](https://www.shanda.com/). The simulation engine is powered by [OASIS](https://github.com/camel-ai/oasis) from the CAMEL-AI team.

**Modifications in this fork:**
- Backend migrated from Zep Cloud to local Neo4j CE 5.15 + Ollama
- Entire frontend translated from Chinese to English (20 files, 1,000+ strings)
- All Zep references replaced with Neo4j across the UI
- Rebranded to MiroFish Offline
- **FINsim module added:** Financial promotion simulator with A/B testing, 5 scenarios, 20-round progression
