"""
populate_finsim.py — Genera dati per tutti 5 gli scenari (S0-S4) e popola Neo4j.
Dati sintetici deterministici senza LLM/ThreadPool: topologia pura.
FINSIM-MOD: Genera ScenarioMacro e DirettivaBancaria per S0, S1, S2, S3, S4.
"""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone

from backend.app.finsim.ontology.ontology_loader import OntologyLoader

logger = logging.getLogger('finsim.populate')


def generate_scenarios_macro() -> List[Dict[str, Any]]:
    """Genera 5 nodi ScenarioMacro per S0-S4 con proprietà distinte."""
    return [
        {
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
        },
        {
            'uuid': 'scenario-s1-baseline',
            'label': 'ScenarioMacro',
            'properties': {
                'scenario_id': 'S1',
                'nome': 'S1 - Shock Tassi / Rialzo',
                'descrizione': 'Rialzo tassi improvviso (2.5%), crollo equity, spread allargamento',
                'tasso_riferimento': 2.5,
                'liquidita_mercato': 0.4,
                'pressione_normativa': 0.7,
                'round_corrente': 0,
                'tassi_interesse': 2.5,
                'inflazione': 2.5,
                'sentiment_mercato': 'pessimista',
            }
        },
        {
            'uuid': 'scenario-s2-baseline',
            'label': 'ScenarioMacro',
            'properties': {
                'scenario_id': 'S2',
                'nome': 'S2 - Crisi Acuta / Liquidità',
                'descrizione': 'Blocco geopolitico totale, flight to quality massico, PIL negativo',
                'tasso_riferimento': 3.0,
                'liquidita_mercato': 0.2,
                'pressione_normativa': 0.9,
                'round_corrente': 0,
                'tassi_interesse': 3.0,
                'inflazione': 3.5,
                'sentiment_mercato': 'panico',
            }
        },
        {
            'uuid': 'scenario-s3-baseline',
            'label': 'ScenarioMacro',
            'properties': {
                'scenario_id': 'S3',
                'nome': 'S3 - Opportunità / Pressione Normativa',
                'descrizione': 'Distensione geopolitica, rimbalzo azionario, forte pressione compliance',
                'tasso_riferimento': 1.8,
                'liquidita_mercato': 0.9,
                'pressione_normativa': 0.8,
                'round_corrente': 0,
                'tassi_interesse': 1.8,
                'inflazione': 1.5,
                'sentiment_mercato': 'ottimista',
            }
        },
        {
            'uuid': 'scenario-s4-baseline',
            'label': 'ScenarioMacro',
            'properties': {
                'scenario_id': 'S4',
                'nome': 'S4 - Biforcazione Dinamica',
                'descrizione': 'Identico a S0 fino al Round 10, poi cambio drastico della direttiva',
                'tasso_riferimento': 2.0,
                'liquidita_mercato': 0.8,
                'pressione_normativa': 0.5,
                'round_corrente': 0,
                'tassi_interesse': 2.0,
                'inflazione': 1.8,
                'sentiment_mercato': 'ansioso',
            }
        },
    ]


def generate_direttive_bancarie() -> List[Dict[str, Any]]:
    """Genera 5 DirettivaBancaria, una per ciascuno scenario (S0-S4)."""
    return [
        {
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
        },
        {
            'uuid': 'direttiva-s1-v1',
            'label': 'DirettivaBancaria',
            'properties': {
                'direttiva_id': 'DIR-S1-V1',
                'scenario_rif': 'S1',
                'tipo': 'Conservativo Difensivo',
                'contenuto': 'Ridurre esposizione equity, aumentare allocation obbligazionaria, gestire rischio duration',
                'priorita': 2,
                'data_emissione': datetime.now(timezone.utc).isoformat(),
                'attiva': True,
                'focus_prodotto': 'Bond_Sovereign',
                'tolleranza_rischio_min': 0.1,
                'pressione_commerciale': 0.4,
            }
        },
        {
            'uuid': 'direttiva-s2-v1',
            'label': 'DirettivaBancaria',
            'properties': {
                'direttiva_id': 'DIR-S2-V1',
                'scenario_rif': 'S2',
                'tipo': 'Crisi - Flight to Quality',
                'contenuto': 'Ridurre rischio sistematico, enfasi su attivi altamente liquidi e sicuri',
                'priorita': 3,
                'data_emissione': datetime.now(timezone.utc).isoformat(),
                'attiva': True,
                'focus_prodotto': 'Cash_Equivalents',
                'tolleranza_rischio_min': 0.0,
                'pressione_commerciale': 0.2,
            }
        },
        {
            'uuid': 'direttiva-s3-v1',
            'label': 'DirettivaBancaria',
            'properties': {
                'direttiva_id': 'DIR-S3-V1',
                'scenario_rif': 'S3',
                'tipo': 'Opportunità Equilibrata',
                'contenuto': 'Captare rimbalzo azionario con compliance-ready products, bilanciamento risk-return',
                'priorita': 2,
                'data_emissione': datetime.now(timezone.utc).isoformat(),
                'attiva': True,
                'focus_prodotto': 'Mixed_Funds',
                'tolleranza_rischio_min': 0.4,
                'pressione_commerciale': 0.7,
            }
        },
        {
            'uuid': 'direttiva-s4-v1',
            'label': 'DirettivaBancaria',
            'properties': {
                'direttiva_id': 'DIR-S4-V1',
                'scenario_rif': 'S4',
                'tipo': 'Broadcast Fisso (Pre-Biforcazione)',
                'contenuto': 'Promuovere bond corporate investment grade (identico a S0 fino al Round 10)',
                'priorita': 1,
                'data_emissione': datetime.now(timezone.utc).isoformat(),
                'attiva': True,
                'focus_prodotto': 'Bond_Corporate',
                'tolleranza_rischio_min': 0.3,
                'pressione_commerciale': 0.6,
            }
        },
    ]


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
                'portafoglio_clienti': 50,
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
                'portafoglio_clienti': 50,
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
    Genera relazioni per tutti e 5 gli scenari (S0-S4).
    Relazioni: ScenarioMacro→DirettivaBancaria, Promotori→ScenarioMacro, ecc.
    """
    rels = []
    scenarios = ['s0', 's1', 's2', 's3', 's4']

    # DEFINISCE: ScenarioMacro → DirettivaBancaria (per ogni scenario)
    for scenario in scenarios:
        rels.append({
            'uuid': str(uuid.uuid4()),
            'type': 'DEFINISCE',
            'source_uuid': f'scenario-{scenario}-baseline',
            'target_uuid': f'direttiva-{scenario}-v1',
            'properties': {'fact': f'{scenario.upper()} defines directive v1'},
        })

    # OPERA_IN: Promotori → ScenarioMacro (2 promotori × 5 scenari = 10 relazioni)
    for scenario in scenarios:
        for prom_uuid in [
            'promotore-fisso-1',
            'promotore-adattativo-1',
        ]:
            rels.append({
                'uuid': str(uuid.uuid4()),
                'type': 'OPERA_IN',
                'source_uuid': prom_uuid,
                'target_uuid': f'scenario-{scenario}-baseline',
                'properties': {'fact': f'Promoter operates in scenario {scenario.upper()}'},
            })

    # EMETTE: DirettivaBancaria → Promotori (per ogni scenario: 2 promotori)
    for scenario in scenarios:
        for prom_uuid in [
            'promotore-fisso-1',
            'promotore-adattativo-1',
        ]:
            rels.append({
                'uuid': str(uuid.uuid4()),
                'type': 'EMETTE',
                'source_uuid': f'direttiva-{scenario}-v1',
                'target_uuid': prom_uuid,
                'properties': {'fact': f'Directive {scenario.upper()} emitted to promoter'},
            })

    # GESTISCE: Promotori → Clienti (A/B split: cluster_riga < 2 → Fisso, cluster_riga >= 2 → Adattativo)
    for i in range(100):
        # Determina cluster_riga usando la stessa logica di generate_clienti()
        cluster_row = (i // 5) % 4
        # Split esclusivo basato su cluster_riga: < 2 → Fisso, >= 2 → Adattativo
        prom_uuid = 'promotore-fisso-1' if cluster_row < 2 else 'promotore-adattativo-1'

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


def populate_all_scenarios(graph_id: str = 'finsim-multi-scenario') -> Dict[str, Any]:
    """
    Entry point: genera e carica dati per tutti e 5 gli scenari (S0-S4) su Neo4j.
    Usa MERGE per idempotenza: eseguibile più volte in sicurezza.

    Args:
        graph_id: ID del grafo (default 'finsim-multi-scenario')

    Returns:
        Dict con statistiche e errori.
    """
    logger.info(f"=== Inizio popolamento Multi-Scenario (S0-S4) (graph_id={graph_id}) ===")

    loader = OntologyLoader()

    try:
        # Genera dati sintetici
        logger.info("Generazione dati sintetici per tutti gli scenari...")
        scenarios = generate_scenarios_macro()
        direttive = generate_direttive_bancarie()
        promotori = generate_promotori()
        clusters = generate_cluster_profili()
        clienti = generate_clienti(100)

        all_nodes = scenarios + direttive + promotori + clusters + clienti
        logger.info(
            f"Generati {len(all_nodes)} nodi: "
            f"5 ScenarioMacro, 5 DirettivaBancaria, 2 Promotori, 20 Cluster, 100 Clienti"
        )

        # Genera relazioni per tutti gli scenari
        relationships = generate_relationships()
        logger.info(f"Generati {len(relationships)} relazioni iniziali")

        # Carica su Neo4j (MERGE-based per idempotenza)
        logger.info("Caricamento su Neo4j via OntologyLoader...")
        result = loader.load(
            graph_id=graph_id,
            nodes=all_nodes,
            relationships=relationships,
        )

        logger.info(f"Nodi creati/aggiornati: {result['nodes_created']}")
        logger.info(f"Relazioni create/aggiornate: {result['relationships_created']}")

        if result['errors']:
            logger.error(f"Errori durante caricamento: {len(result['errors'])}")
            for err in result['errors']:
                logger.error(f"  • {err}")
        else:
            logger.info("✓ Caricamento completato senza errori")

        logger.info("=== Popolamento Multi-Scenario terminato ===")
        return result

    except Exception as e:
        logger.exception(f"Errore critico durante popolamento multi-scenario: {e}")
        raise

    finally:
        loader.close()


# Alias per backward compatibility
def populate_s0(graph_id: str = 'finsim-multi-scenario') -> Dict[str, Any]:
    """Alias per populate_all_scenarios (backward compatibility)."""
    return populate_all_scenarios(graph_id)


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
