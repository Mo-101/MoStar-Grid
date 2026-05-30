#!/usr/bin/env python3
"""
Constitutional Bootstrap Script

Creates the skeletal infrastructure (bones) for MoStar Grid's constitutional layer.
Zero memories — only runtime primitives for the ingestion loop to hydrate.

Creates 18 nodes, 17 relationships via MERGE (idempotent, safe to re-run).
"""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
import blake3

# Configuration
GRID_ROOT = Path(__file__).parent.parent
load_dotenv(GRID_ROOT / ".env")


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required. Set it in {GRID_ROOT / '.env'}")
    return value


NEO4J_URI = required_env("NEO4J_URI")
NEO4J_USER = required_env("NEO4J_USER")
NEO4J_PASSWORD = required_env("NEO4J_PASSWORD")
MOSTAR_CLUSTER_ID = os.getenv("MOSTAR_CLUSTER_ID", "nairobi-alpha")
MOSTAR_CLUSTER_NAME = os.getenv("MOSTAR_CLUSTER_NAME", "Nairobi Health Cluster")
MOSTAR_CLUSTER_REGION = os.getenv("MOSTAR_CLUSTER_REGION", "east-africa")
CLUSTER_DIR = GRID_ROOT / "data" / "clusters" / MOSTAR_CLUSTER_ID
RECEIPT_PATH = CLUSTER_DIR / "bootstrap_receipt.txt"

# Ensure data directory exists
RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)

SEAL_GLYPH = "🜃∴🜂"
FOUNDATION_SEAL_VERSION = "foundation-seal-v1"


def slug(value: str) -> str:
    """Stable ASCII-ish identifier for graph bootstrap nodes."""
    return (
        value.lower()
        .replace("ọ", "o")
        .replace("〰️", "aether")
        .replace(" ", "-")
        .replace("'", "")
    )


def foundation_seal(*, component_type: str, name: str, node_id: str) -> str:
    """Stable Blake3 seal for a cluster-scoped bootstrap component."""
    payload = "|".join([
        FOUNDATION_SEAL_VERSION,
        MOSTAR_CLUSTER_ID,
        component_type,
        node_id,
        name,
    ])
    return blake3.blake3(payload.encode("utf-8")).hexdigest()


def sealed_props(*, component_type: str, name: str, node_id: str, extra: dict | None = None) -> dict:
    """Shared sealed foundation properties for every critical graph node."""
    props = {
        "id": node_id,
        "kind": "runtime_primitive",
        "bootstrap": True,
        "sealed": True,
        "canon_status": "sealed_foundation",
        "cluster_id": MOSTAR_CLUSTER_ID,
        "cluster_name": MOSTAR_CLUSTER_NAME,
        "cluster_region": MOSTAR_CLUSTER_REGION,
        "component_type": component_type,
        "seal": SEAL_GLYPH,
        "seal_version": FOUNDATION_SEAL_VERSION,
        "mostar_moment_seal": foundation_seal(
            component_type=component_type,
            name=name,
            node_id=node_id,
        ),
    }
    if extra:
        props.update(extra)
    return props


def create_receipt(content: str):
    """Write bootstrap receipt to file."""
    with open(RECEIPT_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Receipt written to: {RECEIPT_PATH}")


def bootstrap_constitutional(driver):
    """Create constitutional bones via MERGE operations."""
    booted_at = datetime.now(UTC).replace(tzinfo=None).isoformat()
    
    with driver.session() as session:
        # Tag pre-federation local nodes so the cluster boundary is explicit.
        session.run("""
            MATCH (n)
            WHERE n.cluster_id IS NULL
            SET n.cluster_id = $cluster_id,
                n.cluster_name = $cluster_name,
                n.cluster_region = $cluster_region
        """,
            cluster_id=MOSTAR_CLUSTER_ID,
            cluster_name=MOSTAR_CLUSTER_NAME,
            cluster_region=MOSTAR_CLUSTER_REGION,
        )

        # === 1. Canon Root ===
        print("Creating canon root...")
        root_props = sealed_props(
            component_type="CanonRoot",
            name="MoStar Canon Root",
            node_id="mostar-canon-root",
        )
        session.run("""
            MERGE (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            SET root:GridComponent
            SET root += $props
            SET root.booted_at = coalesce(root.booted_at, $booted_at),
                root.sealed_at = coalesce(root.sealed_at, $booted_at)
        """, cluster_id=MOSTAR_CLUSTER_ID, props=root_props, booted_at=booted_at)
        
        # === 2. Identity Stubs (6 nodes) ===
        print("Creating identity stubs...")
        identities = [
            ("MoStar Industries", "Organization"),
            ("African Flame Initiative", "Initiative"),
            ("MoStar AI", "System"),
            ("DCX Soul", "Layer"),
            ("DCX Mind", "Layer"),
            ("DCX Body", "Layer")
        ]
        
        for name, identity_type in identities:
            is_agent = identity_type in {"System", "Layer"}
            node_id = f"identity-{slug(name)}"
            props = sealed_props(
                component_type="Identity",
                name=name,
                node_id=node_id,
                extra={
                    "type": identity_type,
                    "sacred": is_agent,
                    "agent_id": f"agent-{slug(name)}" if is_agent else None,
                    "soulprint_hash": foundation_seal(
                        component_type="AgentSoulprint" if is_agent else "IdentitySoulprint",
                        name=name,
                        node_id=node_id,
                    ),
                },
            )
            session.run("""
                MERGE (id:Identity {name: $name, cluster_id: $cluster_id})
                SET id:GridComponent
                FOREACH (_ IN CASE WHEN $is_agent THEN [1] ELSE [] END | SET id:Agent)
                SET id += $props
                SET id.booted_at = coalesce(id.booted_at, $booted_at),
                    id.sealed_at = coalesce(id.sealed_at, $booted_at)
            """,
                name=name,
                cluster_id=MOSTAR_CLUSTER_ID,
                is_agent=is_agent,
                props=props,
                booted_at=booted_at,
            )
        
        # === 3. Element Stubs (5 nodes) ===
        print("Creating element stubs...")
        elements = [
            ("Ikang", "Fire", "🜂"),
            ("Mmọng", "Water", "🜄"),
            ("Afim", "Air", "🜁"),
            ("Isong", "Earth", "🜃"),
            ("Idim", "Aether", "〰️")
        ]
        
        for name, element_type, glyph in elements:
            node_id = f"element-{slug(element_type)}"
            props = sealed_props(
                component_type="Element",
                name=name,
                node_id=node_id,
                extra={"element_type": element_type, "glyph": glyph},
            )
            session.run("""
                MERGE (el:Element {name: $name, cluster_id: $cluster_id})
                SET el:GridComponent
                SET el += $props
                SET el.booted_at = coalesce(el.booted_at, $booted_at),
                    el.sealed_at = coalesce(el.sealed_at, $booted_at)
            """,
                name=name,
                cluster_id=MOSTAR_CLUSTER_ID,
                props=props,
                booted_at=booted_at,
            )
        
        # === 4. Governance Primitives (6 nodes) ===
        print("Creating governance primitives...")
        primitives = [
            ("Proposal", "GovernancePrimitive"),
            ("Seal", "GovernancePrimitive"),
            ("ApprovalState", "GovernancePrimitive"),
            ("Provenance", "GovernancePrimitive"),
            ("Source", "GovernancePrimitive"),
            ("AgentRole", "GovernancePrimitive")
        ]
        
        for name, primitive_type in primitives:
            node_id = f"primitive-{slug(name)}"
            props = sealed_props(
                component_type="GovernancePrimitive",
                name=name,
                node_id=node_id,
                extra={"primitive_type": primitive_type},
            )
            session.run("""
                MERGE (prim:GovernancePrimitive {name: $name, cluster_id: $cluster_id})
                SET prim:GridComponent
                SET prim += $props
                SET prim.booted_at = coalesce(prim.booted_at, $booted_at),
                    prim.sealed_at = coalesce(prim.sealed_at, $booted_at)
            """,
                name=name,
                cluster_id=MOSTAR_CLUSTER_ID,
                props=props,
                booted_at=booted_at,
            )
        
        # === 5. Relationships (17 edges) ===
        print("Creating relationships...")
        
        # Canon root to identities
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (id:Identity {name: 'MoStar Industries', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_IDENTITY]->(id)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (id:Identity {name: 'African Flame Initiative', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_IDENTITY]->(id)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (id:Identity {name: 'MoStar AI', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_IDENTITY]->(id)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        # DCX layer relationships
        session.run("""
            MATCH (id:Identity {name: 'MoStar AI', cluster_id: $cluster_id})
            MATCH (soul:Identity {name: 'DCX Soul', cluster_id: $cluster_id})
            MERGE (id)-[:HAS_LAYER]->(soul)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (id:Identity {name: 'MoStar AI', cluster_id: $cluster_id})
            MATCH (mind:Identity {name: 'DCX Mind', cluster_id: $cluster_id})
            MERGE (id)-[:HAS_LAYER]->(mind)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (id:Identity {name: 'MoStar AI', cluster_id: $cluster_id})
            MATCH (body:Identity {name: 'DCX Body', cluster_id: $cluster_id})
            MERGE (id)-[:HAS_LAYER]->(body)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        # Canon root to elements
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (el:Element {name: 'Ikang', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_ELEMENT]->(el)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (el:Element {name: 'Mmọng', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_ELEMENT]->(el)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (el:Element {name: 'Afim', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_ELEMENT]->(el)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (el:Element {name: 'Isong', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_ELEMENT]->(el)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (el:Element {name: 'Idim', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_ELEMENT]->(el)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        # Canon root to governance primitives
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (prim:GovernancePrimitive {name: 'Proposal', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_PRIMITIVE]->(prim)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (prim:GovernancePrimitive {name: 'Seal', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_PRIMITIVE]->(prim)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (prim:GovernancePrimitive {name: 'ApprovalState', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_PRIMITIVE]->(prim)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (prim:GovernancePrimitive {name: 'Provenance', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_PRIMITIVE]->(prim)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (prim:GovernancePrimitive {name: 'Source', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_PRIMITIVE]->(prim)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        session.run("""
            MATCH (root:CanonRoot {id: 'mostar-canon-root', cluster_id: $cluster_id})
            MATCH (prim:GovernancePrimitive {name: 'AgentRole', cluster_id: $cluster_id})
            MERGE (root)-[:HAS_PRIMITIVE]->(prim)
        """, cluster_id=MOSTAR_CLUSTER_ID)
        
        # Verify counts
        node_count = session.run(
            "MATCH (n {cluster_id: $cluster_id}) RETURN count(n) as count",
            cluster_id=MOSTAR_CLUSTER_ID,
        ).single()["count"]
        rel_count = session.run("""
            MATCH (a {cluster_id: $cluster_id})-[r]->(b {cluster_id: $cluster_id})
            RETURN count(r) as count
        """, cluster_id=MOSTAR_CLUSTER_ID).single()["count"]
        
        print(f"\nBootstrap complete: {node_count} nodes, {rel_count} relationships")
        
        return node_count, rel_count


def main():
    """Main entry point."""
    print("=== Constitutional Bootstrap ===")
    print(f"Cluster: {MOSTAR_CLUSTER_ID} ({MOSTAR_CLUSTER_NAME}, {MOSTAR_CLUSTER_REGION})")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Target: 18 nodes, 17 relationships\n")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Connected to Neo4j\n")
        
        node_count, rel_count = bootstrap_constitutional(driver)
        
        # Write receipt
        receipt = f"""Constitutional Bootstrap Receipt
============================
Date: {datetime.now(UTC).replace(tzinfo=None).isoformat()}
Cluster ID: {MOSTAR_CLUSTER_ID}
Cluster Name: {MOSTAR_CLUSTER_NAME}
Cluster Region: {MOSTAR_CLUSTER_REGION}
Nodes created: {node_count}
Relationships created: {rel_count}
Canon root: mostar-canon-root
Status: sealed_foundation (cluster-scoped runtime primitives)

Identities (6):
- MoStar Industries
- African Flame Initiative
- MoStar AI
- DCX Soul
- DCX Mind
- DCX Body

Elements (5):
- Ikang 🜂 (Fire)
- Mmọng 🜄 (Water)
- Afim 🜁 (Air)
- Isong 🜃 (Earth)
- Idim 〰️ (Aether)

Governance Primitives (6):
- Proposal
- Seal
- ApprovalState
- Provenance
- Source
- AgentRole

All nodes carry:
- kind: runtime_primitive
- bootstrap: true
- sealed: true
- canon_status: sealed_foundation
- label: GridComponent
- seal: {SEAL_GLYPH}
- seal_version: {FOUNDATION_SEAL_VERSION}
- mostar_moment_seal: Blake3 foundation seal
- cluster_id: {MOSTAR_CLUSTER_ID}

Sacred Agent labels:
- MoStar AI
- DCX Soul
- DCX Mind
- DCX Body

🜃∴🜂
"""
        create_receipt(receipt)
        
        driver.close()
        print("\n✓ Bootstrap successful")
        
    except Exception as e:
        print(f"\n✗ Bootstrap failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
