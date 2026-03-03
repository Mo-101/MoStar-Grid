# ═══════════════════════════════════════════════════════════════
# MOSTAR GRID — LIVE TELEMETRY QUERIES
# Powers the Hyper-Spine Dashboard with real Neo4j data
# MSTR-⚡
# ═══════════════════════════════════════════════════════════════

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "mostar123") # Update to mostar123 based on recent usage

def _get_driver():
    if not NEO4J_AVAILABLE:
        return None
    try:
        return GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASS),
            connection_timeout=3,
        )
    except Exception as e:
        logging.warning(f"[TELEMETRY] Neo4j driver failed: {e}")
        return None


def get_grid_telemetry() -> dict:
    """
    Full Grid telemetry for Hyper-Spine Dashboard.
    Returns live counts, recent moments, layer health,
    node label distribution, and system vitals.
    """
    driver = _get_driver()
    if not driver:
        return _offline_fallback()

    try:
        with driver.session() as s:
            # ── Total node count ──────────────────────────────
            total = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]

            # ── Node label distribution ───────────────────────
            label_rows = s.run("""
                MATCH (n)
                UNWIND labels(n) AS lbl
                RETURN lbl, count(*) AS cnt
                ORDER BY cnt DESC
                LIMIT 30
            """).data()

            # ── Recent MoStarMoments (last 24hr) ─────────────
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            moments_24h = s.run("""
                MATCH (m:MoStarMoment)
                WHERE m.timestamp >= $cutoff
                RETURN count(m) AS c
            """, cutoff=cutoff).single()["c"]

            # ── Moment layer distribution ─────────────────────
            layer_dist = s.run("""
                MATCH (m:MoStarMoment)
                RETURN m.layer AS layer,
                       count(m) AS cnt,
                       avg(m.resonance_score) AS avg_res
                ORDER BY cnt DESC
            """).data()

            # ── Last 10 moments ───────────────────────────────
            recent = s.run("""
                MATCH (m:MoStarMoment)
                RETURN m.quantum_id    AS id,
                       m.initiator     AS initiator,
                       m.receiver      AS receiver,
                       m.description   AS description,
                       m.trigger_type  AS trigger_type,
                       m.resonance_score AS resonance,
                       m.layer         AS layer,
                       m.timestamp     AS timestamp
                ORDER BY m.timestamp DESC
                LIMIT 10
            """).data()

            # ── Ifa system stats ──────────────────────────────
            ifa_count = s.run("""
                MATCH (n:IfaMajorOdu) RETURN count(n) AS c
            """).single()["c"]

            odu_count = s.run("""
                MATCH (n:IfaCompoundOdu) RETURN count(n) AS c
            """).single()["c"]

            # ── Ibibio stats ──────────────────────────────────
            ibibio_words = s.run("""
                MATCH (n:IbibioWord) RETURN count(n) AS c
            """).single()["c"]

            ibibio_audio = s.run("""
                MATCH (n:IbibioAudio) RETURN count(n) AS c
            """).single()["c"]

            # ── Agent count ───────────────────────────────────
            agents = s.run("""
                MATCH (n:Agent) RETURN count(n) AS c
            """).single()["c"]

            # ── Relationship count ────────────────────────────
            rel_count = s.run("""
                MATCH ()-[r]->() RETURN count(r) AS c
            """).single()["c"]

            # ── Avg resonance all time ────────────────────────
            avg_res_row = s.run("""
                MATCH (m:MoStarMoment)
                RETURN avg(m.resonance_score) AS avg_res
            """).single()
            avg_resonance = round(avg_res_row["avg_res"] or 0, 3)

            # ── Layer node mapping ────────────────────────────
            layer_nodes = _map_labels_to_layers(label_rows)

        driver.close()

        return {
            "status":         "live",
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "insignia":       "MSTR-⚡",

            # Core counts
            "total_nodes":    total,
            "total_relations": rel_count,
            "total_moments":  sum(1 for r in recent) if recent else 0,
            "moments_24h":    moments_24h,
            "avg_resonance":  avg_resonance,
            "agents":         agents,

            # Domain counts
            "ifa_major_odu":  ifa_count,
            "ifa_compound_odu": odu_count,
            "ibibio_words":   ibibio_words,
            "ibibio_audio":   ibibio_audio,

            # Layer data for dashboard nodes
            "layer_nodes":    layer_nodes,
            "layer_moments":  {
                r["layer"] or "UNKNOWN": {
                    "count":       r["cnt"],
                    "avg_resonance": round(r["avg_res"] or 0, 3),
                }
                for r in layer_dist
            },

            # Recent activity feed
            "recent_moments": recent,

            # Label distribution
            "label_counts": {r["lbl"]: r["cnt"] for r in label_rows},
        }

    except Exception as e:
        logging.error(f"[TELEMETRY] Query failed: {e}")
        if driver:
            driver.close()
        return _offline_fallback()


def get_node_detail(node_id: str) -> dict:
    """
    Fetch live Neo4j data for a specific dashboard node ID.
    Maps dashboard node IDs to Neo4j labels/queries.
    """
    driver = _get_driver()
    if not driver:
        return {"status": "offline", "node_id": node_id}

    # Dashboard node → Neo4j query mapping
    NODE_QUERIES = {
        "truth_engine": """
            MATCH (m:MoStarMoment {trigger_type: 'boot'})
            RETURN count(m) AS activations,
                   max(m.timestamp) AS last_active
        """,
        "radx_consensus": """
            MATCH (m:MoStarMoment)
            WHERE m.trigger_type IN ['maternal_alert','health_signal','voice_dialogue']
            RETURN count(m) AS signals,
                   avg(m.resonance_score) AS avg_res,
                   max(m.timestamp) AS last_signal
        """,
        "scope_firewall": """
            MATCH (m:MoStarMoment {trigger_type: 'covenant_violation'})
            RETURN count(m) AS violations,
                   max(m.timestamp) AS last_violation
        """,
        "compliance_gate": """
            MATCH (m:MoStarMoment {trigger_type: 'capture_alarm'})
            RETURN count(m) AS alarms
        """,
        "ledger_audit": """
            MATCH (m:MoStarMoment)
            RETURN count(m) AS total_moments,
                   avg(m.resonance_score) AS avg_resonance
        """,
        "capture_alarm": """
            MATCH (m:MoStarMoment {trigger_type: 'capture_alarm'})
            RETURN count(m) AS total_alarms,
                   max(m.timestamp) AS last_alarm
        """,
        "drift_engine": """
            MATCH (m:MoStarMoment)
            WHERE m.resonance_score < 0.5
            RETURN count(m) AS low_resonance_events
        """,
    }

    default_q = """
        MATCH (m:MoStarMoment)
        WHERE m.receiver CONTAINS $node_id OR m.initiator CONTAINS $node_id
        RETURN count(m) AS related_moments,
               max(m.timestamp) AS last_active
    """

    try:
        with driver.session() as s:
            q = NODE_QUERIES.get(node_id, default_q)
            result = s.run(q, node_id=node_id).data()
        driver.close()
        return {
            "status":  "live",
            "node_id": node_id,
            "data":    result[0] if result else {},
        }
    except Exception as e:
        driver.close()
        return {"status": "error", "node_id": node_id, "error": str(e)}


def _map_labels_to_layers(label_rows: list) -> dict:
    """Map Neo4j labels to dashboard layer IDs."""
    LABEL_LAYER_MAP = {
        # Covenant Kernel
        "MoStarMoment":       "COVENANT_KERNEL",
        "MoScriptExecution":  "COVENANT_KERNEL",
        "GridDocument":       "COVENANT_KERNEL",

        # Mesh Intelligence
        "IfaMajorOdu":        "MESH_INTELLIGENCE",
        "IfaCompoundOdu":     "MESH_INTELLIGENCE",
        "IfaOduOntology":     "MESH_INTELLIGENCE",
        "IbibioWord":         "MESH_INTELLIGENCE",
        "IbibioAudio":        "MESH_INTELLIGENCE",
        "IbibioDictionaryEntry": "MESH_INTELLIGENCE",
        "AfricanPhilosophies":"MESH_INTELLIGENCE",
        "KnowledgeGraph":     "MESH_INTELLIGENCE",
        "OmniNeuroSymbolicAi":"MESH_INTELLIGENCE",

        # Execution Ring
        "Agent":              "EXECUTION_RING",
        "HealingPractice":    "EXECUTION_RING",
        "MedicinalPlants":    "EXECUTION_RING",
        "Plant":              "EXECUTION_RING",
        "Event":              "EXECUTION_RING",
        "Culture":            "EXECUTION_RING",
        "IndigenousGovernance":"EXECUTION_RING",

        # Ledger Spine
        "MostarApiDoc":       "LEDGER_SPINE",
        "APIEndpoint":        "LEDGER_SPINE",
        "GridBinaryDoc":      "LEDGER_SPINE",
        "Neo4jSnapshot":      "LEDGER_SPINE",

        # Public Interface
        "Entity":             "PUBLIC_INTERFACE",
        "Metric":             "PUBLIC_INTERFACE",
        "Neo4jMetrics":       "PUBLIC_INTERFACE",
    }

    layer_totals = {}
    for row in label_rows:
        layer = LABEL_LAYER_MAP.get(row["lbl"], "MESH_INTELLIGENCE")
        layer_totals[layer] = layer_totals.get(layer, 0) + row["cnt"]

    return layer_totals


def _offline_fallback() -> dict:
    return {
        "status":        "offline",
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "insignia":      "MSTR-⚡",
        "total_nodes":   0,
        "moments_24h":   0,
        "avg_resonance": 0,
        "agents":        0,
        "layer_nodes":   {},
        "layer_moments": {},
        "recent_moments": [],
        "label_counts":  {},
    }
