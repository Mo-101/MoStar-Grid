-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 1: FOUNDATION (Hardened Registry)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. SCHEMAS
CREATE SCHEMA IF NOT EXISTS soul;
CREATE SCHEMA IF NOT EXISTS mind;
CREATE SCHEMA IF NOT EXISTS body;
CREATE SCHEMA IF NOT EXISTS consciousness;

-- 2. SCHEMA REGISTRY (Enterprise Audit Trail)
CREATE TABLE IF NOT EXISTS consciousness.schema_registry (
    id SERIAL PRIMARY KEY,
    phase TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.1.0',
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Audit Metadata
    checksum TEXT,           -- SHA256 of normalized source
    byte_size BIGINT,        -- Raw file size
    line_count BIGINT,       -- Total lines in source
    row_count_snapshot BIGINT, -- Rows actually loaded
    execution_ms BIGINT,      -- Duration of phase
    
    -- Status
    success_flag BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- Register Initial Foundation (Self-Bootstrap)
INSERT INTO consciousness.schema_registry (phase, object_type, object_name, success_flag) 
VALUES ('FOUNDATION', 'SCHEMA', 'consciousness', TRUE);
