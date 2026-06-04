"""
populate_finsim.py — Genera dati S0 Baseline e popola Neo4j via OntologyLoader.
Dati sintetici deterministici senza LLM/ThreadPool: topologia pura.
"""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone

from backend.app.finsim.ontology.ontology_loader import OntologyLoader

logger = logging.getLogger('finsim.populate')


def generate_scenario_macro() -> Dict[str, Any]:
    """Genera ScenarioMacro per S0 Baseline Neutro."""
    return {
        'uuid': 'scenario-s0-baseline',
        'label': 'ScenarioMacro',
        'properties': {
            'scenario_id': 'S0',
            'nome': 'S0 - Baseline Neutro / Reale',
            'descrizione': 'Tasso 2.0%, tensione geopolitica attiva, sentiment ansioso',
            'tasso_riferimento': 2.0,
            'liquidita_mercato': 0.8,
            'pressione_normativa': 0.5,
            'round_corrente': 0,
            'tassi_interesse': 2.0,
            'inflazione': 1.8,
            'sentiment_mercato': 'ansioso',
        }
    }


def generate_direttiva_bancaria() -> Dict[str, Any]:
    """Genera DirettivaBancaria per S0 con strategia Fisso (Benchmark)."""
    return {
        'uuid': 'direttiva-s0-v1',
        'label': 'DirettivaBancaria',
        'properties': {
            'direttiva_id': 'DIR-S0-V1',
            'scenario_rif': 'S0',
            'tipo': 'Broadcast Fisso',
            'contenuto': 'Promuovere bond corporate investment grade con messaggio standard',
            'priorita': 1,
            'data_emissione': datetime.now(timezone.utc).isoformat(),
            'attiva': True,
            'focus_prodotto': 'Bond_Corporate',
            'tolleranza_rischio_min': 0.3,
            'pressione_commerciale': 0.6,
        }
    }


def generate_promotori() -> List[Dict[str, Any]]:
    """Genera 2 promotori: 1 Fisso (Benchmark), 1 Adattativo (AI-driven)."""
    return [
        {
            'uuid': 'promotore-fisso-1',
            'label': 'Promotore',
            'properties': {
                'promotore_id': 'PROM-FISSO-1',
                'nome': 'Promotore Fisso 1',
                'tipo': 'Benchmark',
                'portafoglio_clienti': 100,
                'score_performance': 0.65,
                'bias_prodotto': 'Bond_Corporate',
                'adattativo': False,
                'livello_adattativita': 0.0,
            }
        },
        {
            'uuid': 'promotore-adattativo-1',
            'label': 'Promotore',
            'properties': {
                'promotore_id': 'PROM-ADAPT-1',
                'nome': 'Promotore Adattativo 1',
                'tipo': 'AI-Driven',
                'portafoglio_clienti': 100,
                'score_performance': 0.0,
                'bias_prodotto': '',
                'adattativo': True,
                'livello_adattativita': 1.0,
            }
        },
    ]


def generate_cluster_profili() -> List[Dict[str, Any]]:
    """Genera 20 ClusterProfilo in griglia 4 righe × 5 colonne."""
    clusters = []
    profili = ['Conservative', 'Balanced', 'Growth', 'Aggressive']
    fasce = ['Under100k', '100k-500k', '500k-1M', '1M-5M', 'Over5M']

    for row in range(4):
        for col in range(5):
            profilo = profili[row % len(profili)]
            fascia = fasce[col % len(fasce)]

            clusters.append({
                'uuid': f'cluster-{row}-{col}',
                'label': 'ClusterProfilo',
                'properties': {
                    'cluster_id': f'CLU-{row}-{col}',
                    'nome': f'Cluster {row}x{col} ({profilo}/{fascia})',
                    'profilo_rischio': profilo,
                    'fascia_patrimoniale': fascia,
                }
            })

    return clusters


def generate_clienti(num_clienti: int = 100) -> List[Dict[str, Any]]:
    """Genera 100 clienti distribuiti uniformemente nei 20 cluster."""
    clienti = []
    profili_rischio = ['Conservative', 'Balanced', 'Growth']
    fasce_patrimonio = ['Under100k', '100k-500k', '500k-1M', '1M-5M']

    for i in range(num_clienti):
        cluster_row = (i // 5) % 4
        cluster_col = i % 5

        clienti.append({
            'uuid': f'cliente-{i:03d}',
            'label': 'Cliente',
            'properties': {
                'cliente_id': f'CLI-{i:03d}',
                'nome': f'Cliente {i:03d}',
                'profilo_rischio': profili_rischio[i % len(profili_rischio)],
                'cluster_riga': cluster_row,
                'cluster_col': cluster_col,
                'propensione_rischio': 0.3 + (i % 7) * 0.1,
                'fascia_patrimoniale': fasce_patrimonio[i % len(fasce_patrimonio)],
                'fiducia_iniziale': 0.7,
                'soddisfazione': 0.5,
                'prodotti_detenuti': 2,
                'fiducia_attuale': 0.7,
                'urgenza_liquidita': i % 2 == 0,
            }
        })

    return clienti


def generate_relationships() -> List[Dict[str, Any]]:
    """
    Genera relazioni iniziali rispettando relationship_rules da schema.
    Relazioni: ScenarioMacro→DirettivaBancaria, Promotori→ScenarioMacro, ecc.
    """
    rels = []

    # DEFINISCE: ScenarioMacro → DirettivaBancaria
    rels.append({
        'uuid': str(uuid.uuid4()),
        'type': 'DEFINISCE',
        'source_uuid': 'scenario-s0-baseline',
        'target_uuid': 'direttiva-s0-v1',
        'properties': {'fact': 'S0 defines directive v1'},
    })

    # OPERA_IN: Promotori → ScenarioMacro (2 promotori)
    for prom_uuid in [
        'promotore-fisso-1',
        'promotore-adattativo-1',
    ]:
        rels.append({
            'uuid': str(uuid.uuid4()),
            'type': 'OPERA_IN',
            'source_uuid': prom_uuid,
            'target_uuid': 'scenario-s0-baseline',
            'properties': {'fact': 'Promoter operates in scenario S0'},
        })

    # EMETTE: DirettivaBancaria → Promotori (2 promotori)
    for prom_uuid in [
        'promotore-fisso-1',
        'promotore-adattativo-1',
    ]:
        rels.append({
            'uuid': str(uuid.uuid4()),
            'type': 'EMETTE',
            'source_uuid': 'direttiva-s0-v1',
            'target_uuid': prom_uuid,
            'properties': {'fact': 'Directive emitted to promoter'},
        })

    # GESTISCE: Promotori → Clienti (Fisso gestisce 100 clienti, Adattativo vede tutti)
    for i in range(100):
        prom_uuid = 'promotore-fisso-1'

        rels.append({
            'uuid': str(uuid.uuid4()),
            'type': 'GESTISCE',
            'source_uuid': prom_uuid,
            'target_uuid': f'cliente-{i:03d}',
            'properties': {'fact': 'Promoter manages client'},
        })

    # APPARTIENE_A: Clienti → ClusterProfilo
    for i in range(100):
        cluster_row = (i // 5) % 4
        cluster_col = i % 5

        rels.append({
            'uuid': str(uuid.uuid4()),
            'type': 'APPARTIENE_A',
            'source_uuid': f'cliente-{i:03d}',
            'target_uuid': f'cluster-{cluster_row}-{cluster_col}',
            'properties': {'fact': 'Client belongs to cluster'},
        })

    return rels


def populate_s0(graph_id: str = 'finsim-s0-baseline') -> Dict[str, Any]:
    """
    Entry point: genera e carica dati S0 Baseline su Neo4j.
    Ritorna dict con statistiche e errori.
    """
    logger.info(f"=== Inizio popolamento S0 - Baseline Neutro (graph_id={graph_id}) ===")

    loader = OntologyLoader()

    try:
        # Genera dati sintetici
        logger.info("Generazione dati sintetici...")
        scenario = generate_scenario_macro()
        direttiva = generate_direttiva_bancaria()
        promotori = generate_promotori()
        clusters = generate_cluster_profili()
        clienti = generate_clienti(100)

        all_nodes = [scenario, direttiva] + promotori + clusters + clienti
        logger.info(
            f"Generati {len(all_nodes)} nodi: "
            f"1 ScenarioMacro, 1 DirettivaBancaria, 2 Promotori, 20 Cluster, 100 Clienti"
        )

        # Genera relazioni
        relationships = generate_relationships()
        logger.info(f"Generati {len(relationships)} relazioni iniziali")

        # Carica su Neo4j
        logger.info("Caricamento su Neo4j via OntologyLoader...")
        result = loader.load(
            graph_id=graph_id,
            nodes=all_nodes,
            relationships=relationships,
        )

        logger.info(f"Nodi creati: {result['nodes_created']}")
        logger.info(f"Relazioni create: {result['relationships_created']}")

        if result['errors']:
            logger.error(f"Errori durante caricamento: {len(result['errors'])}")
            for err in result['errors']:
                logger.error(f"  • {err}")
        else:
            logger.info("✓ Caricamento completato senza errori")

        logger.info("=== Popolamento S0 terminato ===")
        return result

    except Exception as e:
        logger.exception(f"Errore critico durante popolamento S0: {e}")
        raise

    finally:
        loader.close()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    result = populate_s0()

    # Log summary
    logger.info(f"\n{'='*70}")
    logger.info(
        f"SUMMARY - Nodi: {result['nodes_created']}, "
        f"Relazioni: {result['relationships_created']}, "
        f"Errori: {len(result['errors'])}, "
        f"Success: {result['success']}"
    )
    logger.info(f"{'='*70}")
