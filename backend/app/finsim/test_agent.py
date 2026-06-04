#!/usr/bin/env python3
"""
Test script for FINsim Promotore Agent — Fase 3 (LLM Backend-Only)

Executable test for integrated OllamaClient, FinsimSearcher, and PromotoreAgent.
Tests strategy generation for scenario S0, Adaptive promoter, cluster (0, 0).

Usage:
    python -m backend.app.finsim.test_agent
    or
    python backend/app/finsim/test_agent.py
"""

import json
import logging
import sys
from pathlib import Path

# Configure logging for visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger('finsim.test_agent')


def main() -> int:
    """
    Test PromotoreAgent strategy generation.

    Returns:
        Exit code (0 on success, 1 on failure)
    """
    logger.info("=" * 80)
    logger.info("FINsim Promotore Agent Test — Fase 3")
    logger.info("=" * 80)

    try:
        from backend.app.finsim.llm.ollama_client import OllamaClient
        from backend.app.finsim.search_finsim import create_searcher
        from backend.app.finsim.agents.promotore_agent import PromotoreAgent

        logger.info("Successfully imported OllamaClient, FinsimSearcher, PromotoreAgent")

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return 1

    # Initialize components
    logger.info("-" * 80)
    logger.info("Initializing components...")
    logger.info("-" * 80)

    try:
        # 1. Initialize OllamaClient
        ollama = OllamaClient(
            base_url="http://localhost:11434",
            timeout_seconds=30.0,
        )
        logger.info("✓ OllamaClient initialized")

        # 2. Initialize FinsimSearcher
        searcher = create_searcher()
        logger.info("✓ FinsimSearcher initialized")

        # 3. Initialize PromotoreAgent
        agent = PromotoreAgent(
            ollama_client=ollama,
            searcher=searcher,
            model_name="qwen2.5:3b",
        )
        logger.info("✓ PromotoreAgent initialized")

    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        return 1

    # Test strategy generation
    logger.info("-" * 80)
    logger.info("Testing strategy generation...")
    logger.info("-" * 80)

    scenario_id = "S0"
    promotore_id = "PROM-ADAPT-1"  # Adaptive promoter
    riga = 0
    col = 0

    logger.info(
        f"Generating strategy: scenario={scenario_id}, promotore={promotore_id}, "
        f"cluster=({riga},{col})"
    )

    result = agent.genera_strategia_cluster(
        scenario_id=scenario_id,
        promotore_id=promotore_id,
        riga=riga,
        col=col,
    )

    # Display results
    logger.info("-" * 80)
    logger.info("Strategy Generation Result")
    logger.info("-" * 80)

    logger.info(f"Scenario ID: {result['scenario_id']}")
    logger.info(f"Promotore ID: {result['promotore_id']}")
    logger.info(f"Cluster Position: {result['cluster_position']}")

    if result.get('error'):
        logger.error(f"Error: {result['error']}")
        logger.info(f"LLM Response: {json.dumps(result['llm_raw_response'], indent=2)}")
        return 1

    logger.info(f"Strategia: {result['strategia']}")
    logger.info(f"Approccio Comunicativo: {result['approccio_comunicativo']}")
    logger.info(f"Prodotto Suggerito: {result['prodotto_suggerito']}")

    logger.info("-" * 80)
    logger.info("Full JSON Response:")
    logger.info("-" * 80)

    # Pretty-print the full result
    result_clean = {
        'scenario_id': result['scenario_id'],
        'promotore_id': result['promotore_id'],
        'cluster_position': result['cluster_position'],
        'strategia': result['strategia'],
        'approccio_comunicativo': result['approccio_comunicativo'],
        'prodotto_suggerito': result['prodotto_suggerito'],
    }

    logger.info(json.dumps(result_clean, indent=2, ensure_ascii=False))

    logger.info("-" * 80)
    logger.info("✓ Test completed successfully")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
