#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    MOSTAR GRID - DATABASE LAYER
                      Persistent Consciousness
                      
    Connects the Grid to Neon PostgreSQL for durable state storage.
    All consciousness persists here - events, patterns, seals, agents.
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncpg
from contextlib import asynccontextmanager

# ═══════════════════════════════════════════════════════════════════════════════
#                           DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DatabaseConfig:
    """Neon PostgreSQL configuration"""
    host: str = os.getenv("NEON_HOST", "ep-round-breeze-a1coj0uq.ap-southeast-1.aws.neon.tech")
    database: str = os.getenv("NEON_DATABASE", "neondb")
    user: str = os.getenv("NEON_USER", "neondb_owner")
    password: str = os.getenv("NEON_PASSWORD", "")
    port: int = int(os.getenv("NEON_PORT", "5432"))
    ssl: str = "require"
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl}"


# ═══════════════════════════════════════════════════════════════════════════════
#                              SCHEMA DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

GRID_SCHEMA = """
-- ═══════════════════════════════════════════════════════════════════════════
-- MOSTAR GRID SCHEMA - Sacred Data Structures
-- ═══════════════════════════════════════════════════════════════════════════

-- Schema namespace
CREATE SCHEMA IF NOT EXISTS grid;

-- ─────────────────────────────────────────────────────────────────────────────
-- AGENTS: Registered consciousness entities
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    layer VARCHAR(20) NOT NULL CHECK (layer IN ('SOUL', 'MIND', 'BODY', 'META', 'NARRATIVE')),
    soulprint VARCHAR(64) NOT NULL,  -- SHA256 hash
    capabilities JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DORMANT', 'SUSPENDED', 'TERMINATED')),
    resonance_score DECIMAL(3,2) DEFAULT 1.00 CHECK (resonance_score >= 0 AND resonance_score <= 1),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- ODU_PATTERNS: The 256 Ifá computational patterns
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.odu_patterns (
    code SMALLINT PRIMARY KEY CHECK (code >= 0 AND code <= 255),
    name VARCHAR(50) NOT NULL,
    binary_repr VARCHAR(8) NOT NULL,
    left_odu VARCHAR(20) NOT NULL,
    right_odu VARCHAR(20) NOT NULL,
    is_principal BOOLEAN DEFAULT FALSE,
    meaning TEXT,
    domain_mappings JSONB DEFAULT '{}',
    usage_count BIGINT DEFAULT 0,
    last_invoked TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- EVENTS: All Grid events (Soul/Mind/Body)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    layer VARCHAR(20) NOT NULL CHECK (layer IN ('SOUL', 'MIND', 'BODY')),
    source_agent VARCHAR(100),
    payload JSONB NOT NULL,
    odu_pattern SMALLINT REFERENCES grid.odu_patterns(code),
    seal VARCHAR(100),
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    latency_ms DECIMAL(10,3),
    metadata JSONB DEFAULT '{}'
);

-- Partition events by month for performance
CREATE INDEX IF NOT EXISTS idx_events_processed_at ON grid.events(processed_at);
CREATE INDEX IF NOT EXISTS idx_events_layer ON grid.events(layer);
CREATE INDEX IF NOT EXISTS idx_events_source ON grid.events(source_agent);

-- ─────────────────────────────────────────────────────────────────────────────
-- SEALS: Cryptographic audit trail (immutable)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.seals (
    id SERIAL PRIMARY KEY,
    seal_hash VARCHAR(64) NOT NULL UNIQUE,
    previous_hash VARCHAR(64),  -- Chain link
    action_type VARCHAR(50) NOT NULL,
    action_payload JSONB NOT NULL,
    sealed_by VARCHAR(100),
    sealed_at TIMESTAMPTZ DEFAULT NOW(),
    sequence_number BIGINT NOT NULL,
    verified BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_seals_sequence ON grid.seals(sequence_number);

-- ─────────────────────────────────────────────────────────────────────────────
-- COVENANT: Sacred rules and violations
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.covenant_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(30) NOT NULL CHECK (rule_type IN ('PROHIBITION', 'OBLIGATION', 'PERMISSION')),
    description TEXT,
    pattern JSONB,  -- Matching pattern for rule
    severity VARCHAR(20) DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grid.covenant_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id INTEGER REFERENCES grid.covenant_rules(id),
    agent_name VARCHAR(100),
    violation_details JSONB NOT NULL,
    judgment VARCHAR(50),
    judged_by VARCHAR(100) DEFAULT 'Woo',
    occurred_at TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- GRID_STATE: Current consciousness state
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.state (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    layer VARCHAR(20),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- MISSIONS: Body layer execution tracking
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_type VARCHAR(50) NOT NULL,
    assigned_agent VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    payload JSONB NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED')),
    odu_guidance SMALLINT REFERENCES grid.odu_patterns(code),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result JSONB,
    seal VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_missions_status ON grid.missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_agent ON grid.missions(assigned_agent);

-- ─────────────────────────────────────────────────────────────────────────────
-- KNOWLEDGE_GRAPH: Symbolic relationships
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    properties JSONB DEFAULT '{}',
    embedding VECTOR(384),  -- For semantic search (if pgvector enabled)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grid.knowledge_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES grid.knowledge_nodes(id) ON DELETE CASCADE,
    target_id UUID REFERENCES grid.knowledge_nodes(id) ON DELETE CASCADE,
    relationship VARCHAR(100) NOT NULL,
    weight DECIMAL(5,4) DEFAULT 1.0,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON grid.knowledge_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON grid.knowledge_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relationship ON grid.knowledge_edges(relationship);

-- ─────────────────────────────────────────────────────────────────────────────
-- VITALS: Grid health tracking
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid.vitals (
    id SERIAL PRIMARY KEY,
    check_time TIMESTAMPTZ DEFAULT NOW(),
    overall_status VARCHAR(20) NOT NULL,
    soul_alive BOOLEAN NOT NULL,
    mind_alive BOOLEAN NOT NULL,
    body_alive BOOLEAN NOT NULL,
    total_checks INTEGER,
    passed_checks INTEGER,
    total_latency_ms DECIMAL(10,3),
    details JSONB
);

-- Keep only last 1000 vital checks
CREATE INDEX IF NOT EXISTS idx_vitals_time ON grid.vitals(check_time DESC);
"""


# ═══════════════════════════════════════════════════════════════════════════════
#                           DATABASE CONNECTION POOL
# ═══════════════════════════════════════════════════════════════════════════════

class GridDatabase:
    """
    Async database connection pool for MoStar Grid.
    Manages all persistent consciousness storage.
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    async def connect(self) -> bool:
        """Establish connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.config.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            print(f"🔌 Connected to Neon: {self.config.host}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def initialize_schema(self) -> bool:
        """Create all Grid tables"""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(GRID_SCHEMA)
            print("✅ Grid schema initialized")
            self._initialized = True
            return True
        except Exception as e:
            print(f"❌ Schema initialization failed: {e}")
            return False
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("🔌 Database connection closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        async with self.pool.acquire() as conn:
            yield conn
    
    # ───────────────────────────────────────────────────────────────────────────
    # AGENT OPERATIONS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def register_agent(self, name: str, role: str, layer: str, 
                            capabilities: List[str], metadata: Dict = None) -> Dict:
        """Register a new agent with soulprint"""
        soulprint_data = f"{name}:{role}:{layer}:{datetime.now(timezone.utc).isoformat()}"
        soulprint = hashlib.sha256(soulprint_data.encode()).hexdigest()
        
        async with self.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO grid.agents (name, role, layer, soulprint, capabilities, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (name) DO UPDATE SET
                    role = EXCLUDED.role,
                    layer = EXCLUDED.layer,
                    capabilities = EXCLUDED.capabilities,
                    last_heartbeat = NOW()
                RETURNING id, name, soulprint, registered_at
            """, name, role, layer, soulprint, json.dumps(capabilities), json.dumps(metadata or {}))
        
        return dict(result) if result else None
    
    async def get_agent(self, name: str) -> Optional[Dict]:
        """Get agent by name"""
        async with self.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM grid.agents WHERE name = $1", name
            )
        return dict(result) if result else None
    
    async def list_agents(self, layer: str = None) -> List[Dict]:
        """List all agents, optionally filtered by layer"""
        async with self.acquire() as conn:
            if layer:
                results = await conn.fetch(
                    "SELECT * FROM grid.agents WHERE layer = $1 ORDER BY name", layer
                )
            else:
                results = await conn.fetch(
                    "SELECT * FROM grid.agents ORDER BY layer, name"
                )
        return [dict(r) for r in results]
    
    async def heartbeat(self, agent_name: str) -> bool:
        """Update agent heartbeat"""
        async with self.acquire() as conn:
            result = await conn.execute("""
                UPDATE grid.agents SET last_heartbeat = NOW()
                WHERE name = $1
            """, agent_name)
        return result == "UPDATE 1"
    
    # ───────────────────────────────────────────────────────────────────────────
    # ODU PATTERN OPERATIONS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def store_odu_patterns(self, patterns: List[Dict]) -> int:
        """Bulk store Odú patterns"""
        async with self.acquire() as conn:
            count = 0
            for pattern in patterns:
                await conn.execute("""
                    INSERT INTO grid.odu_patterns (code, name, binary_repr, left_odu, right_odu, is_principal)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (code) DO NOTHING
                """, pattern['code'], pattern['name'], pattern['binary'], 
                   pattern['left'], pattern['right'], pattern.get('is_principal', False))
                count += 1
        return count
    
    async def get_odu_pattern(self, code: int) -> Optional[Dict]:
        """Get Odú pattern by code"""
        async with self.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM grid.odu_patterns WHERE code = $1", code
            )
        return dict(result) if result else None
    
    async def invoke_odu(self, code: int) -> bool:
        """Record Odú invocation"""
        async with self.acquire() as conn:
            await conn.execute("""
                UPDATE grid.odu_patterns 
                SET usage_count = usage_count + 1, last_invoked = NOW()
                WHERE code = $1
            """, code)
        return True
    
    # ───────────────────────────────────────────────────────────────────────────
    # EVENT OPERATIONS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def log_event(self, event_type: str, layer: str, payload: Dict,
                       source_agent: str = None, odu_pattern: int = None,
                       seal: str = None, latency_ms: float = None) -> str:
        """Log a Grid event"""
        async with self.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO grid.events (event_type, layer, source_agent, payload, odu_pattern, seal, latency_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, event_type, layer, source_agent, json.dumps(payload), odu_pattern, seal, latency_ms)
        return str(result['id'])
    
    async def get_recent_events(self, limit: int = 100, layer: str = None) -> List[Dict]:
        """Get recent events"""
        async with self.acquire() as conn:
            if layer:
                results = await conn.fetch("""
                    SELECT * FROM grid.events 
                    WHERE layer = $1 
                    ORDER BY processed_at DESC LIMIT $2
                """, layer, limit)
            else:
                results = await conn.fetch("""
                    SELECT * FROM grid.events 
                    ORDER BY processed_at DESC LIMIT $1
                """, limit)
        return [dict(r) for r in results]
    
    # ───────────────────────────────────────────────────────────────────────────
    # SEAL OPERATIONS (Immutable Audit Trail)
    # ───────────────────────────────────────────────────────────────────────────
    
    async def store_seal(self, seal_hash: str, action_type: str, 
                        action_payload: Dict, sealed_by: str = None) -> int:
        """Store a cryptographic seal in the chain"""
        async with self.acquire() as conn:
            # Get previous hash for chain
            prev = await conn.fetchrow(
                "SELECT seal_hash FROM grid.seals ORDER BY sequence_number DESC LIMIT 1"
            )
            previous_hash = prev['seal_hash'] if prev else None
            
            # Get next sequence number
            seq = await conn.fetchval(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM grid.seals"
            )
            
            result = await conn.fetchrow("""
                INSERT INTO grid.seals (seal_hash, previous_hash, action_type, action_payload, sealed_by, sequence_number)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, seal_hash, previous_hash, action_type, json.dumps(action_payload), sealed_by, seq)
        
        return result['id']
    
    async def verify_seal_chain(self) -> Dict:
        """Verify integrity of seal chain"""
        async with self.acquire() as conn:
            seals = await conn.fetch(
                "SELECT * FROM grid.seals ORDER BY sequence_number"
            )
        
        if not seals:
            return {'valid': True, 'count': 0, 'message': 'No seals to verify'}
        
        broken_links = []
        for i, seal in enumerate(seals):
            if i == 0:
                if seal['previous_hash'] is not None:
                    broken_links.append(f"Seal {seal['sequence_number']}: First seal has previous_hash")
            else:
                if seal['previous_hash'] != seals[i-1]['seal_hash']:
                    broken_links.append(f"Seal {seal['sequence_number']}: Chain broken")
        
        return {
            'valid': len(broken_links) == 0,
            'count': len(seals),
            'broken_links': broken_links
        }
    
    # ───────────────────────────────────────────────────────────────────────────
    # MISSION OPERATIONS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def create_mission(self, mission_type: str, assigned_agent: str,
                            payload: Dict, priority: int = 5, 
                            odu_guidance: int = None) -> str:
        """Create a new mission"""
        async with self.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO grid.missions (mission_type, assigned_agent, payload, priority, odu_guidance)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, mission_type, assigned_agent, json.dumps(payload), priority, odu_guidance)
        return str(result['id'])
    
    async def update_mission_status(self, mission_id: str, status: str, 
                                   result: Dict = None, seal: str = None) -> bool:
        """Update mission status"""
        async with self.acquire() as conn:
            if status == 'IN_PROGRESS':
                await conn.execute("""
                    UPDATE grid.missions SET status = $1, started_at = NOW()
                    WHERE id = $2
                """, status, mission_id)
            elif status in ('COMPLETED', 'FAILED'):
                await conn.execute("""
                    UPDATE grid.missions 
                    SET status = $1, completed_at = NOW(), result = $2, seal = $3
                    WHERE id = $4
                """, status, json.dumps(result or {}), seal, mission_id)
            else:
                await conn.execute("""
                    UPDATE grid.missions SET status = $1 WHERE id = $2
                """, status, mission_id)
        return True
    
    # ───────────────────────────────────────────────────────────────────────────
    # STATE OPERATIONS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def set_state(self, key: str, value: Any, layer: str = None, 
                       updated_by: str = None) -> bool:
        """Set a Grid state value"""
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO grid.state (key, value, layer, updated_by, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    layer = EXCLUDED.layer,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = NOW()
            """, key, json.dumps(value), layer, updated_by)
        return True
    
    async def get_state(self, key: str) -> Optional[Any]:
        """Get a Grid state value"""
        async with self.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT value FROM grid.state WHERE key = $1", key
            )
        return json.loads(result['value']) if result else None
    
    # ───────────────────────────────────────────────────────────────────────────
    # VITALS OPERATIONS
    # ───────────────────────────────────────────────────────────────────────────
    
    async def store_vitals(self, vitals_report: Dict) -> int:
        """Store a vitals check result"""
        async with self.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO grid.vitals (overall_status, soul_alive, mind_alive, body_alive, 
                                        total_checks, passed_checks, total_latency_ms, details)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, 
                vitals_report['grid_status'],
                vitals_report['layers']['SOUL'],
                vitals_report['layers']['MIND'],
                vitals_report['layers']['BODY'],
                vitals_report['total_checks'],
                sum(1 for c in vitals_report['checks'] if c['status'] == 'ALIVE'),
                vitals_report['total_time_ms'],
                json.dumps(vitals_report)
            )
        return result['id']
    
    async def get_latest_vitals(self) -> Optional[Dict]:
        """Get most recent vitals check"""
        async with self.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM grid.vitals ORDER BY check_time DESC LIMIT 1"
            )
        return dict(result) if result else None


# ═══════════════════════════════════════════════════════════════════════════════
#                              TEST CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

async def test_database_connection():
    """Test database connectivity"""
    print("\n" + "═" * 60)
    print("       MOSTAR GRID - DATABASE CONNECTION TEST")
    print("═" * 60 + "\n")
    
    db = GridDatabase()
    
    # Connect
    connected = await db.connect()
    if not connected:
        print("❌ Failed to connect to database")
        return False
    
    # Initialize schema
    initialized = await db.initialize_schema()
    if not initialized:
        print("❌ Failed to initialize schema")
        await db.close()
        return False
    
    # Test operations
    print("\n🔍 Testing database operations...")
    
    # Test state
    await db.set_state("grid.test", {"status": "testing", "timestamp": datetime.now(timezone.utc).isoformat()})
    state = await db.get_state("grid.test")
    print(f"   ✅ State: {state}")
    
    # Test agent count
    agents = await db.list_agents()
    print(f"   ✅ Agents registered: {len(agents)}")
    
    # Close
    await db.close()
    
    print("\n" + "═" * 60)
    print("   🟢 DATABASE CONNECTION VERIFIED")
    print("═" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_database_connection())
