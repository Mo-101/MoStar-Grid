BEGIN;

CREATE TABLE IF NOT EXISTS control_plane_resonance_state (
    id UUID PRIMARY KEY,
    component_id TEXT NOT NULL UNIQUE,
    current_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    level TEXT NOT NULL DEFAULT 'INFO',
    contributing_events JSONB NOT NULL DEFAULT '[]'::jsonb,
    decay_reason TEXT,
    threshold_crossed_at TIMESTAMPTZ,
    last_computed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    previous_level TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS graph_audit_event (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_canonical_id TEXT NOT NULL,
    related_canonical_id TEXT,
    status TEXT NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS graph_audit_event_type_created_idx
    ON graph_audit_event (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS graph_audit_event_entity_created_idx
    ON graph_audit_event (entity_canonical_id, created_at DESC);

INSERT INTO control_plane_resonance_state (
    id, component_id, current_score, level, contributing_events,
    last_computed, created_at, updated_at
)
SELECT
    gen_random_uuid(), component_id, 0, 'INFO', '[]'::jsonb,
    NOW(), NOW(), NOW()
FROM unnest(ARRAY[
    'agents',
    'mo_woo_nexus',
    'decision_engine',
    'moscript_registry'
]) AS component_id
ON CONFLICT (component_id) DO NOTHING;

COMMIT;
