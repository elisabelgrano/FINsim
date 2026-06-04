#!/usr/bin/env python3
"""
Run FINsim Simulation — Phase 4 Round 1 Execution
FINSIM-MOD: Standalone simulation runner for local execution

Instantiates SimulationEngine, executes Round 1 for scenario S0,
and prints detailed summary of commercial decisions and client trust metrics.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import Config
from backend.app.finsim.simulation_engine import SimulationEngine

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
)
logger = logging.getLogger('finsim.run_simulation')


# ============================================================================
# Main Simulation Runner
# ============================================================================


def run_round_1(engine: SimulationEngine) -> None:
    """
    Execute Round 1 of scenario S0 and print comprehensive summary.

    Args:
        engine: Initialized SimulationEngine
    """
    logger.info("=" * 80)
    logger.info("FINsim Round 1 Execution — Scenario S0 (Baseline)")
    logger.info("=" * 80)

    # Execute round
    round_result = engine.esegui_round(scenario_id="S0", round_n=1)

    # Print execution summary
    print("\n" + "=" * 80)
    print("ROUND 1 EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Scenario: {round_result['scenario_id']}")
    print(f"Round: {round_result['round']}")
    print(f"Promoters Processed: {round_result['promoters_processed']}")
    print(f"Total Clusters: {round_result['total_clusters']}")
    print(f"Commercial Decisions Created: {round_result['decisions_created']}")
    print(f"Clients Updated: {round_result['clients_updated']}")

    if round_result['errors']:
        print(f"\nErrors ({len(round_result['errors'])}):")
        for error in round_result['errors']:
            print(f"  - {error}")
    else:
        print("\n✓ No errors during execution")

    # Query DB for detailed decision summary
    print("\n" + "=" * 80)
    print("COMMERCIAL DECISIONS SUMMARY")
    print("=" * 80)

    decisions_summary = _fetch_decisions_summary(
        neo4j_uri=Config.NEO4J_URI,
        neo4j_user=Config.NEO4J_USER,
        neo4j_password=Config.NEO4J_PASSWORD,
        round_n=1,
    )

    if decisions_summary:
        for i, decision in enumerate(decisions_summary, 1):
            print(f"\n[Decision {i}]")
            print(f"  Promoter: {decision['promotore_id']}")
            print(f"  Cluster: ({decision['cluster_riga']}, {decision['cluster_col']})")
            print(f"  Strategy: {decision['strategia'][:60]}...")
            print(f"  Approach: {decision['approccio_comunicativo']}")
            print(f"  Product: {decision['prodotto_suggerito']}")
    else:
        print("No decisions found in database")

    # Query client trust metrics
    print("\n" + "=" * 80)
    print("CLIENT TRUST METRICS")
    print("=" * 80)

    trust_metrics = _fetch_client_trust_metrics(
        neo4j_uri=Config.NEO4J_URI,
        neo4j_user=Config.NEO4J_USER,
        neo4j_password=Config.NEO4J_PASSWORD,
    )

    print(f"Total Clients: {trust_metrics['total_clients']}")
    print(f"Average Trust: {trust_metrics['avg_trust']:.3f}")
    print(f"Min Trust: {trust_metrics['min_trust']:.3f}")
    print(f"Max Trust: {trust_metrics['max_trust']:.3f}")
    print(f"Std Dev: {trust_metrics['std_dev']:.3f}")

    # Distribution by trust range
    print("\nTrust Distribution:")
    for range_name, count in trust_metrics['trust_distribution'].items():
        pct = (count / trust_metrics['total_clients'] * 100) if trust_metrics['total_clients'] > 0 else 0
        print(f"  {range_name}: {count} ({pct:.1f}%)")

    print("\n" + "=" * 80)
    logger.info("Round 1 execution completed successfully")


# ============================================================================
# Database Query Functions
# ============================================================================


def _fetch_decisions_summary(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    round_n: int,
) -> list:
    """
    Fetch all DecisioneCommerciale nodes created in a round.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Database username
        neo4j_password: Database password
        round_n: Round number

    Returns:
        List of decision dicts
    """
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            query = """
            MATCH (p:Promotore)-[:EFFETTUA]->(d:DecisioneCommerciale {round: $round})
            RETURN
                p.promotore_id as promotore_id,
                d.cluster_riga as cluster_riga,
                d.cluster_col as cluster_col,
                d.strategia as strategia,
                d.approccio_comunicativo as approccio_comunicativo,
                d.prodotto_suggerito as prodotto_suggerito
            ORDER BY p.promotore_id, d.cluster_riga, d.cluster_col
            """

            result = session.run(query, round=round_n)
            decisions = [dict(record) for record in result]

        driver.close()
        return decisions

    except Neo4jError as e:
        logger.error(f"Neo4j error fetching decisions: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching decisions: {e}")
        return []


def _fetch_client_trust_metrics(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
) -> Dict[str, Any]:
    """
    Fetch client trust statistics from database.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Database username
        neo4j_password: Database password

    Returns:
        Dict with trust metrics
    """
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            # Get aggregate metrics
            metrics_query = """
            MATCH (c:Cliente)
            RETURN
                COUNT(c) as total_clients,
                AVG(c.fiducia_attuale) as avg_trust,
                MIN(c.fiducia_attuale) as min_trust,
                MAX(c.fiducia_attuale) as max_trust,
                STDEV(c.fiducia_attuale) as std_dev,
                COLLECT(c.fiducia_attuale) as trust_values
            """

            result = session.run(metrics_query)
            record = result.single()

            total = record['total_clients']
            trust_values = record['trust_values'] or []

            # Calculate distribution
            distribution = {
                '[0.0 - 0.25)': sum(1 for t in trust_values if 0.0 <= t < 0.25),
                '[0.25 - 0.50)': sum(1 for t in trust_values if 0.25 <= t < 0.50),
                '[0.50 - 0.75)': sum(1 for t in trust_values if 0.50 <= t < 0.75),
                '[0.75 - 1.00]': sum(1 for t in trust_values if 0.75 <= t <= 1.0),
            }

            metrics = {
                'total_clients': total,
                'avg_trust': record['avg_trust'] or 0.0,
                'min_trust': record['min_trust'] or 0.0,
                'max_trust': record['max_trust'] or 0.0,
                'std_dev': record['std_dev'] or 0.0,
                'trust_distribution': distribution,
            }

        driver.close()
        return metrics

    except Neo4jError as e:
        logger.error(f"Neo4j error fetching metrics: {e}")
        return {
            'total_clients': 0,
            'avg_trust': 0.0,
            'min_trust': 0.0,
            'max_trust': 0.0,
            'std_dev': 0.0,
            'trust_distribution': {},
        }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return {
            'total_clients': 0,
            'avg_trust': 0.0,
            'min_trust': 0.0,
            'max_trust': 0.0,
            'std_dev': 0.0,
            'trust_distribution': {},
        }


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Main entry point for simulation runner."""
    try:
        logger.info("Initializing SimulationEngine...")
        engine = SimulationEngine(
            neo4j_uri=Config.NEO4J_URI,
            neo4j_user=Config.NEO4J_USER,
            neo4j_password=Config.NEO4J_PASSWORD,
            ollama_base_url=Config.EMBEDDING_BASE_URL,
        )

        run_round_1(engine)
        esporta_json_risultati(engine, round_n=1)

        engine.close()
        logger.info("Simulation runner completed successfully")

    except KeyError as e:
        logger.error(f"Configuration error: missing {e}")
        logger.error("Ensure Config class has NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, EMBEDDING_BASE_URL")
        sys.exit(1)
    except Neo4jError as e:
        logger.error(f"Neo4j connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

def esporta_json_risultati(engine, round_n=1):
    import json
    from pathlib import Path
    
    # 1. Scriviamo la query per estrarre i dati che ci servono
    query = """
    MATCH (p:Promotore)-[:EFFETTUA]->(d:DecisioneCommerciale {round: $round_n})
    RETURN p.promotore_id AS promotore, d.cluster_riga AS riga, d.cluster_col AS col,
           d.strategia AS strategia, d.approccio_comunicativo AS approccio, d.prodotto_suggerito AS prodotto
    ORDER BY p.promotore_id, d.cluster_riga, d.cluster_col
    """
    
    decisioni_da_salvare = []
    
    # 2. Chiediamo all'engine di eseguire la query su Neo4j
    with engine._driver.session() as session:
        risultati = session.run(query, round_n=round_n)
        
        # 3. Trasformiamo i risultati in una lista di dizionari
        for record in risultati:
            decisione = {
                "promotore": record["promotore"],
                "cluster": f"({record['riga']}, {record['col']})",
                "strategia": record["strategia"],
                "approccio_comunicativo": record["approccio"],
                "prodotto_suggerito": record["prodotto"]
            }
            decisioni_da_salvare.append(decisione)
    
    # 4. CREAZIONE DELLA CARTELLA 'output'
    # Calcola il percorso della cartella 'finsim' dove si trova questo script
    finsim_dir = Path(__file__).parent
    
    # Crea il percorso per la nuova cartella 'output'
    output_dir = finsim_dir / "output"
    
    # Crea fisicamente la cartella se non esiste già (senza dare errore se c'è già)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. Salva il file dentro la cartella 'output'
    nome_file = f"risultati_round_{round_n}.json"
    percorso_file = output_dir / nome_file
    
    with open(percorso_file, "w", encoding="utf-8") as file_json:
        json.dump(decisioni_da_salvare, file_json, indent=4, ensure_ascii=False)
        
    print(f"\n[+] FILE CREATO: Ho salvato {len(decisioni_da_salvare)} decisioni nel file:\n -> {percorso_file}")

if __name__ == '__main__':
    main()