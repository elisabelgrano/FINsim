"""
SimulationEngine — Phase 4 orchestration for FINsim round loop
FINSIM-MOD: Standalone backend simulation engine with cluster optimization

Manages round advancement, promoter strategy generation, decision persistence,
and client reaction calculation using Neo4j queries and OllamaClient integration.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4

from neo4j import GraphDatabase, Session as Neo4jSession
from neo4j.exceptions import Neo4jError
from sklearn import metrics

from backend.app.finsim.agents.promotore_agent import PromotoreAgent
from backend.app.finsim.llm.ollama_client import OllamaClient
from backend.app.finsim.search_finsim import FinsimSearcher

logger = logging.getLogger('finsim.simulation_engine')


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
            'promoters_data': []
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

                try:
                    logger.info(f"Processing promoter: {promotore_id} (uuid={promotore_uuid})")

                    # Get active clusters for this promoter
                    active_clusters = self._get_active_clusters(session, promotore_uuid)
                    logger.info(f"  → {len(active_clusters)} active clusters")
                    result['total_clusters'] += len(active_clusters)

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
                            )

                            if strategy_result.get('error'):
                                logger.warning(
                                    f"    Strategy generation failed: {strategy_result['error']}"
                                )
                                result['errors'].append(
                                    f"Cluster ({riga}, {col}): {strategy_result['error']}"
                                )
                                continue

                            # Extract strategy details
                            strategy_json = {
                                'strategia': strategy_result['strategia'],
                                'approccio_comunicativo': strategy_result['approccio_comunicativo'],
                                'prodotto_suggerito': strategy_result['prodotto_suggerito'],
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

                            # Calculate client reactions
                            prodotto_suggerito = strategy_result['prodotto_suggerito']
                            clients_updated = self.calcola_reazione_clienti(
                                session=session,
                                promotore_uuid=promotore_uuid,
                                riga=riga,
                                col=col,
                                prodotto_suggerito=prodotto_suggerito,
                            )

                            result['clients_updated'] += clients_updated
                            logger.info(f"    Updated {clients_updated} clients")
                            
                            metrics_query = """
                            MATCH (p:Promotore {uuid: $promotore_uuid})-[g:GESTISCE]->(c:Cliente)-[:APPARTIENE_A]->(clu:ClusterProfilo)
                            WHere c.cluster_riga = $riga AND c.cluster_col = $col
                            RETURN
                                avg(c.fiducia_attuale - c.fiducia_iniziale) as avg_delta_fiducia,
                                avg(c.soddisfazione - 0.5) as avg_delta_soddisfazione
                            """
                            metrics_res = session.run(metrics_query, promotore_uuid=promotore_uuid, riga=riga, col=col).single()
                            
                            delta_fiducia = round(metrics_res['avg_delta_fiducia'], 4) if metrics_res and metrics_res['avg_delta_fiducia'] is not None else 0.0
                            delta_soddisfazione = round(metrics_res['avg_delta_soddisfazione'], 4) if metrics_res and metrics_res['avg_delta_soddisfazione'] is not None else 0.0
                            
                            promoter_data_for_mongo['strategies'].append({
                                'cluster_coords': [riga, col],
                                'clients_in_cluster': clients_updated,
                                'llm_strategy': strategy_result['strategia'],
                                'approccio_comunicativo': strategy_result['approccio_comunicativo'],
                                'prodotto_suggerito': strategy_result['prodotto_suggerito'],
                                'performance_metrics': {
                                    'delta_fiducia_medio': delta_fiducia,
                                    'delta_soddisfazione_medio': delta_soddisfazione
                                }
                            })

                        except Exception as e:
                            error_msg = f"Cluster ({riga}, {col}): {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            result['errors'].append(error_msg)

                    result['promoters_processed'] += 1
                    
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
        session,
        promotore_uuid: str,
        riga: int,
        col: int,
        prodotto_suggerito: str,
    ) -> int:
        try:
            # Map product risk
            prodotto_lower = prodotto_suggerito.lower()
            if 'azion' in prodotto_lower or 'equity' in prodotto_lower:
                rischio_prodotto = 'ALTO'
            elif 'obblig' in prodotto_lower or 'bond' in prodotto_lower:
                rischio_prodotto = 'MEDIO'
            else:
                rischio_prodotto = 'BASSO'

            # Get all clients in cluster managed by this promoter
            # ORA CHIEDIAMO ANCHE LA SODDISFAZIONE!
            get_clients_query = """
            MATCH (p:Promotore {uuid: $promotore_uuid})-[:GESTISCE]->(c:Cliente)
            WHERE c.cluster_riga = $riga AND c.cluster_col = $col
            RETURN c.uuid as client_uuid, c.profilo_rischio as profilo_rischio,
                   c.fiducia_attuale as fiducia_attuale, c.soddisfazione as soddisfazione
            """

            clients_result = session.run(
                get_clients_query, promotore_uuid=promotore_uuid, riga=riga, col=col
            )
            clients = list(clients_result)
            clients_updated = 0

            for client in clients:
                client_uuid = client['client_uuid']
                profilo_rischio = client['profilo_rischio']
                fiducia_attuale = client['fiducia_attuale'] or 0.5
                soddisfazione = client['soddisfazione'] or 0.5

                # Map client risk
                if profilo_rischio in ['Aggressivo', 'Growth']:
                    rischio_cliente = 'ALTO'
                elif profilo_rischio in ['Moderato', 'Balanced']:
                    rischio_cliente = 'MEDIO'
                else:
                    rischio_cliente = 'BASSO'

                # Calcoliamo i Delta
                delta_fiducia = self._calcola_delta_fiducia(rischio_prodotto, rischio_cliente)
                
                # Leghiamo la soddisfazione alla fiducia in modo logico (+10% di delta fiducia = +5% soddisfazione)
                delta_soddisfazione = delta_fiducia * 0.5 

                # Apply update (assicurandoci che stiano tra 0 e 1)
                fiducia_nuova = max(0.0, min(1.0, fiducia_attuale + delta_fiducia))
                soddisf_nuova = max(0.0, min(1.0, soddisfazione + delta_soddisfazione))

                # Update BOTH properties in DB!
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
    
    def _calcola_metriche_business(self, scenario_data):
        """
        Calcola i KPI di business aggregando i dati storici dei round simulati.
        """
        metrics = {
            "valore_aggiunto_personalizzazione": 0.0,
            "soddisfazione_ponderata_fisso": 0.0,
            "soddisfazione_ponderata_adattivo": 0.0,
            "clienti_salvati_dal_churn": 0,
            "velocita_variazione_soddisfazione": [],
            "efficacia_strategica_prodotti": {}
        }
        
        # pesi per fascia patrimoniale
        pesi_patrimonio = {0: 1, 1: 2, 2: 5, 3: 10, 4: 25}
        storia_soddisfazione_adattivo = []
        
        for r_idx, round_data in enumerate(scenario_data.get('rounds', [])):
            round_num = round_data.get('round')
            
            fisso_data = next((p for p in round_data.get('promoters_data', []) if p['promotore_id'] == 'PROM-FISSO-1'), None)
            adapt_data = next((p for p in round_data.get('promoters_data', []) if p['promotore_id'] == 'PROM-ADATTIVO-1'), None)
            
            sodd_fisso_round = 0.0
            sodd_adapt_round = 0.0
            mappa_fisso = {}
            
            # calcoli promotore fisso
            if fisso_data:
                for strat in fisso_data.get('strategies', []):
                    coords = tuple(strat['cluster_coords'])
                    col = coords[1]
                    peso = pesi_patrimonio.get(col, 1)
                    
                    # estrae delta json
                    delta_sodd = strat.get('performance_metrics', {}).get('delta_soddisfazione_medio', 0.0)
                
                    sodd_fisso_round += delta_sodd
                    metrics["soddisfazione_ponderata_fisso"] += (delta_sodd * peso)
                    mappa_fisso[coords] = delta_sodd
                    
                    # Gestione prodotto
                    prod_raw = strat.get('prodotto_suggerito', 'Sconosciuto')
                    if isinstance(prod_raw, list) and len(prod_raw) > 0 and isinstance(prod_raw[0], dict):
                        prod = prod_raw[0].get('nome_prodotto', 'Misto')
                    else:
                        prod = str(prod_raw)
                        
                    if prod not in metrics["efficacia_strategica_prodotti"]:
                        metrics["efficacia_strategica_prodotti"][prod] = {"utilizzi": 0, "soddisfazione_generata": 0.0}
                    metrics["efficacia_strategica_prodotti"][prod]["utilizzi"] += 1
                    metrics["efficacia_strategica_prodotti"][prod]["soddisfazione_generata"] += delta_sodd

            # Calcoli Promotore Adattativo
            if adapt_data:
                for strat in adapt_data.get('strategies', []):
                    coords = tuple(strat['cluster_coords'])
                    col = coords[1]
                    peso = pesi_patrimonio.get(col, 1)
                    delta_sodd = strat.get('performance_metrics', {}).get('delta_soddisfazione_medio', 0.0)
                    
                    sodd_adapt_round += delta_sodd
                    metrics["soddisfazione_ponderata_adattivo"] += (delta_sodd * peso)
                    
                    # METRICA: Salvataggio Churn
                    if coords in mappa_fisso:
                        if mappa_fisso[coords] < 0 and delta_sodd >= 0:
                            metrics["clienti_salvati_dal_churn"] += 1
                            
                    # Gestione Prodotto Adattativo
                    prod_raw = strat.get('prodotto_suggerito', 'Sconosciuto')
                    if isinstance(prod_raw, list) and len(prod_raw) > 0 and isinstance(prod_raw[0], dict):
                        prod = prod_raw[0].get('nome_prodotto', 'Misto')
                    else:
                        prod = str(prod_raw)

                    if prod not in metrics["efficacia_strategica_prodotti"]:
                        metrics["efficacia_strategica_prodotti"][prod] = {"utilizzi": 0, "soddisfazione_generata": 0.0}
                    metrics["efficacia_strategica_prodotti"][prod]["utilizzi"] += 1
                    metrics["efficacia_strategica_prodotti"][prod]["soddisfazione_generata"] += delta_sodd

            # 3. Valore Aggiunto Personalizzazione
            metrics["valore_aggiunto_personalizzazione"] += (sodd_adapt_round - sodd_fisso_round)

            # 4. Velocità di Variazione (Momentum)
            storia_soddisfazione_adattivo.append(sodd_adapt_round)
            if r_idx > 0:
                variazione = sodd_adapt_round - storia_soddisfazione_adattivo[r_idx - 1]
                metrics["velocita_variazione_soddisfazione"].append({
                    "round": round_num,
                    "variazione_netta": round(variazione, 4)
                })

        # Pulizia finale dei decimali
        metrics["valore_aggiunto_personalizzazione"] = round(metrics["valore_aggiunto_personalizzazione"], 4)
        metrics["soddisfazione_ponderata_fisso"] = round(metrics["soddisfazione_ponderata_fisso"], 4)
        metrics["soddisfazione_ponderata_adattivo"] = round(metrics["soddisfazione_ponderata_adattivo"], 4)
        for k in metrics["efficacia_strategica_prodotti"]:
            metrics["efficacia_strategica_prodotti"][k]["soddisfazione_generata"] = round(metrics["efficacia_strategica_prodotti"][k]["soddisfazione_generata"], 4)

        return metrics                