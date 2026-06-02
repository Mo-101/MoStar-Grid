#!/usr/bin/env python3
"""
MoStar Grid — Namespace-Aware Re-Import
Loads the April 6 export (92k nodes) into the running Neo4j at bolt://localhost:47687.
Each node receives its entity label PLUS the correct namespace label:
  :Grid              — all nodes
  :Grid:MindGraph    — knowledge layer
  :Grid:Phantom      — epidemiological layer
  :Grid              — core runtime (no extra subgraph label)

Relationships are loaded after all nodes.
Safe to re-run: uses MERGE on id.
"""
import os, csv
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:47687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "mostar123")

EXPORT_DIR = Path(__file__).parent.parent / "import" / "database_export"
NODES_DIR  = EXPORT_DIR / "nodes_20260406_032038"
RELS_CSV   = EXPORT_DIR / "all_relationships_20260406_032038.csv"

BATCH = 500

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


def subgraph_for(label: str) -> str:
    if label in MINDGRAPH_LABELS:
        return "MindGraph"
    if label in PHANTOM_LABELS:
        return "Phantom"
    return ""


def clean(row: dict) -> dict:
    """Strip empty strings to None so Neo4j skips them."""
    return {k: (None if v == "" else v) for k, v in row.items()}


def load_nodes(driver):
    csvs = sorted(NODES_DIR.glob("*.csv"))
    total = 0
    for csv_path in csvs:
        label = csv_path.stem
        sub   = subgraph_for(label)
        sub_clause = f"SET n:{sub}" if sub else ""

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch, count = [], 0
            for row in reader:
                batch.append(clean(row))
                if len(batch) >= BATCH:
                    _write_node_batch(driver, label, sub_clause, batch)
                    count += len(batch)
                    batch = []
            if batch:
                _write_node_batch(driver, label, sub_clause, batch)
                count += len(batch)

        total += count
        sub_tag = f" :MindGraph" if sub == "MindGraph" else f" :Phantom" if sub == "Phantom" else ""
        print(f"  :{label}{sub_tag:<14}  {count:>6} nodes")

    print(f"\n  Total nodes loaded: {total}")


def _write_node_batch(driver, label, sub_clause, batch):
    with driver.session() as s:
        s.run(f"""
            UNWIND $rows AS row
            MERGE (n:{label} {{id: row.id}})
            SET n += row
            SET n:Grid
            {sub_clause}
        """, rows=batch)


def _write_rel_batch_no_apoc(driver, batch):
    """Groups rows by rel_type and issues one MERGE per type."""
    by_type = {}
    for row in batch:
        by_type.setdefault(row["rel_type"], []).append(row)
    with driver.session() as s:
        for rel_type, rows in by_type.items():
            s.run(f"""
                UNWIND $rows AS row
                MATCH (a {{id: row.from_id}})
                MATCH (b {{id: row.to_id}})
                MERGE (a)-[:{rel_type}]->(b)
            """, rows=rows)


if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    try:
        print("═" * 60)
        print("  MoStar Grid — Namespace Import (92k)")
        print("═" * 60)
        print("\n── Nodes ──────────────────────────────────────────────────")
        load_nodes(driver)

        print("\n── Relationships ──────────────────────────────────────────")
        total = 0
        batch = []
        with open(RELS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                batch.append(row)
                if len(batch) >= BATCH:
                    _write_rel_batch_no_apoc(driver, batch)
                    total += len(batch)
                    batch = []
            if batch:
                _write_rel_batch_no_apoc(driver, batch)
                total += len(batch)
        print(f"  Total relationships loaded: {total}")

        print("\n── Final namespace counts ─────────────────────────────────")
        with driver.session() as s:
            r = s.run("""
                MATCH (n:Grid)
                RETURN
                  count(n) AS grid_total,
                  sum(CASE WHEN n:MindGraph THEN 1 ELSE 0 END) AS mindgraph,
                  sum(CASE WHEN n:Phantom   THEN 1 ELSE 0 END) AS phantom,
                  sum(CASE WHEN NOT n:MindGraph AND NOT n:Phantom THEN 1 ELSE 0 END) AS core
            """)
            rec = r.single()
            print(f"  :Grid (total)   {rec['grid_total']:>8}")
            print(f"    └ core        {rec['core']:>8}")
            print(f"    └ :MindGraph  {rec['mindgraph']:>8}")
            print(f"    └ :Phantom    {rec['phantom']:>8}")

        print("\n✅ Import complete — 🜃∴🜂")
    finally:
        driver.close()
