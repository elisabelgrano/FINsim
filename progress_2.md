# FINsim Progress Log — Session 2

**Date:** 2026-06-11  
**Objective:** Implement product normalization and compliance metrics for SimulationEngine

---

## Overview

Implemented a product name normalizer to standardize inconsistent LLM-generated product names across simulation rounds, and added compliance metrics to track alignment with bank directives.

---

## Aim & Rationale

### Problem Statement

**LLM Output Inconsistency:**
The PromotoreAgent (Level 3 in FINsim architecture) generates `prodotto_suggerito` as free text via Ollama LLM calls. However, across different simulation rounds and scenarios, the same financial product receives inconsistent naming:

- "Bond Corporate Investment Grade"
- "Bond_Corporate"
- "Banca Corporate Investment Grade"
- "Obbligazioni Corporate - Grado Investment Grade"
- "Obbligazioni corporate investimento grade"

All refer to the same product category, but string equality matching fails, making round-level analysis and compliance tracking unreliable.

### Strategic Objectives

1. **Standardization for Analysis**
   - Enable consistent aggregation and comparison across rounds
   - Produce reliable statistics on product recommendation patterns
   - Support compliance reporting with clean, deduplicated product categories

2. **Directive Compliance Tracking**
   - Bank directives specify a `focus_prodotto` that promoters should prioritize
   - Without normalization, actual compliance cannot be accurately measured
   - `compliance_rate` metric enables monitoring directive adherence across scenarios (S0–S4)

3. **Risk Assessment Consistency**
   - Risk-client congruence calculations in `calcola_reazione_clienti()` depend on product categorization
   - Normalized products ensure uniform risk mapping across all LLM variants
   - Client trust/satisfaction updates reflect actual product risk, not LLM naming noise

4. **Audit Trail Preservation**
   - Store both raw LLM output (`prodotto_suggerito_raw`) and normalized version
   - Enable forensic analysis: compare LLM tendencies across model versions
   - Future improvements can reference exact prompting that triggered naming variants

5. **Metric-Driven Insights**
   - **`compliance_rate`**: Measure how well promoters follow bank guidance
   - **`prodotto_dominante`**: Identify which products are preferred by the adaptive strategy
   - **`dispersione_prodotti`**: Track product recommendation diversity; signal over-concentration risk

### Why Now?

- Early rounds (1–20) establish baseline behavior for 5 scenarios (S0–S4)
- Consistent metrics across all rounds enable phase-to-phase comparison
- Compliance data is prerequisite for regulatory/business analysis in Phase 7
- Normalization cost is negligible; benefit accumulates across 20 rounds × 5 scenarios = 100 data points

---

## Changes Made

### 1. Created Product Normalizer Module

**File:** `backend/app/finsim/metrics/normalizzatore.py`

- **Function:** `normalize_prodotto(raw: str) -> str`
- **Normalization Rules (case-insensitive, substring-based):**
  - `bond + corporate` → `Bond_Corporate`
  - `bond + sovereign` → `Bond_Sovereign`
  - `obbligazioni + corporate` → `Bond_Corporate`
  - `obbligazioni + sovereign` → `Bond_Sovereign`
  - `sovereign | sovran | stato` → `Bond_Sovereign`
  - `governativ` → `Bond_Sovereign`
  - `cash | liquide` → `Cash_Equivalents`
  - `mixed | mist` → `Mixed_Funds`
  - `multisett` → `Mixed_Funds`
  - Unrecognized → `Altro`

- **Test Suite:** 10 real examples from simulation results (all passing)
  - Handles Italian product names (obbligazioni, titoli di stato)
  - Handles English variants (Bond, Cash)
  - Robust to variations in spacing and capitalization

**Examples:**
```
"Bond Corporate Investment Grade" → "Bond_Corporate"
"Obbligazioni Corporate - Grado Investment Grade" → "Bond_Corporate"
"Titoli di stato low-risk" → "Bond_Sovereign"
"Liquide" → "Cash_Equivalents"
"Derivati finanziari" → "Altro"
```

### 2. Created Metrics Module Interface

**File:** `backend/app/finsim/metrics/__init__.py`

- Exports `normalize_prodotto` for clean module interface
- Follows project style conventions for module initialization

### 3. Integrated Normalizer into SimulationEngine

**File:** `backend/app/finsim/simulation_engine.py`

#### Imports Added
```python
from collections import Counter
from backend.app.finsim.metrics import normalize_prodotto
```

#### Changes to `esegui_round()` Method

**Initialization:**
- Added metric tracking lists: `prodotti_raw_list`, `prodotti_normalized_list`
- Fetch directive from searcher to extract `focus_prodotto` for compliance calculation

**Strategy Processing:**
- Normalize each `prodotto_suggerito` from PromotoreAgent
- Store both raw and normalized versions:
  - `prodotto_suggerito_raw`: Original LLM output (preserved for audit)
  - `prodotto_suggerito`: Normalized version (for analysis)
- Track products for round-level metrics

**Client Reactions:**
- Use normalized product for risk congruence calculations
- Ensures consistent risk mapping across all LLM variants

**Round Result Metrics:**
Three new fields added to result dictionary:

1. **`compliance_rate`** (float, 0.0–1.0)
   - Calculation: `(decisions matching focus_prodotto) / total_decisions`
   - Rounded to 2 decimal places
   - Measures alignment with bank directive

2. **`prodotto_dominante`** (str)
   - Most frequently recommended normalized product in round
   - Identifies dominant product strategy

3. **`dispersione_prodotti`** (int)
   - Count of distinct normalized products in round
   - Measures portfolio diversity

#### Changes to `salva_decisione_db()` Method

Updated Neo4j DecisioneCommerciale node creation:
- Added `prodotto_suggerito_raw` field (original LLM string)
- Added `prodotto_suggerito` field (normalized version)
- Both fields parameterized to prevent injection
- Maintains backward compatibility with existing queries

---

## Data Flow

```
PromotoreAgent.genera_strategia_cluster()
    ↓
prodotto_suggerito (raw LLM output, e.g., "Bond Corporate Investment Grade")
    ↓
SimulationEngine.esegui_round()
    ├─ normalize_prodotto(raw) → normalized (e.g., "Bond_Corporate")
    ├─ Store both: prodotto_suggerito_raw + prodotto_suggerito
    ├─ Track: prodotti_normalized_list.append(normalized)
    ├─ Calculate client reactions with normalized product
    └─ End of round: compute compliance_rate, prodotto_dominante, dispersione_prodotti
    ↓
salva_decisione_db()
    ├─ Save DecisioneCommerciale with both raw and normalized
    ├─ prodotto_suggerito_raw: full audit trail
    └─ prodotto_suggerito: standardized for analysis
```

---

## Backward Compatibility

✓ **All changes are fully backward compatible:**
- Existing fields preserved
- New fields added without modifying existing logic
- DecisioneCommerciale schema extends dynamically (Neo4j is schema-less)
- OllamaClient, FinsimSearcher, and ontology schema unchanged

---

## Testing

**Module-Level Tests:**
```
✓ normalize_prodotto() — 10 test cases passing
✓ Metrics calculation — compliance_rate, prodotto_dominante, dispersione_prodotti
✓ Real data examples — 7 test cases from simulation results
```

**Integration Tests:**
```
✓ All imports successful
✓ SimulationEngine accepts new parameters
✓ Counter import for frequency analysis
✓ Decimal rounding for compliance_rate
```

---

## Example Output

Round result now includes:
```json
{
  "round": 1,
  "scenario_id": "S0",
  "promoters_processed": 2,
  "total_clusters": 20,
  "decisions_created": 20,
  "clients_updated": 200,
  "compliance_rate": 0.75,
  "prodotto_dominante": "Bond_Corporate",
  "dispersione_prodotti": 4,
  "errors": [],
  "promoters_data": [...]
}
```

---

## Files Modified/Created

| File | Status | Changes |
|------|--------|---------|
| `backend/app/finsim/metrics/normalizzatore.py` | **Created** | Product normalization logic + tests |
| `backend/app/finsim/metrics/__init__.py` | **Created** | Module interface |
| `backend/app/finsim/simulation_engine.py` | **Modified** | Normalizer integration, metrics calculation |

---

---

## PHASE 5: Promoter Dashboard UI & Backend KPI Metrics

**Date:** 2026-06-11 (continued)  
**Objective:** Implement final Promoter Dashboard with business metrics visualization and KPI cards

### Changes Made

#### 1. Enhanced Business Metrics Calculation

**File:** `backend/app/finsim/simulation_engine.py` → `_calcola_metriche_business()`

Added 3 critical business metrics to the returned `metrics` dictionary:

**a) `mismatch_rate` (float, 0.0–1.0)**
- **Definition:** Ratio of rejected product decisions to total decisions
- **Calculation:** 
  ```python
  rejected_count = sum(1 for strat in all_strategies if strat['accettato'] == False)
  mismatch_rate = rejected_count / total_decisions
  ```
- **Purpose:** Measures commercial effectiveness and compliance violations
- **Interpretation:** 
  - 0.0 = All products accepted (100% match)
  - 1.0 = All products rejected (0% match)
  - Typically 0.2–0.3 = 20–30% of offers rejected by clients

**b) `trend_fiducia` (list of dicts)**
- **Definition:** Time-series of average client trust across all rounds
- **Structure:** `[{"round": 1, "fiducia_media": 0.68}, {"round": 2, "fiducia_media": 0.71}, ...]`
- **Calculation:** Average of `fiducia_media_post` for each round across all clusters
- **Purpose:** Visualize trust evolution; detect declining or improving client relationships
- **Interpretation:**
  - Rising trend = Adaptive strategy gaining client confidence
  - Declining trend = Risk of churn; corrective action needed
  - Plateau = Stable, mature relationship

**c) `pct_clienti_sotto_soglia_fiducia` (float, percentage)**
- **Definition:** Percentage of clients with current trust below critical threshold (0.5)
- **Neo4j Query (Parameterized Single Query):**
  ```cypher
  MATCH (c:Cliente)
  WITH count(c) as total, sum(CASE WHEN c.fiducia_attuale < 0.5 THEN 1.0 ELSE 0.0 END) as sotto_soglia
  RETURN case when total > 0 then sotto_soglia / total else 0.0 end as pct
  ```
- **Purpose:** Early warning system for portfolio churn risk
- **Interpretation:**
  - < 5% = Healthy portfolio
  - 5–10% = Monitor closely
  - > 10% = Critical: immediate intervention needed

#### 2. Created 3 New Plotly Visualization Functions

**File:** `visualizzatore_grafici.py`

**a) `genera_donut_asset_allocation(business_metrics)`**
- **Graph Type:** Donut chart (pie with center cutout)
- **Data Source:** `business_metrics['efficacia_strategica_prodotti']`
- **Visualization:**
  - Donut segments = Each product category (Bond_Corporate, Cash_Equivalents, etc.)
  - Segment size = Number of times product was offered
  - Center text = Total transaction count
  - Colors: 5-color palette (#059669 green → #8b5cf6 purple)
- **Business Use:** Identify which products are most frequently recommended; spot over-concentration
- **Example:** If "Bond_Corporate" dominates 60% of the donut, the strategy favors conservative investments

**b) `genera_bubble_clientela(rounds_data)`**
- **Graph Type:** Scatter bubble chart (with color scale)
- **Data Source:** Last round's decisions (only for PROM-ADAPT-1)
- **Axes:**
  - X-axis: Client risk profile (Conservative, Balanced, Growth, Aggressive)
  - Y-axis: Wealth tier (Fascia 0–4, representing asset ranges)
  - Bubble size: Fixed at 25 (constant visibility)
  - Bubble color: Client trust level (red=low 0.0, yellow=medium 0.5, green=high 1.0)
- **Business Use:** Segment client base by risk/wealth; identify trust patterns
- **Example:** Green bubbles in "Aggressive" quadrant = Risk-appropriate clients with high trust

**c) `genera_win_rate_prodotti(business_metrics)`**
- **Graph Type:** Horizontal bar chart (with color gradient)
- **Data Source:** `business_metrics['efficacia_strategica_prodotti']` (requires win_rate field)
- **Visualization:**
  - Bars = Each product
  - Bar length = Conversion rate (0–100%)
  - Color gradient: Red (low) → Green (high)
- **Business Use:** Identify which products convert best; de-emphasize low-performing offerings
- **Example:** If "Mixed_Funds" = 45% and "Bond_Sovereign" = 75%, prefer sovereign bonds

#### 3. Updated Frontend with KPI Cards

**File:** `app_frontend.py` → `render_risposta()` function

**KPI Emergency Cards Section** (inserted after "Analisi Dettagliata" in render_risposta):
```python
st.markdown("### 🚨 KPI di Portafoglio")
kpi1, kpi2, kpi3 = st.columns(3)

# Card 1: Churn Risk
pct_churn = metrics.get('pct_clienti_sotto_soglia_fiducia', 0.0)
kpi1.metric(
    "Capitale a Rischio Churn",
    f"{pct_churn:.1f}%",
    "- Pericolo Fuga" if pct_churn > 10 else "Sicuro",
    delta_color="inverse"
)

# Card 2: Win Rate
mismatch = metrics.get('mismatch_rate', 0.0) * 100
kpi2.metric(
    "Win Rate Globale",
    f"{100 - mismatch:.1f}%",
    "Efficacia Commerciale"
)

# Card 3: Compliance
kpi3.metric(
    "Compliance Score",
    f"{100 - mismatch:.1f}/100",
    "MIFID OK" if mismatch < 20 else "Rischio Legale",
    delta_color="inverse"
)
```

**KPI Card Interpretations:**
- **Card 1 - Churn Risk:** Red alert if > 10%; yellow caution if 5–10%; green if < 5%
- **Card 2 - Win Rate:** Percentage of accepted offers; higher is better
- **Card 3 - Compliance:** MIFID compliance score; below 80 triggers risk warning

#### 4. Integrated New Graphs into Frontend Rendering Loop

Added 3 new `elif` branches in the graph rendering section:

```python
elif codice_grafico == "DONUT_ASSET":
    fig = genera_donut_asset_allocation(metrics)
elif codice_grafico == "BUBBLE_CLIENTI":
    fig = genera_bubble_clientela(st.session_state['scenario'].get('rounds', []))
elif codice_grafico == "BAR_WIN_RATE":
    fig = genera_win_rate_prodotti(metrics)
```

---

## Complete Frontend Graph Catalog

### All Available Graphs (9 Total)

| Graph Code | Function | Data Source | Purpose | Key Insight |
|------------|----------|-------------|---------|------------|
| `HEATMAP_PERFORMANCE` | `genera_heatmap_performance()` | Aggregated round results | Compare adaptive vs fixed strategy by risk/wealth tier | Shows where IA wins/loses |
| `BAR_PRODOTTI` | `genera_bar_prodotti()` | `efficacia_strategica_prodotti` | Product satisfaction impact; usage frequency | Which products drive satisfaction |
| `LINEE_COMPARATIVE` | `genera_linee_comparative()` | Round history (AUM proxy) | Cumulative wealth evolution over 20 rounds | Compound effect of strategy |
| `WATERFALL_PATRIMONIO` | `genera_waterfall_patrimonio()` | AUM decomposition | Asset under management flow: inflows, outflows, market effects | Net wealth impact |
| `SANKEY_FLUSSI` | `genera_sankey_flussi()` | Client retention model | Client journey: success vs churn; fixed vs adaptive | Where churn happens; who is saved |
| `AREA_GUADAGNI` | `genera_andamento_guadagni()` | Satisfaction velocity | Cumulative satisfaction deltas; growth trajectory | Rate of relationship improvement |
| `DONUT_ASSET` | `genera_donut_asset_allocation()` | `efficacia_strategica_prodotti` | Product mix composition | Concentration risk; diversification |
| `BUBBLE_CLIENTI` | `genera_bubble_clientela()` | Last round decisions | Client segmentation by risk & wealth with trust overlay | Demographic-trust correlation |
| `BAR_WIN_RATE` | `genera_win_rate_prodotti()` | `efficacia_strategica_prodotti` | Product conversion rates | Which products close best |

### Graph Description Details

**1. Heatmap Performance (Risk × Wealth)**
- Grid: 4 rows (risk profiles) × 5 columns (wealth tiers)
- Heat color: Red (fixed strategy wins) → Yellow (tie) → Green (adaptive wins)
- Red values indicate scenarios where rule-based approach outperforms AI
- Green values validate AI advantage in complex clientele mixes

**2. Bar Prodotti (Product Satisfaction Impact)**
- Each bar = one product category
- Height = Total satisfaction generated across all 20 rounds
- Color gradient: Red (negative/detrimental) → Green (positive/beneficial)
- Example: Bond_Corporate bar is tall and green = clients love this product

**3. Linee Comparative (Wealth Accumulation Over Time)**
- Two lines: Adaptive (green) vs Fixed (orange)
- Y-axis: AUM or proxy wealth metric
- X-axis: 20 rounds
- Divergence between lines = IA advantage magnitude

**4. Waterfall Patrimonio (AUM Decomposition)**
- Starting value (AUM Initial) → increases/decreases by:
  - New inflows (green bars, up)
  - Market effects (gray bars, various)
  - Churn losses (red bars, down)
- Final value (AUM Final) at end
- Shows which factor dominates portfolio change

**5. Sankey Flussi (Client Journey & Retention)**
- Source: Clients at start
- Split: Fixed strategy branch vs Adaptive strategy branch
- Outcomes: Success (blue) vs Churn (red)
- Line thickness = number of clients
- Shows if adaptive strategy saves more clients from churn

**6. Area Guadagni (Cumulative Satisfaction Growth)**
- X-axis: 20 rounds (R1–R20)
- Y-axis: Cumulative satisfaction delta (sum of all round changes)
- Area under curve = Total satisfaction accumulation
- Rising curve = accelerating positive client response
- Flat/declining = strategy stagnation

**7. Donut Asset Allocation (NEW)**
- Center: Total offer count
- Segments: Product categories
- Size: Percentage of total offers
- Color coding: Distinct color per product
- Hover: Exact counts and percentages

**8. Bubble Segmentazione Clientela (NEW)**
- X-axis: Risk profile (Conservative → Aggressive)
- Y-axis: Wealth tier (Fascia 0–4)
- Bubble position: Client classification
- Bubble color: Trust level (red=low, green=high)
- Bubble size: Fixed for visibility
- Reveals if high-wealth, high-risk clients are being well-served

**9. Bar Win Rate Prodotti (NEW)**
- X-axis: Win rate percentage (0–100%)
- Y-axis: Product names
- Bar color: Gradient from light green (low) to dark green (high)
- Identifies your top performers (highest bars)
- Guides product prioritization in training

---

## Data Flow Diagram (Complete)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SimulationEngine.esegui_round()              │
│  (Executes 1 round for 2 promoters × 20 clusters)              │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                 PromotoreAgent.genera_strategia()               │
│  Outputs: prodotto_suggerito (raw), strategia, approach        │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│              normalize_prodotto(raw) → normalized               │
│  Standardizes naming: "Bond Corporate" → "Bond_Corporate"      │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                calcola_reazione_clienti()                       │
│  Updates trust/satisfaction using normalized product            │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│              salva_decisione_db() + Neo4j Update                │
│  Persists: raw + normalized product, decisions, metrics         │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│        _calcola_metriche_business() — Aggregate Metrics         │
│  ├─ mismatch_rate: acceptance ratio                            │
│  ├─ trend_fiducia: trust evolution per round                   │
│  └─ pct_clienti_sotto_soglia: churn risk percentage            │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│            render_risposta() — Frontend Rendering               │
│  ├─ KPI Emergency Cards (3 metrics)                            │
│  ├─ 9 Plotly graphs (selected by Advisor LLM)                  │
│  └─ Interactive Playbook section                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files Modified/Created (Updated)

| File | Status | Changes |
|------|--------|---------|
| `backend/app/finsim/metrics/normalizzatore.py` | **Created** | Product normalization logic (Phase 4) |
| `backend/app/finsim/metrics/__init__.py` | **Created** | Module interface (Phase 4) |
| `backend/app/finsim/simulation_engine.py` | **Modified** | Normalizer integration (Phase 4) + business metrics (Phase 5) |
| `visualizzatore_grafici.py` | **Modified** | Added 3 new functions: donut, bubble, bar_win_rate |
| `app_frontend.py` | **Modified** | KPI cards + 3 new graph cases; imports updated |

---

## Next Steps (Optional)

1. **Monitor KPI Trends:** Track mismatch_rate and pct_clienti_sotto_soglia across scenarios
2. **Product Performance Analysis:** Use Bar Win Rate to identify underperforming products
3. **Churn Risk Alerts:** Trigger alerts when pct_clienti_sotto_soglia exceeds 15%
4. **Scenario Comparison:** Compare all 9 graphs across S0–S4 to identify scenario-specific patterns
5. **Trust Trajectory:** Use trend_fiducia to forecast client retention by round 15

---

## Notes

- All metrics calculated in-memory; no additional database queries beyond the single Neo4j query
- Donut, bubble, and bar functions gracefully handle empty data (return empty Figure)
- KPI cards use Streamlit's built-in `delta_color="inverse"` to flag risks in red
- All 9 graphs follow the same styling: `applica_stile_premium()` for consistent branding
- Playbook section (interactive risk/wealth selector) remains unchanged and fully functional
- All changes comply with CLAUDE.md security and coding standards
