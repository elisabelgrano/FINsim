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

from ..utils.logger import get_logger

logger = get_logger("finsim.advisor")

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


class AdvisorResponse(BaseModel):
    """Structured response from advisor"""
    suggerimento_breve: str = Field(
        ...,
        description="Short tactical imperative (e.g. 'Reduce equity exposure on conservative profiles')"
    )
    dettaglio_risposta: str = Field(
        ...,
        description="Detailed discursive explanation"
    )
    grafici_consigliati: List[str] = Field(
        default_factory=list,
        description="Array of recommended chart codes: HEATMAP_PERFORMANCE, MOMENTUM_TIMELINE, BAR_PRODOTTI, KPI_MACRO"
    )


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
- Choose ONLY from these chart codes: HEATMAP_PERFORMANCE, MOMENTUM_TIMELINE, BAR_PRODOTTI, KPI_MACRO
- Use Italian for all responses
- Focus on actionable insights, not abstract analysis
- When user_message is empty, generate an initial tactical summary for the round

## Metrics Context (if present in input):
- performance_metrics: Overall KPI performance vs benchmark
- client_engagement: Client interaction and trust levels
- product_distribution: Product mix and cross-sell opportunities
- market_conditions: Macro signals and sentiment indicators
- heatmap_data: Performance intensity by client/product segment
- momentum_indicators: Trend strength and reversals

IMPORTANT: You MUST respond with ONLY a valid JSON object matching this exact structure:
{
  "suggerimento_breve": "tactical instruction here",
  "dettaglio_risposta": "detailed explanation here",
  "grafici_consigliati": ["CHART_CODE1", "CHART_CODE2"]
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
        allowed_charts = {"HEATMAP_PERFORMANCE", "MOMENTUM_TIMELINE", "BAR_PRODOTTI", "KPI_MACRO"}
        charts = parsed_json.get("grafici_consigliati", [])
        
        validated_charts = [str(c) for c in charts if str(c) in allowed_charts]
        parsed_json["grafici_consigliati"] = validated_charts

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)