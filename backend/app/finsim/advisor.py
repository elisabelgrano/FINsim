"""
Virtual Advisor API for Promoters - FastAPI endpoint
Analyzes financial metrics and provides strategic recommendations using Ollama (qwen2.5:3b)
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
    MODEL_NAME = "qwen2.5:3b"

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
        Extract and validate JSON response from Ollama.
        Handles cases where model returns extra text before/after JSON.
        """
        # Try to parse as-is first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON object from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                json_str = response_text[start_idx:end_idx + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Unable to extract valid JSON from response: {response_text[:200]}")

    @classmethod
    def generate_advice(
        cls,
        metrics_data: Dict[str, Any],
        user_message: Optional[str] = None
    ) -> AdvisorResponse:
        """
        Generate tactical advice using Ollama with structured JSON output.

        Args:
            metrics_data: Dictionary of calculated metrics
            user_message: Optional user question/prompt

        Returns:
            AdvisorResponse with structured tactical guidance

        Raises:
            HTTPException: On timeout, invalid response, or connection error
        """
        metrics_context = cls._format_metrics_context(metrics_data)

        # Build user prompt
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
            "format": "json"  # Force JSON output format
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
            raise HTTPException(
                status_code=504,
                detail="LLM request timed out - advisor unavailable"
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise HTTPException(
                status_code=503,
                detail="LLM service unavailable"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="LLM request failed"
            )

        # Extract and validate JSON response
        try:
            response_data = response.json()
            response_text = response_data.get("response", "")

            if not response_text:
                logger.error("Empty response from Ollama")
                raise HTTPException(
                    status_code=500,
                    detail="Empty response from LLM"
                )

            parsed_json = cls._validate_response_json(response_text)

            # Validate required fields
            required_fields = ["suggerimento_breve", "dettaglio_risposta", "grafici_consigliati"]
            missing = [f for f in required_fields if f not in parsed_json]
            if missing:
                logger.error(f"Response missing required fields: {missing}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid LLM response structure"
                )

            # Validate chart codes
            allowed_charts = {"HEATMAP_PERFORMANCE", "MOMENTUM_TIMELINE", "BAR_PRODOTTI", "KPI_MACRO"}
            charts = parsed_json.get("grafici_consigliati", [])
            if not isinstance(charts, list):
                logger.error(f"grafici_consigliati is not a list: {type(charts)}")
                charts = []

            validated_charts = [c for c in charts if c in allowed_charts]
            if len(validated_charts) < len(charts):
                logger.warning(f"Some invalid chart codes filtered out")

            parsed_json["grafici_consigliati"] = validated_charts

            return AdvisorResponse(**parsed_json)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON response: {e}")
            raise HTTPException(
                status_code=500,
                detail="LLM response format invalid"
            )
        except ValueError as e:
            logger.error(f"Response validation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="LLM response validation failed"
            )
        except Exception as e:
            logger.error(f"Unexpected error processing LLM response: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error processing LLM response"
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
    """
    Generate tactical advice based on financial metrics.

    **Request Parameters:**
    - `metrics_data`: Dictionary of calculated metrics (e.g., performance, engagement, products)
    - `user_message`: Optional promoter question. If empty, generates initial tactical summary.

    **Response:**
    - `suggerimento_breve`: Short tactical instruction (imperative)
    - `dettaglio_risposta`: Detailed discursive explanation
    - `grafici_consigliati`: Recommended chart codes for frontend visualization

    **Example Request:**
    ```json
    {
      "metrics_data": {
        "performance_metrics": {"adaptive": 85, "benchmark": 70},
        "client_engagement": {"active_clients": 45, "trust_score": 7.2}
      },
      "user_message": "Why is engagement dropping in segment B?"
    }
    ```

    **Example Response:**
    ```json
    {
      "suggerimento_breve": "Increase contact frequency for segment B clients and emphasize performance gains.",
      "dettaglio_risposta": "Analysis shows...",
      "grafici_consigliati": ["HEATMAP_PERFORMANCE", "MOMENTUM_TIMELINE"]
    }
    ```
    """
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


@app.get("/api/advisor/charts", tags=["advisor"])
async def get_available_charts() -> dict:
    """
    Get list of available chart codes that advisor can recommend.

    Useful for frontend to understand which visualizations are supported.
    """
    return {
        "available_charts": [
            {
                "code": "HEATMAP_PERFORMANCE",
                "description": "Performance intensity by client/product segment"
            },
            {
                "code": "MOMENTUM_TIMELINE",
                "description": "Trend strength and reversals over time"
            },
            {
                "code": "BAR_PRODOTTI",
                "description": "Product distribution and mix analysis"
            },
            {
                "code": "KPI_MACRO",
                "description": "Macro KPI indicators and benchmarks"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
