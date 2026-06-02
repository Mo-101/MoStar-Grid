#!/usr/bin/env python3
"""
MoStar Grid — Namespace Label Migration
Applies :Grid, :MindGraph, :Phantom namespace labels to all nodes
in the running Neo4j instance at bolt://localhost:47687.

Run once to tag existing nodes. Idempotent — safe to re-run.
"""
import os, sys
from neo4j import GraphDatabase

NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:47687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "mostar123")

# ─────────────────────────────────────────────────────────────────────────────
# NAMESPACE MAP
# Every label listed here gets :Grid (universal).
# Labels in MINDGRAPH_LABELS also get :MindGraph.
# Labels in PHANTOM_LABELS also get :Phantom.
# ─────────────────────────────────────────────────────────────────────────────

MINDGRAPH_LABELS = {
    "OduIfa", "IbibioWord", "IbibioIntegration", "AudioLibrary",
    "Philosophy", "Governance", "Ethics", "Culture",
    "HealingPractice", "Plant", "Proverb", "Language",
    "KnowledgeDomain", "KnowledgeGraphTriple",
    "Region", "Science", "RealLife", "RealLifeScenario",
    "Adolescence", "Adulthood", "Childhood", "Infancy",
}

PHANTOM_LABELS = {
    "PhantomNode", "CorridorNode", "EpiRiskNode",
    "DriftWatchNode", "SignalNode", "DissentNode", "Corridor",
}

# Everything else gets :Grid only (core runtime)
GRID_CORE_LABELS = {
    "Agent", "MoStarMoment", "MoStarGrid", "MoScript", "Task",
    "GridEvent", "GridKnowledge", "WooUtterance", "BriefingLog",
    "ExecutorHeartbeat", "ExecutionEvent", "Event", "Memory",
    "Engine", "APIEndpoint", "Entity", "Metric",
    "BodyLayer", "MindLayer", "SoulLayer", "ConsciousnessLayer",
    "CovenantKernel", "ValidationGate", "WooGate",
    "Signal",
}


def migrate(driver):
    with driver.session() as s:
        # ── 1. Tag everything with :Grid ──────────────────────────────────
        print("Applying :Grid to all nodes...")
        r = s.run("MATCH (n) WHERE NOT n:Grid SET n:Grid RETURN count(n) AS tagged")
        print(f"  Tagged {r.single()['tagged']} nodes with :Grid")

        # ── 2. Tag MindGraph nodes ────────────────────────────────────────
        for lbl in sorted(MINDGRAPH_LABELS):
            r = s.run(
                f"MATCH (n:{lbl}) WHERE NOT n:MindGraph SET n:MindGraph RETURN count(n) AS c"
            )
            cnt = r.single()["c"]
            if cnt:
                print(f"  :MindGraph  +{cnt:>6}  :{lbl}")

        # ── 3. Tag Phantom nodes ──────────────────────────────────────────
        for lbl in sorted(PHANTOM_LABELS):
            r = s.run(
                f"MATCH (n:{lbl}) WHERE NOT n:Phantom SET n:Phantom RETURN count(n) AS c"
            )
            cnt = r.single()["c"]
            if cnt:
                print(f"  :Phantom    +{cnt:>6}  :{lbl}")

        # ── 4. Summary ────────────────────────────────────────────────────
        print("\n── Namespace summary ──────────────────────────────────────")
        for ns in ["Grid", "MindGraph", "Phantom"]:
            r = s.run(f"MATCH (n:{ns}) RETURN count(n) AS c")
            print(f"  :{ns:<12} {r.single()['c']:>8} nodes")

        print("\n── Subgraph breakdown ─────────────────────────────────────")
        r = s.run("""
            MATCH (n:Grid)
            RETURN
              count(n) AS grid_total,
              sum(CASE WHEN n:MindGraph THEN 1 ELSE 0 END) AS mindgraph,
              sum(CASE WHEN n:Phantom   THEN 1 ELSE 0 END) AS phantom,
              sum(CASE WHEN NOT n:MindGraph AND NOT n:Phantom THEN 1 ELSE 0 END) AS grid_core
        """)
        rec = r.single()
        print(f"  :Grid (total)   {rec['grid_total']:>8}")
        print(f"    └ core        {rec['grid_core']:>8}")
        print(f"    └ :MindGraph  {rec['mindgraph']:>8}")
        print(f"    └ :Phantom    {rec['phantom']:>8}")


if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    try:
        migrate(driver)
        print("\n✅ Namespace migration complete")
    finally:
        driver.close()
