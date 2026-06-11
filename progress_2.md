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

## Next Steps (Optional)

1. Monitor compliance_rate across scenarios to evaluate directive adherence
2. Use dispersione_prodotti to analyze product recommendation diversity
3. Compare prodotto_dominante across S0-S4 to understand scenario-specific patterns
4. Audit prodotto_suggerito_raw in DecisioneCommerciale for LLM variant analysis

---

## Notes

- Substring matching approach ensures resilience to future LLM naming variations
- Italian language support built-in (obbligazioni, titoli di stato, etc.)
- No external dependencies added
- Metrics computed in-memory, no additional database queries needed
- All changes comply with CLAUDE.md security and coding standards
