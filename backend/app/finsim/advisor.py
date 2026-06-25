"""
Virtual Advisor API for Promoters - FastAPI endpoint
Analyzes financial metrics and provides strategic recommendations using Ollama (gemma4:e4b)
Returns structured JSON with tactical suggestions and recommended visualizations
"""

import json
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import Config

from ..utils.logger import get_logger

logger = get_logger("finsim.advisor")

mongo_client = MongoClient(Config.MONGO_URI)
mongo_db = mongo_client["finsim_analytics"]
mongo_collection = mongo_db["simulation_history"]

# ============== Pydantic Models ==============

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


# ============== System Prompt ==============

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
- HEATMAP_PERFORMANCE: Use "Asse X (Patrimonio)", "Asse Y (Rischio)". Explain that green cells mean Adaptive outperforms Fixed strategy, red cells mean Fixed outperforms Adaptive. Describe specific high-value segments.
- BAR_PRODOTTI: Use "Asse X (Prodotti Finanziari)", "Asse Y (Livello di Soddisfazione)".
- LINEE_COMPARATIVE: Use "Asse X (Evoluzione dei Round 1-20)", "Asse Y (Valore della Raccolta Cumulata)".
- WATERFALL_PATRIMONIO: DO NOT use X/Y axes terminology! Use "Mattoncini di variazione" or "Fattori di scomposizione". Explain the steps from Initial AUM, through inflows/outflows, to Final AUM.
- SANKEY_FLUSSI: DO NOT use X/Y axes terminology! You MUST use "Nodi di Sinistra (Cluster di rischio di partenza)", "Nodi di Destra (Stato finale o Churn)" and "Nastri / Flussi colorati (Volume di migrazione dei clienti)".
- AREA_GUADAGNI: Use "Asse X (Round Temporali)", "Asse Y (Ricavi Generati in Euro)". Le aree colorate mostrano il volume dei guadagni.

Structure the didascalia like this:
1. COME LEGGERLO: Explain the correct visual components using the STRICT TERMINOLOGY DICTIONARY above.
2. ESEMPIO CONCRETO: Highlight a specific visual finding based on the context (e.g., for HEATMAP: "Nota come la cella Verde nel Cluster Patrimonio Alto / Rischio Medio mostra una dominanza dell'IA sul benchmark..."; for other charts, provide chart-specific insights).
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
      "didascalia": \\n\\n"1. Interpretazione... \\nn\\n2. Esempio...  \\n\\n3. Riferimento..."
    },
    {
      "codice": "CHART_CODE_2",
      "didascalia": \\n\\n"1. Interpretazione... \\nn\\n2. Esempio...  \\n\\n3. Riferimento..."
    }
  ]
}
"""


# ============== Ollama Integration ==============

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
            logger.error(f"Failed to decode JSON from LLM. Raw response: {response_text[:200]}")
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

        logger.debug(f"Calling Ollama with model {cls.MODEL_NAME}")

        try:
            response = requests.post(
                cls.OLLAMA_GENERATE_URL,
                json=payload,
                timeout=cls.OLLAMA_TIMEOUT
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {cls.OLLAMA_TIMEOUT}s")
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

        # Filtraggio codici grafici consentiti
        allowed_charts = {
            "HEATMAP_PERFORMANCE", "BAR_PRODOTTI", "LINEE_COMPARATIVE",
            "WATERFALL_PATRIMONIO", "SANKEY_FLUSSI", "AREA_GUADAGNI",
            "SEMAFORO_ADEGUATEZZA", "ACCETTAZIONI_SCENARI",
            "TREND_COMPLIANCE"
        }
        charts = parsed_json.get("grafici_consigliati", [])
        
        parsed_json["grafici_consigliati"] = charts

        # Creazione sicura dell'oggetto Pydantic
        try:
            return AdvisorResponse(**parsed_json)
        except Exception as e:
            logger.error(f"Pydantic instantiation failed: {e}. Data: {parsed_json}")
            return AdvisorResponse(
                suggerimento_breve="Analisi elaborata.",
                dettaglio_risposta=parsed_json.get("dettaglio_risposta", response_text),
                grafici_consigliati=[]
            )


# ============== FastAPI Application ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("Advisor API starting...")
    yield
    logger.info("Advisor API shutting down...")


app = FastAPI(
    title="FINsim Virtual Advisor API",
    description="On-demand virtual advisor for promoters using Ollama LLM",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://10.12.7.53:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/api/advisor/chat",
    response_model=AdvisorResponse,
    summary="Get tactical advice from Virtual Advisor",
    tags=["advisor"]
)
async def chat_with_advisor(request: AdvisorRequest) -> AdvisorResponse:
    """Generate tactical advice based on financial metrics."""
    logger.info(f"Advisor request: user_message='{request.user_message[:50] if request.user_message else '(empty)'}...'")

    response = OllamaAdvisor.generate_advice(
        metrics_data=request.metrics_data,
        user_message=request.user_message
    )

    logger.info(f"Advisor response: {len(response.dettaglio_risposta)} chars, {len(response.grafici_consigliati)} charts")
    return response


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "FINsim Virtual Advisor API",
        "llm_model": OllamaAdvisor.MODEL_NAME
    }


@app.get("/api/dashboard/scenari", tags=["dashboard"])
async def get_scenari():
    docs = list(mongo_collection.find({}, {"scenario_id": 1}))
    return {"scenari": [d["scenario_id"] for d in docs if "scenario_id" in d]}


@app.get("/api/dashboard/scenario/{scenario_id}", tags=["dashboard"])
async def get_scenario(scenario_id: str):
    doc = mongo_collection.find_one({"scenario_id": scenario_id})
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
    docs = list(mongo_collection.find({}, {
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