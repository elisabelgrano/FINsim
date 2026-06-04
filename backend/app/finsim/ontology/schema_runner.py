#!/usr/bin/env python3
"""
Schema Runner — Execute Neo4j schema queries from Cypher file
FINSIM-MOD: Initializes FINsim ontology constraints and indexes on Neo4j

This script reads neo4j_schema.cypher and executes all queries sequentially,
logging each operation with timestamps and error handling.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable, AuthError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s',
    handlers=[
        logging.FileHandler(
            Path(__file__).parent / f'schema_runner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger('finsim.schema_runner')


def parse_cypher_file(file_path: str) -> List[str]:
    """
    Read .cypher file and parse individual queries.

    Returns a list of query strings, filtering out comments and empty lines.
    Queries are separated by semicolons and stripped of whitespace.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cypher file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by semicolon
    raw_queries = content.split(';')

    queries = []
    for query in raw_queries:
        # Remove comments
        lines = []
        for line in query.split('\n'):
            # Remove line comments
            if '//' in line:
                line = line[:line.index('//')]
            # Remove block comments
            if '/*' in line or '*/' in line:
                continue
            line = line.strip()
            if line:
                lines.append(line)

        # Join lines and strip
        cleaned = ' '.join(lines).strip()
        if cleaned:
            queries.append(cleaned)

    return queries


def execute_schema(
    uri: str,
    user: str,
    password: str,
    queries: List[str],
    dry_run: bool = False,
) -> Tuple[int, int, int]:
    """
    Execute schema queries on Neo4j database.

    Args:
        uri: Neo4j connection URI
        user: Database user
        password: Database password
        queries: List of Cypher query strings
        dry_run: If True, log queries but don't execute

    Returns:
        (total, successful, failed) — query counts
    """
    driver = None
    try:
        logger.info(f"Connecting to Neo4j at {uri}...")
        driver = GraphDatabase.driver(uri, auth=(user, password))

        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        logger.info("✓ Neo4j connection successful")

    except AuthError as e:
        logger.error(f"✗ Authentication failed: {e}")
        raise
    except ServiceUnavailable as e:
        logger.error(f"✗ Neo4j service unavailable: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        raise

    successful = 0
    failed = 0

    try:
        with driver.session() as session:
            for idx, query in enumerate(queries, 1):
                try:
                    if dry_run:
                        logger.info(f"[DRY-RUN {idx}/{len(queries)}] {query[:80]}...")
                    else:
                        logger.info(f"[{idx}/{len(queries)}] Executing: {query[:80]}...")
                        result = session.run(query)
                        # Consume result to ensure query completes
                        list(result)
                        logger.info(f"[{idx}/{len(queries)}] ✓ SUCCESS")
                        successful += 1

                except Neo4jError as e:
                    # Some errors are expected (constraint already exists, etc.)
                    if "already exists" in str(e).lower() or "constraint" in str(e).lower():
                        logger.warning(f"[{idx}/{len(queries)}] ⚠ WARNING (expected): {e}")
                        successful += 1  # Count as success since it's idempotent
                    else:
                        logger.error(f"[{idx}/{len(queries)}] ✗ ERROR: {e}")
                        failed += 1

                except Exception as e:
                    logger.error(f"[{idx}/{len(queries)}] ✗ UNEXPECTED ERROR: {e}")
                    failed += 1

    finally:
        if driver:
            driver.close()
            logger.info("Neo4j driver closed")

    return len(queries), successful, failed


def main():
    """Parse arguments and run schema initialization."""
    parser = argparse.ArgumentParser(
        description='Execute FINsim Neo4j schema queries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                          # Use default config
  %(prog)s --uri bolt://localhost:7687 --user neo4j
  %(prog)s --dry-run                                # Preview queries without executing
  %(prog)s --file /path/to/custom_schema.cypher
        """
    )

    parser.add_argument(
        '--file',
        default=None,
        help='Path to .cypher file (default: ./neo4j_schema.cypher)',
    )
    parser.add_argument(
        '--uri',
        default=None,
        help='Neo4j connection URI (default: from config or NEO4J_URI env var)',
    )
    parser.add_argument(
        '--user',
        default=None,
        help='Neo4j username (default: from config or NEO4J_USER env var)',
    )
    parser.add_argument(
        '--password',
        default=None,
        help='Neo4j password (default: from config or NEO4J_PASSWORD env var)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and preview queries without executing',
    )

    args = parser.parse_args()

    # Determine cypher file path
    if args.file:
        cypher_file = args.file
    else:
        # Default to neo4j_schema.cypher in same directory as this script
        cypher_file = os.path.join(os.path.dirname(__file__), 'neo4j_schema.cypher')

    # Load configuration from config.py if available
    try:
        # Add parent directories to path for imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
        from config import Config

        neo4j_uri = args.uri or os.environ.get('NEO4J_URI') or Config.NEO4J_URI
        neo4j_user = args.user or os.environ.get('NEO4J_USER') or Config.NEO4J_USER
        neo4j_password = args.password or os.environ.get('NEO4J_PASSWORD') or Config.NEO4J_PASSWORD

    except ImportError:
        # Fallback to environment variables
        neo4j_uri = args.uri or os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = args.user or os.environ.get('NEO4J_USER', 'neo4j')
        neo4j_password = args.password or os.environ.get('NEO4J_PASSWORD', 'mirofish')

    logger.info("=" * 70)
    logger.info("FINsim Neo4j Schema Runner")
    logger.info("=" * 70)
    logger.info(f"Cypher file: {cypher_file}")
    logger.info(f"Target URI: {neo4j_uri}")
    logger.info(f"User: {neo4j_user}")
    logger.info(f"Dry-run mode: {args.dry_run}")
    logger.info("=" * 70)

    try:
        # Parse queries
        logger.info("Parsing Cypher file...")
        queries = parse_cypher_file(cypher_file)
        logger.info(f"✓ Parsed {len(queries)} queries from {cypher_file}")

        if args.dry_run:
            logger.info("\n--- DRY-RUN: Preview of queries ---")
            for idx, query in enumerate(queries, 1):
                logger.info(f"[{idx}/{len(queries)}] {query}")
            logger.info(f"\nTotal queries to execute: {len(queries)}")
            return 0

        # Execute queries
        logger.info(f"\nExecuting {len(queries)} queries...")
        total, successful, failed = execute_schema(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            queries,
        )

        # Report results
        logger.info("=" * 70)
        logger.info("SCHEMA EXECUTION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total queries:     {total}")
        logger.info(f"Successful:        {successful} ✓")
        logger.info(f"Failed:            {failed} ✗")
        logger.info("=" * 70)

        if failed > 0:
            logger.error(f"Schema initialization completed with {failed} error(s)")
            return 1
        else:
            logger.info("✓ Schema initialization completed successfully")
            return 0

    except FileNotFoundError as e:
        logger.error(f"✗ {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
