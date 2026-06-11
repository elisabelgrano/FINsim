"""
Promotore Agent — LLM-driven financial promoter strategy generation
FINSIM-MOD: Adaptive strategy generation for FINsim promoter layer (Level 3)

Coordinates with FinsimSearcher to fetch scenario/directive/client context,
then invokes OllamaClient to generate personalized client strategies.
"""

import json
import logging
from typing import Dict, Any

from backend.app.finsim.llm.ollama_client import OllamaClient
from backend.app.finsim.search_finsim import FinsimSearcher
from backend.app.finsim.metrics.normalizzatore import normalize_prodotto

logger = logging.getLogger('finsim.agents.promotore')


class PromotoreAgent:
    """
    Adaptive financial promoter agent for FINsim Level 3.

    Generates cluster-specific marketing strategies based on:
    - Scenario macro state (rates, market liquidity, regulatory pressure)
    - Bank directive (product focus, risk tolerance, sales pressure)
    - Client profile distribution in target grid cell
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        searcher: FinsimSearcher,
        model_name: str = "qwen2.5:3b",
    ):
        """
        Initialize PromotoreAgent.

        Args:
            ollama_client: Initialized OllamaClient instance
            searcher: Initialized FinsimSearcher instance
            model_name: Model to use for generation (default: qwen2.5:32b)
        """
        self.ollama_client = ollama_client
        self.searcher = searcher
        self.model_name = model_name
        logger.info(f"PromotoreAgent initialized: model={model_name}")

    def genera_strategia_cluster(
        self,
        scenario_id: str,
        promotore_id: str,
        riga: int,
        col: int,
    ) -> Dict[str, Any]:
        """
        Generate marketing strategy for a client cluster.

        Fetches scenario state, directive, and client profiles for the grid cell.
        Constructs system and user prompts, invokes LLM, returns parsed strategy.

        Args:
            scenario_id: Scenario ID (e.g., 'S0', 'S1', ...)
            promotore_id: Promoter ID
            riga: Cluster grid row
            col: Cluster grid column

        Returns:
            Dict with structure:
            {
                'scenario_id': str,
                'promotore_id': str,
                'cluster_position': {'riga': int, 'col': int},
                'strategia': str,
                'approccio_comunicativo': str,
                'prodotto_suggerito': str,
                'llm_raw_response': dict,
                'error': str | None
            }
        """
        logger.info(
            f"Generating strategy: scenario={scenario_id}, promotore={promotore_id}, "
            f"cluster=({riga},{col})"
        )

        result = {
            'scenario_id': scenario_id,
            'promotore_id': promotore_id,
            'cluster_position': {'riga': riga, 'col': col},
            'strategia': None,
            'approccio_comunicativo': None,
            'prodotto_suggerito': None,
            'llm_raw_response': None,
            'error': None,
        }

        try:
            # Fetch scenario and directive context
            scenario_state = self.searcher.get_scenario_state(scenario_id, round_n=1)
            if not scenario_state.get('scenario'):
                result['error'] = f"Scenario not found: {scenario_id}"
                logger.error(result['error'])
                return result

            scenario = scenario_state['scenario']
            direttiva = scenario_state['direttiva_bancaria']

            # Fetch promoter info
            promoter_data = self.searcher.get_promotore_portfolio(promotore_id)
            if not promoter_data.get('promotore'):
                result['error'] = f"Promoter not found: {promotore_id}"
                logger.error(result['error'])
                return result

            promoter = promoter_data['promotore']

            # Fetch cluster clients
            cluster_data = self.searcher.get_cluster_clients(riga, col)

            logger.info(
                f"Fetched: scenario={scenario.get('scenario_id')}, "
                f"directive={direttiva.get('direttiva_id') if direttiva else 'None'}, "
                f"cluster_clients={cluster_data['client_count']}"
            )

            # Build system prompt
            system_prompt = self._build_system_prompt(promoter)

            # Build user prompt with scenario/directive/client context
            user_prompt = self._build_user_prompt(
                scenario, direttiva, cluster_data, promoter
            )

            logger.debug(f"System prompt length: {len(system_prompt)}")
            logger.debug(f"User prompt length: {len(user_prompt)}")

            # Invoke LLM
            llm_response = self.ollama_client.generate(
                model_name=self.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                format="json",
            )

            result['llm_raw_response'] = llm_response

            if llm_response.get('error'):
                result['error'] = f"LLM generation failed: {llm_response.get('error')}"
                logger.error(result['error'])
                return result

            # Parse LLM response
            try:
                response_text = llm_response.get('content', '').strip()

                # Try to extract JSON from response
                if response_text.startswith('{'):
                    strategy_json = json.loads(response_text)
                else:
                    # Try to find JSON within the response
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        strategy_json = json.loads(response_text[start_idx:end_idx])
                    else:
                        raise json.JSONDecodeError("No JSON found", response_text, 0)

                result['strategia'] = strategy_json.get('strategia', '')
                result['approccio_comunicativo'] = strategy_json.get('approccio_comunicativo', '')
                prodotto_suggerito = strategy_json.get('prodotto_suggerito', '')

                # Sanitize prodotto_suggerito to ensure it's a valid non-empty string
                if isinstance(prodotto_suggerito, list):
                    for item in prodotto_suggerito:
                        if isinstance(item, dict) and 'prodotto' in item:
                            prodotto_suggerito = item['prodotto']
                            break
                    else:
                        if prodotto_suggerito:
                            prodotto_suggerito = str(prodotto_suggerito[0])
                        else:
                            prodotto_suggerito = ''
                elif isinstance(prodotto_suggerito, dict):
                    if 'prodotto' in prodotto_suggerito:
                        prodotto_suggerito = prodotto_suggerito['prodotto']
                    else:
                        prodotto_suggerito = ''

                if not isinstance(prodotto_suggerito, str) or not prodotto_suggerito.strip():
                    prodotto_suggerito = 'Altro'
                
                prodotto_pulito_standard = normalize_prodotto(prodotto_suggerito)
                result['prodotto_suggerito'] = prodotto_pulito_standard
                
                logger.info(
                    f"Strategy generated successfully: "
                    f"scenario={scenario_id}, promotore={promotore_id}, cluster=({riga},{col})"
                )

            except json.JSONDecodeError as e:
                result['error'] = f"Failed to parse LLM JSON response: {e}"
                logger.error(f"{result['error']}\nRaw response: {llm_response.get('content')}")

        except Exception as e:
            result['error'] = f"Unexpected error in genera_strategia_cluster: {str(e)}"
            logger.error(result['error'], exc_info=True)

        return result

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    @staticmethod
    def _build_system_prompt(promoter: Dict[str, Any]) -> str:
        """Build system prompt defining the promoter's role and constraints."""
        tipo = promoter.get('tipo', 'Sconosciuto')
        adattativo = promoter.get('adattativo', False)

        system_prompt = f"""Tu sei un promotore finanziario esperto nel contesto della simulazione FINsim.

Tipo di promotore: {tipo}
Adattativo: {adattativo}
Performance Score: {promoter.get('score_performance', 0.0)}
Bias Prodotto: {promoter.get('bias_prodotto', 'Neutro')}

Il tuo compito è generare una strategia commerciale personalizzata per un cluster di clienti,
considerando:
1. Lo scenario macroeconomico attuale
2. Le direttive bancarie in vigore
3. Il profilo e le preferenze dei clienti nel cluster

Rispondi SEMPRE con un JSON valido contenente i seguenti campi:
- "strategia": descrizione della strategia commerciale da adottare
- "approccio_comunicativo": tono e stile di comunicazione verso i clienti
- "prodotto_suggerito": prodotto finanziario da proporre prioritariamente

Non includere testo fuori dal JSON."""

        return system_prompt

    @staticmethod
    def _build_user_prompt(
        scenario: Dict[str, Any],
        direttiva: Dict[str, Any] | None,
        cluster_data: Dict[str, Any],
        promoter: Dict[str, Any],
    ) -> str:
        """Build user prompt with scenario, directive, and cluster context."""
        scenario_json = json.dumps(scenario, indent=2, ensure_ascii=False)
        direttiva_json = json.dumps(direttiva, indent=2, ensure_ascii=False) if direttiva else "null"
        cluster_json = json.dumps(cluster_data, indent=2, ensure_ascii=False)

        user_prompt = f"""Analizza il seguente contesto e genera una strategia personalizzata:

### Scenario Macroeconomico
{scenario_json}

### Direttiva Bancaria Attiva
{direttiva_json}

### Cluster di Clienti (Posizione: riga={cluster_data['cluster_position']['riga']}, col={cluster_data['cluster_position']['col']})
{cluster_json}

### Informazioni sul Promotore
Tipo: {promoter.get('tipo', 'Sconosciuto')}
Strategia: {'Adattativa (AI-driven)' if promoter.get('adattativo') else 'Fissa (Benchmark)'}
Score Performance: {promoter.get('score_performance', 0.0)}

Genera una strategia commerciale ottimale per questo cluster, considerando:
- I rischi e le preferenze dei clienti
- I vincoli normativi
- Le condizioni di mercato attuali
- La performance target del promotore

Rispondi con JSON valido."""

        return user_prompt
