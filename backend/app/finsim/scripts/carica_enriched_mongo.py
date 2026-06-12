#!/usr/bin/env python3
"""
MongoDB Loader for Enriched Simulation Results
Loads enriched JSON files (S0-S4) from backend/app/finsim/output/enriched/
into MongoDB collection finsim_analytics.simulation_history.
"""

import json
import sys
from pathlib import Path
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError


def get_project_root() -> Path:
    """Get project root directory."""
    current = Path(__file__).resolve()
    # Navigate from scripts/ -> finsim/ -> app/ -> backend/ -> project_root
    return current.parent.parent.parent.parent.parent


def load_config():
    """Load configuration from Config class."""
    sys.path.insert(0, str(get_project_root() / 'backend'))
    from app.config import Config
    return Config


def load_enriched_scenarios(enriched_dir: Path) -> dict:
    """Load all enriched JSON files from directory."""
    scenarios = {}
    scenario_ids = ['S0', 'S1', 'S2', 'S3', 'S4']

    for scenario_id in scenario_ids:
        file_path = enriched_dir / f'risultati_{scenario_id}.json'
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            scenarios[scenario_id] = data
            print(f"✓ Loaded {scenario_id}: {file_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"✗ Error loading {scenario_id}: {e}")
            continue

    return scenarios


def load_to_mongodb(
    mongo_uri: str,
    scenarios: dict,
    db_name: str = 'finsim_analytics',
    collection_name: str = 'simulation_history'
) -> tuple[int, int]:
    """Load scenarios into MongoDB."""
    loaded_count = 0
    error_count = 0

    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]

        print(f"\n{'='*70}")
        print(f"Connecting to MongoDB: {mongo_uri}")
        print(f"Database: {db_name} | Collection: {collection_name}")
        print(f"{'='*70}\n")

        # Test connection
        client.admin.command('ping')
        print("✓ MongoDB connection successful\n")

        for scenario_id, data in sorted(scenarios.items()):
            try:
                # Delete existing document with same scenario_id
                delete_result = collection.delete_many({'scenario_id': scenario_id})
                if delete_result.deleted_count > 0:
                    print(f"  Deleted {delete_result.deleted_count} existing document(s) for {scenario_id}")

                # Insert enriched document
                result = collection.insert_one(data)

                # Extract metrics from summary
                summary = data.get('summary', {})
                total_decisions = summary.get('total_decisions', 0)
                compliance_rate = summary.get('overall_compliance_rate', 0)

                # Log with required format
                log_msg = (
                    f"Scenario {scenario_id}: loaded, "
                    f"{total_decisions} decisions, "
                    f"compliance {compliance_rate:.1%}"
                )
                print(f"✓ {log_msg}")
                loaded_count += 1

            except PyMongoError as e:
                print(f"✗ Error loading scenario {scenario_id}: {e}")
                error_count += 1

        client.close()

    except PyMongoError as e:
        print(f"✗ MongoDB connection error: {e}")
        error_count = len(scenarios)
        return 0, error_count

    return loaded_count, error_count


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("MongoDB Enriched Simulation Loader")
    print("="*70 + "\n")

    # Get paths
    project_root = get_project_root()
    enriched_dir = project_root / 'backend' / 'app' / 'finsim' / 'output' / 'enriched'

    # Load config
    config = load_config()

    # Check enriched directory
    if not enriched_dir.exists():
        print(f"✗ Error: Enriched directory not found: {enriched_dir}")
        return 1

    print(f"Loading enriched files from: {enriched_dir}\n")

    # Load scenarios from JSON files
    scenarios = load_enriched_scenarios(enriched_dir)

    if not scenarios:
        print("✗ No enriched JSON files loaded. Exiting.")
        return 1

    print(f"Loaded {len(scenarios)} scenario(s) from JSON files\n")

    # Load to MongoDB
    loaded_count, error_count = load_to_mongodb(
        config.MONGO_URI,
        scenarios
    )

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total documents loaded: {loaded_count}")
    if error_count > 0:
        print(f"Errors: {error_count}")
        return 1
    else:
        print("✓ All scenarios loaded successfully!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
