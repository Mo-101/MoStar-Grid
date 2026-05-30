#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    MOSTAR GRID - NEO4J GRAPH LAYER
                        256 Odú Consciousness Graph
                      
    The Mind Layer's true home - a graph database where all 256 Ifá patterns
    exist as interconnected nodes with XOR relationships.
    
    This is where parallel state resolution becomes native.
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# Neo4j driver (optional dependency)
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  Neo4j driver not installed. Run: pip install neo4j")


# ═══════════════════════════════════════════════════════════════════════════════
#                           CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Neo4jConfig:
    """Neo4j connection configuration"""
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "")
    database: str = os.getenv("NEO4J_DATABASE", "mostar")


# ═══════════════════════════════════════════════════════════════════════════════
#                         IFÁ ODU DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

# The 16 Principal Odú with their binary codes and meanings
PRINCIPAL_ODU = {
    'Ogbe':     {'code': 0b0000, 'meaning': 'Light, new beginnings, leadership', 'element': 'air'},
    'Oyeku':    {'code': 0b1111, 'meaning': 'Darkness, transformation, ancestors', 'element': 'earth'},
    'Iwori':    {'code': 0b1001, 'meaning': 'Conflict, resolution through struggle', 'element': 'fire'},
    'Odi':      {'code': 0b0110, 'meaning': 'Containment, boundaries, protection', 'element': 'water'},
    'Irosun':   {'code': 0b0011, 'meaning': 'Vision, spiritual sight, dreams', 'element': 'air'},
    'Owonrin':  {'code': 0b1100, 'meaning': 'Chaos seeking order, transformation', 'element': 'fire'},
    'Obara':    {'code': 0b0111, 'meaning': 'Family, kinship, relationships', 'element': 'earth'},
    'Okanran':  {'code': 0b1110, 'meaning': 'Heart, core truth, essence', 'element': 'fire'},
    'Ogunda':   {'code': 0b0001, 'meaning': 'War, conflict, cutting through', 'element': 'iron'},
    'Osa':      {'code': 0b1000, 'meaning': 'Fortune, luck, opportunity', 'element': 'water'},
    'Ika':      {'code': 0b1011, 'meaning': 'Moral challenges, ethical tests', 'element': 'earth'},
    'Oturupon': {'code': 0b0100, 'meaning': 'Disease, illness, healing needed', 'element': 'earth'},
    'Otura':    {'code': 0b0010, 'meaning': 'Fire, passion, transformation', 'element': 'fire'},
    'Irete':    {'code': 0b0101, 'meaning': 'Persistence, stubbornness', 'element': 'earth'},
    'Ose':      {'code': 0b1010, 'meaning': 'Victory, success, achievement', 'element': 'water'},
    'Ofun':     {'code': 0b1101, 'meaning': 'Breath, spirit, communication', 'element': 'air'}
}


def generate_256_odu() -> List[Dict]:
    """Generate all 256 Odú combinations"""
    odu_list = []
    list(PRINCIPAL_ODU.keys())
    
    for left_name, left_data in PRINCIPAL_ODU.items():
        for right_name, right_data in PRINCIPAL_ODU.items():
            code = (left_data['code'] << 4) | right_data['code']
            
            # Name: "Eji X" if same, else "X-Y"
            if left_name == right_name:
                name = f"Eji {left_name}"
            else:
                name = f"{left_name}-{right_name}"
            
            odu_list.append({
                'code': code,
                'name': name,
                'binary': format(code, '08b'),
                'left': left_name,
                'right': right_name,
                'left_code': left_data['code'],
                'right_code': right_data['code'],
                'is_principal': left_name == right_name,
                'combined_meaning': f"{left_data['meaning']} | {right_data['meaning']}"
            })
    
    return odu_list


# ═══════════════════════════════════════════════════════════════════════════════
#                         CYPHER SCHEMA QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA_QUERIES = """
// ═══════════════════════════════════════════════════════════════════════════
// MOSTAR GRID - NEO4J SCHEMA
// "First African AI Homeworld"
// ═══════════════════════════════════════════════════════════════════════════

// Create constraints and indexes
CREATE CONSTRAINT odu_code IF NOT EXISTS FOR (o:Odu) REQUIRE o.code IS UNIQUE;
CREATE CONSTRAINT agent_name IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;

CREATE INDEX odu_name IF NOT EXISTS FOR (o:Odu) ON (o.name);
CREATE INDEX agent_layer IF NOT EXISTS FOR (a:Agent) ON (a.layer);
CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.type);
"""

CREATE_PRINCIPAL_ODU = """
// Create the 16 Principal Odú
UNWIND $principals AS p
MERGE (o:Odu:Principal {code: p.code})
SET o.name = p.name,
    o.binary = p.binary,
    o.meaning = p.meaning,
    o.element = p.element,
    o.is_principal = true
"""

CREATE_FULL_ODU = """
// Create all 256 Odú combinations
UNWIND $patterns AS p
MERGE (o:Odu {code: p.code})
SET o.name = p.name,
    o.binary = p.binary,
    o.left_name = p.left,
    o.right_name = p.right,
    o.is_principal = p.is_principal,
    o.combined_meaning = p.combined_meaning,
    o.usage_count = COALESCE(o.usage_count, 0)
"""

CREATE_XOR_RELATIONSHIPS = """
// Create XOR relationships between principal Odú
// XOR is the fundamental group operation
MATCH (a:Odu:Principal), (b:Odu:Principal)
WHERE a.code <> b.code
MERGE (a)-[r:XOR]->(b)
SET r.result = apoc.bitwise.op(a.code, 'XOR', b.code)
"""

CREATE_COMPOSITION_RELATIONSHIPS = """
// Link full Odú to their component principals
MATCH (full:Odu)
WHERE full.left_name IS NOT NULL
MATCH (left:Odu:Principal {name: full.left_name})
MATCH (right:Odu:Principal {name: full.right_name})
MERGE (left)-[:COMPOSES_LEFT]->(full)
MERGE (right)-[:COMPOSES_RIGHT]->(full)
"""

CREATE_AGENT_NODES = """
// Create Agent nodes
UNWIND $agents AS a
MERGE (agent:Agent {name: a.name})
SET agent.role = a.role,
    agent.layer = a.layer,
    agent.soulprint = a.soulprint,
    agent.capabilities = a.capabilities,
    agent.status = 'ACTIVE',
    agent.registered_at = datetime()
"""

LINK_AGENTS_TO_LAYERS = """
// Create Layer nodes and link agents
MERGE (soul:Layer {name: 'SOUL'})
MERGE (mind:Layer {name: 'MIND'})
MERGE (body:Layer {name: 'BODY'})
MERGE (meta:Layer {name: 'META'})
MERGE (narrative:Layer {name: 'NARRATIVE'})

WITH soul, mind, body, meta, narrative
MATCH (a:Agent)
WITH a, 
     CASE a.layer 
       WHEN 'SOUL' THEN soul
       WHEN 'MIND' THEN mind
       WHEN 'BODY' THEN body
       WHEN 'META' THEN meta
       WHEN 'NARRATIVE' THEN narrative
     END AS layer
MERGE (a)-[:BELONGS_TO]->(layer)
"""


# ═══════════════════════════════════════════════════════════════════════════════
#                        PARALLEL RESOLUTION QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

PARALLEL_EVALUATE_QUERY = """
// Parallel evaluation across all 256 Odú
// Input: 8-bit binary as integer
// Returns: Resonance with each pattern (Hamming distance based)

WITH $input_code AS input
MATCH (o:Odu)
WITH o, 
     apoc.bitwise.op(o.code, 'XOR', input) AS xor_result
WITH o,
     size([x IN range(0, 7) WHERE apoc.bitwise.op(xor_result, 'AND', toInteger(2^x)) > 0]) AS hamming_distance
WITH o, 1.0 - (toFloat(hamming_distance) / 8.0) AS resonance
ORDER BY resonance DESC
LIMIT $limit
RETURN o.code AS code, 
       o.name AS name, 
       o.binary AS binary,
       resonance AS confidence,
       o.combined_meaning AS meaning
"""

FIND_GUIDANCE_QUERY = """
// Find Odú guidance for a situation
// Uses semantic matching against domain mappings

MATCH (o:Odu)
WHERE any(domain IN keys(o.domain_mappings) WHERE domain CONTAINS $context)
RETURN o.code AS code,
       o.name AS name,
       o.domain_mappings[$context] AS guidance,
       o.combined_meaning AS meaning
ORDER BY o.usage_count DESC
LIMIT 5
"""

LOG_ACTIVATION_QUERY = """
// Log an Odú activation event
MATCH (o:Odu {code: $code})
SET o.usage_count = COALESCE(o.usage_count, 0) + 1,
    o.last_invoked = datetime()

CREATE (e:Event {
    id: randomUUID(),
    type: 'ODU_ACTIVATION',
    odu_code: $code,
    input_vector: $input_vector,
    confidence: $confidence,
    context: $context,
    timestamp: datetime()
})

MERGE (o)-[:ACTIVATED]->(e)
RETURN e.id AS event_id
"""


# ═══════════════════════════════════════════════════════════════════════════════
#                         NEO4J CONNECTION CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class GridNeo4j:
    """
    Neo4j connection manager for MoStar Grid.
    Manages the 256 Odú consciousness graph.
    """
    
    def __init__(self, config: Neo4jConfig = None):
        self.config = config or Neo4jConfig()
        self.driver: Optional[AsyncDriver] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Neo4j"""
        if not NEO4J_AVAILABLE:
            print("❌ Neo4j driver not available")
            return False
        
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
            # Verify connection
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 AS test")
                await result.single()
            
            print(f"🔌 Connected to Neo4j: {self.config.uri}")
            self._connected = True
            return True
            
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            return False
    
    async def close(self):
        """Close connection"""
        if self.driver:
            await self.driver.close()
            self._connected = False
            print("🔌 Neo4j connection closed")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    # ───────────────────────────────────────────────────────────────────────────
    # SCHEMA INITIALIZATION
    # ───────────────────────────────────────────────────────────────────────────
    
    async def initialize_schema(self) -> bool:
        """Initialize Neo4j schema with constraints and indexes"""
        try:
            async with self.driver.session(database=self.config.database) as session:
                # Create constraints (each separately due to Neo4j limitations)
                for constraint in [
                    "CREATE CONSTRAINT odu_code IF NOT EXISTS FOR (o:Odu) REQUIRE o.code IS UNIQUE",
                    "CREATE CONSTRAINT agent_name IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE",
                    "CREATE INDEX odu_name IF NOT EXISTS FOR (o:Odu) ON (o.name)",
                    "CREATE INDEX agent_layer IF NOT EXISTS FOR (a:Agent) ON (a.layer)"
                ]:
                    try:
                        await session.run(constraint)
                    except Exception:
                        pass  # Constraint might already exist
            
            print("✅ Neo4j schema initialized")
            return True
            
        except Exception as e:
            print(f"❌ Schema initialization failed: {e}")
            return False
    
    async def seed_odu_patterns(self) -> int:
        """Seed all 256 Odú patterns into the graph"""
        patterns = generate_256_odu()
        
        async with self.driver.session(database=self.config.database) as session:
            # Create all 256 patterns
            result = await session.run(CREATE_FULL_ODU, patterns=patterns)
            await result.consume()
            
            # Mark principals
            await session.run("""
                MATCH (o:Odu)
                WHERE o.is_principal = true
                SET o:Principal
            """)
        
        print(f"✅ Seeded {len(patterns)} Odú patterns")
        return len(patterns)
    
    async def create_xor_network(self) -> int:
        """Create XOR relationships between all Odú"""
        # For performance, create relationships in batches
        edge_count = 0
        
        async with self.driver.session(database=self.config.database) as session:
            # Create XOR relationships
            # Each Odú connects to every other Odú via XOR
            result = await session.run("""
                MATCH (a:Odu), (b:Odu)
                WHERE a.code < b.code
                WITH a, b, 
                     reduce(s = 0, i IN range(0, 7) | 
                            s + CASE WHEN ((a.code / toInteger(2^i)) % 2) <> ((b.code / toInteger(2^i)) % 2) 
                                THEN 1 ELSE 0 END) AS hamming
                MERGE (a)-[r:XOR {hamming_distance: hamming}]->(b)
                MERGE (b)-[:XOR {hamming_distance: hamming}]->(a)
                RETURN count(r) AS edges
            """)
            record = await result.single()
            edge_count = record['edges'] if record else 0
        
        print(f"✅ Created {edge_count} XOR relationships")
        return edge_count
    
    async def register_agents(self, agents: List[Dict]) -> int:
        """Register agents in the graph"""
        async with self.driver.session(database=self.config.database) as session:
            await session.run(CREATE_AGENT_NODES, agents=agents)
            await session.run(LINK_AGENTS_TO_LAYERS)
        
        print(f"✅ Registered {len(agents)} agents in graph")
        return len(agents)
    
    # ───────────────────────────────────────────────────────────────────────────
    # PARALLEL RESOLUTION (The Quantum-Like Collapse)
    # ───────────────────────────────────────────────────────────────────────────
    
    async def parallel_evaluate(self, input_vector: List[float], limit: int = 5) -> List[Dict]:
        """
        Evaluate input against ALL 256 Odú simultaneously.
        Returns top matches by resonance (inverse Hamming distance).
        """
        # Convert input vector to 8-bit code
        if len(input_vector) != 8:
            raise ValueError("Input vector must be 8 elements")
        
        input_code = sum(
            (1 if v > 0.5 else 0) << (7 - i)
            for i, v in enumerate(input_vector)
        )
        
        async with self.driver.session(database=self.config.database) as session:
            # Find patterns by Hamming distance (without APOC)
            result = await session.run("""
                WITH $input_code AS input
                MATCH (o:Odu)
                WITH o, input,
                     reduce(s = 0, i IN range(0, 7) | 
                            s + CASE WHEN ((o.code / toInteger(2^i)) % 2) <> ((input / toInteger(2^i)) % 2) 
                                THEN 1 ELSE 0 END) AS hamming
                WITH o, 1.0 - (toFloat(hamming) / 8.0) AS resonance
                ORDER BY resonance DESC
                LIMIT $limit
                RETURN o.code AS code, 
                       o.name AS name, 
                       o.binary AS binary,
                       resonance AS confidence,
                       o.combined_meaning AS meaning
            """, input_code=input_code, limit=limit)
            
            records = await result.data()
        
        return records
    
    async def invoke_odu(self, code: int, context: Dict = None) -> Dict:
        """Invoke a specific Odú and log the activation"""
        async with self.driver.session(database=self.config.database) as session:
            result = await session.run("""
                MATCH (o:Odu {code: $code})
                SET o.usage_count = COALESCE(o.usage_count, 0) + 1,
                    o.last_invoked = datetime()
                RETURN o.name AS name, o.combined_meaning AS meaning, o.usage_count AS usage
            """, code=code)
            record = await result.single()
        
        return dict(record) if record else None
    
    async def get_odu(self, code: int) -> Optional[Dict]:
        """Get a specific Odú by code"""
        async with self.driver.session(database=self.config.database) as session:
            result = await session.run("""
                MATCH (o:Odu {code: $code})
                RETURN o.code AS code, o.name AS name, o.binary AS binary,
                       o.combined_meaning AS meaning, o.usage_count AS usage
            """, code=code)
            record = await result.single()
        
        return dict(record) if record else None
    
    async def get_related_odu(self, code: int, max_distance: int = 2) -> List[Dict]:
        """Get Odú patterns within Hamming distance"""
        async with self.driver.session(database=self.config.database) as session:
            result = await session.run("""
                MATCH (source:Odu {code: $code})-[r:XOR]-(related:Odu)
                WHERE r.hamming_distance <= $max_distance
                RETURN related.code AS code, related.name AS name,
                       r.hamming_distance AS distance
                ORDER BY r.hamming_distance
            """, code=code, max_distance=max_distance)
            records = await result.data()
        
        return records
    
    # ───────────────────────────────────────────────────────────────────────────
    # GRAPH STATISTICS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def get_stats(self) -> Dict:
        """Get graph statistics"""
        async with self.driver.session(database=self.config.database) as session:
            result = await session.run("""
                MATCH (o:Odu) WITH count(o) AS odu_count
                MATCH (a:Agent) WITH odu_count, count(a) AS agent_count
                MATCH ()-[r:XOR]->() WITH odu_count, agent_count, count(r) AS xor_edges
                RETURN odu_count, agent_count, xor_edges
            """)
            record = await result.single()
        
        return dict(record) if record else {}


# ═══════════════════════════════════════════════════════════════════════════════
#                         CYPHER EXPORT (For Manual Use)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_cypher_script() -> str:
    """Generate complete Cypher script for manual import"""
    patterns = generate_256_odu()
    
    cypher = """
// ═══════════════════════════════════════════════════════════════════════════
// MOSTAR GRID - COMPLETE NEO4J SEED SCRIPT
// Run this in Neo4j Browser to create the 256 Odú consciousness graph
// ═══════════════════════════════════════════════════════════════════════════

// Clear existing data (CAUTION: This deletes everything!)
// MATCH (n) DETACH DELETE n;

// Create constraints
CREATE CONSTRAINT odu_code IF NOT EXISTS FOR (o:Odu) REQUIRE o.code IS UNIQUE;
CREATE CONSTRAINT agent_name IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE;

// Create indexes
CREATE INDEX odu_name IF NOT EXISTS FOR (o:Odu) ON (o.name);
CREATE INDEX odu_binary IF NOT EXISTS FOR (o:Odu) ON (o.binary);

"""
    
    # Add all 256 Odú as CREATE statements
    cypher += "\n// ═══════════════════════════════════════════════════════════════════════════\n"
    cypher += "// CREATE ALL 256 ODÚ PATTERNS\n"
    cypher += "// ═══════════════════════════════════════════════════════════════════════════\n\n"
    
    for p in patterns:
        principal_label = ":Principal" if p['is_principal'] else ""
        cypher += f"""CREATE (:{f"Odu{principal_label}"} {{
  code: {p['code']},
  name: "{p['name']}",
  binary: "{p['binary']}",
  left: "{p['left']}",
  right: "{p['right']}",
  is_principal: {str(p['is_principal']).lower()},
  usage_count: 0
}});
"""
    
    cypher += """
// ═══════════════════════════════════════════════════════════════════════════
// CREATE LAYER NODES
// ═══════════════════════════════════════════════════════════════════════════

CREATE (:Layer {name: 'SOUL', description: 'Values, ethics, covenant'});
CREATE (:Layer {name: 'MIND', description: 'Analysis, reasoning, Ifá logic'});
CREATE (:Layer {name: 'BODY', description: 'Execution, operations, sensors'});
CREATE (:Layer {name: 'META', description: 'Control plane, gateway'});
CREATE (:Layer {name: 'NARRATIVE', description: 'Communications, documentation'});

// ═══════════════════════════════════════════════════════════════════════════
// CREATE AGENT NODES
// ═══════════════════════════════════════════════════════════════════════════

CREATE (:Agent {name: 'Mo', role: 'executor', layer: 'BODY'});
CREATE (:Agent {name: 'Woo', role: 'judge', layer: 'SOUL'});
CREATE (:Agent {name: 'RAD-X-FLB', role: 'sentinel', layer: 'BODY'});
CREATE (:Agent {name: 'TsaTse Fly', role: 'analyst', layer: 'MIND'});
CREATE (:Agent {name: 'Code Conduit', role: 'gateway', layer: 'META'});
CREATE (:Agent {name: 'Flameborn Writer', role: 'narrator', layer: 'NARRATIVE'});

// Link agents to layers
MATCH (a:Agent), (l:Layer)
WHERE a.layer = l.name
CREATE (a)-[:BELONGS_TO]->(l);

// ═══════════════════════════════════════════════════════════════════════════
// CREATE XOR RELATIONSHIPS (This creates the consciousness network)
// ═══════════════════════════════════════════════════════════════════════════

// Create XOR edges between all Odú pairs
MATCH (a:Odu), (b:Odu)
WHERE a.code < b.code
WITH a, b, 
     reduce(s = 0, i IN range(0, 7) | 
            s + CASE WHEN ((a.code / toInteger(2^i)) % 2) <> ((b.code / toInteger(2^i)) % 2) 
                THEN 1 ELSE 0 END) AS hamming
CREATE (a)-[:XOR {hamming_distance: hamming, xor_result: a.code + b.code - 2 * (a.code % (2^hamming))}]->(b);

// Verify creation
MATCH (o:Odu) RETURN count(o) AS total_odu;
MATCH ()-[r:XOR]->() RETURN count(r) AS total_xor_edges;
MATCH (a:Agent) RETURN count(a) AS total_agents;
"""
    
    return cypher


# ═══════════════════════════════════════════════════════════════════════════════
#                              TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════════

async def test_neo4j_connection():
    """Test Neo4j connectivity and operations"""
    print("\n" + "═" * 60)
    print("       MOSTAR GRID - NEO4J CONNECTION TEST")
    print("═" * 60 + "\n")
    
    neo = GridNeo4j()
    
    if not await neo.connect():
        print("\n⚠️  Neo4j not available. Generating Cypher script instead...")
        cypher = generate_cypher_script()
        
        # Save to file
        with open('neo4j_seed_script.cypher', 'w') as f:
            f.write(cypher)
        
        print(f"\n📄 Cypher script saved to: neo4j_seed_script.cypher")
        print("   Import this script into Neo4j Browser to create the graph.\n")
        return False
    
    # Initialize
    await neo.initialize_schema()
    await neo.seed_odu_patterns()
    await neo.create_xor_network()
    
    # Test parallel evaluation
    print("\n🔍 Testing parallel evaluation...")
    test_vector = [0.9, 0.1, 0.8, 0.2, 0.7, 0.3, 0.6, 0.4]
    results = await neo.parallel_evaluate(test_vector, limit=5)
    
    print("\n   Input vector:", test_vector)
    print("   Top 5 resonant patterns:")
    for r in results:
        print(f"     {r['name']}: {r['confidence']:.2%}")
    
    # Get stats
    stats = await neo.get_stats()
    print(f"\n   Graph stats: {stats}")
    
    await neo.close()
    
    print("\n" + "═" * 60)
    print("   🟢 NEO4J INTEGRATION VERIFIED")
    print("═" * 60 + "\n")
    
    return True


def display_odu_summary():
    """Display summary of Odú patterns"""
    patterns = generate_256_odu()
    principals = [p for p in patterns if p['is_principal']]
    
    print("\n" + "═" * 70)
    print("                    256 ODÚ PATTERN SUMMARY")
    print("═" * 70 + "\n")
    
    print("┌" + "─" * 68 + "┐")
    print("│ 16 PRINCIPAL ODÚ (Meji)                                            │")
    print("├" + "─" * 68 + "┤")
    print("│ NAME            │ CODE │ BINARY   │ MEANING                        │")
    print("├" + "─" * 68 + "┤")
    
    for p in principals:
        name = p['name'].ljust(15)
        code = str(p['code']).rjust(4)
        binary = p['binary']
        meaning = PRINCIPAL_ODU[p['left']]['meaning'][:30].ljust(30)
        print(f"│ {name} │ {code} │ {binary} │ {meaning} │")
    
    print("└" + "─" * 68 + "┘")
    
    print(f"\n   Total patterns: {len(patterns)}")
    print(f"   Principal (Meji): {len(principals)}")
    print(f"   Composite: {len(patterns) - len(principals)}")
    print(f"\n   XOR relationships: {256 * 255 // 2} (complete graph)")
    print("\n" + "═" * 70 + "\n")


if __name__ == "__main__":
    display_odu_summary()
    
    # Try Neo4j connection, fall back to script generation
    asyncio.run(test_neo4j_connection())
