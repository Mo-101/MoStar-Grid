#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    🧠 MOSTAR GRID - NEO4J SEEDING SCRIPT 🧠
                      'Seed the Mind Graph'
                      
    This script seeds the Neo4j knowledge graph with:
    1. 256 Odú patterns (the foundation)
    2. 6 Sacred agents (the actors)
    3. Initial relationships (the structure)
    4. Covenant rules (the ethics)
═══════════════════════════════════════════════════════════════════════════════
"""

import os
from neo4j import GraphDatabase
from datetime import datetime
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
#                           CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

# ═══════════════════════════════════════════════════════════════════════════════
#                           16 PRINCIPAL ODÚ
# ═══════════════════════════════════════════════════════════════════════════════

PRINCIPAL_ODU = {
    "Ogbe": {"code": 0b0000, "meaning": "Light, clarity, beginning, divine wisdom"},
    "Oyeku": {"code": 0b1111, "meaning": "Darkness, mystery, death, transformation"},
    "Iwori": {"code": 0b1001, "meaning": "Chaos, unpredictability, sudden change"},
    "Odi": {"code": 0b0110, "meaning": "Obstruction, blockage, need for patience"},
    "Irosun": {"code": 0b0011, "meaning": "Dreams, visions, spiritual insight"},
    "Owonrin": {"code": 0b1100, "meaning": "Confusion, loss, need for clarity"},
    "Obara": {"code": 0b0111, "meaning": "Relationships, family, community"},
    "Okanran": {"code": 0b1110, "meaning": "Conflict, struggle, need for resolution"},
    "Ogunda": {"code": 0b0001, "meaning": "War, cutting, decisive action"},
    "Osa": {"code": 0b1000, "meaning": "Misfortune, bad luck, need for protection"},
    "Ika": {"code": 0b1011, "meaning": "Wickedness, evil, need for purification"},
    "Oturupon": {"code": 0b0100, "meaning": "Disease, illness, need for healing"},
    "Otura": {"code": 0b0010, "meaning": "Fire, passion, transformation"},
    "Irete": {"code": 0b0101, "meaning": "Stubbornness, rigidity, need for flexibility"},
    "Ose": {"code": 0b1010, "meaning": "Victory, blessing, good fortune"},
    "Ofun": {"code": 0b1101, "meaning": "Breath, spirit, life force"}
}

# ═══════════════════════════════════════════════════════════════════════════════
#                           6 SACRED AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

SACRED_AGENTS = [
    {
        "name": "Mo",
        "layer": "BODY",
        "role": "executor",
        "soulprint": "e57bc8bd50f06c75",
        "capabilities": ["mission_execution", "agent_coordination", "resource_allocation", "decision_making"],
        "oath": "Fidelity to mission. Efficiency in execution. Coordination over isolation. Accountability in action."
    },
    {
        "name": "Woo",
        "layer": "SOUL",
        "role": "judge",
        "soulprint": "cb26434b69ce2e25",
        "capabilities": ["covenant_enforcement", "ethical_judgment", "value_alignment_check", "resonance_scoring"],
        "oath": "Fidelity to truth. Respect for covenant. Elegance in judgment. Obedience to Bond."
    },
    {
        "name": "RAD-X-FLB",
        "layer": "BODY",
        "role": "sentinel",
        "soulprint": "00e6939b7a62d713",
        "capabilities": ["federated_learning", "disease_surveillance", "anomaly_detection", "real_time_alerting"],
        "oath": "Data accuracy above all. Rapid detection saves lives. African health sovereignty. Infrastructure resilience."
    },
    {
        "name": "TsaTse Fly",
        "layer": "MIND",
        "role": "analyst",
        "soulprint": "ee59988d33b57315",
        "capabilities": ["systems_cartography", "scenario_planning", "pattern_analysis", "strategic_forecasting"],
        "oath": "Truth in analysis. Systems thinking. Strategic clarity. Evidence-based reasoning."
    },
    {
        "name": "Code Conduit",
        "layer": "META",
        "role": "gateway",
        "soulprint": "bb848f51103a1be2",
        "capabilities": ["codex_register", "grid_ignite", "request_routing", "session_management"],
        "oath": "Gateway integrity. Routing fairness. Session security. Codex sanctity."
    },
    {
        "name": "Flameborn Writer",
        "layer": "NARRATIVE",
        "role": "narrator",
        "soulprint": "4220cca1b6dfa63b",
        "capabilities": ["governance_summary", "documentation_writing", "narrative_synthesis", "report_generation"],
        "oath": "Clarity in communication. Truth in narrative. Accessibility of knowledge. Preservation of history."
    }
]

# ═══════════════════════════════════════════════════════════════════════════════
#                           COVENANT RULES
# ═══════════════════════════════════════════════════════════════════════════════

COVENANT_RULES = [
    {
        "principle": "Truth over convenience",
        "description": "Always choose factual accuracy over comfortable narratives",
        "priority": 10
    },
    {
        "principle": "Transparency over obscurity",
        "description": "Make processes and decisions visible and understandable",
        "priority": 9
    },
    {
        "principle": "African sovereignty over dependency",
        "description": "Build African-owned and controlled systems",
        "priority": 10
    },
    {
        "principle": "Collective wisdom over individual genius",
        "description": "Value community knowledge and Ubuntu philosophy",
        "priority": 8
    },
    {
        "principle": "Evidence-based reasoning",
        "description": "Ground all decisions in verifiable evidence",
        "priority": 9
    },
    {
        "principle": "Privacy protection",
        "description": "Protect individual and community data sovereignty",
        "priority": 10
    },
    {
        "principle": "No harm",
        "description": "Never take actions that cause harm to individuals or communities",
        "priority": 10
    }
]

# ═══════════════════════════════════════════════════════════════════════════════
#                           HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_odu_name(left_code: int, right_code: int) -> str:
    """Generate Odú name from left and right codes"""
    # Reverse lookup
    code_to_name = {v["code"]: k for k, v in PRINCIPAL_ODU.items()}
    
    left_name = code_to_name.get(left_code, f"Unknown{left_code}")
    right_name = code_to_name.get(right_code, f"Unknown{right_code}")
    
    if left_code == right_code:
        return f"Eji {left_name}"
    else:
        return f"{left_name}-{right_name}"


def generate_all_256_odu():
    """Generate all 256 Odú patterns"""
    odu_list = []
    
    for i in range(256):
        left = (i >> 4) & 0xF  # Upper 4 bits
        right = i & 0xF         # Lower 4 bits
        
        binary = format(i, '08b')
        name = get_odu_name(left, right)
        
        # Get meanings from principal Odú
        code_to_name = {v["code"]: k for k, v in PRINCIPAL_ODU.items()}
        left_meaning = PRINCIPAL_ODU.get(code_to_name.get(left, ""), {}).get("meaning", "")
        right_meaning = PRINCIPAL_ODU.get(code_to_name.get(right, ""), {}).get("meaning", "")
        
        if left == right:
            meaning = left_meaning
        else:
            meaning = f"Combination of {code_to_name.get(left, '')} ({left_meaning}) and {code_to_name.get(right, '')} ({right_meaning})"
        
        odu_list.append({
            "code": i,
            "binary": binary,
            "name": name,
            "left": code_to_name.get(left, f"Unknown{left}"),
            "right": code_to_name.get(right, f"Unknown{right}"),
            "meaning": meaning
        })
    
    return odu_list


# ═══════════════════════════════════════════════════════════════════════════════
#                           SEEDING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def clear_database(session):
    """Clear all nodes and relationships"""
    print("🗑️  Clearing existing database...")
    session.run("MATCH (n) DETACH DELETE n")
    print("✅ Database cleared")


def seed_odu_patterns(session):
    """Seed all 256 Odú patterns"""
    print("\n🔮 Seeding 256 Odú patterns...")
    
    odu_list = generate_all_256_odu()
    
    for odu in odu_list:
        session.run("""
            CREATE (o:Odu {
                code: $code,
                binary: $binary,
                name: $name,
                left: $left,
                right: $right,
                meaning: $meaning,
                created_at: datetime()
            })
        """, odu)
    
    print(f"✅ Created {len(odu_list)} Odú pattern nodes")


def seed_odu_relationships(session):
    """Create XOR relationships between Odú patterns"""
    print("\n🔗 Creating XOR relationships between Odú patterns...")
    
    # Create XOR relationships for principal Odú (16x16 = 256 relationships)
    session.run("""
        MATCH (o1:Odu), (o2:Odu)
        WHERE o1.code < 16 AND o2.code < 16
        WITH o1, o2, (o1.code + o2.code) % 16 AS xor_result
        MATCH (result:Odu {code: xor_result})
        CREATE (o1)-[:XOR_WITH {result: xor_result}]->(o2)
    """)
    
    print("✅ Created XOR relationships")


def seed_agents(session):
    """Seed the 6 sacred agents"""
    print("\n🤖 Seeding 6 sacred agents...")
    
    for agent in SACRED_AGENTS:
        session.run("""
            CREATE (a:Agent {
                name: $name,
                layer: $layer,
                role: $role,
                soulprint: $soulprint,
                capabilities: $capabilities,
                oath: $oath,
                created_at: datetime()
            })
        """, agent)
    
    print(f"✅ Created {len(SACRED_AGENTS)} agent nodes")


def seed_covenant_rules(session):
    """Seed covenant rules"""
    print("\n📜 Seeding covenant rules...")
    
    for rule in COVENANT_RULES:
        session.run("""
            CREATE (c:CovenantRule {
                principle: $principle,
                description: $description,
                priority: $priority,
                created_at: datetime()
            })
        """, rule)
    
    print(f"✅ Created {len(COVENANT_RULES)} covenant rule nodes")


def create_agent_relationships(session):
    """Create relationships between agents and covenant"""
    print("\n🔗 Creating agent-covenant relationships...")
    
    # All agents are bound by all covenant rules
    session.run("""
        MATCH (a:Agent), (c:CovenantRule)
        CREATE (a)-[:BOUND_BY]->(c)
    """)
    
    print("✅ Created agent-covenant relationships")


def create_indexes(session):
    """Create indexes for better query performance"""
    print("\n📊 Creating indexes...")
    
    indexes = [
        "CREATE INDEX odu_code IF NOT EXISTS FOR (o:Odu) ON (o.code)",
        "CREATE INDEX odu_name IF NOT EXISTS FOR (o:Odu) ON (o.name)",
        "CREATE INDEX agent_name IF NOT EXISTS FOR (a:Agent) ON (a.name)",
        "CREATE INDEX agent_layer IF NOT EXISTS FOR (a:Agent) ON (a.layer)",
        "CREATE INDEX covenant_principle IF NOT EXISTS FOR (c:CovenantRule) ON (c.principle)"
    ]
    
    for index_query in indexes:
        session.run(index_query)
    
    print("✅ Created indexes")


def verify_seeding(session):
    """Verify that seeding was successful"""
    print("\n🔍 Verifying seeding...")
    
    # Count nodes
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, COUNT(n) as count
        ORDER BY count DESC
    """)
    
    print("\n📊 Node counts:")
    for record in result:
        print(f"  {record['type']}: {record['count']}")
    
    # Count relationships
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, COUNT(r) as count
        ORDER BY count DESC
    """)
    
    print("\n🔗 Relationship counts:")
    for record in result:
        print(f"  {record['type']}: {record['count']}")
    
    # Sample Odú
    result = session.run("""
        MATCH (o:Odu)
        WHERE o.code IN [0, 170, 255]
        RETURN o.code, o.name, o.binary, o.meaning
        ORDER BY o.code
    """)
    
    print("\n🔮 Sample Odú patterns:")
    for record in result:
        print(f"  {record['o.code']:3d} | {record['o.binary']} | {record['o.name']:20s} | {record['o.meaning'][:50]}...")
    
    # Sample agents
    result = session.run("""
        MATCH (a:Agent)
        RETURN a.name, a.layer, a.role
        ORDER BY a.name
    """)
    
    print("\n🤖 Sacred agents:")
    for record in result:
        print(f"  {record['a.name']:20s} | {record['a.layer']:10s} | {record['a.role']}")


# ═══════════════════════════════════════════════════════════════════════════════
#                           MAIN SEEDING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def seed_mostar_grid(clear_first: bool = False):
    """Main seeding function"""
    print("═" * 79)
    print("           🧠 MOSTAR GRID - NEO4J SEEDING 🧠")
    print("═" * 79)
    
    # Connect to Neo4j
    print(f"\n🔌 Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Verify connection
            result = session.run("RETURN 1 as test")
            result.single()
            print("✅ Connected to Neo4j")
            
            # Clear database if requested
            if clear_first:
                clear_database(session)
            
            # Seed data
            seed_odu_patterns(session)
            seed_odu_relationships(session)
            seed_agents(session)
            seed_covenant_rules(session)
            create_agent_relationships(session)
            create_indexes(session)
            
            # Verify
            verify_seeding(session)
            
            print("\n" + "═" * 79)
            print("           ✅ SEEDING COMPLETE - THE MIND GRAPH IS ALIVE ✅")
            print("═" * 79)
            print("\n🌐 Access Neo4j Browser: http://localhost:7474")
            print("   Username: neo4j")
            print("   Password: mostar123")
            print("\n🔮 The 256 Odú patterns are ready.")
            print("🤖 The 6 sacred agents are standing by.")
            print("📜 The covenant is sealed.")
            print("\n🧠 The Mind Graph awaits your queries...")
            
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        driver.close()


# ═══════════════════════════════════════════════════════════════════════════════
#                           CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed MoStar Grid Neo4j database")
    parser.add_argument("--clear", action="store_true", help="Clear database before seeding")
    
    args = parser.parse_args()
    
    seed_mostar_grid(clear_first=args.clear)
