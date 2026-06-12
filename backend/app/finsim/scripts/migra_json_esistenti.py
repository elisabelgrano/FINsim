"""
Migration script to enrich existing risultati JSON files with metrics.

Reads 5 existing risultati JSON files (S0-S4), enriches each decision with:
- Normalized product names
- Directive compliance assessment
- Risk profile from Neo4j cluster profiles
- Adequacy scores
- Round and scenario summaries
"""

import json
import logging
import os
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from neo4j import GraphDatabase, Session as Neo4jSession

from backend.app.config import Config
from backend.app.finsim.metrics.normalizzatore import normalize_prodotto


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finsim.migration')


# Directive focus products per scenario
FOCUS_PRODOTTO = {
    'S0': 'Bond_Corporate',
    'S1': 'Bond_Sovereign',
    'S2': 'Cash_Equivalents',
    'S3': 'Mixed_Funds',
    'S4': 'Bond_Corporate'
}

# Product-risk adequacy matrix
ADEGUATEZZA_MATRIX = {
    "Conservative": {
        "Cash_Equivalents": 1.0,
        "Bond_Sovereign":   0.9,
        "Bond_Corporate":   0.5,
        "Mixed_Funds":      0.1,
        "Altro":            0.2
    },
    "Balanced": {
        "Bond_Sovereign":   1.0,
        "Bond_Corporate":   0.8,
        "Cash_Equivalents": 0.6,
        "Mixed_Funds":      0.5,
        "Altro":            0.3
    },
    "Growth": {
        "Bond_Corporate":   1.0,
        "Mixed_Funds":      0.8,
        "Bond_Sovereign":   0.5,
        "Cash_Equivalents": 0.3,
        "Altro":            0.3
    },
    "Aggressive": {
        "Mixed_Funds":      1.0,
        "Bond_Corporate":   0.7,
        "Bond_Sovereign":   0.3,
        "Cash_Equivalents": 0.2,
        "Altro":            0.2
    }
}

SOGLIA_ACCETTAZIONE = 0.5


def get_neo4j_driver():
    """Initialize Neo4j driver using Config."""
    return GraphDatabase.driver(
        Config.NEO4J_URI,
        auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
    )


def build_cluster_profiles(driver) -> Dict[Tuple[int, int], str]:
    """
    Query Neo4j to build cluster profile lookup.

    Returns:
        Dict mapping (riga, col) → most common risk profile in cluster
    """
    query = """
    MATCH (c:Cliente)
    RETURN c.cluster_riga as riga,
           c.cluster_col as col,
           collect(c.profilo_rischio) as profili
    """

    cluster_profili = {}

    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                riga = record["riga"]
                col = record["col"]
                profili = record["profili"]

                if riga is None or col is None:
                    continue

                if profili and len(profili) > 0:
                    # Get most common profile
                    counter = Counter(profili)
                    most_common = counter.most_common(1)[0][0]
                    cluster_profili[(int(riga), int(col))] = most_common
                else:
                    cluster_profili[(int(riga), int(col))] = 'Balanced'

        logger.info(f"Loaded {len(cluster_profili)} cluster profiles from Neo4j")
    except Exception as e:
        logger.error(f"Error querying Neo4j for cluster profiles: {e}")
        # Return empty dict to continue with defaults
        return {}

    return cluster_profili


def extract_cluster_coords(cluster_str: str) -> Optional[Tuple[int, int]]:
    """
    Extract (riga, col) from cluster string like "(2, 0)".

    Args:
        cluster_str: String like "(2, 0)"

    Returns:
        Tuple of (riga, col) as ints, or None if parsing fails
    """
    try:
        # Match pattern (number, number)
        match = re.match(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', cluster_str)
        if match:
            riga = int(match.group(1))
            col = int(match.group(2))
            return (riga, col)
    except Exception as e:
        logger.debug(f"Failed to parse cluster string '{cluster_str}': {e}")

    return None


def sanitize_prodotto(raw: Any) -> str:
    """
    Sanitize raw prodotto field (may be list, dict, or string).

    Handles cases where LLM response is malformed:
    - If list: extract first dict item's 'prodotto' key, else first element as str
    - If dict: extract 'prodotto' key if present
    - If not non-empty string: return 'Altro'

    Args:
        raw: Raw prodotto_suggerito value from JSON

    Returns:
        Sanitized string value
    """
    if isinstance(raw, list):
        if len(raw) > 0:
            first = raw[0]
            if isinstance(first, dict) and 'prodotto' in first:
                return str(first['prodotto']).strip()
            else:
                return str(first).strip()
        return 'Altro'
    elif isinstance(raw, dict):
        if 'prodotto' in raw:
            return str(raw['prodotto']).strip()
        return 'Altro'
    elif isinstance(raw, str):
        sanitized = raw.strip()
        return sanitized if sanitized else 'Altro'
    else:
        return 'Altro'


def enrich_decision(
    decision: Dict[str, Any],
    cluster_profili: Dict[Tuple[int, int], str],
    focus_prodotto: str
) -> Dict[str, Any]:
    """
    Enrich a single decision with computed metrics.

    Args:
        decision: Original decision dict
        cluster_profili: Cluster profile lookup
        focus_prodotto: Expected product for this scenario

    Returns:
        Enriched decision dict
    """
    # Extract cluster coordinates
    cluster_str = decision.get('cluster', '')
    coords = extract_cluster_coords(cluster_str)

    # Sanitize and normalize product
    prodotto_raw = sanitize_prodotto(decision.get('prodotto_suggerito', 'Altro'))
    prodotto_normalizzato = normalize_prodotto(prodotto_raw)

    # Directive compliance
    conforme_direttiva = (prodotto_normalizzato == focus_prodotto)

    # Get risk profile and compute adequacy
    profilo = 'Balanced'
    if coords:
        profilo = cluster_profili.get(coords, 'Balanced')

    adeguatezza_score = round(
        ADEGUATEZZA_MATRIX.get(profilo, {}).get(prodotto_normalizzato, 0.0), 2
    )
    accettato = adeguatezza_score >= SOGLIA_ACCETTAZIONE

    # Add enriched fields
    decision['prodotto_suggerito_raw'] = prodotto_raw
    decision['prodotto_suggerito'] = prodotto_normalizzato
    decision['profilo_rischio_prevalente'] = profilo
    decision['conforme_direttiva'] = conforme_direttiva
    decision['adeguatezza_score'] = adeguatezza_score
    decision['accettato'] = accettato

    return decision


def enrich_scenario(scenario_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add scenario-level summary metrics.

    Args:
        scenario_dict: Scenario dict with enriched rounds

    Returns:
        Scenario dict with scenario summary added
    """
    rounds = scenario_dict.get('rounds', [])

    if not rounds:
        return scenario_dict

    # Overall compliance rate (mean of round rates)
    compliance_rates = [r.get('compliance_rate', 0) for r in rounds]
    overall_compliance_rate = round(
        sum(compliance_rates) / len(compliance_rates), 2
    ) if compliance_rates else 0.0

    # Overall mismatch rate
    mismatch_rates = [r.get('mismatch_rate', 0) for r in rounds]
    overall_mismatch_rate = round(
        sum(mismatch_rates) / len(mismatch_rates), 2
    ) if mismatch_rates else 0.0

    # Overall acceptance rate
    overall_acceptance_rate = round(1 - overall_mismatch_rate, 2)

    # Build strategic matrix (all decisions grouped by profile + product)
    matrice_data = {}

    for round_dict in rounds:
        for decision in round_dict.get('decisions', []):
            profilo = decision.get('profilo_rischio_prevalente', 'Unknown')
            prodotto = decision.get('prodotto_suggerito', 'Altro')
            adeguatezza = decision.get('adeguatezza_score', 0.0)
            accettato = decision.get('accettato', False)

            key = (profilo, prodotto)
            if key not in matrice_data:
                matrice_data[key] = {
                    'count': 0,
                    'sum_adeguatezza': 0.0,
                    'accepted_count': 0
                }

            matrice_data[key]['count'] += 1
            matrice_data[key]['sum_adeguatezza'] += adeguatezza
            if accettato:
                matrice_data[key]['accepted_count'] += 1

    # Format matrice_strategica
    matrice_strategica = []
    for (profilo, prodotto), data in matrice_data.items():
        matrice_strategica.append({
            'profilo': profilo,
            'prodotto': prodotto,
            'num_decisioni': data['count'],
            'adeguatezza_media': round(data['sum_adeguatezza'] / data['count'], 2),
            'acceptance_rate': round(data['accepted_count'] / data['count'], 2)
        })

    # Sort by adeguatezza_media descending
    matrice_strategica.sort(
        key=lambda x: x['adeguatezza_media'],
        reverse=True
    )

    # Add to scenario summary
    if 'summary' not in scenario_dict:
        scenario_dict['summary'] = {}

    scenario_dict['summary']['overall_compliance_rate'] = overall_compliance_rate
    scenario_dict['summary']['overall_mismatch_rate'] = overall_mismatch_rate
    scenario_dict['summary']['overall_acceptance_rate'] = overall_acceptance_rate
    scenario_dict['summary']['matrice_strategica'] = matrice_strategica

    return scenario_dict


def migrate_scenario(
    scenario_id: str,
    cluster_profili: Dict[Tuple[int, int], str],
    input_dir: Path,
    output_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Migrate a single scenario JSON file.

    Args:
        scenario_id: Scenario identifier (S0-S4)
        cluster_profili: Cluster profile lookup
        input_dir: Input directory path
        output_dir: Output directory path

    Returns:
        Summary dict with migration result, or None if failed
    """
    input_file = input_dir / f'risultati_{scenario_id}.json'
    output_file = output_dir / f'risultati_{scenario_id}.json'

    # Read input JSON
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            scenario_dict = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON {input_file}: {e}")
        return None

    focus_prodotto = FOCUS_PRODOTTO.get(scenario_id, 'Altro')

    # Process each round in exact order: enrich → compute metrics
    total_decisions_enriched = 0
    rounds = scenario_dict.get('rounds', [])

    for round_dict in rounds:
        # Step 1: Get the decisions list
        decisions = round_dict['decisions']

        # Step 2: Enrich all decisions IN PLACE with computed fields
        for decision in decisions:
            enrich_decision(decision, cluster_profili, focus_prodotto)
            total_decisions_enriched += 1

        # Verify: print sample decision after enrichment
        if decisions:
            sample = decisions[0]
            logger.info(
                f"Sample enriched decision (first of {len(decisions)}): "
                f"conforme_direttiva={sample.get('conforme_direttiva')}, "
                f"accettato={sample.get('accettato')}, "
                f"prodotto_suggerito={sample.get('prodotto_suggerito')}"
            )

        # Step 3: AFTER enriching all decisions, compute round metrics
        # from the now-enriched decision dicts
        compliance_count = sum(1 for d in decisions if d.get('conforme_direttiva', False))
        compliance_rate = round(compliance_count / len(decisions), 2) if decisions else 0.0

        mismatch_count = sum(1 for d in decisions if not d.get('accettato', False))
        mismatch_rate = round(mismatch_count / len(decisions), 2) if decisions else 0.0

        prodotti = [d.get('prodotto_suggerito', 'Altro') for d in decisions]
        prodotto_counter = Counter(prodotti)
        prodotto_dominante = prodotto_counter.most_common(1)[0][0] if prodotto_counter else 'Altro'

        dispersione_prodotti = len(set(prodotti))

        # Compliance per promoter
        compliance_per_promotore = {}
        promoters = {}
        for decision in decisions:
            promotore = decision.get('promotore', 'Unknown')
            if promotore not in promoters:
                promoters[promotore] = {'conforme': 0, 'total': 0}

            promoters[promotore]['total'] += 1
            if decision.get('conforme_direttiva', False):
                promoters[promotore]['conforme'] += 1

        for promotore, counts in promoters.items():
            compliance_per_promotore[promotore] = round(
                counts['conforme'] / counts['total'], 2
            ) if counts['total'] > 0 else 0.0

        # Step 4: Write round metrics to round_data dict
        round_dict['compliance_rate'] = compliance_rate
        round_dict['mismatch_rate'] = mismatch_rate
        round_dict['prodotto_dominante'] = prodotto_dominante
        round_dict['dispersione_prodotti'] = dispersione_prodotti
        round_dict['compliance_per_promotore'] = compliance_per_promotore

    # Step 5: AFTER all rounds processed, compute scenario summary
    enrich_scenario(scenario_dict)

    # Write output JSON
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        all_decisions = [
            d
            for r in scenario_dict['rounds']
            for d in r.get('decisions', [])
        ]

        round_compliances = [
            r.get('compliance_rate', 0.0)
            for r in scenario_dict['rounds']
            if r.get('compliance_rate') is not None
        ]
        round_mismatches = [
            r.get('mismatch_rate', 0.0)
            for r in scenario_dict['rounds']
            if r.get('mismatch_rate') is not None
        ]

        overall_compliance = round(
            sum(round_compliances) / len(round_compliances), 2
        ) if round_compliances else 0.0

        overall_mismatch = round(
            sum(round_mismatches) / len(round_mismatches), 2
        ) if round_mismatches else 0.0

        scenario_dict['summary']['overall_compliance_rate'] = overall_compliance
        scenario_dict['summary']['overall_mismatch_rate'] = overall_mismatch
        scenario_dict['summary']['overall_acceptance_rate'] = round(
            1 - overall_mismatch, 2
        )

        from collections import defaultdict
        gruppi = defaultdict(list)
        for d in all_decisions:
            key = (
                d.get('profilo_rischio_prevalente', 'Balanced'),
                d.get('prodotto_suggerito', 'Altro')
            )
            gruppi[key].append(d)

        matrice = []
        for (profilo, prodotto), decisioni in gruppi.items():
            matrice.append({
                'profilo': profilo,
                'prodotto': prodotto,
                'num_decisioni': len(decisioni),
                'adeguatezza_media': round(
                    sum(d.get('adeguatezza_score', 0.0)
                        for d in decisioni) / len(decisioni), 2
                ),
                'acceptance_rate': round(
                    sum(1 for d in decisioni
                        if d.get('accettato')) / len(decisioni), 2
                ),
            })

        matrice.sort(key=lambda x: x['adeguatezza_media'], reverse=True)
        scenario_dict['summary']['matrice_strategica'] = matrice

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scenario_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote enriched JSON: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file {output_file}: {e}")
        return None

    # Prepare summary
    summary = {
        'scenario_id': scenario_id,
        'decisions_enriched': total_decisions_enriched,
        'compliance_rate': scenario_dict.get('overall_compliance_rate', 0.0),
        'mismatch_rate': scenario_dict.get('overall_mismatch_rate', 0.0),
        'acceptance_rate': scenario_dict.get('overall_acceptance_rate', 0.0)
    }

    return summary


def main():
    """Run the migration for all 5 scenarios."""
    logger.info("=== FINsim JSON Migration Script ===")

    # Setup paths
    backend_dir = Path(__file__).parent.parent.parent
    input_dir = backend_dir / 'finsim' / 'output'
    output_dir = backend_dir / 'finsim' / 'output' / 'enriched'

    # Connect to Neo4j
    driver = None
    try:
        driver = get_neo4j_driver()
        logger.info(f"Connected to Neo4j at {Config.NEO4J_URI}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        logger.warning("Continuing without cluster profiles from Neo4j (defaults will be used)")
        driver = None

    # Build cluster profiles
    cluster_profili = {}
    if driver:
        try:
            cluster_profili = build_cluster_profiles(driver)
        except Exception as e:
            logger.error(f"Error building cluster profiles: {e}")
            cluster_profili = {}

    # Migrate all scenarios
    scenarios = ['S0', 'S1', 'S2', 'S3', 'S4']
    summaries = []

    for scenario_id in scenarios:
        logger.info(f"\n--- Processing {scenario_id} ---")
        summary = migrate_scenario(scenario_id, cluster_profili, input_dir, output_dir)
        if summary:
            summaries.append(summary)
            logger.info(
                f"Scenario {summary['scenario_id']}: "
                f"{summary['decisions_enriched']} decisions enriched, "
                f"compliance {summary['compliance_rate']}, "
                f"mismatch {summary['mismatch_rate']}"
            )
        else:
            logger.error(f"Failed to migrate {scenario_id}")

    # Overall summary
    logger.info("\n=== Migration Summary ===")
    if summaries:
        avg_compliance = round(
            sum(s['compliance_rate'] for s in summaries) / len(summaries), 2
        )
        avg_mismatch = round(
            sum(s['mismatch_rate'] for s in summaries) / len(summaries), 2
        )
        total_decisions = sum(s['decisions_enriched'] for s in summaries)

        logger.info(f"Scenarios migrated: {len(summaries)}/{len(scenarios)}")
        logger.info(f"Total decisions enriched: {total_decisions}")
        logger.info(f"Average compliance rate: {avg_compliance}")
        logger.info(f"Average mismatch rate: {avg_mismatch}")
        logger.info(f"Output directory: {output_dir}")
    else:
        logger.error("No scenarios were successfully migrated")

    # Close driver
    if driver:
        try:
            driver.close()
            logger.info("Closed Neo4j driver")
        except Exception as e:
            logger.error(f"Error closing driver: {e}")


if __name__ == '__main__':
    main()
