-- ═══════════════════════════════════════════════════════════════════════════════
-- 003_mostar_cognition_schema.sql
-- mostar_cognition — types, tables, view, indexes, privileges.
--
-- CONNECT TO mostar_cognition BEFORE APPLYING THIS FILE:
--   \c mostar_cognition
--   (or: psql -U postgres -d mostar_cognition -p 5433 -f 003_mostar_cognition_schema.sql)
--
-- Prerequisite: 002_create_db_and_role.sql applied and verified.
-- Run as a superuser or as cognition_owner.
--
-- ARCHITECTURAL AUTHORITY:
--   Neo4j/Grid is authoritative for MoStar Moments and Graph synthesis.
--   PostgreSQL is the durable, queryable projection of those outputs.
--   Real-time manifestations originate from control plane/orchestrator/watchers
--   /mindgraph/agents and are persisted directly here.
--   This database is not the source of truth that supersedes the Grid.
--
-- CLUSTER POLICY:
--   There is one MoStar. No cluster tables. No cluster_id columns.
--   No composite cluster foreign keys. No speculative multi-tenant machinery.
--
-- RLS POLICY:
--   RLS is not enabled in this migration. No policies exist yet.
--   security_invoker=true on the view is set now so that if RLS is deliberately
--   introduced later, the view will correctly respect caller privileges rather
--   than requiring a retroactive fix.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 0. Harden public schema ──────────────────────────────────────────────────
-- PostgreSQL grants CREATE on public to all roles by default.
-- Revoke it. cognition_owner retains ownership. cognition_app gets only
-- what is explicitly granted below.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ── 1. Shared epistemic mode type ────────────────────────────────────────────
-- One closed enum used across all three tables.
-- Do not duplicate as CHECK constraints — drift between three copies is a real risk.
-- Changing this vocabulary requires a migration; that is intentional and correct.
CREATE TYPE epistemic_mode_t AS ENUM (
    'recorded',   -- directly observed and written as-is
    'inferred',   -- derived from observed inputs by reasoning
    'projected',  -- forward-projected or extrapolated
    'imported'    -- brought in from an external system with its own provenance
);

-- ── 2. mo_moments ────────────────────────────────────────────────────────────
-- Sealed MoStar thought cycles.
-- Authoritative source: Neo4j MoStarMoment nodes.
-- Written by the orchestrator at seal time.
-- Append-only: no application UPDATE or DELETE. Data is sovereign.
CREATE TABLE mo_moments (
    id                   UUID              PRIMARY KEY DEFAULT gen_random_uuid(),

    quantum_id           TEXT              NOT NULL UNIQUE,
        -- Canonical Neo4j identifier. The structural bridge back to the
        -- authoritative graph. Uniqueness here mirrors the graph's own constraint.

    talk_input           TEXT              NOT NULL,
    think_output         TEXT              NOT NULL,
    seal                 TEXT              NOT NULL,

    source_type          TEXT              NOT NULL
                         CHECK (source_type IN ('live', 'replay', 'imported')),
        -- 'live'    : produced during a running session
        -- 'replay'  : replayed from prior state
        -- 'imported': brought in from an external source with preserved provenance

    epistemic_mode       epistemic_mode_t  NOT NULL,

    -- ── Sovereign time ────────────────────────────────────────────────────────
    -- Africa/Nairobi is the governance rule, not an incidental numeric offset.
    -- The named timezone is intentionally present in the schema.
    -- occurred_at stores the unambiguous UTC instant (timestamptz).
    -- sovereign_date derives the Nairobi calendar date from that instant.
    occurred_at          TIMESTAMPTZ       NOT NULL,
    sovereign_date       DATE              GENERATED ALWAYS AS (
                             (occurred_at AT TIME ZONE 'Africa/Nairobi')::date
                         ) STORED,

    -- ── Source provenance (preserved; never overrides sovereign) ─────────────
    source_timezone      TEXT,
        -- Timezone the source reported, if any. Documentation only.
    source_timestamp_raw TEXT,
        -- Raw timestamp string from source, if any. Documentation only.

    -- ── Epistemic provenance ──────────────────────────────────────────────────
    -- Doctrine: attested_by and origin_model are different epistemic roles.
    --   attested_by  = who/what vouches for this moment's validity.
    --   origin_model = who/what produced the raw output. Not trust evidence alone.
    -- They are not interchangeable. They are not required to differ in text value.
    -- Do not add CHECK (attested_by <> origin_model) — the doctrine is about
    -- epistemic roles, not string inequality.
    attested_by          TEXT              NOT NULL,
    origin_model         TEXT              NOT NULL,

    -- ── Timestamps ───────────────────────────────────────────────────────────
    -- occurred_at: when the source event/reality says it happened (above).
    -- recorded_at: when mostar_cognition persisted this projection. Distinct.
    recorded_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE mo_moments IS
'Sealed MoStar thought cycles projected from Neo4j MoStarMoment nodes. '
'Neo4j is authoritative. This table is the durable Postgres projection. '
'Append-only: sealed moments are not rewritten by the application layer.';

CREATE INDEX mo_moments_occurred_idx    ON mo_moments (occurred_at DESC);
CREATE INDEX mo_moments_sovereign_idx   ON mo_moments (sovereign_date DESC);
CREATE INDEX mo_moments_epistemic_idx   ON mo_moments (epistemic_mode);
CREATE INDEX mo_moments_source_type_idx ON mo_moments (source_type);

-- ── 3. neo4j_synthesis ───────────────────────────────────────────────────────
-- Postgres projection of what the Grid/Neo4j graph has concluded.
-- Includes: adjudication decisions, canonical promotions, attestations,
--           claim resolutions, testimony.
-- Neo4j is authoritative. When the Graph's canonical state changes, this table
-- may be updated in place (re-projection). That is why UPDATE is permitted here
-- but not on the other two tables.
-- The Neo4j projector is not yet built; this table waits for it (Step 5 of
-- the sequencing discipline). The table exists before the projector does.
CREATE TABLE neo4j_synthesis (
    id                   UUID              PRIMARY KEY DEFAULT gen_random_uuid(),

    canonical_id         TEXT              NOT NULL,
        -- Neo4j node canonical_id. Reference back to the authoritative graph node.

    entity_type          TEXT              NOT NULL,
        -- Intentionally no CHECK constraint — the Graph's constitutional vocabulary
        -- is extensible. Known values: Claim, AdjudicationDecision,
        -- CanonicalPromotion, Attestation, Testimony, AuthorizationDecision.

    synthesis_type       TEXT              NOT NULL
                         CHECK (synthesis_type IN (
                             'adjudication_decision',
                             'canonical_promotion',
                             'attestation',
                             'claim_resolution',
                             'testimony'
                         )),

    payload              JSONB             NOT NULL DEFAULT '{}'::jsonb,
        -- Full graph node payload at time of projection.

    -- ── Epistemic provenance ──────────────────────────────────────────────────
    attested_by          TEXT              NOT NULL,
    origin_model         TEXT              NOT NULL,
    epistemic_mode       epistemic_mode_t  NOT NULL,

    -- ── Sovereign time ────────────────────────────────────────────────────────
    occurred_at          TIMESTAMPTZ       NOT NULL,
    sovereign_date       DATE              GENERATED ALWAYS AS (
                             (occurred_at AT TIME ZONE 'Africa/Nairobi')::date
                         ) STORED,
    source_timezone      TEXT,
    source_timestamp_raw TEXT,

    -- ── Timestamps ───────────────────────────────────────────────────────────
    recorded_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
        -- When this row was first projected into Postgres.
    projected_at         TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
        -- Updated each time the Graph re-projects this row. Enables operational
        -- visibility into how current this projection is relative to the Graph.

    -- ── Idempotency / upsert anchor ───────────────────────────────────────────
    UNIQUE (canonical_id, synthesis_type)
        -- Same graph node cannot produce duplicate rows per synthesis type.
        -- Use: INSERT ... ON CONFLICT (canonical_id, synthesis_type) DO UPDATE
        --   SET payload = EXCLUDED.payload,
        --       projected_at = NOW(), ...
        -- to re-project without duplication.
);

COMMENT ON TABLE neo4j_synthesis IS
'Postgres projection of Grid/Neo4j graph conclusions. '
'Neo4j is authoritative. Re-projection (UPDATE) is permitted here when the '
'Graph canonical state changes. The Neo4j projector (Step 5 of sequencing '
'discipline) writes to this table. projected_at tracks projection currency.';

CREATE INDEX neo4j_synthesis_canonical_idx  ON neo4j_synthesis (canonical_id);
CREATE INDEX neo4j_synthesis_entity_idx     ON neo4j_synthesis (entity_type);
CREATE INDEX neo4j_synthesis_occurred_idx   ON neo4j_synthesis (occurred_at DESC);
CREATE INDEX neo4j_synthesis_sovereign_idx  ON neo4j_synthesis (sovereign_date DESC);
CREATE INDEX neo4j_synthesis_type_idx       ON neo4j_synthesis (synthesis_type);

-- ── 4. rt_manifestations ─────────────────────────────────────────────────────
-- Real-time events from the control plane, orchestrator, watchers, mindgraph,
-- and agents. Persisted directly (not via Neo4j). Append-only.
-- Deterministic source identity: replay-stable, producer-assigned.
CREATE TABLE rt_manifestations (
    id                   UUID              PRIMARY KEY DEFAULT gen_random_uuid(),

    ingest_seq           BIGINT            GENERATED ALWAYS AS IDENTITY,
        -- LOCAL INGEST ORDINAL ONLY. Not logical event identity.
        -- Not part of event_id hash. Not replay-stable.
        -- Useful for ingest-order debugging only.

    -- ── Deterministic event identity ─────────────────────────────────────────
    event_id             TEXT              NOT NULL UNIQUE
                         CHECK (event_id ~ '^[0-9a-f]{64}$'),

    -- event_id algorithm (application-side, mandatory):
    --
    --   Step 1 — canonical payload hash:
    --     payload_hash = lower(hex(SHA256(UTF8(JCS(payload)))))
    --     JCS = RFC 8785 JSON Canonicalization Scheme (sorted keys, no
    --     insignificant whitespace). Do NOT use jsonb::text as wire format.
    --
    --   Step 2 — canonical event envelope:
    --     envelope = JCS([
    --       "MOSTAR_COGNITION_EVENT_V1",
    --       source_system,
    --       producer_id,
    --       producer_epoch,
    --       producer_sequence,              ← integer (not string)
    --       occurred_at_epoch_microseconds, ← signed integer Unix epoch μs
    --       manifestation_type,
    --       payload_hash
    --     ])
    --
    --   Step 3:
    --     event_id = lower(hex(SHA256(UTF8(envelope))))
    --
    --   "MOSTAR_COGNITION_EVENT_V1" is a mandatory domain/version marker.
    --   A future hash algorithm must use a different marker to prevent silent
    --   semantic collision with this version.
    --
    --   String concatenation without delimiters is prohibited:
    --     "12" || "3"  ==  "1" || "23"  — ambiguous and insecure.
    --   The JCS array envelope above eliminates this ambiguity.

    manifestation_type   TEXT              NOT NULL
                         CHECK (manifestation_type IN (
                             'resonance_shift',
                             'gap_registered',
                             'moment_sealed',
                             'agent_signal',
                             'watcher_event'
                         )),

    source_system        TEXT              NOT NULL
                         CHECK (source_system IN (
                             'control_plane',
                             'orchestrator',
                             'watcher',
                             'mindgraph',
                             'agents'
                         )),

    -- ── Replay-stable source identity ─────────────────────────────────────────
    producer_id          TEXT              NOT NULL,
        -- Stable identity of the producing component.
        -- If the producer has an existing stable event ID, map it here rather
        -- than introducing a competing identity system.
    producer_epoch       TEXT              NOT NULL,
        -- Distinguishes producer restarts/incarnations where the sequence resets.
        -- The producer determines the format (e.g. ISO timestamp of startup).
    producer_sequence    BIGINT            NOT NULL
                         CHECK (producer_sequence >= 0),
        -- Monotonic counter within (producer_id, producer_epoch).
        -- Must come from the logical producer. Must survive replay unchanged.
        -- ingest_seq is NOT a substitute for this.

    UNIQUE (source_system, producer_id, producer_epoch, producer_sequence),
        -- Replay-safety gate: the same logical event cannot be inserted twice.
        -- Replay delivers the same producer_sequence → INSERT is rejected
        -- (or handled via ON CONFLICT DO NOTHING).

    -- ── Payload ───────────────────────────────────────────────────────────────
    payload              JSONB             NOT NULL DEFAULT '{}'::jsonb,
    payload_hash         TEXT              NOT NULL
                         CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
        -- SHA-256 of JCS (RFC 8785) canonical serialization of payload.
        -- Computed application-side from the same canonical representation used
        -- in the event_id envelope. Not recomputed from the stored JSONB column,
        -- which may differ from the canonical form in key ordering.

    epistemic_mode       epistemic_mode_t  NOT NULL,

    -- ── Sovereign time ────────────────────────────────────────────────────────
    occurred_at          TIMESTAMPTZ       NOT NULL,
    sovereign_date       DATE              GENERATED ALWAYS AS (
                             (occurred_at AT TIME ZONE 'Africa/Nairobi')::date
                         ) STORED,
    source_timezone      TEXT,
    source_timestamp_raw TEXT,

    -- ── Epistemic provenance ──────────────────────────────────────────────────
    attested_by          TEXT              NOT NULL,
    origin_model         TEXT,
        -- NULLABLE. Control-plane and watcher events may originate without a
        -- model. Do not fabricate a model name. Do not misuse source_system
        -- as a substitute for origin_model. Set only when a model genuinely
        -- produced or shaped this event.

    recorded_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE rt_manifestations IS
'Real-time events from control plane, orchestrator, watchers, mindgraph, agents. '
'Append-only. Deterministic source identity via producer_id/epoch/sequence. '
'ingest_seq is local arrival order only; it is not logical event identity.';

COMMENT ON COLUMN rt_manifestations.event_id IS
'SHA-256 hex of MOSTAR_COGNITION_EVENT_V1 JCS canonical envelope. '
'See inline algorithm comment above. '
'payload_hash = lower(hex(SHA256(UTF8(JCS(payload))))). '
'Domain marker MOSTAR_COGNITION_EVENT_V1 is mandatory; '
'a future algorithm must use a different version marker.';

COMMENT ON COLUMN rt_manifestations.ingest_seq IS
'Local ingest ordinal. NOT logical event identity. NOT replay-stable. '
'Not part of event_id. For ingest-order debugging only.';

CREATE INDEX rt_manifestations_occurred_idx  ON rt_manifestations (occurred_at DESC);
CREATE INDEX rt_manifestations_sovereign_idx ON rt_manifestations (sovereign_date DESC);
CREATE INDEX rt_manifestations_type_idx      ON rt_manifestations (manifestation_type);
CREATE INDEX rt_manifestations_source_idx    ON rt_manifestations (source_system);
CREATE INDEX rt_manifestations_producer_idx  ON rt_manifestations (producer_id, producer_epoch);

-- ── 5. cognition_stream view ─────────────────────────────────────────────────
-- Unified query stream of MoStar's persisted cognition outputs:
-- sealed moments, current Neo4j synthesis projections, and real-time manifestations.
--
-- Note: neo4j_synthesis rows reflect current Graph state (may be updated).
-- This view is therefore NOT an immutable historical ledger. It is the current
-- queryable state of all three sources.
--
-- security_invoker=true: when RLS is added to underlying tables in the future,
-- this view will respect the querying role's privileges, not the view creator's.
-- A security-definer view would silently bypass RLS. Setting this now avoids
-- a retroactive fix after RLS is enabled.
--
-- WARNING: SELECT * FROM cognition_stream returns NO guaranteed ordering.
-- Consumers requiring deterministic order must supply an explicit ORDER BY, e.g.:
--   ORDER BY occurred_at, stream_type, stream_key
-- This is deterministic tie-breaking; it is not a claim of causal ordering.
CREATE OR REPLACE VIEW cognition_stream
WITH (security_invoker = true) AS

    SELECT
        'mo_moment'                          AS stream_type,
        quantum_id                           AS stream_key,
        epistemic_mode,
        attested_by,
        origin_model,
        occurred_at,
        sovereign_date,
        jsonb_build_object(
            'talk_input',   talk_input,
            'think_output', think_output,
            'seal',         seal,
            'source_type',  source_type
        )                                    AS payload,
        recorded_at
    FROM mo_moments

    UNION ALL

    SELECT
        'neo4j_synthesis'                    AS stream_type,
        canonical_id                         AS stream_key,
        epistemic_mode,
        attested_by,
        origin_model,
        occurred_at,
        sovereign_date,
        payload,
        recorded_at
    FROM neo4j_synthesis

    UNION ALL

    SELECT
        'rt_manifestation'                   AS stream_type,
        event_id                             AS stream_key,
        epistemic_mode,
        attested_by,
        origin_model,
        occurred_at,
        sovereign_date,
        payload,
        recorded_at
    FROM rt_manifestations;

COMMENT ON VIEW cognition_stream IS
'Unified query stream across mo_moments, neo4j_synthesis, rt_manifestations. '
'Not an immutable ledger: neo4j_synthesis reflects current Graph state. '
'security_invoker=true: caller privileges apply (RLS-safe for future policies). '
'No ordering guarantee without explicit ORDER BY occurred_at, stream_type, stream_key.';

-- ── 6. Privileges ────────────────────────────────────────────────────────────

-- Schema-level: cognition_app may use public schema objects but not create them.
GRANT USAGE ON SCHEMA public TO cognition_app;

-- mo_moments: append-only. Sealed moments are not rewritten by the application.
GRANT SELECT, INSERT ON mo_moments TO cognition_app;

-- neo4j_synthesis: re-projectable. Neo4j is authoritative; UPDATE permitted
-- so that projections converge with Graph canonical state.
GRANT SELECT, INSERT, UPDATE ON neo4j_synthesis TO cognition_app;

-- rt_manifestations: event-oriented, append-only.
GRANT SELECT, INSERT ON rt_manifestations TO cognition_app;

-- cognition_stream: query only.
GRANT SELECT ON cognition_stream TO cognition_app;

-- Sequences: ingest_seq implicit via INSERT; listed explicitly for clarity.
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO cognition_app;

-- Default privileges: future objects created by cognition_owner in this schema
-- inherit the same base pattern. Per-table restrictions (no UPDATE on moments)
-- must be explicitly re-applied if new tables are added.
ALTER DEFAULT PRIVILEGES FOR ROLE cognition_owner IN SCHEMA public
    GRANT SELECT, INSERT ON TABLES TO cognition_app;
ALTER DEFAULT PRIVILEGES FOR ROLE cognition_owner IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO cognition_app;

-- No DELETE granted anywhere. No TRUNCATE. No CREATE TABLE for cognition_app.
-- Data is sovereign. The runtime does not get blanket authority to rewrite history.

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- VERIFICATION GATES (run after COMMIT)
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Objects exist:
--    \dt          → mo_moments, neo4j_synthesis, rt_manifestations
--    \dv          → cognition_stream
--    \dT          → epistemic_mode_t

-- 2. Smoke test (as cognition_app or superuser):
--
--    INSERT INTO mo_moments (quantum_id, talk_input, think_output, seal, source_type,
--        epistemic_mode, occurred_at, attested_by, origin_model)
--    VALUES ('qid:test:001', 'test input', 'test output', '⬡', 'live',
--        'recorded', NOW(), 'Devin', 'none');
--
--    INSERT INTO neo4j_synthesis (canonical_id, entity_type, synthesis_type,
--        payload, attested_by, origin_model, epistemic_mode, occurred_at)
--    VALUES ('claim:test:001', 'Claim', 'claim_resolution',
--        '{"status":"resolved"}'::jsonb, 'Devin', 'none', 'recorded', NOW());
--
--    INSERT INTO rt_manifestations (event_id, manifestation_type, source_system,
--        producer_id, producer_epoch, producer_sequence, payload, payload_hash,
--        epistemic_mode, occurred_at, attested_by)
--    VALUES (
--        lower(encode(sha256('test-event-placeholder'), 'hex')),
--        'agent_signal', 'control_plane',
--        'test-producer', '2026-08-20T00:00:00Z', 0,
--        '{"signal":"ok"}'::jsonb,
--        lower(encode(sha256('{"signal":"ok"}'), 'hex')),
--        'recorded', NOW(), 'Devin'
--    );
--
--    SELECT stream_type, stream_key, epistemic_mode, occurred_at
--    FROM   cognition_stream
--    ORDER BY occurred_at, stream_type, stream_key;
--    → 3 rows

-- 3. Sovereign time boundary test:
--    Nairobi midnight = 21:00:00 UTC the previous calendar day.
--
--    SELECT occurred_at, sovereign_date FROM mo_moments
--    WHERE quantum_id IN ('qid:boundary:before', 'qid:boundary:after');
--
--    occurred_at = '2026-08-19 20:59:59.999999+00' → sovereign_date = '2026-08-19'
--    occurred_at = '2026-08-19 21:00:00.000000+00' → sovereign_date = '2026-08-20'
--
--    Run under different session timezones (SET timezone = 'UTC';  SET timezone = 'US/Eastern';).
--    sovereign_date must not change.

-- 4. Manifestation identity probe:
--    Same logical event replayed twice → second INSERT hits UNIQUE constraint
--      (source_system, producer_id, producer_epoch, producer_sequence).
--    Same occurred_at microsecond + different producer_sequence → two rows persist.

-- 5. Privilege gates (as cognition_app):
--    SELECT on all three tables/view → succeeds
--    INSERT on mo_moments            → succeeds
--    INSERT on rt_manifestations     → succeeds
--    INSERT on neo4j_synthesis       → succeeds
--    UPDATE on neo4j_synthesis       → succeeds
--    UPDATE on mo_moments            → fails (permission denied)
--    UPDATE on rt_manifestations     → fails (permission denied)
--    DELETE on any table             → fails
--    TRUNCATE any table              → fails
--    CREATE TABLE                    → fails

-- 6. Restart-survival gate (before building Neo4j projector):
--    Restart WSL / PostgreSQL service.
--    Reconnect to :5433.
--    mostar_cognition returns (\l).
--    Sentinel rows from smoke test return unchanged.
--    Only after this gate passes does projector work begin.
