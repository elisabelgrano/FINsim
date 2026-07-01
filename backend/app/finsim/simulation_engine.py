"""
SimulationEngine — Phase 4 orchestration for FINsim round loop
FINSIM-MOD: Standalone backend simulation engine with cluster optimization

Manages round advancement, promoter strategy generation, decision persistence,
and client reaction calculation using Neo4j queries and OllamaClient integration.
"""

import json
import logging
from collections import Counter
from typing import Dict, Any, List, Optional
from uuid import uuid4

from neo4j import GraphDatabase, Session as Neo4jSession
from neo4j.exceptions import Neo4jError

from backend.app.finsim.agents.promotore_agent import PromotoreAgent
from backend.app.finsim.llm.ollama_client import OllamaClient
from backend.app.finsim.search_finsim import FinsimSearcher
from backend.app.finsim.metrics import normalize_prodotto

logger = logging.getLogger('finsim.simulation_engine')

ADEGUATEZZA_MATRIX = {
    "Conservative": {
        "Cash_Equivalents":      1.0,
        "Bond_Sovereign":        0.9,
        "Bond_Corporate":        0.5,
        "Polizze_Assicurative":  0.8,
        "Real_Estate":           0.3,
        "Mixed_Funds":           0.1,
        "ETF_Tematici":          0.2,
        "Fondi_Azionari":        0.1,
        "Derivati":              0.0,
        "Altro":                 0.2
    },
    "Balanced": {
        "Bond_Sovereign":        1.0,
        "Bond_Corporate":        0.8,
        "Cash_Equivalents":      0.6,
        "Polizze_Assicurative":  0.6,
        "Real_Estate":           0.6,
        "Mixed_Funds":           0.5,
        "ETF_Tematici":          0.5,
        "Fondi_Azionari":        0.4,
        "Derivati":              0.1,
        "Altro":                 0.3
    },
    "Growth": {
        "Bond_Corporate":        1.0,
        "Mixed_Funds":           0.8,
        "ETF_Tematici":          0.8,
        "Real_Estate":           0.7,
        "Bond_Sovereign":        0.5,
        "Polizze_Assicurative":  0.3,
        "Fondi_Azionari":        0.9,
        "Cash_Equivalents":      0.3,
        "Derivati":              0.4,
        "Altro":                 0.3
    },
    "Aggressive": {
        "Mixed_Funds":           1.0,
        "Fondi_Azionari":        1.0,
        "Derivati":              0.9,
        "Bond_Corporate":        0.7,
        "ETF_Tematici":          0.7,
        "Real_Estate":           0.6,
        "Bond_Sovereign":        0.3,
        "Polizze_Assicurative":  0.1,
        "Cash_Equivalents":      0.2,
        "Altro":                 0.2
    }
}

SOGLIA_ACCETTAZIONE = 0.5
MALUS_FIDUCIA_RIFIUTO = -0.15


class SimulationEngine:
    """
    Orchestrates FINsim round progression with cluster-optimized promoter strategy execution.

    Manages:
    - Round advancement for all promoters
    - Cluster-level strategy generation via PromotoreAgent
    - Decision persistence to Neo4j
    - Client trust/reaction updates based on product-risk congruence
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        ollama_base_url: str = "http://localhost:11434",
    ):
        """
        Initialize SimulationEngine with Neo4j and Ollama connectivity.

        Args:
            neo4j_uri: Neo4j connection URI (e.g., 'bolt://localhost:7687')
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            ollama_base_url: Ollama REST endpoint
        """
        self._neo4j_uri = neo4j_uri
        self._neo4j_user = neo4j_user
        self._neo4j_password = neo4j_password
        self._driver = GraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_password)
        )

        self.ollama_client = OllamaClient(base_url=ollama_base_url)
        self.searcher = FinsimSearcher(neo4j_uri, neo4j_user, neo4j_password)
        self.promotore_agent = PromotoreAgent(self.ollama_client, self.searcher)

        logger.info(
            f"SimulationEngine initialized: neo4j={neo4j_uri}, "
            f"ollama={ollama_base_url}"
        )

    def close(self):
        """Close Neo4j driver and searcher connections."""
        self._driver.close()
        self.searcher.close()
        logger.info("SimulationEngine closed")

    # ========================================================================
    # Public API
    # ========================================================================

    def esegui_round(self, scenario_id: str, round_n: int) -> Dict[str, Any]:
        """
        Execute a complete round of simulation for all promoters.

        For each promoter:
        1. Query Neo4j for active clusters (clusters with clients managed by promoter)
        2. Generate strategy via PromotoreAgent for each cluster
        3. Save decision to DB
        4. Calculate client reactions

        Args:
            scenario_id: Scenario identifier (e.g., 'S0', 'S1')
            round_n: Round number (1-20)

        Returns:
            Dict with structure:
            {
                'round': int,
                'scenario_id': str,
                'promoters_processed': int,
                'total_clusters': int,
                'decisions_created': int,
                'clients_updated': int,
                'errors': List[str],
                'timestamp': str
            }
        """
        logger.info(f"========== ROUND {round_n} STARTED (Scenario {scenario_id}) ==========")

        result = {
            'round': round_n,
            'scenario_id': scenario_id,
            'promoters_processed': 0,
            'total_clusters': 0,
            'decisions_created': 0,
            'clients_updated': 0,
            'errors': [],
            'promoters_data': [],
            'compliance_per_promotore': {}
        }

        with self._driver.session() as session:
            # Fetch all promoters
            promoters = self._get_all_promoters(session)
            logger.info(f"Found {len(promoters)} promoters")

            for promoter in promoters:
                promotore_id = promoter['promotore_id']
                promotore_uuid = promoter['uuid']
                
                promoter_data_for_mongo = {
                    'promotore_id': promotore_id,
                    'strategies': []}

                prodotti_per_promotore = []

                try:
                    logger.info(f"Processing promoter: {promotore_id} (uuid={promotore_uuid})")

                    # Get active clusters for this promoter
                    active_clusters = self._get_active_clusters(session, promotore_uuid)
                    logger.info(f"  → {len(active_clusters)} active clusters")
                    result['total_clusters'] += len(active_clusters)

                    # Track metrics for this promoter across all clusters
                    cluster_products_raw = []
                    cluster_products_normalized = []
                    cluster_focus_prodotto = None

                    for cluster in active_clusters:
                        riga = cluster['riga']
                        col = cluster['col']

                        try:
                            logger.info(f"  → Cluster ({riga}, {col})")

                            # Generate strategy via PromotoreAgent
                            strategy_result = self.promotore_agent.genera_strategia_cluster(
                                scenario_id=scenario_id,
                                promotore_id=promotore_id,
                                riga=riga,
                                col=col,
                                round_n=round_n
                            )

                            if strategy_result.get('error'):
                                logger.warning(
                                    f"    Strategy generation failed: {strategy_result['error']}"
                                )
                                result['errors'].append(
                                    f"Cluster ({riga}, {col}): {strategy_result['error']}"
                                )
                                continue

                            # Extract raw product suggestion
                            prodotto_raw = strategy_result['prodotto_suggerito']
                            prodotto_normalized = normalize_prodotto(prodotto_raw)

                            # Track products for metrics calculation
                            cluster_products_raw.append(prodotto_raw)
                            cluster_products_normalized.append(prodotto_normalized)

                            # Extract strategy details
                            strategy_json = {
                                'strategia': strategy_result['strategia'],
                                'approccio_comunicativo': strategy_result['approccio_comunicativo'],
                                'prodotto_suggerito_raw': prodotto_raw,
                                'prodotto_suggerito': prodotto_normalized,
                            }

                            # Save decision to DB
                            decision_created = self.salva_decisione_db(
                                session=session,
                                promotore_uuid=promotore_uuid,
                                riga=riga,
                                col=col,
                                round_n=round_n,
                                strategia_json=strategy_json,
                            )

                            if decision_created:
                                result['decisions_created'] += 1
                                logger.info(f"    Decision saved")
                            else:
                                logger.warning(f"    Failed to save decision")
                                result['errors'].append(
                                    f"Cluster ({riga}, {col}): DB save failed"
                                )
                                continue

                            # Get pre-reaction metrics
                            pre_metrics_query = """
                            MATCH (p:Promotore {uuid: $promotore_uuid})-[:GESTISCE]->(c:Cliente)
                            WHERE c.cluster_riga = $riga AND c.cluster_col = $col
                            RETURN
                              avg(c.fiducia_attuale) as fiducia_media_pre,
                              collect(c.profilo_rischio) as profili_rischio
                            """
                            pre_metrics_res = session.run(
                                pre_metrics_query,
                                promotore_uuid=promotore_uuid,
                                riga=riga,
                                col=col
                            ).single()

                            fiducia_media_pre = round(pre_metrics_res['fiducia_media_pre'], 4) if pre_metrics_res and pre_metrics_res['fiducia_media_pre'] is not None else 0.0
                            profili_rischio_list = pre_metrics_res['profili_rischio'] if pre_metrics_res else []

                            if profili_rischio_list:
                                profilo_rischio_prevalente = Counter(profili_rischio_list).most_common(1)[0][0]
                            else:
                                profilo_rischio_prevalente = 'Balanced'
                                
                            # Post-processing: correggi prodotto se fuori lista per il profilo
                            PRODOTTI_AMMESSI_PER_PROFILO = {
                                'Conservative': {'Cash_Equivalents', 'Bond_Sovereign', 'Polizze_Assicurative', 'Bond_Corporate'},
                                'Balanced':     {'Bond_Sovereign', 'Bond_Corporate', 'Cash_Equivalents', 'ETF_Tematici', 'Mixed_Funds'},
                                'Growth':       {'Bond_Corporate', 'Fondi_Azionari', 'ETF_Tematici', 'Mixed_Funds', 'Bond_Sovereign'},
                                'Aggressive':   {'Fondi_Azionari', 'Derivati', 'ETF_Tematici', 'Bond_Corporate', 'Mixed_Funds'},
                            }
                            ammessi = PRODOTTI_AMMESSI_PER_PROFILO.get(profilo_rischio_prevalente, set())
                            if prodotto_normalized not in ammessi and ammessi:
                                prodotto_normalized = max(
                                    ammessi,
                                    key=lambda p: ADEGUATEZZA_MATRIX.get(profilo_rischio_prevalente, {}).get(p, 0)
                                )
                                logger.info(f"    Post-processing: prodotto corretto a {prodotto_normalized} per profilo {profilo_rischio_prevalente}")

                            # Compute adequacy score
                            adeguatezza_score = round(
                                ADEGUATEZZA_MATRIX
                                .get(profilo_rischio_prevalente, {})
                                .get(prodotto_normalized, 0.0),
                                2
                            )
                            accettato = adeguatezza_score >= SOGLIA_ACCETTAZIONE

                            # Track product for compliance calculation
                            prodotti_per_promotore.append(prodotto_normalized)

                            # Calculate client reactions
                            prodotto_suggerito = strategy_result['prodotto_suggerito']
                            clients_updated = self.calcola_reazione_clienti(
                                session=session,
                                promotore_uuid=promotore_uuid,
                                riga=riga,
                                col=col,
                                prodotto_suggerito=prodotto_suggerito,
                                adeguatezza_score=adeguatezza_score,
                            )

                            result['clients_updated'] += clients_updated
                            logger.info(f"    Updated {clients_updated} clients")

                            # Apply trust malus if product not adequate
                            if not accettato:
                                malus_query = """
                                MATCH (p:Promotore {uuid: $promotore_uuid})-[:GESTISCE]->(c:Cliente)
                                WHERE c.cluster_riga = $riga AND c.cluster_col = $col
                                SET c.fiducia_attuale = CASE
                                  WHEN c.fiducia_attuale + $malus < 0.0 THEN 0.0
                                  ELSE c.fiducia_attuale + $malus
                                END
                                """
                                session.run(
                                    malus_query,
                                    promotore_uuid=promotore_uuid,
                                    riga=riga,
                                    col=col,
                                    malus=MALUS_FIDUCIA_RIFIUTO
                                )
                                logger.info(f"    Applied adequacy malus (score={adeguatezza_score})")

                            metrics_query = """
                            MATCH (p:Promotore {uuid: $promotore_uuid})-[g:GESTISCE]->(c:Cliente)-[:APPARTIENE_A]->(clu:ClusterProfilo)
                            WHERE c.cluster_riga = $riga AND c.cluster_col = $col
                            RETURN
                                avg(c.fiducia_attuale - c.fiducia_iniziale) as avg_delta_fiducia,
                                avg(c.soddisfazione - 0.5) as avg_delta_soddisfazione,
                                avg(c.fiducia_attuale) as fiducia_media_post
                            """
                            metrics_res = session.run(metrics_query, promotore_uuid=promotore_uuid, riga=riga, col=col).single()

                            delta_fiducia = round(metrics_res['avg_delta_fiducia'], 4) if metrics_res and metrics_res['avg_delta_fiducia'] is not None else 0.0
                            delta_soddisfazione = round(metrics_res['avg_delta_soddisfazione'], 4) if metrics_res and metrics_res['avg_delta_soddisfazione'] is not None else 0.0
                            fiducia_media_post = round(metrics_res['fiducia_media_post'], 4) if metrics_res and metrics_res['fiducia_media_post'] is not None else 0.0

                            promoter_data_for_mongo['strategies'].append({
                                'cluster_coords': [riga, col],
                                'clients_in_cluster': clients_updated,
                                'llm_strategy': strategy_result['strategia'],
                                'approccio_comunicativo': strategy_result['approccio_comunicativo'],
                                'prodotto_suggerito_raw': prodotto_raw,
                                'prodotto_suggerito': prodotto_normalized,
                                'fiducia_media_pre': fiducia_media_pre,
                                'fiducia_media_post': fiducia_media_post,
                                'delta_fiducia_medio': round(fiducia_media_post - fiducia_media_pre, 4),
                                'profilo_rischio_prevalente': profilo_rischio_prevalente,
                                'adeguatezza_score': adeguatezza_score,
                                'accettato': accettato,
                                'performance_metrics': {
                                    'delta_fiducia_medio': delta_fiducia,
                                    'delta_soddisfazione_medio': delta_soddisfazione
                                }
                            })

                        except Exception as e:
                            error_msg = f"Cluster ({riga}, {col}): {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            result['errors'].append(error_msg)

                    # Compute metrics for this promoter
                    compliance_rate = 0.0
                    prodotto_dominante = "Altro"
                    dispersione_prodotti = 0

                    if cluster_products_normalized:
                        dispersione_prodotti = len(set(cluster_products_normalized))
                        product_counts = {}
                        for prod in cluster_products_normalized:
                            product_counts[prod] = product_counts.get(prod, 0) + 1
                        prodotto_dominante = max(product_counts, key=product_counts.get)

                    # Try to get focus_prodotto from directive for compliance calculation
                    try:
                        scenario_state = self.searcher.get_scenario_state(scenario_id, round_n=round_n)
                        if scenario_state and scenario_state.get('direttiva_bancaria'):
                            focus_prodotto = scenario_state['direttiva_bancaria'].get('focus_prodotto')
                            if focus_prodotto:
                                focus_norm = normalize_prodotto(focus_prodotto)
                                matches = sum(1 for p in cluster_products_normalized if p == focus_norm)
                                compliance_rate = round(matches / len(cluster_products_normalized), 2) if cluster_products_normalized else 0.0
                    except Exception as e:
                        logger.debug(f"Could not calculate compliance rate for {promotore_id}: {e}")

                    # Compute compliance_per_promotore
                    conformi = sum(1 for p in prodotti_per_promotore if p == prodotto_dominante)
                    compliance_per_promotore = round(
                        conformi / len(prodotti_per_promotore), 2
                    ) if prodotti_per_promotore else 0.0

                    promoter_data_for_mongo['compliance_metrics'] = {
                        'compliance_rate': compliance_rate,
                        'prodotto_dominante': prodotto_dominante,
                        'dispersione_prodotti': dispersione_prodotti
                    }

                    result['promoters_processed'] += 1
                    result['compliance_per_promotore'][promotore_id] = compliance_per_promotore

                    result['promoters_data'].append(promoter_data_for_mongo)

                except Exception as e:
                    error_msg = f"Promoter {promotore_id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    result['errors'].append(error_msg)

        logger.info(
            f"========== ROUND {round_n} COMPLETED ==========\n"
            f"Promoters: {result['promoters_processed']}\n"
            f"Clusters: {result['total_clusters']}\n"
            f"Decisions: {result['decisions_created']}\n"
            f"Clients Updated: {result['clients_updated']}\n"
            f"Errors: {len(result['errors'])}"
        )

        return result

    # ========================================================================
    # Decision Persistence
    # ========================================================================

    def salva_decisione_db(
        self,
        session: Neo4jSession,
        promotore_uuid: str,
        riga: int,
        col: int,
        round_n: int,
        strategia_json: Dict[str, Any],
    ) -> bool:
        """
        Create DecisioneCommerciale node and link it to promoter.

        Uses parametrized Cypher queries to prevent injection.

        Args:
            session: Neo4j session
            promotore_uuid: Promoter UUID
            riga: Cluster row
            col: Cluster column
            round_n: Round number
            strategia_json: Strategy dict with keys: strategia, approccio_comunicativo, prodotto_suggerito

        Returns:
            True if decision was saved, False otherwise
        """
        # --- FIX ANTI-ALLUCINAZIONE ---
        # Forziamo la conversione in testo (str) per evitare crash su Neo4j
        sicuro_strategia = str(strategia_json.get('strategia', ''))
        sicuro_prodotto = str(strategia_json.get('prodotto_suggerito', ''))
        sicuro_approccio = str(strategia_json.get('approccio_comunicativo', ''))
        # ------------------------------
        try:
            decisione_uuid = f"decisione-{uuid4()}"

            query = """
            MATCH (p:Promotore {uuid: $promotore_uuid})
            CREATE (d:DecisioneCommerciale {
                uuid: $decisione_uuid,
                round: $round_n,
                strategia: $strategia,
                approccio_comunicativo: $approccio_comunicativo,
                prodotto_suggerito: $prodotto_suggerito,
                cluster_riga: $riga,
                cluster_col: $col,
                timestamp_creazione: datetime()
            })
            CREATE (p)-[:EFFETTUA]->(d)
            RETURN d.uuid as decisione_uuid
            """

            result = session.run(
                query,
                promotore_uuid=promotore_uuid,
                decisione_uuid=decisione_uuid,
                round_n=round_n,
                strategia=sicuro_strategia,
                approccio_comunicativo=sicuro_approccio,
                prodotto_suggerito=sicuro_prodotto,
                riga=riga,
                col=col,
            )

            record = result.single()
            if record:
                logger.info(f"Decision created: {record['decisione_uuid']}")
                return True
            else:
                logger.error(f"Failed to create decision for promoter {promotore_uuid}")
                return False

        except Neo4jError as e:
            logger.error(f"Neo4j error in salva_decisione_db: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in salva_decisione_db: {e}")
            return False

    # ========================================================================
    # Client Reaction Calculation
    # ========================================================================

    def calcola_reazione_clienti(
        self,
        session: Neo4jSession,
        promotore_uuid: str,
        riga: int,
        col: int,
        prodotto_suggerito: str,
        adeguatezza_score: float = 0.5,
    ) -> int:
        try:
            # Calcola delta fiducia direttamente dall'adeguatezza del prodotto
            if adeguatezza_score >= 0.8:
                delta_fiducia_base = 0.05    # prodotto molto adatto
            elif adeguatezza_score >= 0.5:
                delta_fiducia_base = 0.02    # prodotto accettabile
            elif adeguatezza_score >= 0.3:
                delta_fiducia_base = -0.01   # prodotto poco adatto
            else:
                delta_fiducia_base = -0.04   # prodotto inadatto

            # Get all clients in cluster managed by this promoter
            get_clients_query = """
            MATCH (p:Promotore {uuid: $promotore_uuid})-[:GESTISCE]->(c:Cliente)
            WHERE c.cluster_riga = $riga AND c.cluster_col = $col
            RETURN c.uuid as client_uuid,
                   c.fiducia_attuale as fiducia_attuale, c.soddisfazione as soddisfazione
            """

            clients_result = session.run(
                get_clients_query, promotore_uuid=promotore_uuid, riga=riga, col=col
            )
            clients = list(clients_result)
            clients_updated = 0

            for client in clients:
                client_uuid = client['client_uuid']
                fiducia_attuale = client['fiducia_attuale'] or 0.5
                soddisfazione = client['soddisfazione'] or 0.5

                delta_fiducia = delta_fiducia_base
                delta_soddisfazione = delta_fiducia * 0.5

                fiducia_nuova = max(0.0, min(1.0, fiducia_attuale + delta_fiducia))
                soddisf_nuova = max(0.0, min(1.0, soddisfazione + delta_soddisfazione))

                update_query = """
                MATCH (c:Cliente {uuid: $client_uuid})
                SET c.fiducia_attuale = $fiducia_nuova,
                    c.soddisfazione = $soddisf_nuova
                RETURN c.uuid
                """

                update_result = session.run(
                    update_query,
                    client_uuid=client_uuid,
                    fiducia_nuova=fiducia_nuova,
                    soddisf_nuova=soddisf_nuova,
                )

                if update_result.single():
                    clients_updated += 1

            return clients_updated

        except Exception as e:
            logger.error(f"Error in calcola_reazione_clienti: {e}")
            return 0

    @staticmethod
    def _calcola_delta_fiducia(rischio_prodotto: str, rischio_cliente: str) -> float:
        """
        Calculate trust delta based on product-client risk congruence.

        Args:
            rischio_prodotto: Product risk level ('ALTO', 'MEDIO', 'BASSO')
            rischio_cliente: Client risk profile ('ALTO', 'MEDIO', 'BASSO')

        Returns:
            Trust delta to apply
        """
        risk_levels = {'BASSO': 0, 'MEDIO': 1, 'ALTO': 2}

        prod_level = risk_levels.get(rischio_prodotto, 1)
        client_level = risk_levels.get(rischio_cliente, 1)

        diff = abs(prod_level - client_level)

        if diff == 0:  # Exact match
            return 0.1
        elif diff == 1:  # 1-level mismatch
            return 0.0
        else:  # 2-level mismatch
            return -0.15

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    @staticmethod
    def _get_all_promoters(session: Neo4jSession) -> List[Dict[str, Any]]:
        """
        Fetch all Promotore nodes with their IDs and UUIDs.

        Args:
            session: Neo4j session

        Returns:
            List of dicts with keys: promotore_id, uuid
        """
        query = "MATCH (p:Promotore) RETURN p.promotore_id as promotore_id, p.uuid as uuid"

        result = session.run(query)
        promoters = [
            {
                'promotore_id': record['promotore_id'],
                'uuid': record['uuid'],
            }
            for record in result
        ]

        return promoters

    @staticmethod
    def _get_active_clusters(
        session: Neo4jSession, promotore_uuid: str
    ) -> List[Dict[str, int]]:
        """
        Get all active clusters (with clients) managed by a promoter.

        Optimization: Only queries clusters that actually have clients linked
        via GESTISCE relationship, avoiding full 5x5 grid scan.

        Args:
            session: Neo4j session
            promotore_uuid: Promoter UUID

        Returns:
            List of dicts with keys: riga, col
        """
        query = """
        MATCH (p:Promotore {uuid: $promotore_uuid})-[:GESTISCE]->(c:Cliente)
        RETURN DISTINCT c.cluster_riga as riga, c.cluster_col as col
        ORDER BY riga, col
        """

        result = session.run(query, promotore_uuid=promotore_uuid)
        clusters = [
            {
                'riga': record['riga'],
                'col': record['col'],
            }
            for record in result
        ]

        return clusters

    def _calcola_metriche_business(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcola i KPI di business aggregando i dati storici dei round simulati.
        Include pre-calcolo griglia 4x5 per heatmap e analisi automatica covariate.

        Args:
            scenario_data: Dict con 'rounds' contenente i dati aggregati per ogni round

        Returns:
            Dict con metriche di business calcolate, heatmap e covariate
        """
        metrics = {
            "valore_aggiunto_personalizzazione": 0.0,
            "soddisfazione_ponderata_fisso": 0.0,
            "soddisfazione_ponderata_adattativo": 0.0,
            "clienti_salvati_dal_churn": 0,
            "velocita_variazione_soddisfazione": [],
            "efficacia_strategica_prodotti": {},
            "stato_finale_mappa_cluster": [],
            "analisi_covariate": {}
        }

        pesi_patrimonio = {0: 1, 1: 2, 2: 5, 3: 10, 4: 25}
        storia_soddisfazione_adattativo = []

        mappa_accumulazione = {}
        for riga in range(4):
            for colonna in range(5):
                mappa_accumulazione[(riga, colonna)] = {
                    "soddisfazione_accumulata_fisso": 0.0,
                    "soddisfazione_accumulata_adattivo": 0.0
                }

        for r_idx, round_data in enumerate(scenario_data.get('rounds', [])):
            round_num = round_data.get('round')

            fisso_data = next((p for p in round_data.get('promoters_data', [])
                               if p['promotore_id'] == 'PROM-FISSO-1'), None)
            adapt_data = next((p for p in round_data.get('promoters_data', [])
                              if p['promotore_id'] == 'PROM-ADAPT-1'), None)

            sodd_fisso_round = 0.0
            sodd_adapt_round = 0.0
            mappa_fisso = {}

            if fisso_data:
                for strat in fisso_data.get('strategies', []):
                    coords = tuple(strat['cluster_coords'])
                    colonna = coords[1]
                    peso = pesi_patrimonio.get(colonna, 1)

                    delta_sodd = strat.get('performance_metrics', {}).get('delta_soddisfazione_medio', 0.0)

                    sodd_fisso_round += delta_sodd
                    metrics["soddisfazione_ponderata_fisso"] += (delta_sodd * peso)
                    mappa_fisso[coords] = strat.get('delta_fiducia_medio', 0.0)

                    if coords in mappa_accumulazione:
                        mappa_accumulazione[coords]["soddisfazione_accumulata_fisso"] += delta_sodd

                    prod_raw = strat.get('prodotto_suggerito', 'Sconosciuto')
                    prod = normalize_prodotto(prod_raw)

                    if prod not in metrics["efficacia_strategica_prodotti"]:
                        metrics["efficacia_strategica_prodotti"][prod] = {"utilizzi": 0, "soddisfazione_generata": 0.0}
                    metrics["efficacia_strategica_prodotti"][prod]["utilizzi"] += 1
                    metrics["efficacia_strategica_prodotti"][prod]["soddisfazione_generata"] += delta_sodd

            if adapt_data:
                for strat in adapt_data.get('strategies', []):
                    coords = tuple(strat['cluster_coords'])
                    colonna = coords[1]
                    peso = pesi_patrimonio.get(colonna, 1)
                    delta_sodd = strat.get('performance_metrics', {}).get('delta_soddisfazione_medio', 0.0)

                    sodd_adapt_round += delta_sodd
                    metrics["soddisfazione_ponderata_adattativo"] += (delta_sodd * peso)

                    if coords in mappa_accumulazione:
                        mappa_accumulazione[coords]["soddisfazione_accumulata_adattivo"] += delta_sodd

                    if coords in mappa_fisso:
                        delta_fid_adapt = strat.get('delta_fiducia_medio', 0.0)
                        if mappa_fisso[coords] < 0 and delta_fid_adapt >= 0:
                            metrics["clienti_salvati_dal_churn"] += 1

                    prod_raw = strat.get('prodotto_suggerito', 'Sconosciuto')
                    prod = normalize_prodotto(prod_raw)

                    if prod not in metrics["efficacia_strategica_prodotti"]:
                        metrics["efficacia_strategica_prodotti"][prod] = {"utilizzi": 0, "soddisfazione_generata": 0.0}
                    metrics["efficacia_strategica_prodotti"][prod]["utilizzi"] += 1
                    metrics["efficacia_strategica_prodotti"][prod]["soddisfazione_generata"] += delta_sodd

            metrics["valore_aggiunto_personalizzazione"] += (sodd_adapt_round - sodd_fisso_round)

            storia_soddisfazione_adattativo.append(sodd_adapt_round)
            if r_idx > 0:
                variazione = sodd_adapt_round - storia_soddisfazione_adattativo[r_idx - 1]
                metrics["velocita_variazione_soddisfazione"].append({
                    "round": round_num,
                    "variazione_netta": round(variazione, 4)
                })

        mappa_cluster_lista = []
        vantaggio_per_riga = {i: [] for i in range(4)}
        vantaggio_per_colonna = {j: [] for j in range(5)}

        for riga in range(4):
            for colonna in range(5):
                coords = (riga, colonna)
                acc_fisso = mappa_accumulazione[coords]["soddisfazione_accumulata_fisso"]
                acc_adattivo = mappa_accumulazione[coords]["soddisfazione_accumulata_adattivo"]
                vantaggio_netto = acc_adattivo - acc_fisso

                mappa_cluster_lista.append({
                    "riga": riga,
                    "colonna": colonna,
                    "soddisfazione_accumulata_fisso": round(acc_fisso, 4),
                    "soddisfazione_accumulata_adattivo": round(acc_adattivo, 4),
                    "vantaggio_netto_ia": round(vantaggio_netto, 4)
                })

                vantaggio_per_riga[riga].append(vantaggio_netto)
                vantaggio_per_colonna[colonna].append(vantaggio_netto)

        metrics["stato_finale_mappa_cluster"] = mappa_cluster_lista

        media_vantaggio_riga = {i: sum(vals) / len(vals) if vals else 0.0 for i, vals in vantaggio_per_riga.items()}
        media_vantaggio_colonna = {j: sum(vals) / len(vals) if vals else 0.0 for j, vals in vantaggio_per_colonna.items()}

        miglior_riga_adattivo = max(media_vantaggio_riga, key=media_vantaggio_riga.get)
        media_vantaggio_riga_adattivo = round(media_vantaggio_riga[miglior_riga_adattivo], 4)

        miglior_colonna_adattivo = max(media_vantaggio_colonna, key=media_vantaggio_colonna.get)
        media_vantaggio_colonna_adattivo = round(media_vantaggio_colonna[miglior_colonna_adattivo], 4)

        peggiore_riga_fisso = min(media_vantaggio_riga, key=media_vantaggio_riga.get)
        media_vantaggio_riga_fisso = round(media_vantaggio_riga[peggiore_riga_fisso], 4)

        peggiore_colonna_fisso = min(media_vantaggio_colonna, key=media_vantaggio_colonna.get)
        media_vantaggio_colonna_fisso = round(media_vantaggio_colonna[peggiore_colonna_fisso], 4)

        metrics["analisi_covariate"] = {
            "miglior_riga_adattivo": miglior_riga_adattivo,
            "media_vantaggio_riga_adattivo": media_vantaggio_riga_adattivo,
            "miglior_colonna_adattivo": miglior_colonna_adattivo,
            "media_vantaggio_colonna_adattivo": media_vantaggio_colonna_adattivo,
            "peggiore_riga_fisso": peggiore_riga_fisso,
            "media_vantaggio_riga_fisso": media_vantaggio_riga_fisso,
            "peggiore_colonna_fisso": peggiore_colonna_fisso,
            "media_vantaggio_colonna_fisso": media_vantaggio_colonna_fisso
        }

        metrics["valore_aggiunto_personalizzazione"] = round(metrics["valore_aggiunto_personalizzazione"], 4)
        metrics["soddisfazione_ponderata_fisso"] = round(metrics["soddisfazione_ponderata_fisso"], 4)
        metrics["soddisfazione_ponderata_adattativo"] = round(metrics["soddisfazione_ponderata_adattativo"], 4)
        for k in metrics["efficacia_strategica_prodotti"]:
            metrics["efficacia_strategica_prodotti"][k]["soddisfazione_generata"] = round(
                metrics["efficacia_strategica_prodotti"][k]["soddisfazione_generata"], 4
            )

        # Metric -1: tasso_conversione per promotore
        adapt_acc, adapt_tot = 0, 0
        fisso_acc, fisso_tot = 0, 0
        fisso_fid_sum, fisso_fid_count = 0.0, 0
        adapt_fid_sum, adapt_fid_count = 0.0, 0

        for round_data in scenario_data.get('rounds', []):
            for promoter_data in round_data.get('promoters_data', []):
                pid = promoter_data.get('promotore_id', '')
                for strategy in promoter_data.get('strategies', []):
                    acc = strategy.get('accettato', False)
                    fid = strategy.get('fiducia_media_post', 0.0)
                    if 'ADAPT' in pid:
                        adapt_tot += 1
                        adapt_fid_sum += fid
                        adapt_fid_count += 1
                        if acc: adapt_acc += 1
                    elif 'FISSO' in pid:
                        fisso_tot += 1
                        fisso_fid_sum += fid
                        fisso_fid_count += 1
                        if acc: fisso_acc += 1

        metrics["tasso_conversione_adapt_pct"] = round(adapt_acc / adapt_tot * 100, 1) if adapt_tot > 0 else 0.0
        metrics["tasso_conversione_fisso_pct"] = round(fisso_acc / fisso_tot * 100, 1) if fisso_tot > 0 else 0.0
        metrics["fiducia_media_adapt"] = round(adapt_fid_sum / adapt_fid_count * 100, 1) if adapt_fid_count > 0 else 0.0
        metrics["fiducia_media_fisso"] = round(fisso_fid_sum / fisso_fid_count * 100, 1) if fisso_fid_count > 0 else 0.0

        # Metric 0: delta_fiducia_cumulato
        fiducia_cumulata = {
            "adapt_delta_totale": 0.0,
            "fisso_delta_totale": 0.0,
            "adapt_conteggio": 0,
            "fisso_conteggio": 0
        }
        
        for round_data in scenario_data.get('rounds', []):
            for promoter_data in round_data.get('promoters_data', []):
                pid = promoter_data.get('promotore_id', '')
                for strategy in promoter_data.get('strategies', []):
                    delta = strategy.get('delta_fiducia_medio', 0.0)
                    if 'ADAPT' in pid:
                        fiducia_cumulata['adapt_delta_totale'] += delta
                        fiducia_cumulata['adapt_conteggio'] += 1
                    elif 'FISSO' in pid:
                        fiducia_cumulata['fisso_delta_totale'] += delta
                        fiducia_cumulata['fisso_conteggio'] += 1
                        
        adapt_count = fiducia_cumulata['adapt_conteggio']
        fisso_count = fiducia_cumulata['fisso_conteggio']
        
        metrics["fiducia_cumulata"] = {
            "adapt_delta_totale": round(fiducia_cumulata['adapt_delta_totale'], 4),
            "fisso_delta_totale": round(fiducia_cumulata['fisso_delta_totale'], 4),
            "adapt_delta_medio_per_round": round(fiducia_cumulata['adapt_delta_totale'] / adapt_count, 4) if adapt_count > 0 else 0.0,
            "fisso_delta_medio_per_round": round(fiducia_cumulata['fisso_delta_totale'] / fisso_count, 4) if fisso_count > 0 else 0.0,
            "vantaggio_adapt": round(fiducia_cumulata['adapt_delta_totale'] - fiducia_cumulata['fisso_delta_totale'], 4)
        }

        # Metric 1: mismatch_rate
        rifiutate = 0
        totale = 0
        for round_data in scenario_data.get('rounds', []):
            for promoter_data in round_data.get('promoters_data', []):
                for strategy in promoter_data.get('strategies', []):
                    totale += 1
                    if not strategy.get('accettato', False):
                        rifiutate += 1
        mismatch_rate = round(rifiutate / totale, 2) if totale > 0 else 0.0
        metrics["mismatch_rate"] = mismatch_rate

        # Metric 2: trend_fiducia
        trend_fiducia = []
        for round_data in scenario_data.get('rounds', []):
            round_num = round_data.get('round')
            fiducia_values = []
            for promoter_data in round_data.get('promoters_data', []):
                for strategy in promoter_data.get('strategies', []):
                    fiducia_media_post = strategy.get('fiducia_media_post', 0.0)
                    fiducia_values.append(fiducia_media_post)

            if fiducia_values:
                fiducia_media = round(sum(fiducia_values) / len(fiducia_values), 4)
            else:
                fiducia_media = 0.0

            trend_fiducia.append({'round': round_num, 'fiducia_media': fiducia_media})
        metrics["trend_fiducia"] = trend_fiducia

        # Metric 3: pct_clienti_sotto_soglia_fiducia
        try:
            with self._driver.session() as session:
                query_sotto_soglia = "MATCH (c:Cliente) WHERE c.fiducia_attuale < 0.5 RETURN count(c) as sotto_soglia"
                query_totale = "MATCH (c:Cliente) RETURN count(c) as totale"

                result_sotto = session.run(query_sotto_soglia).single()
                result_totale = session.run(query_totale).single()

                sotto_soglia = result_sotto['sotto_soglia'] if result_sotto else 0
                totale_clienti = result_totale['totale'] if result_totale else 0

                pct_clienti_sotto_soglia_fiducia = round(sotto_soglia / totale_clienti * 100, 2) if totale_clienti > 0 else 0.0
        except Exception as e:
            logger.warning(f"Error calculating pct_clienti_sotto_soglia_fiducia: {e}")
            pct_clienti_sotto_soglia_fiducia = 0.0

        metrics["pct_clienti_sotto_soglia_fiducia"] = pct_clienti_sotto_soglia_fiducia

        # Metric 4: matrice_strategica
        matrice_data = {}
        for round_data in scenario_data.get('rounds', []):
            for promoter_data in round_data.get('promoters_data', []):
                for strategy in promoter_data.get('strategies', []):
                    profilo = strategy.get('profilo_rischio_prevalente', 'Balanced')
                    prodotto = strategy.get('prodotto_suggerito', 'Altro')
                    key = (profilo, prodotto)

                    if key not in matrice_data:
                        matrice_data[key] = {
                            'num_decisioni': 0,
                            'adeguatezza_scores': [],
                            'accettati': [],
                            'delta_fiducia_values': []
                        }

                    matrice_data[key]['num_decisioni'] += 1
                    matrice_data[key]['adeguatezza_scores'].append(strategy.get('adeguatezza_score', 0.0))
                    matrice_data[key]['accettati'].append(1 if strategy.get('accettato', False) else 0)
                    matrice_data[key]['delta_fiducia_values'].append(strategy.get('delta_fiducia_medio', 0.0))

        matrice_strategica = []
        for (profilo, prodotto), data in matrice_data.items():
            adeguatezza_media = round(sum(data['adeguatezza_scores']) / len(data['adeguatezza_scores']), 2) if data['adeguatezza_scores'] else 0.0
            acceptance_rate = round(sum(data['accettati']) / len(data['accettati']), 2) if data['accettati'] else 0.0
            delta_fiducia_medio = round(sum(data['delta_fiducia_values']) / len(data['delta_fiducia_values']), 4) if data['delta_fiducia_values'] else 0.0

            matrice_strategica.append({
                'profilo': profilo,
                'prodotto': prodotto,
                'num_decisioni': data['num_decisioni'],
                'adeguatezza_media': adeguatezza_media,
                'acceptance_rate': acceptance_rate,
                'delta_fiducia_medio': delta_fiducia_medio
            })

        matrice_strategica.sort(key=lambda x: x['adeguatezza_media'], reverse=True)
        metrics["matrice_strategica"] = matrice_strategica

        return metrics

