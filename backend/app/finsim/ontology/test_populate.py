"""
test_populate.py — Verifica struttura dati S0 senza connessione Neo4j.
Testa generazione nodi, relazioni, validazione schema.
"""

import logging
from typing import Dict, Any, List

from .ontology_loader import OntologyLoader
from .populate_finsim import (
    generate_scenario_macro,
    generate_direttiva_bancaria,
    generate_promotori,
    generate_cluster_profili,
    generate_clienti,
    generate_relationships,
)

logger = logging.getLogger('finsim.test_populate')


def test_data_generation() -> bool:
    """Testa che la generazione di dati non fallisca e ritorna strutture valide."""
    logger.info("Test 1: Generazione dati sintetici...")

    try:
        scenario = generate_scenario_macro()
        assert scenario['label'] == 'ScenarioMacro', "Label scenario non valida"
        assert scenario['uuid'], "UUID scenario mancante"
        assert scenario['properties']['scenario_id'] == 'S0', "ID scenario non valido"
        logger.info("  ✓ ScenarioMacro")

        direttiva = generate_direttiva_bancaria()
        assert direttiva['label'] == 'DirettivaBancaria', "Label direttiva non valida"
        assert direttiva['uuid'], "UUID direttiva mancante"
        logger.info("  ✓ DirettivaBancaria")

        promotori = generate_promotori()
        assert len(promotori) == 3, "Numero promotori non valido"
        assert promotori[2]['properties']['adattativo'] is True, "Promotore adattativo non segnalato"
        logger.info("  ✓ 3 Promotori (2 Fissi, 1 Adattativo)")

        clusters = generate_cluster_profili()
        assert len(clusters) == 20, "Numero cluster non valido"
        logger.info("  ✓ 20 ClusterProfilo (4x5)")

        clienti = generate_clienti(100)
        assert len(clienti) == 100, "Numero clienti non valido"
        # Verifica distribuzione cluster
        client_clusters = set()
        for c in clienti:
            row = c['properties']['cluster_riga']
            col = c['properties']['cluster_col']
            client_clusters.add((row, col))
        assert len(client_clusters) == 20, "Clienti non distribuiti in 20 cluster"
        logger.info("  ✓ 100 Clienti distribuiti uniformemente")

        relationships = generate_relationships()
        assert len(relationships) > 0, "Nessuna relazione generata"
        logger.info(f"  ✓ {len(relationships)} Relazioni")

        return True

    except AssertionError as e:
        logger.error(f"  ✗ Asserzione fallita: {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Errore: {e}")
        return False


def test_schema_validation() -> bool:
    """Testa che OntologyLoader valida correttamente label e relationship."""
    logger.info("Test 2: Validazione schema...")

    try:
        loader = OntologyLoader()

        # Test label valide
        for label in ['ScenarioMacro', 'DirettivaBancaria', 'Promotore', 'Cliente', 'ClusterProfilo']:
            assert loader.validate_label(label), f"Label '{label}' dovrebbe essere valida"
        logger.info("  ✓ Label valide riconosciute")

        # Test label non valide
        assert not loader.validate_label('InvalidLabel'), "Label non valida dovrebbe essere rifiutata"
        logger.info("  ✓ Label non valide rifiutate")

        # Test relationship valide
        for rel_type in ['DEFINISCE', 'OPERA_IN', 'EMETTE', 'GESTISCE', 'APPARTIENE_A']:
            assert loader.validate_relationship(rel_type), f"Rel '{rel_type}' dovrebbe essere valida"
        logger.info("  ✓ Relationship valide riconosciute")

        # Test relationship non valide
        assert not loader.validate_relationship('INVALID_REL'), "Rel non valida dovrebbe essere rifiutata"
        logger.info("  ✓ Relationship non valide rifiutate")

        loader.close()
        return True

    except AssertionError as e:
        logger.error(f"  ✗ Asserzione fallita: {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Errore: {e}")
        return False


def test_node_structure() -> bool:
    """Testa che i nodi abbiano struttura corretta per il caricamento."""
    logger.info("Test 3: Struttura nodi...")

    try:
        all_nodes = []
        all_nodes.append(generate_scenario_macro())
        all_nodes.append(generate_direttiva_bancaria())
        all_nodes.extend(generate_promotori())
        all_nodes.extend(generate_cluster_profili())
        all_nodes.extend(generate_clienti(10))  # Test subset

        for idx, node in enumerate(all_nodes):
            assert 'uuid' in node, f"Nodo {idx}: 'uuid' mancante"
            assert 'label' in node, f"Nodo {idx}: 'label' mancante"
            assert 'properties' in node, f"Nodo {idx}: 'properties' mancante"
            assert isinstance(node['properties'], dict), f"Nodo {idx}: 'properties' non dict"

        logger.info(f"  ✓ {len(all_nodes)} nodi con struttura valida")
        return True

    except AssertionError as e:
        logger.error(f"  ✗ {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Errore: {e}")
        return False


def test_relationship_structure() -> bool:
    """Testa che le relazioni abbiano struttura corretta."""
    logger.info("Test 4: Struttura relazioni...")

    try:
        relationships = generate_relationships()

        for idx, rel in enumerate(relationships):
            assert 'uuid' in rel, f"Rel {idx}: 'uuid' mancante"
            assert 'type' in rel, f"Rel {idx}: 'type' mancante"
            assert 'source_uuid' in rel, f"Rel {idx}: 'source_uuid' mancante"
            assert 'target_uuid' in rel, f"Rel {idx}: 'target_uuid' mancante"
            assert 'properties' in rel, f"Rel {idx}: 'properties' mancante"

        logger.info(f"  ✓ {len(relationships)} relazioni con struttura valida")
        return True

    except AssertionError as e:
        logger.error(f"  ✗ {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Errore: {e}")
        return False


def run_all_tests() -> bool:
    """Esegue tutti i test e ritorna True se tutto passa."""
    logger.info("="*70)
    logger.info("Avvio test Suite populate_finsim")
    logger.info("="*70)

    results = [
        test_data_generation(),
        test_schema_validation(),
        test_node_structure(),
        test_relationship_structure(),
    ]

    logger.info("="*70)
    passed = sum(results)
    total = len(results)
    logger.info(f"Risultati: {passed}/{total} test passati")
    logger.info("="*70)

    return all(results)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    success = run_all_tests()
    exit(0 if success else 1)
