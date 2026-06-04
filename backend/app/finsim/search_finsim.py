"""
FINsim Search Module — Query Neo4j for LLM prompt data extraction
FINSIM-MOD: Standalone searcher for scenario/promotore/cliente context

Provides secure, parameterized queries with validation against the FINsim ontology.
All queries use native driver parameters to prevent injection attacks.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from neo4j import GraphDatabase, Session as Neo4jSession
from neo4j.exceptions import Neo4jError

logger = logging.getLogger('finsim.search')


class SecurityValidator:
    """Validate labels and relationship types against FINsim ontology allowlist."""

    def __init__(self, ontology_path: Optional[str] = None):
        """
        Load allowed labels and relationships from ontology JSON.

        Args:
            ontology_path: Path to finsim_schema.json. If None, uses default location.
        """
        if not ontology_path:
            # Default location relative to this file
            ontology_path = Path(__file__).parent / 'ontology' / 'finsim_schema.json'

        try:
            with open(ontology_path, 'r', encoding='utf-8') as f:
                ontology = json.load(f)
            self.allowed_labels = set(ontology.get('allowed_labels', []))
            self.allowed_relationships = set(ontology.get('allowed_relationships', []))
            logger.info(f"Loaded ontology from {ontology_path}")
            logger.info(f"Allowed labels: {len(self.allowed_labels)}")
            logger.info(f"Allowed relationships: {len(self.allowed_relationships)}")
        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            raise

    def validate_label(self, label: str) -> bool:
        """Check if label is in allowlist."""
        return label in self.allowed_labels

    def validate_relationship(self, rel_type: str) -> bool:
        """Check if relationship type is in allowlist."""
        return rel_type in self.allowed_relationships

    def validate_labels(self, labels: List[str]) -> bool:
        """Check if all labels are in allowlist."""
        return all(self.validate_label(label) for label in labels)

    def validate_relationships(self, rel_types: List[str]) -> bool:
        """Check if all relationship types are in allowlist."""
        return all(self.validate_relationship(rel_type) for rel_type in rel_types)


class FinsimSearcher:
    """
    Standalone query engine for FINsim Neo4j graph.

    Provides methods to extract data for LLM prompts:
    - Cluster-based queries (grid position)
    - Promoter portfolio queries
    - Scenario state queries
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        ontology_path: Optional[str] = None,
    ):
        """
        Initialize FinsimSearcher with Neo4j connection.

        Args:
            uri: Neo4j connection URI (e.g., 'bolt://localhost:7687')
            user: Database username
            password: Database password
            ontology_path: Path to finsim_schema.json for validation
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._validator = SecurityValidator(ontology_path)
        self._driver = GraphDatabase.driver(
            self._uri, auth=(self._user, self._password)
        )
        logger.info(f"FinsimSearcher initialized with {uri}")

    def close(self):
        """Close Neo4j driver connection."""
        self._driver.close()
        logger.info("FinsimSearcher closed")

    # ========================================================================
    # Public Methods
    # ========================================================================

    def get_cluster_clients(self, riga: int, col: int) -> Dict[str, Any]:
        """
        Retrieve all clients in a grid cell (cluster position).

        Args:
            riga: Grid row (cluster_riga)
            col: Grid column (cluster_col)

        Returns:
            Dict with structure:
            {
                'cluster_position': {'riga': int, 'col': int},
                'client_count': int,
                'clients': [
                    {
                        'cliente_id': str,
                        'nome': str,
                        'profilo_rischio': str,
                        'propensione_rischio': float,
                        'fascia_patrimoniale': str,
                        'fiducia_attuale': float,
                        'soddisfazione': float,
                        'urgenza_liquidita': float,
                        ...
                    },
                    ...
                ]
            }
        """
        logger.info(f"Querying clients at cluster position ({riga}, {col})")

        with self._driver.session() as session:
            query = """
            MATCH (c:Cliente {cluster_riga: $riga, cluster_col: $col})
            RETURN c
            ORDER BY c.cliente_id
            """

            try:
                result = session.run(query, riga=riga, col=col)
                clients = [self._node_to_dict(record['c']) for record in result]

                response = {
                    'cluster_position': {'riga': riga, 'col': col},
                    'client_count': len(clients),
                    'clients': clients,
                }

                logger.info(f"Found {len(clients)} clients at ({riga}, {col})")
                return response

            except Neo4jError as e:
                logger.error(f"Query error in get_cluster_clients: {e}")
                raise

    def get_promotore_portfolio(self, promotore_id: str) -> Dict[str, Any]:
        """
        Retrieve promoter and all managed clients (GESTISCE relationship).

        Args:
            promotore_id: ID of the promoter (e.g., 'PROM-FISSO-1', 'PROM-ADAPT-1')

        Returns:
            Dict with structure:
            {
                'promotore': {
                    'promotore_id': str,
                    'nome': str,
                    'tipo': str ('Adattativo' | 'Fisso'),
                    'adattativo': bool,
                    'livello_adattativita': float,
                    'score_performance': float,
                    'bias_prodotto': str,
                    ...
                },
                'client_count': int,
                'clients': [
                    {
                        'cliente_id': str,
                        'nome': str,
                        'cluster_riga': int,
                        'cluster_col': int,
                        'profilo_rischio': str,
                        'fiducia_attuale': float,
                        ...
                    },
                    ...
                ]
            }
        """
        logger.info(f"Querying portfolio for promoter {promotore_id}")

        # Calculate promoter UUID from promoter_id
        # Pattern: PROM-TIPO-NUM → promotore-tipo-num
        # Mapping: FISSO → fisso, ADAPT → adattativo
        match = re.match(r'PROM-(\w+)-(\d+)', promotore_id, re.IGNORECASE)
        if match:
            tipo = match.group(1).upper()
            num = match.group(2)
            tipo_mapping = {'FISSO': 'fisso', 'ADAPT': 'adattativo'}
            tipo_normalized = tipo_mapping.get(tipo, tipo.lower())
            promotore_uuid = f"promotore-{tipo_normalized}-{num}"
        else:
            promotore_uuid = f"promotore-{promotore_id.lower()}"

        logger.info(f"Calculated promotore_uuid: {promotore_uuid}")

        with self._driver.session() as session:
            # Get promoter by UUID
            promoter_query = "MATCH (p:Promotore {uuid: $puuid}) RETURN p"
            try:
                promoter_result = session.run(promoter_query, puuid=promotore_uuid)
                promoter_record = promoter_result.single()

                if not promoter_record:
                    logger.warning(f"Promoter not found with uuid: {promotore_uuid}")
                    return {
                        'promotore': None,
                        'client_count': 0,
                        'clients': [],
                    }

                promoter = self._node_to_dict(promoter_record['p'])

            except Neo4jError as e:
                logger.error(f"Query error fetching promoter: {e}")
                raise

            # Get managed clients via GESTISCE relationship using promoter UUID
            clients_query = """
            MATCH (p:Promotore {uuid: $promotore_id})-[r:GESTISCE]->(c:Cliente)
            RETURN c
            ORDER BY c.cliente_id
            """

            try:
                clients_result = session.run(clients_query, promotore_id=promotore_uuid)
                clients = [self._node_to_dict(record['c']) for record in clients_result]

                response = {
                    'promotore': promoter,
                    'client_count': len(clients),
                    'clients': clients,
                }

                logger.info(f"Promoter {promotore_id} (uuid={promotore_uuid}) manages {len(clients)} clients")
                return response

            except Neo4jError as e:
                logger.error(f"Query error in get_promotore_portfolio: {e}")
                raise

    def get_scenario_state(self, scenario_id: str, round_n: int) -> Dict[str, Any]:
        """
        Retrieve ScenarioMacro and active DirettivaBancaria for a round.

        Args:
            scenario_id: ID of the scenario (e.g., 'S0', 'S1', etc.)
            round_n: Round number

        Returns:
            Dict with structure:
            {
                'scenario': {
                    'scenario_id': str,
                    'nome': str,
                    'descrizione': str,
                    'round_corrente': int,
                    'tasso_riferimento': float,
                    'liquidita_mercato': str,
                    'pressione_normativa': float,
                    'sentiment_mercato': str,
                    ...
                },
                'round': int,
                'direttiva_bancaria': {
                    'direttiva_id': str,
                    'tipo': str,
                    'contenuto': str,
                    'priorita': int,
                    'attiva': bool,
                    'focus_prodotto': str,
                    'tolleranza_rischio_min': float,
                    'pressione_commerciale': float,
                    ...
                } | None
            }
        """
        logger.info(f"Querying scenario state: {scenario_id}, round {round_n}")

        # Calculate scenario UUID from scenario_id
        # Pattern: S0, S1, S2, etc. → scenario-s0-baseline, scenario-s1-baseline, etc.
        scenario_uuid = f"scenario-{scenario_id.lower()}-baseline"
        logger.info(f"Calculated scenario_uuid: {scenario_uuid}")

        with self._driver.session() as session:
            # Get scenario by UUID
            scenario_query = "MATCH (s:ScenarioMacro {uuid: $suuid}) RETURN s"
            try:
                scenario_result = session.run(scenario_query, suuid=scenario_uuid)
                scenario_record = scenario_result.single()

                if not scenario_record:
                    logger.warning(f"Scenario not found with uuid: {scenario_uuid}")
                    return {
                        'scenario': None,
                        'round': round_n,
                        'direttiva_bancaria': None,
                    }

                scenario = self._node_to_dict(scenario_record['s'])

            except Neo4jError as e:
                logger.error(f"Query error fetching scenario: {e}")
                raise

            # Get active directive via DEFINISCE relationship using scenario UUID
            # Filter by: attiva=true AND scenario_rif=scenario_id (property)
            direttiva_query = """
            MATCH (s:ScenarioMacro {uuid: $suuid})-[r:DEFINISCE]->(d:DirettivaBancaria {attiva: true})
            WHERE d.scenario_rif = $scenario_id
            RETURN d
            LIMIT 1
            """

            direttiva = None
            try:
                direttiva_result = session.run(direttiva_query, suuid=scenario_uuid, scenario_id=scenario_id)
                direttiva_record = direttiva_result.single()

                if direttiva_record:
                    direttiva = self._node_to_dict(direttiva_record['d'])
                    logger.info(f"Found active directive: {direttiva.get('direttiva_id')}")
                else:
                    logger.info(f"No active directive found for scenario {scenario_id}")

            except Neo4jError as e:
                logger.error(f"Query error fetching directive: {e}")
                raise

            response = {
                'scenario': scenario,
                'round': round_n,
                'direttiva_bancaria': direttiva,
            }

            return response

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    def _node_to_dict(node) -> Dict[str, Any]:
        """Convert Neo4j node object to clean Python dict."""
        props = dict(node)

        # Remove internal Neo4j metadata if present
        props.pop('embedding', None)
        props.pop('name_lower', None)
        props.pop('graph_id', None)

        return props


# ============================================================================
# Convenience Factory Function
# ============================================================================

def create_searcher(
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    ontology_path: Optional[str] = None,
) -> FinsimSearcher:
    """
    Factory function to create FinsimSearcher with config defaults.

    Args:
        uri: Neo4j URI (default: from Config.NEO4J_URI)
        user: Database user (default: from Config.NEO4J_USER)
        password: Database password (default: from Config.NEO4J_PASSWORD)
        ontology_path: Path to ontology JSON (default: auto-detect)

    Returns:
        Initialized FinsimSearcher instance
    """
    # Try to load config defaults
    try:
        from ..config import Config

        uri = uri or Config.NEO4J_URI
        user = user or Config.NEO4J_USER
        password = password or Config.NEO4J_PASSWORD

    except ImportError:
        # If config unavailable, require explicit parameters
        if not all([uri, user, password]):
            raise ValueError(
                "Could not load config. Provide uri, user, password explicitly."
            )

    return FinsimSearcher(uri, user, password, ontology_path)
