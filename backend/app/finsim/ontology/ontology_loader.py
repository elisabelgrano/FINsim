"""
OntologyLoader — Bulk insert di nodi e relazioni FINsim su Neo4j.
Validazione rigorosa contro finsim_schema.json, zero concatenazioni di parametri.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from neo4j import GraphDatabase

from backend.app.config import Config

logger = logging.getLogger('finsim.ontology_loader')


class OntologyLoader:
    """
    Carica bulk nodi e relazioni FINsim su Neo4j.

    Validazione rigorosa: ogni label e relationship deve essere nell'allowlist
    dello schema prima di essere utilizzata. Query sempre parametrizzate.
    Label dinamiche validate rigorosamente, usate SOLO dopo validazione.
    """

    def __init__(
        self,
        schema_path: Optional[str] = None,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Inizializza loader e carica schema.

        Args:
            schema_path: Path a finsim_schema.json. Se None, usa default.
            uri: Neo4j connection URI. Se None, usa Config.NEO4J_URI.
            user: Neo4j user. Se None, usa Config.NEO4J_USER.
            password: Neo4j password. Se None, usa Config.NEO4J_PASSWORD.
        """
        self._schema: Dict[str, Any] = {}
        self._allowed_labels: List[str] = []
        self._allowed_relationships: List[str] = []

        # Carica schema JSON
        schema_file = schema_path or self._get_default_schema_path()
        self._load_schema(schema_file)

        # Connetti a Neo4j
        self._uri = uri or Config.NEO4J_URI
        self._user = user or Config.NEO4J_USER
        self._password = password or Config.NEO4J_PASSWORD
        self._driver = GraphDatabase.driver(
            self._uri, auth=(self._user, self._password)
        )

        logger.info(f"OntologyLoader inizializzato, connesso a {self._uri}")

    def _get_default_schema_path(self) -> str:
        """Ritorna il path default a finsim_schema.json."""
        current_dir = Path(__file__).parent
        return str(current_dir / 'finsim_schema.json')

    def _load_schema(self, schema_path: str) -> None:
        """Carica e valida lo schema JSON."""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)

            self._allowed_labels = self._schema.get('allowed_labels', [])
            self._allowed_relationships = self._schema.get('allowed_relationships', [])

            if not self._allowed_labels or not self._allowed_relationships:
                raise ValueError("Schema non contiene allowed_labels o allowed_relationships")

            logger.info(
                f"Schema caricato da {schema_path}: "
                f"{len(self._allowed_labels)} label, "
                f"{len(self._allowed_relationships)} relationship"
            )
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Errore caricamento schema: {e}")
            raise

    def validate_label(self, label: str) -> bool:
        """
        Verifica che label sia in allowed_labels.

        Args:
            label: Label da validare

        Returns:
            True se valida, False altrimenti
        """
        is_valid = label in self._allowed_labels
        if not is_valid:
            logger.warning(f"Label non valida: '{label}' (allowed: {self._allowed_labels})")
        return is_valid

    def validate_relationship(self, rel_type: str) -> bool:
        """
        Verifica che relationship type sia in allowed_relationships.

        Args:
            rel_type: Tipo di relazione da validare

        Returns:
            True se valida, False altrimenti
        """
        is_valid = rel_type in self._allowed_relationships
        if not is_valid:
            logger.warning(
                f"Relationship non valida: '{rel_type}' (allowed: {self._allowed_relationships})"
            )
        return is_valid

    def create_nodes_bulk(
        self,
        graph_id: str,
        nodes_data: List[Dict[str, Any]],
    ) -> Tuple[int, List[str]]:
        """
        Bulk insert nodi su Neo4j.

        Args:
            graph_id: ID del grafo
            nodes_data: Lista di nodi con formato:
                {
                    'uuid': str (opzionale, generato se manca),
                    'label': str,  # Dalla allowed_labels
                    'properties': Dict[str, Any]
                }

        Returns:
            (num_created, errors_list)
        """
        errors: List[str] = []
        created_count = 0

        if not nodes_data:
            logger.info("Nessun nodo da caricare")
            return 0, []

        # Valida tutte le label PRIMA di procedere
        for idx, node in enumerate(nodes_data):
            label = node.get('label', '')
            if not label:
                errors.append(f"Nodo {idx}: 'label' non fornita")
            elif not self.validate_label(label):
                errors.append(f"Nodo {idx}: label '{label}' non valida")

        if errors:
            logger.error(f"Validazione label fallita: {len(errors)} errori")
            return 0, errors

        # Prepara batch per UNWIND
        nodes_batch = []
        for node in nodes_data:
            props = node.get('properties', {})
            node_uuid = node.get('uuid') or str(uuid.uuid4())
            nodes_batch.append({
                'uuid': node_uuid,
                'label': node.get('label'),
                'properties': props,
                'attributes_json': json.dumps(props, ensure_ascii=False),
            })

        # Inserisce nodi base + aggiunge label validate
        def _create_nodes(tx):
            now = datetime.now(timezone.utc).isoformat()
            inserted = 0

            # Query 1: Merge tutti i nodi come Entity base + proprietà dal properties dict
            # Usa MERGE per idempotenza: se eseguito più volte, aggiorna o preserva
            query_base = """
            UNWIND $nodes_batch AS node_data
            MERGE (n:Entity {uuid: node_data.uuid})
            SET n.graph_id = $graph_id,
                n.name = node_data.properties.nome,
                n.summary = node_data.properties.descrizione,
                n.attributes_json = node_data.attributes_json,
                n.created_at = $now
            SET n += node_data.properties
            RETURN count(n) AS created
            """

            result = tx.run(
                query_base,
                nodes_batch=nodes_batch,
                graph_id=graph_id,
                now=now,
            )
            record = result.single()
            inserted = record['created'] if record else len(nodes_batch)

            # Query 2: Aggiunge label specifiche (per ogni label distinta)
            # La label è VALIDATA, quindi è sicuro usarla in f-string
            unique_labels = set(node['label'] for node in nodes_batch)
            for label in unique_labels:
                label_uuids = [
                    node['uuid'] for node in nodes_batch
                    if node['label'] == label
                ]

                # IMPORTANTE: label è stato validato, f-string è sicuro
                query_label = f"""
                MATCH (n:Entity {{graph_id: $graph_id}})
                WHERE n.uuid IN $uuids
                SET n:`{label}`
                """

                tx.run(
                    query_label,
                    graph_id=graph_id,
                    uuids=label_uuids,
                )
                logger.debug(f"Aggiunta label '{label}' a {len(label_uuids)} nodi")

            return inserted

        try:
            with self._driver.session() as session:
                created_count = session.execute_write(_create_nodes)
                logger.info(f"Creati {created_count} nodi con label validate")
        except Exception as e:
            msg = f"Bulk insert nodi fallito: {str(e)}"
            errors.append(msg)
            logger.error(msg)

        return created_count, errors

    def create_relationships_bulk(
        self,
        graph_id: str,
        relationships_data: List[Dict[str, Any]],
    ) -> Tuple[int, List[str]]:
        """
        Bulk insert relazioni su Neo4j.

        Args:
            graph_id: ID del grafo
            relationships_data: Lista di relazioni con formato:
                {
                    'uuid': str (opzionale, generato se manca),
                    'type': str,  # Dalla allowed_relationships
                    'source_uuid': str,
                    'target_uuid': str,
                    'properties': Dict[str, Any]
                }

        Returns:
            (num_created, errors_list)
        """
        errors: List[str] = []
        created_count = 0

        if not relationships_data:
            logger.info("Nessuna relazione da caricare")
            return 0, []

        # Valida tutti i tipi di relationship PRIMA di procedere
        for idx, rel in enumerate(relationships_data):
            rel_type = rel.get('type', '')
            if not rel_type:
                errors.append(f"Relazione {idx}: 'type' non fornito")
            elif not self.validate_relationship(rel_type):
                errors.append(f"Relazione {idx}: tipo '{rel_type}' non valido")

            # Valida anche source/target UUID
            if not rel.get('source_uuid'):
                errors.append(f"Relazione {idx}: 'source_uuid' mancante")
            if not rel.get('target_uuid'):
                errors.append(f"Relazione {idx}: 'target_uuid' mancante")

        if errors:
            logger.error(f"Validazione relationship fallita: {len(errors)} errori")
            return 0, errors

        # Prepara batch per UNWIND
        rels_batch = []
        for rel in relationships_data:
            props = rel.get('properties', {})
            rel_uuid = rel.get('uuid') or str(uuid.uuid4())
            rels_batch.append({
                'uuid': rel_uuid,
                'type': rel.get('type'),
                'source_uuid': rel.get('source_uuid'),
                'target_uuid': rel.get('target_uuid'),
                'properties': props,
                'attributes_json': json.dumps(props, ensure_ascii=False),
                'fact': props.get('fact', ''),
            })

        # Inserisce relazioni
        def _create_relationships(tx):
            now = datetime.now(timezone.utc).isoformat()
            created = 0

            # Crea relazioni per ogni tipo validato, raggruppando per efficienza
            rel_types = set(rel['type'] for rel in rels_batch)

            for rel_type in rel_types:
                # Filtra batch per questo tipo di relazione
                batch_for_type = [r for r in rels_batch if r['type'] == rel_type]

                # Genera query dinamica con tipo di relazione validato (sicuro perché validato)
                # Usa MERGE per idempotenza: se eseguito più volte, preserva esistenti
                # IMPORTANTE: rel_type è stato validato contro allowed_relationships
                query = f"""
                UNWIND $batch AS rel_data
                MATCH (src:Entity {{uuid: rel_data.source_uuid}})
                MATCH (tgt:Entity {{uuid: rel_data.target_uuid}})
                MERGE (src)-[r:{rel_type} {{uuid: rel_data.uuid}}]->(tgt)
                SET r.graph_id = $graph_id,
                    r.name = rel_data.type,
                    r.fact = rel_data.fact,
                    r.attributes_json = rel_data.attributes_json,
                    r.created_at = $now,
                    r.valid_at = null,
                    r.invalid_at = null,
                    r.expired_at = null,
                    r.episode_ids = []
                RETURN count(r) AS created
                """

                result = tx.run(
                    query,
                    batch=batch_for_type,
                    graph_id=graph_id,
                    now=now,
                )
                record = result.single()
                created += record['created'] if record else len(batch_for_type)

            return created

        try:
            with self._driver.session() as session:
                created_count = session.execute_write(_create_relationships)
                logger.info(f"Create {created_count} relazioni")
        except Exception as e:
            msg = f"Bulk insert relazioni fallito: {str(e)}"
            errors.append(msg)
            logger.error(msg)

        return created_count, errors

    def load(
        self,
        graph_id: str,
        nodes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Entry point: carica nodi e relazioni in bulk.

        Args:
            graph_id: ID del grafo di destinazione
            nodes: Lista di nodi
            relationships: Lista di relazioni

        Returns:
            {
                'nodes_created': int,
                'relationships_created': int,
                'errors': List[str],
                'success': bool
            }
        """
        logger.info(
            f"Inizio caricamento: {len(nodes)} nodi, "
            f"{len(relationships)} relazioni, graph_id={graph_id}"
        )

        all_errors: List[str] = []
        nodes_created = 0
        rels_created = 0

        # Carica nodi
        nodes_created, node_errors = self.create_nodes_bulk(graph_id, nodes)
        all_errors.extend(node_errors)

        # Carica relazioni (anche se alcuni nodi hanno fallito)
        rels_created, rel_errors = self.create_relationships_bulk(graph_id, relationships)
        all_errors.extend(rel_errors)

        result = {
            'nodes_created': nodes_created,
            'relationships_created': rels_created,
            'errors': all_errors,
            'success': len(all_errors) == 0,
        }

        logger.info(
            f"Caricamento completato: {nodes_created} nodi, "
            f"{rels_created} relazioni, {len(all_errors)} errori"
        )

        return result

    def close(self) -> None:
        """Chiude la connessione Neo4j."""
        if self._driver:
            self._driver.close()
            logger.info("Connessione Neo4j chiusa")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
