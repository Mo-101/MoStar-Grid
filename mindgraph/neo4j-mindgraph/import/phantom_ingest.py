import json
from neo4j import GraphDatabase
import os
from datetime import datetime

class PhantomIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ingest_phantom_payload(self, payload: dict):
        """
        Receives a Phantom JSON output payload and merges it into the Neo4j Mother Graph
        as part of the Phantom Epidemiological Subgraph.
        """
        with self.driver.session() as session:
            session.execute_write(self._merge_epi_risk, payload)
            
            if "drift_metrics" in payload:
                session.execute_write(self._merge_drift_watch, payload)
                
            if "dissent" in payload:
                session.execute_write(self._merge_dissent, payload)

    @staticmethod
    def _merge_epi_risk(tx, payload):
        query = """
        // 1. Ensure the Corridor exists
        MERGE (c:CorridorNode {location: $location})
        
        // 2. Create the central EpiRiskNode for this week
        MERGE (r:EpiRiskNode {id: $id})
        ON CREATE SET 
            r.week_id = $week_id,
            r.fireScore = $fire_score,
            r.diseaseFloor = $disease_floor,
            r.timestamp = $timestamp,
            r.sealed = $sealed,
            r.covenant_seal = $covenant_seal
        ON MATCH SET 
            r.fireScore = $fire_score,
            r.diseaseFloor = $disease_floor,
            r.timestamp = $timestamp,
            r.sealed = $sealed,
            r.covenant_seal = $covenant_seal
            
        // 3. Link Corridor to Risk
        MERGE (c)-[:HAS_EPIDEMIOLOGICAL_RISK]->(r)
        
        // 4. Link back to AFRO Sentinel Signals
        WITH r
        UNWIND $signal_ids AS signal_id
        MERGE (s:SignalNode {id: signal_id})
        MERGE (r)-[:INFLUENCED_BY]->(s)
        """
        tx.run(query, 
               location=payload["location"],
               id=payload["id"],
               week_id=payload["week_id"],
               fire_score=payload["fire_score"],
               disease_floor=payload["disease_floor"],
               timestamp=payload.get("timestamp", datetime.now().isoformat()),
               sealed=payload.get("sealed", True),
               covenant_seal=payload.get("covenant_seal", ""),
               signal_ids=payload.get("signal_ids", [])
        )

    @staticmethod
    def _merge_drift_watch(tx, payload):
        query = """
        MATCH (r:EpiRiskNode {id: $id})
        UNWIND $drift_metrics AS drift
        MERGE (d:DriftWatchNode {id: drift.id})
        ON CREATE SET 
            d.metric = drift.metric,
            d.severity = drift.severity,
            d.detected_at = drift.detected_at
        MERGE (r)-[:DRIFT_DETECTED_IN]->(d)
        """
        tx.run(query, id=payload["id"], drift_metrics=payload["drift_metrics"])

    @staticmethod
    def _merge_dissent(tx, payload):
        query = """
        MATCH (r:EpiRiskNode {id: $id})
        UNWIND $dissent AS d
        MERGE (node:DissentNode {id: d.id})
        ON CREATE SET 
            node.analyst = d.analyst,
            node.dissent_reason = d.reason,
            node.timestamp = d.timestamp
        MERGE (r)-[:CHALLENGED_BY]->(node)
        """
        tx.run(query, id=payload["id"], dissent=payload["dissent"])


# Webhook Entry Point (Example)
def handle_webhook_payload(payload_json: str):
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Mogrid101")
    
    ingestor = PhantomIngestor(uri, user, password)
    try:
        payload = json.loads(payload_json)
        ingestor.ingest_phantom_payload(payload)
        return {"status": "success", "message": "Phantom Epi Subgraph updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        ingestor.close()
