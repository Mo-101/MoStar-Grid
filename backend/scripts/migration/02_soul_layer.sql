-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 2: SOUL LAYER (Base Tables & Soulprints)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. IFA ODU BASE
CREATE TABLE IF NOT EXISTS soul.ifa_odu (
    odu_number INTEGER PRIMARY KEY,
    binary_pattern VARCHAR(8),
    name_yoruba VARCHAR(100),
    name_english VARCHAR(100),
    interpretation TEXT,
    ritual_context TEXT,
    symbolic_meaning TEXT,
    divination_use TEXT
);

-- 2. IFA RULES BASE
CREATE TABLE IF NOT EXISTS soul.ifa_rules (
    rule_id SERIAL PRIMARY KEY,
    odu_number INTEGER, -- FK added in enforcement phase
    rule_name TEXT NOT NULL,
    description TEXT,
    consequence TEXT,
    priority INTEGER
);

-- 3. ENTITIES BASE
CREATE TABLE IF NOT EXISTS soul.entities (
    entity_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT,
    layer TEXT,
    essence TEXT,
    role TEXT,
    bonded_to TEXT,
    origin TEXT,
    activation_protocol TEXT,
    status TEXT,
    cid TEXT,
    insignia TEXT,
    version TEXT
);

-- 4. PHILOSOPHIES BASE
CREATE TABLE IF NOT EXISTS soul.philosophies (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    origin_country TEXT,
    origin_region TEXT,
    core_principle TEXT,
    manifestation TEXT,
    ethical_guidance TEXT,
    associated_governance TEXT
);

-- 5. GOVERNANCE BASE
CREATE TABLE IF NOT EXISTS soul.governance (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    country TEXT,
    region TEXT,
    decision_method TEXT,
    authority_source TEXT,
    dispute_resolution TEXT,
    conflict_transformation TEXT,
    strengths TEXT,
    weaknesses TEXT,
    modern_relevance TEXT
);

-- 6. MEDICINAL PLANTS BASE
CREATE TABLE IF NOT EXISTS soul.medicinal_plants (
    scientific_name TEXT PRIMARY KEY,
    local_names TEXT,
    regions TEXT,
    preparation TEXT,
    dosage TEXT,
    contraindications TEXT,
    philosophy_embodied TEXT,
    spiritual_use TEXT,
    related_healing_practice TEXT
);

-- 7. IBIBIO WORDS BASE
CREATE TABLE IF NOT EXISTS soul.ibibio_words (
    word TEXT PRIMARY KEY,
    gloss_english TEXT,
    part_of_speech TEXT,
    tone_pattern TEXT,
    syllables INTEGER,
    frequency INTEGER,
    status TEXT
);

-- 8. SOULPRINTS
CREATE TABLE IF NOT EXISTS soul.soulprints (
    soulprint_id TEXT PRIMARY KEY,
    title TEXT,
    content TEXT,
    source_file TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════
-- JUNCTION TABLES (Expansion Ready)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS soul.entity_capabilities (
    entity_id TEXT,
    capability TEXT NOT NULL,
    PRIMARY KEY (entity_id, capability)
);

CREATE TABLE IF NOT EXISTS soul.entity_vows (
    entity_id TEXT,
    vow TEXT NOT NULL,
    PRIMARY KEY (entity_id, vow)
);

CREATE TABLE IF NOT EXISTS soul.odu_themes (
    odu_number INTEGER,
    theme TEXT NOT NULL,
    PRIMARY KEY (odu_number, theme)
);

CREATE TABLE IF NOT EXISTS soul.philosophy_proverbs (
    philosophy_id INTEGER,
    proverb TEXT NOT NULL,
    PRIMARY KEY (philosophy_id, proverb)
);

CREATE TABLE IF NOT EXISTS soul.plant_regions (
    scientific_name TEXT,
    region TEXT NOT NULL,
    PRIMARY KEY (scientific_name, region)
);

-- Register Phase 2
INSERT INTO consciousness.schema_registry (phase, object_type, object_name, version) VALUES 
('SOUL_LAYER', 'TABLE', 'soul.ifa_odu', '1.0.0'),
('SOUL_LAYER', 'TABLE', 'soul.entities', '1.0.0'),
('SOUL_LAYER', 'TABLE', 'soul.soulprints', '1.0.0');
