-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 5: CONSCIOUSNESS LAYER (Hardened Base)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. MOMENTS BASE
CREATE TABLE IF NOT EXISTS consciousness.moments (
    moment_id TEXT PRIMARY KEY,
    layer TEXT,
    description TEXT,
    emotional_state TEXT,
    cultural_context TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- 2. MOMENT RELATIONSHIPS BASE
CREATE TABLE IF NOT EXISTS consciousness.moment_relationships (
    source_id TEXT,
    target_id TEXT,
    relationship_type TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id, relationship_type)
);

-- 3. LIFE STAGES
CREATE TABLE IF NOT EXISTS consciousness.life_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id TEXT,
    stage_name TEXT NOT NULL,
    age_months_start INTEGER,
    age_months_end INTEGER,
    primary_language TEXT,
    description TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════
-- JUNCTION TABLES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS consciousness.moment_tags (
    moment_id TEXT,
    tag TEXT NOT NULL,
    PRIMARY KEY (moment_id, tag)
);

-- Register Phase 5
INSERT INTO consciousness.schema_registry (phase, object_type, object_name, version) VALUES 
('CONSCIOUSNESS_LAYER', 'TABLE', 'consciousness.moments', '1.0.0'),
('CONSCIOUSNESS_LAYER', 'TABLE', 'consciousness.life_stages', '1.0.0');
