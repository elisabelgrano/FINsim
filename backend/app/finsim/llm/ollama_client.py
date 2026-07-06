"""
Ollama REST Client — Local LLM API integration for FINsim
FINSIM-MOD: Standalone client for LLM inference via Ollama

Provides parameterized, timeout-aware requests with retry logic and fallback responses.
"""

import json
import logging
import os
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger('finsim.llm.ollama')


class OllamaClient:
    """
    REST client for Ollama local LLM API.

    Handles generation requests with strict timeouts, retry logic, and fallback responses.
    Designed for LLM calls in FINsim agent hierarchy.
    """

    DEFAULT_BASE_URL: str = "http://localhost:11434"
    DEFAULT_TIMEOUT_SECONDS: float = float(os.getenv('OLLAMA_TIMEOUT_SECONDS', '900.0'))
    MAX_RETRIES: int = 1

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        """
        Initialize Ollama REST client.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            timeout_seconds: Request timeout in seconds (default: 900.0, or OLLAMA_TIMEOUT_SECONDS env var)
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout_seconds = timeout_seconds
        logger.info(f"OllamaClient initialized: {self.base_url}, timeout={timeout_seconds}s")

        if not self.is_healthy():
            logger.warning(f"⚠️  Ollama at {self.base_url} is not responding. Check if it's running.")

    def is_healthy(self) -> bool:
        """
        Check if Ollama API is responsive.

        Returns:
            True if Ollama responds to /api/tags, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False

    def generate(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Generate LLM response via Ollama API.

        Args:
            model_name: Model name (e.g., 'qwen2.5:32b', 'qwen2.5:3b')
            system_prompt: System context for LLM
            user_prompt: User input/query
            format: Output format ('json' or 'text', default: 'json')

        Returns:
            Dict with keys:
            - 'content': Generated text response (str)
            - 'model': Model name used (str)
            - 'error': Error message if generation failed (str, optional)
            - 'timeout': True if request timed out (bool, optional)

            On critical failure (timeout/connection error):
            - Returns fallback dict: {"error": "timeout", "content": ""}
        """
        endpoint = f"{self.base_url}/api/generate"

        payload = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "format": format,
            "stream": False,
            "think": False,
        }

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"Ollama request (attempt {attempt + 1}): model={model_name}, "
                    f"format={format}, timeout={self.timeout_seconds}s"
                )

                response = requests.post(
                    endpoint,
                    json=payload,
                    timeout=self.timeout_seconds,
                )

                response.raise_for_status()

                data = response.json()

                logger.debug(f"Ollama response received (model={model_name})")

                return {
                    "content": data.get("response", ""),
                    "model": model_name,
                }

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Ollama request timeout (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): "
                    f"model={model_name}"
                )
                if attempt == self.MAX_RETRIES:
                    logger.error(
                        f"Ollama timeout exceeded max retries (model={model_name})"
                    )
                    return {"error": "timeout", "content": ""}

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"Ollama connection error (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {e}"
                )
                if attempt == self.MAX_RETRIES:
                    logger.error(
                        f"Ollama connection failed max retries (model={model_name})"
                    )
                    return {"error": "timeout", "content": ""}

            except requests.exceptions.RequestException as e:
                logger.error(f"Ollama request error: {e}")
                return {"error": "timeout", "content": ""}

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Ollama response parsing error: {e}")
                return {"error": "timeout", "content": ""}

        return {"error": "timeout", "content": ""}
