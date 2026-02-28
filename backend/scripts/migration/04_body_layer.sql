-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 4: BODY LAYER (Hardened Base)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. API ENDPOINTS BASE
CREATE TABLE IF NOT EXISTS body.api_endpoints (
    endpoint_id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    description TEXT,
    entity_owner TEXT, -- FK added in Phase 7
    input_schema TEXT,
    output_schema TEXT,
    authentication_required BOOLEAN,
    rate_limit TEXT,
    status TEXT
);

-- 2. EXECUTABLE MODULES BASE
CREATE TABLE IF NOT EXISTS body.executable_modules (
    module_id TEXT PRIMARY KEY,
    filename TEXT,
    layer TEXT,
    owner_entity TEXT, -- FK added in Phase 7
    function_role TEXT,
    security_level TEXT,
    input_schema TEXT,
    output_schema TEXT,
    dependencies TEXT,
    status TEXT
);

-- ═══════════════════════════════════════════════════════════════════════════
-- JUNCTION TABLES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS body.endpoint_tags (
    endpoint_id TEXT,
    tag TEXT NOT NULL,
    PRIMARY KEY (endpoint_id, tag)
);

CREATE TABLE IF NOT EXISTS body.module_dependencies (
    module_id TEXT,
    dependency_name TEXT NOT NULL,
    PRIMARY KEY (module_id, dependency_name)
);

-- Register Phase 4
INSERT INTO consciousness.schema_registry (phase, object_type, object_name, version) VALUES 
('BODY_LAYER', 'TABLE', 'body.api_endpoints', '1.0.0'),
('BODY_LAYER', 'TABLE', 'body.executable_modules', '1.0.0');
