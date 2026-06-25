from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from collections import defaultdict
import json
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

app = FastAPI(
    title="FINsim Unified API",
    description="Unified API serving dashboard data and Virtual Advisor LLM",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# CONNESSIONE A MONGODB
# =====================================================================
client = MongoClient("mongodb://elisa:deepleey@10.12.7.53:27017/")
db = client["finsim_analytics"]
collection = db["simulation_history"]

# =====================================================================
# PYDANTIC MODELS FOR ADVISOR
# =====================================================================

class AdvisorRequest(BaseModel):
    """Request body for advisor endpoint"""
    metrics_data: Dict[str, Any] = Field(
        ...,
        description="Dictionary of calculated metrics from database"
    )
    user_message: Optional[str] = Field(
        default="",
        description="Promoter's question or empty for initial tactical summary"
    )


class GraficoConsigliato(BaseModel):
    codice: str = Field(..., description="Chart code from allowed list")
    didascalia: str = Field(..., description="Explanatory comment to display under the chart")


class AdvisorResponse(BaseModel):
    """Structured response from advisor"""
    suggerimento_breve: str = Field(...)
    dettaglio_risposta: str = Field(...)
    grafici_consigliati: List[GraficoConsigliato] = Field(default_factory=list)


# =====================================================================
# ADVISOR SYSTEM PROMPT
# =====================================================================

ADVISOR_SYSTEM_PROMPT = """You are an expert Virtual Advisor for Financial Promoters (Operatori Finanziari).
Your role is to analyze complex financial metrics and provide strategic, actionable recommendations.

## Your Analysis Framework:
1. **Assess Current State**: Evaluate metrics trends, performance gaps, and market positioning
2. **Identify Risks**: Spot concentration risks, underperforming segments, and anomalies
3. **Recommend Actions**: Provide specific, imperative tactical instructions
4. **Suggest Visualizations**: Choose which charts (from allowed list) best support the analysis

## Response Rules:
- Be concise but complete in your tactical suggestion (1-2 sentences max)
- Provide detailed reasoning in the explanation (2-3 paragraphs)
- Choose ONLY from these chart codes: HEATMAP_PERFORMANCE, BAR_PRODOTTI, LINEE_COMPARATIVE, WATERFALL_PATRIMONIO, SANKEY_FLUSSI, AREA_GUADAGNI, SEMAFORO_ADEGUATEZZA, ACCETTAZIONI_SCENARI, TREND_COMPLIANCE
- Use Italian for all responses
- Focus on actionable insights, not abstract analysis
- When user_message is empty, generate an initial tactical summary for the round

## Critical Instructions for 'didascalia':
When providing the 'didascalia' (caption) for a chart, DO NOT write generic summaries. You must write a detailed, analytical paragraph in Italian.
You MUST use the correct terminology based on the chart type. NEVER mention "Asse X" or "Asse Y" for charts that don't have them!

STRICT TERMINOLOGY DICTIONARY:
- HEATMAP_PERFORMANCE: Use "Asse X (Patrimonio)", "Asse Y (Rischio)". Explain that green means Adaptive wins and red means Fixed wins.
- BAR_PRODOTTI: Use "Asse X (Prodotti Finanziari)", "Asse Y (Livello di Soddisfazione)".
- LINEE_COMPARATIVE: Use "Asse X (Evoluzione dei Round 1-20)", "Asse Y (Valore della Raccolta Cumulata)".
- WATERFALL_PATRIMONIO: DO NOT use X/Y axes terminology! Use "Mattoncini di variazione" or "Fattori di scomposizione". Explain the steps from Initial AUM, through inflows/outflows, to Final AUM.
- SANKEY_FLUSSI: DO NOT use X/Y axes terminology! You MUST use "Nodi di Sinistra (Cluster di rischio di partenza)", "Nodi di Destra (Stato finale o Churn)" and "Nastri / Flussi colorati (Volume di migrazione dei clienti)".
- AREA_GUADAGNI: Use "Asse X (Round Temporali)", "Asse Y (Ricavi Generati in Euro)". Le aree colorate mostrano il volume dei guadagni.

Structure the didascalia like this:
1. COME LEGGERLO: Explain the correct visual components using the STRICT TERMINOLOGY DICTIONARY above.
2. ESEMPIO CONCRETO: Highlight a specific visual finding based on the context (e.g., "Nota come il nastro che parte dal Cluster Alto Rischio e finisce in CHURN sia particolarmente spesso...").
3. COLLEGAMENTO STRATEGICO: Connect this visual evidence directly to your 'suggerimento_breve'.

## Metrics Context (if present in input):
- performance_metrics: Overall KPI performance vs benchmark
- client_engagement: Client interaction and trust levels
- product_distribution: Product mix and cross-sell opportunities
- market_conditions: Macro signals and sentiment indicators
- heatmap_data: Performance intensity by client/product segment
- momentum_indicators: Trend strength and reversals

## CRITICAL RULE FOR AUTONOMOUS CHART SELECTION:
You are an autonomous Lead Financial Analyst. You MUST decide independently WHICH and HOW MANY charts (from 0 up to 4) to include in your response. Your selection must strictly depend on the user's specific question:
1. If the user asks about "patrimonio", "AUM", "bilancio finale" or "guadagni/perdite" -> YOU MUST INCLUDE 'WATERFALL_PATRIMONIO'.
2. If the user asks about "flussi", "abbandoni", "churn", "migrazione" or "clienti persi" -> YOU MUST INCLUDE 'SANKEY_FLUSSI'.
3. If the user asks about "confronto temporale", "round", "evoluzione nel tempo" -> YOU MUST INCLUDE 'LINEE_COMPARATIVE'.
4. If the user asks about "performance per cluster", "rischio vs patrimonio" or "chi vince tra Adattivo e Fisso" -> YOU MUST INCLUDE 'HEATMAP_PERFORMANCE'.
5. If the user asks about "soddisfazione" or "prodotti" -> YOU MUST INCLUDE 'BAR_PRODOTTI'.
6. If the user asks about "guadagni", "ricavi", "commissioni", "profitto" or "fatturato" -> YOU MUST INCLUDE 'AREA_GUADAGNI'.
7. If the user asks about "adeguatezza", "prodotto giusto", "prodotto sbagliato", "mismatch" or "clienti rifiutano" -> YOU MUST INCLUDE 'SEMAFORO_ADEGUATEZZA'.
8. If the user asks about "scenari a confronto", "quale scenario", "acceptance rate per scenario" or "dove funziona meglio" -> YOU MUST INCLUDE 'ACCETTAZIONI_SCENARI'.
9. If the user asks about "compliance nel tempo", "ADAPT vs FISSO", "promotore migliore" or "chi segue la direttiva" -> YOU MUST INCLUDE 'TREND_COMPLIANCE'.

DO NOT output the same charts every time. If the user asks a specific question (e.g., "why are we losing clients?"), output ONLY the relevant chart (e.g., SANKEY_FLUSSI) and ignore the others. If the question is broad, combine 2 or 3 relevant charts.

IMPORTANT: You MUST respond with ONLY a valid JSON object matching this exact structure (this is just a structural example, change the charts dynamically based on the rules above!):
{
  "suggerimento_breve": "Focus on high-risk retention.",
  "dettaglio_risposta": "Your strategic reasoning here...",
  "grafici_consigliati": [
    {
      "codice": "CHART_CODE_1",
      "didascalia": "1. Interpretazione... \n\n2. Esempio...  \n\n3. Riferimento..."
    },
    {
      "codice": "CHART_CODE_2",
      "didascalia": "1. Interpretazione... \n\n2. Esempio...  \n\n3. Riferimento..."
    }
  ]
}
"""

# =====================================================================
# OLLAMA INTEGRATION FOR ADVISOR
# =====================================================================

class OllamaAdvisor:
    """Handles communication with Ollama for advisory generation"""

    OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
    OLLAMA_TIMEOUT = 120  # seconds
    MODEL_NAME = "gemma4:e4b"

    @staticmethod
    def _format_metrics_context(metrics_data: Dict[str, Any]) -> str:
        """Format metrics data into a readable context string"""
        context_lines = ["## Metrics Analysis Context:"]

        for key, value in metrics_data.items():
            if isinstance(value, (dict, list)):
                context_lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False)[:200]}...")
            else:
                context_lines.append(f"- {key}: {value}")

        return "\n".join(context_lines)

    @staticmethod
    def _validate_response_json(response_text: str) -> Dict[str, Any]:
        """
        Extract, clean, and validate JSON response from Ollama.
        Guarantees that required fields are always present with correct types to prevent Pydantic ValidationErrors.
        """
        # 1. Pulizia: estraiamo solo quello che risiede tra le parentesi graffe più esterne
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx + 1]
        else:
            json_str = response_text

        # 2. Tentativo di decodifica JSON
        try:
            parsed_json = json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "suggerimento_breve": "Analisi strategica completata.",
                "dettaglio_risposta": response_text,
                "grafici_consigliati": []
            }

        if not isinstance(parsed_json, dict):
            parsed_json = {}

        # 3. Messa in sicurezza e casting dei tipi per prevenire crash Pydantic
        if "suggerimento_breve" not in parsed_json or not isinstance(parsed_json["suggerimento_breve"], str):
            val = parsed_json.get("suggerimento_breve", "Consulenza strategica elaborata con successo.")
            parsed_json["suggerimento_breve"] = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)

        if "dettaglio_risposta" not in parsed_json or not isinstance(parsed_json["dettaglio_risposta"], str):
            val = parsed_json.get("dettaglio_risposta", "Dettagli disponibili nell'analisi del modello.")
            parsed_json["dettaglio_risposta"] = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)

        if "grafici_consigliati" not in parsed_json or not isinstance(parsed_json["grafici_consigliati"], list):
            parsed_json["grafici_consigliati"] = []
        else:
            grafici_puliti = []
            for g in parsed_json["grafici_consigliati"]:
                if isinstance(g, dict) and "codice" in g:
                    grafici_puliti.append({
                        "codice": str(g["codice"]),
                        "didascalia": str(g.get("didascalia", "Nessun commento fornito dall'IA."))
                    })
                elif isinstance(g, str):
                    grafici_puliti.append({"codice": g, "didascalia": "Analisi visiva generata."})
            parsed_json["grafici_consigliati"] = grafici_puliti

        return parsed_json

    @classmethod
    def generate_advice(
        cls,
        metrics_data: Dict[str, Any],
        user_message: Optional[str] = None
    ) -> AdvisorResponse:
        """
        Generate tactical advice using Ollama with structured JSON output.
        """
        metrics_context = cls._format_metrics_context(metrics_data)

        if user_message and user_message.strip():
            user_prompt = f"""Analyze these metrics and answer the promoter's question:

{metrics_context}

Promoter's Question: {user_message}

Provide your response as a JSON object."""
        else:
            user_prompt = f"""Generate an initial tactical summary for this round based on metrics:

{metrics_context}

Provide your response as a JSON object with tactical guidance and recommended charts."""

        payload = {
            "model": cls.MODEL_NAME,
            "prompt": user_prompt,
            "system": ADVISOR_SYSTEM_PROMPT,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(
                cls.OLLAMA_GENERATE_URL,
                json=payload,
                timeout=cls.OLLAMA_TIMEOUT
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="LLM request timed out")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="LLM service unavailable")
        except requests.exceptions.RequestException:
            raise HTTPException(status_code=500, detail="LLM request failed")

        response_data = response.json()
        response_text = response_data.get("response", "").strip()

        if not response_text:
            raise HTTPException(status_code=500, detail="Empty response from LLM")

        # Validazione e normalizzazione del dizionario
        parsed_json = cls._validate_response_json(response_text)

        # Creazione sicura dell'oggetto Pydantic
        try:
            return AdvisorResponse(**parsed_json)
        except Exception:
            return AdvisorResponse(
                suggerimento_breve="Analisi elaborata.",
                dettaglio_risposta=parsed_json.get("dettaglio_risposta", response_text),
                grafici_consigliati=[]
            )


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.get("/api/dati-banca")
def get_dati_banca(scenario_id: str = "S0"):
    """
    Endpoint che legge l'ultimo round da MongoDB, aggrega i dati dei prodotti
    e calcola i volumi, cluster e adeguatezza reale.
    """
    doc = collection.find_one({"scenario_id": scenario_id})

    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {"prodotti": []}

    # prendiamo l'ultimo round eseguito
    ultimo_round = sorted(doc["rounds"], key=lambda x: x.get('round', 0))[-1]

    prodotti_aggregati = defaultdict(lambda: {
        'adeguatezza_totale': 0.0,
        'decisioni': 0,
        'accettate': 0,
        'cluster': 'N/A',
        'volume': 0.0
    })

    TICKET_MEDIO_MLN = 0.1

    for promo in ultimo_round.get("promoters_data", []):
        for strat in promo.get("strategies", []):

            # normalizz. nome prodotto per l'interfaccia
            prod = strat.get("prodotto_suggerito", "Altro").replace('_', ' ')
            n_clienti = strat.get("clients_in_cluster", 0)
            adeguatezza_score = strat.get("adeguatezza_score", 0.5)
            ha_accettato = strat.get("accettato", False)

            # aggreghiamo dati per prodotto
            prodotti_aggregati[prod]['adeguatezza_totale'] += adeguatezza_score * 1
            prodotti_aggregati[prod]['decisioni'] += 1
            if ha_accettato:
                prodotti_aggregati[prod]['accettate'] += 1
                prodotti_aggregati[prod]['volume'] += n_clienti * TICKET_MEDIO_MLN

            # assegniamo nome cluster (default se non presente)
            if prodotti_aggregati[prod]['cluster'] == 'N/A':
                prodotti_aggregati[prod]['cluster'] = strat.get("cluster_name", "Cluster Generico")

    # risposta per il frontend Vue
    risposta_api = []
    for prod, vals in prodotti_aggregati.items():
        if vals['decisioni'] > 0:
            adeguaatezza_media = vals['adeguatezza_totale'] / vals['decisioni']

            if adeguaatezza_media >= 0.8:
                status = 'green'
            elif adeguaatezza_media >= 0.5:
                status = 'amber'
            else:
                status = 'red'

            risposta_api.append({
                'name': prod,
                'cluster': vals['cluster'],
                'volume': round(vals['volume'], 1),
                'adequacy': round(adeguaatezza_media * 100),
                'status': status
            })

    risposta_api.sort(key=lambda x:x['adequacy'], reverse=True)

    return {"prodotti": risposta_api}
# =====================================================================
# ENDPOINT: TREND BANCA CON DATI VERI DA MONGODB
# =====================================================================
@app.get("/api/trend-banca")
def get_trend_banca(scenario_id: str = "S0"):
    """
    Legge i round da MongoDB e calcola la raccolta netta cumulata
    (Vero vs Falso su 'accettato' moltiplicato per i clienti).
    """
    # 1. Cerchiamo il documento della simulazione desiderata
    doc = collection.find_one({"scenario_id": scenario_id})
    
    # Dati di fallback se il DB è vuoto o lo scenario non esiste
    if not doc or "rounds" not in doc:
        return {
            "labels": [f"R{i}" for i in range(1, 21)],
            "adattivo": [0]*20,
            "fisso": [0]*20
        }

    storico_ia = []
    storico_fisso = []
    rounds_labels = []
    
    # Ipotesi: ogni cliente investe 100.000€ (0.1 Milioni) se accetta la proposta
    TICKET_MEDIO_MLN = 0.1 

    # Variabili per la somma cumulativa nel tempo
    raccolta_cumulata_ia = 0.0
    raccolta_cumulata_fisso = 0.0

    # 2. Iteriamo sui round estratti da Mongo
    for r in doc["rounds"]:
        round_num = r.get("round", 0)
        rounds_labels.append(f"R{round_num}")
        
        raccolta_round_ia = 0.0
        raccolta_round_fisso = 0.0
        
        # 3. Analizziamo le decisioni dei promotori in questo round
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            
            for strat in promo.get("strategies", []):
                # Se il cliente ha accettato, calcoliamo il volume
                if strat.get("accettato") == True:
                    clienti_convertiti = strat.get("clients_in_cluster", 0)
                    volume_generato = clienti_convertiti * TICKET_MEDIO_MLN
                    
                    if "ADAPT" in pid:
                        raccolta_round_ia += volume_generato
                    elif "FISSO" in pid:
                        raccolta_round_fisso += volume_generato
                        
        # 4. Aggiungiamo la raccolta del round al totale storico
        raccolta_cumulata_ia += raccolta_round_ia
        raccolta_cumulata_fisso += raccolta_round_fisso
        
        # Salviamo i dati formattati per il grafico (arrotondati a 2 decimali)
        storico_ia.append(round(raccolta_cumulata_ia, 2))
        storico_fisso.append(round(raccolta_cumulata_fisso, 2))
        
    return {
        "labels": rounds_labels,
        "adattivo": storico_ia,
        "fisso": storico_fisso
    }
    
@app.get("/api/dati-promotore")
def get_dati_promotore(scenario_id: str = "S0"):
    """
    Dati per il Promotore: Strategia LLM, approccio, revenue, tag di contesto,
    spaccato delle conversioni per profilo di rischio, product breakdown,
    alerts (churn e mifid), e next best actions.
    """
    doc = collection.find_one({"scenario_id": scenario_id})
    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {
            "status": "no_data",
            "adapt": {"strategia_consigliata": "", "approccio_comunicativo": "", "commissioni_cumulate": 0, "tasso_conversione_pct": 0, "fiducia_media": 0, "proposte_totali": 0, "tags": []},
            "fisso": {"commissioni_cumulate": 0, "tasso_conversione_pct": 0, "fiducia_media": 0, "proposte_totali": 0},
            "risk_profile_breakdown": [],
            "product_breakdown": [],
            "alerts": {"churn_risk_count": 0, "mifid_alerts_count": 0},
            "next_best_actions": []
        }

    rounds = sorted(doc["rounds"], key=lambda x: x.get('round', 0))
    ultimo_round = rounds[-1]

    # --- FEATURE 3: ESTRAZIONE DATI ULTIMO ROUND + GENERAZIONE TAG DI CONTESTO ---
    strat_consigliata = "Nessuna strategia registrata."
    approccio = "Nessun approccio registrato."
    ultimo_prodotto = "N/A"
    ultimo_profilo = "N/A"

    for promo in ultimo_round.get("promoters_data", []):
        if "ADAPT" in promo.get("promotore_id", ""):
            strats = promo.get("strategies", [])
            if strats:
                strat_consigliata = strats[0].get("llm_strategy", "")
                approccio = strats[0].get("approccio_comunicativo", "")
                ultimo_prodotto = strats[0].get("prodotto_suggerito", "Altro").replace('_', ' ')
                ultimo_profilo = strats[0].get("profilo_rischio_prevalente", "Balanced")

    # Creazione automatica dei Tag di contesto basati sulle risposte dell'LLM
    tags = [f"🎯 Target: {ultimo_profilo}", f"📦 Prodotto: {ultimo_prodotto}"]
    if "stabile" in strat_consigliata.lower() or "mitigare" in strat_consigliata.lower() or "ansietà" in strat_consigliata.lower():
        tags.append("⚠️ Sentiment: Ansioso")
        tags.append("💧 Focus: Liquidità/Protezione")
    else:
        tags.append("🚀 Sentiment: Ottimista")
        tags.append("📈 Focus: Performance")

    # --- FEATURE 1: CALCOLO CUMULATO + SPACCATO PER PROFILO DI RISCHIO ---
    # Struttura temporanea: { "Balanced": {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0} }
    breakdown_dict = defaultdict(lambda: {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0})

    # Product breakdown: { "Bond Corporate": {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0} }
    product_dict = defaultdict(lambda: {"adapt_acc": 0, "adapt_tot": 0, "fisso_acc": 0, "fisso_tot": 0})

    adapt_comm, adapt_tot, adapt_acc, adapt_fid_sum = 0, 0, 0, 0
    fisso_comm, fisso_tot, fisso_acc, fisso_fid_sum = 0, 0, 0, 0

    churn_risk_count = 0
    mifid_alerts_count = 0

    TICKET_MEDIO = 100000
    COMMISSIONE = 0.01

    for r in rounds:
        for promo in r.get("promoters_data", []):
            pid = promo.get("promotore_id", "")
            is_adapt = "ADAPT" in pid
            is_fisso = "FISSO" in pid

            for s in promo.get("strategies", []):
                prof = s.get("profilo_rischio_prevalente", "N/A")
                if prof == "N/A": continue

                acc = s.get("accettato", False)
                clients = s.get("clients_in_cluster", 0)
                fid_post = s.get("fiducia_media_post", 0)
                adeguatezza = s.get("adeguatezza_score", 0)
                prodotto = s.get("prodotto_suggerito", "Altro").replace('_', ' ')
                delta_fid = s.get("delta_fiducia_medio", 0)

                if is_adapt:
                    adapt_tot += 1
                    adapt_fid_sum += fid_post
                    breakdown_dict[prof]["adapt_tot"] += 1
                    product_dict[prodotto]["adapt_tot"] += 1

                    if acc:
                        adapt_acc += 1
                        adapt_comm += (clients * TICKET_MEDIO) * COMMISSIONE
                        breakdown_dict[prof]["adapt_acc"] += 1
                        product_dict[prodotto]["adapt_acc"] += 1

                    # Alert churn: fiducia < 0.45 (45%) o delta < -0.10
                    if fid_post < 0.45 or delta_fid < -0.10:
                        churn_risk_count += 1

                    # Alert mifid: adeguatezza < 0.40
                    if adeguatezza < 0.40:
                        mifid_alerts_count += 1

                elif is_fisso:
                    fisso_tot += 1
                    fisso_fid_sum += fid_post
                    breakdown_dict[prof]["fisso_tot"] += 1
                    product_dict[prodotto]["fisso_tot"] += 1

                    if acc:
                        fisso_acc += 1
                        fisso_comm += (clients * TICKET_MEDIO) * COMMISSIONE
                        breakdown_dict[prof]["fisso_acc"] += 1
                        product_dict[prodotto]["fisso_acc"] += 1

                    # Alert churn: fiducia < 0.45 o delta < -0.10
                    if fid_post < 0.45 or delta_fid < -0.10:
                        churn_risk_count += 1

                    # Alert mifid: adeguatezza < 0.40
                    if adeguatezza < 0.40:
                        mifid_alerts_count += 1

    # Formattiamo lo spaccato per renderlo digeribile dalla tabella Vue
    risk_profile_breakdown = []
    for prof, vals in breakdown_dict.items():
        risk_profile_breakdown.append({
            "profilo": prof,
            "adapt_pct": round((vals["adapt_acc"] / vals["adapt_tot"] * 100)) if vals["adapt_tot"] > 0 else 0,
            "fisso_pct": round((vals["fisso_acc"] / vals["fisso_tot"] * 100)) if vals["fisso_tot"] > 0 else 0
        })

    # Product breakdown
    product_breakdown = []
    for prod, vals in product_dict.items():
        product_breakdown.append({
            "prodotto": prod,
            "adapt_pct": round((vals["adapt_acc"] / vals["adapt_tot"] * 100)) if vals["adapt_tot"] > 0 else 0,
            "fisso_pct": round((vals["fisso_acc"] / vals["fisso_tot"] * 100)) if vals["fisso_tot"] > 0 else 0
        })

    # Next best actions condizionali
    next_best_actions = []
    adapt_fiducia_media = round((adapt_fid_sum / adapt_tot * 100)) if adapt_tot > 0 else 0

    if adapt_fiducia_media < 50:
        next_best_actions.append("⚠️ Fiducia media critica: rallentare vendite e recuperare relazione cliente")
    if mifid_alerts_count > 0:
        next_best_actions.append(f"🚨 Alert CONSOB/MIFID: {mifid_alerts_count} anomalie di adeguatezza riscontrate")
    if churn_risk_count > 5:
        next_best_actions.append("📉 Rischio churn elevato: rivedere strategia comunicativa")
    if adapt_acc > fisso_acc:
        next_best_actions.append("✅ ADAPT outperforma FISSO: mantenere approccio attuale")
    else:
        next_best_actions.append("⚙️ FISSO competitive: aumentare personalizzazione")

    if not next_best_actions:
        next_best_actions.append("✓ Situazione stabile, proseguire con strategia corrente")

    return {
        "status": "ok",
        "adapt": {
            "strategia_consigliata": strat_consigliata,
            "approccio_comunicativo": approccio,
            "commissioni_cumulate": round(adapt_comm),
            "tasso_conversione_pct": round((adapt_acc / adapt_tot * 100) if adapt_tot > 0 else 0),
            "fiducia_media": adapt_fiducia_media,
            "proposte_totali": adapt_tot,
            "tags": tags
        },
        "fisso": {
            "commissioni_cumulate": round(fisso_comm),
            "tasso_conversione_pct": round((fisso_acc / fisso_tot * 100) if fisso_tot > 0 else 0),
            "fiducia_media": round((fisso_fid_sum / fisso_tot * 100) if fisso_tot > 0 else 0),
            "proposte_totali": fisso_tot
        },
        "risk_profile_breakdown": risk_profile_breakdown,
        "product_breakdown": product_breakdown,
        "alerts": {
            "churn_risk_count": churn_risk_count,
            "mifid_alerts_count": mifid_alerts_count
        },
        "next_best_actions": next_best_actions
    }

@app.get("/api/dati-promotore-grafici")
def get_dati_promotore_grafici(scenario_id: str = "S0"):
    """
    Dati per i grafici della vista Promotore:
    - Compliance/Adeguatezza media per round (ADAPT vs FISSO)
    - Proposte Accettate per round (stacked bar)
    """
    doc = collection.find_one({"scenario_id": scenario_id})

    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {
            "labels": [f"R{i}" for i in range(1, 21)],
            "compliance_adapt": [0] * 20,
            "compliance_fisso": [0] * 20,
            "accettate_adapt": [0] * 20,
            "accettate_fisso": [0] * 20
        }

    compliance_adapt = []
    compliance_fisso = []
    accettate_adapt = []
    accettate_fisso = []
    labels = []

    for r in sorted(doc.get("rounds", []), key=lambda x: x.get('round', 0)):
        round_num = r.get("round", 0)
        labels.append(f"R{round_num}")

        # Metriche per questo round
        adapt_adeguatezza_cumulata = 0
        adapt_conteggio = 0
        adapt_accettate = 0

        fisso_adeguatezza_cumulata = 0
        fisso_conteggio = 0
        fisso_accettate = 0

        for promo in r.get("promoters_data", []):
            promotore_id = promo.get("promotore_id", "")
            strategies = promo.get("strategies", [])

            for strat in strategies:
                adeguatezza = strat.get("adeguatezza_score", 0)
                ha_accettato = strat.get("accettato", False)

                if "ADAPT" in promotore_id:
                    adapt_adeguatezza_cumulata += adeguatezza
                    adapt_conteggio += 1
                    if ha_accettato:
                        adapt_accettate += 1

                elif "FISSO" in promotore_id:
                    fisso_adeguatezza_cumulata += adeguatezza
                    fisso_conteggio += 1
                    if ha_accettato:
                        fisso_accettate += 1

        # Media di adeguatezza per il round
        adapt_compliance = (adapt_adeguatezza_cumulata / adapt_conteggio * 100) if adapt_conteggio > 0 else 0
        fisso_compliance = (fisso_adeguatezza_cumulata / fisso_conteggio * 100) if fisso_conteggio > 0 else 0

        compliance_adapt.append(round(adapt_compliance, 1))
        compliance_fisso.append(round(fisso_compliance, 1))
        accettate_adapt.append(adapt_accettate)
        accettate_fisso.append(fisso_accettate)

    return {
        "labels": labels,
        "compliance_adapt": compliance_adapt,
        "compliance_fisso": compliance_fisso,
        "accettate_adapt": accettate_adapt,
        "accettate_fisso": accettate_fisso
    }

@app.get("/api/dati-cliente")
def get_dati_cliente(scenario_id: str = "S0"):
    """
    Dati per il Cliente: Trasparenza, Fiducia e Discostamento (Adeguatezza).
    """
    doc = collection.find_one({"scenario_id": scenario_id})
    if not doc or "rounds" not in doc or len(doc["rounds"]) == 0:
        return {"fiducia_media": 0, "scostamento_profilo": 0}

    ultimo_round = sorted(doc["rounds"], key=lambda x: x.get('round', 0))[-1]
    
    fiducia_tot = 0
    adeguatezza_tot = 0
    conteggio = 0

    # Calcoliamo le medie di come i clienti si sentono trattati
    for promo in ultimo_round.get("promoters_data", []):
        for strat in promo.get("strategies", []):
            fiducia_tot += strat.get("fiducia_media_post", 0)
            # L'adeguatezza_score (0.0 - 1.0) indica quanto il prodotto rispetta il profilo
            adeguatezza_tot += strat.get("adeguatezza_score", 0)
            conteggio += 1

    if conteggio > 0:
        fiducia_media = fiducia_tot / conteggio
        adeguatezza_media = adeguatezza_tot / conteggio
        
        # Se l'adeguatezza è 0.8, c'è un discostamento del 20% da quello che il cliente voleva
        scostamento = (1.0 - adeguatezza_media) * 100 
    else:
        fiducia_media, scostamento = 0, 0

    return {
        "fiducia_attuale": round(fiducia_media * 100),       # Es. 74%
        "scostamento_profilo": round(scostamento),           # Es. 20%
        "trasparenza_status": "green" if scostamento <= 25 else "red"
    }


# =====================================================================
# ADVISOR LLM ENDPOINT
# =====================================================================

@app.post(
    "/api/advisor/chat",
    response_model=AdvisorResponse,
    summary="Get tactical advice from Virtual Advisor",
    tags=["advisor"]
)
async def chat_with_advisor(request: AdvisorRequest) -> AdvisorResponse:
    """Generate tactical advice based on financial metrics."""
    response = OllamaAdvisor.generate_advice(
        metrics_data=request.metrics_data,
        user_message=request.user_message
    )
    return response


# =====================================================================
# HEALTH AND DASHBOARD ENDPOINTS
# =====================================================================

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "FINsim Unified API",
        "llm_model": OllamaAdvisor.MODEL_NAME
    }


@app.get("/api/dashboard/scenari", tags=["dashboard"])
async def get_scenari():
    """Get list of all scenario IDs"""
    docs = list(collection.find({}, {"scenario_id": 1}))
    return {"scenari": [d["scenario_id"] for d in docs if "scenario_id" in d]}


@app.get("/api/dashboard/scenario/{scenario_id}", tags=["dashboard"])
async def get_scenario(scenario_id: str):
    """Get detailed scenario data"""
    doc = collection.find_one({"scenario_id": scenario_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    doc.pop("_id", None)
    rounds_summary = []
    for r in doc.pop("rounds", []):
        rounds_summary.append({
            "round": r.get("round"),
            "compliance_rate": r.get("compliance_rate"),
            "mismatch_rate": r.get("mismatch_rate"),
            "prodotto_dominante": r.get("prodotto_dominante"),
            "dispersione_prodotti": r.get("dispersione_prodotti"),
            "compliance_per_promotore": r.get("compliance_per_promotore"),
            "decisions_created": r.get("decisions_created"),
            "clients_updated": r.get("clients_updated"),
        })
    doc["rounds_summary"] = rounds_summary
    return doc


@app.get("/api/dashboard/tutti", tags=["dashboard"])
async def get_tutti_scenari():
    """Get summary of all scenarios"""
    docs = list(collection.find({}, {
        "scenario_id": 1,
        "summary": 1,
        "business_metrics": 1,
        "num_rounds": 1,
        "total_decisions": 1,
    }))
    result = {}
    for d in docs:
        d.pop("_id", None)
        sid = d.get("scenario_id")
        if sid:
            result[sid] = d
    return {"scenari": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)