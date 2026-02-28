-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 6: ENRICHMENT LAYER (Deep Knowledge)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. IFA ODU ENRICHMENT (JSON Corpus Source)
CREATE TABLE IF NOT EXISTS soul.ifa_odu_enrichment (
    odu_number INTEGER PRIMARY KEY, -- FK added in enforcement
    hex TEXT,
    left_nibble TEXT,
    right_nibble TEXT,
    ones_count INTEGER,
    zeros_count INTEGER,
    parity TEXT,
    is_symmetric BOOLEAN,
    is_palindrome BOOLEAN,
    odu_type TEXT,
    health_domain TEXT,
    infrastructure_domain TEXT,
    positive_manifestation TEXT,
    negative_manifestation TEXT,
    action_guidance TEXT
);

-- 2. IBIBIO WORD ENRICHMENT (JSON Dictionary Source)
CREATE TABLE IF NOT EXISTS soul.ibibio_word_enrichment (
    word TEXT PRIMARY KEY, -- FK added in enforcement
    extended_definition TEXT,
    dialect_variants TEXT,
    notes TEXT
);

-- 3. AUDIO REPOSITORY
CREATE TABLE IF NOT EXISTS soul.audio_samples (
    audio_id SERIAL PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    full_path TEXT NOT NULL,
    speaker TEXT,
    duration_seconds NUMERIC,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. WORD-AUDIO MAPPING (Normalized)
CREATE TABLE IF NOT EXISTS soul.word_audio_map (
    word TEXT,
    audio_id INTEGER,
    PRIMARY KEY (word, audio_id)
);

-- Register Phase 6
INSERT INTO consciousness.schema_registry (phase, object_type, object_name, version) VALUES 
('ENRICHMENT', 'TABLE', 'soul.ifa_odu_enrichment', '1.0.0'),
('ENRICHMENT', 'TABLE', 'soul.ibibio_word_enrichment', '1.0.0'),
('ENRICHMENT', 'TABLE', 'soul.audio_samples', '1.0.0');
