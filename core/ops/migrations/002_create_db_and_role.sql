-- ═══════════════════════════════════════════════════════════════════════════════
-- 002_create_db_and_role.sql
-- mostar_cognition — database and role provisioning.
--
-- Run while connected to the postgres system database on :5433.
-- CRITICAL: Do NOT wrap in BEGIN...COMMIT.
--           CREATE DATABASE cannot run inside an explicit transaction block.
--
-- Prerequisite: 000_preflight_verify.sql must have passed with no failures.
-- Next step:    connect to mostar_cognition, then apply 003_mostar_cognition_schema.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ── 1. Ownership role ────────────────────────────────────────────────────────
-- cognition_owner: owns the database, schema, and all objects.
-- NOLOGIN — the runtime never connects as this role.
-- Ownership is structural; connection is cognition_app only.
CREATE ROLE cognition_owner
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION;

-- ── 2. Application runtime role ──────────────────────────────────────────────
-- cognition_app: the only login used by the Grid/orchestrator at runtime.
-- Scoped to exactly what the application needs — no more.
-- CHANGE PASSWORD before first use.
CREATE ROLE cognition_app
    LOGIN
    PASSWORD 'CHANGE_BEFORE_FIRST_USE'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS;

-- ── 3. Create database ───────────────────────────────────────────────────────
-- Owner is cognition_owner, not the superuser running this script.
-- template0 guarantees clean encoding regardless of cluster defaults.
CREATE DATABASE mostar_cognition
    OWNER      = cognition_owner
    ENCODING   = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE   = 'en_US.UTF-8'
    TEMPLATE   = template0;

-- ── 4. Harden database-level access ─────────────────────────────────────────
-- Remove PUBLIC's default connect right immediately after creation.
-- Only cognition_app may connect to mostar_cognition.
REVOKE ALL ON DATABASE mostar_cognition FROM PUBLIC;
GRANT  CONNECT ON DATABASE mostar_cognition TO cognition_app;

-- ── Verification checklist (run after applying this file) ────────────────────
-- \l mostar_cognition
--   → owner = cognition_owner, encoding UTF8
-- \du cognition_owner
--   → NOLOGIN, no special attributes
-- \du cognition_app
--   → LOGIN, no superuser/createdb/createrole/bypassrls
-- psql -U cognition_app -d mostar_cognition -h 127.0.0.1 -p 5433
--   → connection accepted (after changing password)
-- psql -U postgres -d mostar_cognition -c '\dt'
--   → no tables yet (003 not yet applied)
-- SELECT datname FROM pg_database WHERE datname = 'mostar';
--   → mostar still present and unchanged
