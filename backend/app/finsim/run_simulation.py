#!/usr/bin/env python3
"""
Run FINsim Simulation — Multi-Scenario, Multi-Round Execution
FINSIM-MOD: Standalone simulation runner with scenario cycling and A/B testing

Executes full simulation matrix: S0, S1, S2, S3, S4 scenarios with 1 round each.
For each scenario:
  1. Reset client trust/satisfaction and clean previous decisions
  2. Run consecutive rounds
  3. Save scenario results to MongoDB
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from pymongo import MongoClient

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


def run_scenario_rounds(
    engine: SimulationEngine,
    scenario_id: str,
    num_rounds: int = 200,
) -> Dict[str, Any]:
    """
    Execute multiple consecutive rounds for a scenario with result collection.

    Args:
        engine: Initialized SimulationEngine
        scenario_id: Scenario identifier (e.g., 'S0', 'S1', 'S2')
        num_rounds: Number of consecutive rounds to execute (default 3)

    Returns:
        Dict containing all round results and aggregated metrics
    """
    logger.info("=" * 80)
    logger.info(f"Starting scenario {scenario_id} execution ({num_rounds} rounds)")
    logger.info("=" * 80)

    scenario_result = {
        'scenario_id': scenario_id,
        'num_rounds': num_rounds,
        'rounds': [],
        'total_decisions': 0,
        'total_clients_updated': 0,
        'total_errors': 0,
        'timestamp': datetime.now().isoformat(),
    }

    for round_n in range(1, num_rounds + 1):
        try:
            logger.info(f"\n--- Round {round_n}/{num_rounds} ---")
            round_result = engine.esegui_round(scenario_id=scenario_id, round_n=round_n)

            scenario_result['rounds'].append(round_result)
            scenario_result['total_decisions'] += round_result['decisions_created']
            scenario_result['total_clients_updated'] += round_result['clients_updated']
            scenario_result['total_errors'] += len(round_result['errors'])

            # Print round summary
            print(f"\n[Round {round_n}]")
            print(f"  Promoters: {round_result['promoters_processed']}")
            print(f"  Clusters: {round_result['total_clusters']}")
            print(f"  Decisions: {round_result['decisions_created']}")
            print(f"  Clients Updated: {round_result['clients_updated']}")
            if round_result['errors']:
                print(f"  Errors: {len(round_result['errors'])}")

        except Exception as e:
            error_msg = f"Round {round_n} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            scenario_result['rounds'].append({'error': error_msg})
            scenario_result['total_errors'] += 1
            # Continue with next round instead of failing

    logger.info(f"\n{'='*80}")
    logger.info(f"Scenario {scenario_id} execution completed")
    logger.info(f"  Total Decisions: {scenario_result['total_decisions']}")
    logger.info(f"  Total Clients Updated: {scenario_result['total_clients_updated']}")
    logger.info(f"  Total Errors: {scenario_result['total_errors']}")

    return scenario_result


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
# Reset and State Management
# ============================================================================

def reset_scenario_state(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
) -> bool:
    """
    Reset client trust and satisfaction to initial values before starting a scenario.
    Preserves fiducia_iniziale (initial trust) set during population.
    Also remove any DecisioneCommerciale nodes from previous rounds.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Database username
        neo4j_password: Database password

    Returns:
        True if reset successful, False otherwise
    """
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            # Reset client trust from fiducia_iniziale and satisfaction to defaults
            # This preserves the diversity of initial trust values set during population
            reset_query = """
            MATCH (c:Cliente)
            SET c.fiducia_attuale = c.fiducia_iniziale,
                c.soddisfazione = 0.5
            RETURN COUNT(c) as reset_count
            """

            result = session.run(reset_query)
            reset_record = result.single()
            reset_count = reset_record['reset_count'] if reset_record else 0

            logger.info(
                f"Reset {reset_count} clients "
                f"(fiducia_attuale ← fiducia_iniziale, soddisfazione→0.5)"
            )

            # Remove DecisioneCommerciale nodes from previous rounds
            delete_query = """
            MATCH (d:DecisioneCommerciale)
            DETACH DELETE d
            RETURN COUNT(*) as deleted_count
            """

            result = session.run(delete_query)
            delete_record = result.single()
            deleted_count = delete_record['deleted_count'] if delete_record else 0

            logger.info(f"Deleted {deleted_count} previous DecisioneCommerciale nodes")

        driver.close()
        return True

    except Neo4jError as e:
        logger.error(f"Neo4j error during reset: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during reset: {e}", exc_info=True)
        return False



# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point: run full simulation matrix (S0, S1, S2, S3, S4 with 1 round each)."""
    try:
        logger.info("Initializing SimulationEngine...")
        engine = SimulationEngine(
            neo4j_uri=Config.NEO4J_URI,
            neo4j_user=Config.NEO4J_USER,
            neo4j_password=Config.NEO4J_PASSWORD,
            ollama_base_url=Config.EMBEDDING_BASE_URL,
        )

        # MongoDB connection
        try:
            client = MongoClient(Config.MONGO_URI)
            db = client["finsim_analytics"]
            collection = db["simulation_history"]
            logger.info("MongoDB connection established successfully.")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            return

        # Scenario list
        # Scenario list - TORNANO ORIGINALI PER NEO4J
        scenarios = ['S0', 'S1', 'S2', 'S3', 'S4']
        all_results = []

        for scenario_id in scenarios:
            # Creiamo il nuovo nome SOLO per MongoDB
            mongo_scenario_id = f"{scenario_id}_200"
            
            # Cache check sul NUOVO nome
            existing_doc = collection.find_one({"scenario_id": mongo_scenario_id})
            if existing_doc:
                logger.info(f"Scenario {mongo_scenario_id} already completed. Skipping execution.")
                continue

            try:
                logger.info(f"\n\n{'='*80}")
                logger.info(f"SCENARIO {scenario_id} START (Salvataggio come {mongo_scenario_id})")
                logger.info(f"{'='*80}\n")

                # Reset scenario state before running
                logger.info(f"Resetting state for scenario {scenario_id}...")
                if not reset_scenario_state(
                    neo4j_uri=Config.NEO4J_URI,
                    neo4j_user=Config.NEO4J_USER,
                    neo4j_password=Config.NEO4J_PASSWORD,
                ):
                    logger.error(f"Failed to reset state for scenario {scenario_id}, continuing anyway...")

                # Run consecutive rounds (ASSICURATI CHE SIA 200 QUI)
                scenario_result = run_scenario_rounds(
                    engine=engine,
                    scenario_id=scenario_id,
                    num_rounds=200,
                )

                all_results.append(scenario_result)

                # TRUCCO: Cambiamo l'ID prima di salvare su MongoDB
                scenario_result["scenario_id"] = mongo_scenario_id
                
                logger.info(f"Calcolo metriche di business avanzate per {mongo_scenario_id}...")
                scenario_result["business_metrics"] = engine._calcola_metriche_business(scenario_result)
                
                collection.insert_one(scenario_result)
                logger.info(f"Scenario {mongo_scenario_id} results saved to MongoDB.")

                logger.info(f"SCENARIO {mongo_scenario_id} COMPLETE\n")

            except Exception as e:
                error_msg = f"Error processing scenario {scenario_id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(f"\n[✗] {error_msg}")

        # Print final summary
        print(f"\n\n{'='*80}")
        print("SIMULATION MATRIX COMPLETE")
        print(f"{'='*80}")
        print(f"Scenarios Executed: {len(all_results)}")
        for result in all_results:
            print(f"  - {result['scenario_id']}: {result['total_decisions']} decisions, "
                  f"{result['total_clients_updated']} clients updated")

        engine.close()
        logger.info("Simulation runner completed successfully")

    except KeyError as e:
        logger.error(f"Configuration error: missing {e}")
        logger.error("Ensure Config has NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, EMBEDDING_BASE_URL")
        sys.exit(1)
    except Neo4jError as e:
        logger.error(f"Neo4j connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()