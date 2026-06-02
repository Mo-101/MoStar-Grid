#!/usr/bin/env python3
"""
MoStar Grid — Phantom Sync Daemon
Pulls the latest epidemiological risk payload from the Phantom service
and ingests it into the Neo4j Mother Graph.

Usage:
    python scripts/sync_phantom.py
"""
import os
import sys
import json
import httpx
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PhantomSync] %(levelname)s: %(message)s")
logger = logging.getLogger("phantom_sync")

# Adjust sys.path to import the ingestor from neo4j-mindgraph despite the hyphenated folder
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "mindgraph" / "neo4j-mindgraph" / "import"))

try:
    from phantom_ingest import PhantomIngestor
except ImportError as e:
    logger.error(f"Failed to import PhantomIngestor: {e}")
    sys.exit(1)

PHANTOM_API_URL = os.getenv("PHANTOM_API_URL", "http://localhost:8080/api/v1/epi-risk/latest")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Mogrid101")

async def fetch_phantom_payload() -> dict:
    """Fetch the latest hardened risk outputs from the Phantom API."""
    logger.info(f"Connecting to Phantom service at {PHANTOM_API_URL}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(PHANTOM_API_URL)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Network error while connecting to Phantom: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Phantom returned HTTP error {e.response.status_code}")
            raise

def sync_to_grid(payload: dict):
    """Push the payload into the Neo4j MoStar Grid."""
    logger.info("Initializing PhantomIngestor for Neo4j Mother Graph...")
    ingestor = PhantomIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        ingestor.ingest_phantom_payload(payload)
        logger.info(f"Successfully synchronized Phantom data for week {payload.get('week_id')} (Corridor: {payload.get('location')})")
    except Exception as e:
        logger.error(f"Failed to ingest payload into Neo4j: {e}")
        raise
    finally:
        ingestor.close()

async def main():
    logger.info("Starting Phantom synchronization cycle...")
    try:
        payload = await fetch_phantom_payload()
        # The payload could be a single dict or a list of dicts (one for each corridor)
        if isinstance(payload, list):
            for entry in payload:
                sync_to_grid(entry)
        else:
            sync_to_grid(payload)
            
        logger.info("Phantom synchronization cycle complete.")
    except Exception as e:
        logger.error("Synchronization cycle aborted due to errors.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
