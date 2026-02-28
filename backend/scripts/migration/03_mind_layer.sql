-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 3: MIND LAYER (Hardened Base)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. AI COMPONENTS BASE
CREATE TABLE IF NOT EXISTS mind.ai_components (
    component_id TEXT PRIMARY KEY,
    component_name TEXT,
    layer_type TEXT,
    technology TEXT,
    description TEXT,
    status TEXT,
    reasoning_speed_seconds TEXT,
    explainability_percent INTEGER,
    accuracy_percent INTEGER,
    integration_status TEXT
);

-- 2. DECISION FRAMEWORKS BASE
CREATE TABLE IF NOT EXISTS mind.decision_frameworks (
    decision_framework_id TEXT PRIMARY KEY,
    framework_name TEXT,
    component_type TEXT,
    component_name TEXT,
    description TEXT,
    status TEXT,
    complexity TEXT,
    computational_time_seconds INTEGER,
    accuracy_percent INTEGER,
    data_coverage_required_percent INTEGER,
    component_id TEXT -- FK added in Phase 7
);

-- ═══════════════════════════════════════════════════════════════════════════
-- JUNCTION TABLES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS mind.framework_actors (
    decision_framework_id TEXT,
    entity_id TEXT,
    PRIMARY KEY (decision_framework_id, entity_id)
);

-- Register Phase 3
INSERT INTO consciousness.schema_registry (phase, object_type, object_name, version) VALUES 
('MIND_LAYER', 'TABLE', 'mind.ai_components', '1.0.0'),
('MIND_LAYER', 'TABLE', 'mind.decision_frameworks', '1.0.0');
