-- ═══════════════════════════════════════════════════════════════════════════
-- MOSTAR GRID RELATIONAL SCHEMA - Normalized Layered Architecture
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. SCHEMAS
CREATE SCHEMA IF NOT EXISTS soul;
CREATE SCHEMA IF NOT EXISTS mind;
CREATE SCHEMA IF NOT EXISTS body;
CREATE SCHEMA IF NOT EXISTS consciousness;

-- ─────────────────────────────────────────────────────────────────────────────
-- SOUL LAYER
-- ─────────────────────────────────────────────────────────────────────────────

-- 2. Ifá Odu Core (ifa_odu_system.csv)
CREATE TABLE IF NOT EXISTS soul.ifa_odu (
    odu_number INTEGER PRIMARY KEY,
    binary_pattern VARCHAR(8) NOT NULL,
    name_yoruba VARCHAR(100),
    name_english VARCHAR(100),
    interpretation TEXT,
    ritual_context TEXT,
    symbolic_meaning TEXT,
    divination_use TEXT
);

-- Junction table for themes (normalized from ifa_odu_system.csv:related_themes)
CREATE TABLE IF NOT EXISTS soul.odu_themes (
    odu_number INTEGER REFERENCES soul.ifa_odu(odu_number) ON DELETE CASCADE,
    theme TEXT,
    PRIMARY KEY (odu_number, theme)
);

-- 3. Ifá Rules (ifa_rules.csv)
CREATE TABLE IF NOT EXISTS soul.ifa_rules (
    rule_id SERIAL PRIMARY KEY,
    odu_number INTEGER REFERENCES soul.ifa_odu(odu_number) ON DELETE CASCADE,
    rule_name TEXT NOT NULL,
    description TEXT,
    consequence TEXT,
    priority INTEGER
);

-- 4. Entities (entity_ecosystem.csv)
CREATE TABLE IF NOT EXISTS soul.entities (
    entity_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    title VARCHAR(200),
    layer VARCHAR(50),
    essence TEXT,
    role TEXT,
    vows TEXT,
    bonded_to VARCHAR(100),
    origin TEXT,
    activation_protocol TEXT,
    status VARCHAR(50),
    cid TEXT,
    insignia TEXT,
    version VARCHAR(50)
);

-- Junction table for capabilities (normalized from entity_ecosystem.csv:capabilities)
CREATE TABLE IF NOT EXISTS soul.entity_capabilities (
    entity_id VARCHAR(100) REFERENCES soul.entities(entity_id) ON DELETE CASCADE,
    capability TEXT,
    PRIMARY KEY (entity_id, capability)
);

-- 5. Philosophies (african_philosophies.csv)
CREATE TABLE IF NOT EXISTS soul.philosophies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    origin_country VARCHAR(100),
    origin_region VARCHAR(100),
    core_principle TEXT,
    manifestation TEXT,
    ethical_guidance TEXT,
    associated_governance TEXT
);

-- Junction table for proverbs (normalized from african_philosophies.csv:related_proverbs)
CREATE TABLE IF NOT EXISTS soul.philosophy_proverbs (
    philosophy_id INTEGER REFERENCES soul.philosophies(id) ON DELETE CASCADE,
    proverb TEXT,
    PRIMARY KEY (philosophy_id, proverb)
);

-- 6. Indigenous Governance (indigenous_governance.csv)
CREATE TABLE IF NOT EXISTS soul.governance (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    country VARCHAR(100),
    region VARCHAR(100),
    decision_method TEXT,
    authority_source TEXT,
    dispute_resolution TEXT,
    conflict_transformation TEXT,
    strengths TEXT,
    weaknesses TEXT,
    modern_relevance TEXT
);

-- 7. Medicinal Plants (medicinal_plants.csv)
CREATE TABLE IF NOT EXISTS soul.medicinal_plants (
    scientific_name VARCHAR(200) PRIMARY KEY,
    local_names TEXT,
    regions TEXT,
    preparation TEXT,
    dosage TEXT,
    contraindications TEXT,
    philosophy_embodied TEXT,
    spiritual_use TEXT,
    related_healing_practice TEXT
);

-- Junction table for medicinal uses (normalized from medicinal_plants.csv:medicinal_uses)
CREATE TABLE IF NOT EXISTS soul.plant_uses (
    scientific_name VARCHAR(200) REFERENCES soul.medicinal_plants(scientific_name) ON DELETE CASCADE,
    medicinal_use TEXT,
    PRIMARY KEY (scientific_name, medicinal_use)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- MIND LAYER
-- ─────────────────────────────────────────────────────────────────────────────

-- 8. AI Components (omni_neuro_symbolic_ai.csv)
CREATE TABLE IF NOT EXISTS mind.ai_components (
    component_id VARCHAR(100) PRIMARY KEY,
    component_name VARCHAR(200),
    layer_type VARCHAR(100),
    technology TEXT,
    description TEXT,
    status VARCHAR(50),
    reasoning_speed_seconds VARCHAR(50),
    explainability_percent INTEGER,
    accuracy_percent INTEGER,
    integration_status VARCHAR(50)
);

-- 9. Decision Frameworks (decision_intelligence_framework.csv)
CREATE TABLE IF NOT EXISTS mind.decision_frameworks (
    decision_framework_id VARCHAR(100) PRIMARY KEY,
    framework_name VARCHAR(200),
    component_type VARCHAR(100),
    component_name VARCHAR(200),
    description TEXT,
    status VARCHAR(50),
    complexity VARCHAR(50),
    computational_time_seconds INTEGER,
    accuracy_percent INTEGER,
    data_coverage_required_percent INTEGER,
    component_id VARCHAR(100) REFERENCES mind.ai_components(component_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- BODY LAYER
-- ─────────────────────────────────────────────────────────────────────────────

-- 10. API Endpoints (api_endpoints.csv)
CREATE TABLE IF NOT EXISTS body.api_endpoints (
    endpoint_id VARCHAR(100) PRIMARY KEY,
    path TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    description TEXT,
    entity_owner VARCHAR(100) REFERENCES soul.entities(entity_id),
    input_schema TEXT,
    output_schema TEXT,
    authentication_required BOOLEAN,
    rate_limit VARCHAR(50),
    status VARCHAR(50)
);

-- 11. Executable Modules (executable_modules.csv)
CREATE TABLE IF NOT EXISTS body.executable_modules (
    module_id VARCHAR(100) PRIMARY KEY,
    filename VARCHAR(200),
    layer VARCHAR(50),
    owner_entity VARCHAR(100) REFERENCES soul.entities(entity_id),
    function_role TEXT,
    security_level VARCHAR(50),
    input_schema TEXT,
    output_schema TEXT,
    dependencies TEXT,
    status VARCHAR(50)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- CONSCIOUSNESS LAYER
-- ─────────────────────────────────────────────────────────────────────────────

-- 12. Moments (moment_nodes_seed.csv)
CREATE TABLE IF NOT EXISTS consciousness.moments (
    moment_id VARCHAR(100) PRIMARY KEY,
    layer VARCHAR(50),
    description TEXT,
    emotional_state TEXT,
    cultural_context TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 13. Moment Relationships (moment_rels_seed.csv)
CREATE TABLE IF NOT EXISTS consciousness.moment_relationships (
    source_id VARCHAR(100) REFERENCES consciousness.moments(moment_id) ON DELETE CASCADE,
    target_id VARCHAR(100) REFERENCES consciousness.moments(moment_id) ON DELETE CASCADE,
    relationship_type VARCHAR(100),
    PRIMARY KEY (source_id, target_id, relationship_type)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE INDEX idx_ifa_rules_odu_number ON soul.ifa_rules(odu_number);
CREATE INDEX idx_api_owner ON body.api_endpoints(entity_owner);
CREATE INDEX idx_module_owner ON body.executable_modules(owner_entity);
CREATE INDEX idx_framework_component ON mind.decision_frameworks(component_id);
