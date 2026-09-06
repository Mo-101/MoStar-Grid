-- ═══════════════════════════════════════════════════════════════════════════════
-- 000_preflight_verify.sql
-- mostar_cognition preflight — READ-ONLY. Creates no permanent objects.
--
-- Run against :5433 while connected to the postgres system database.
-- Review every result before proceeding to 002_create_db_and_role.sql.
-- Nothing here modifies any state.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ── 1. Server identity ───────────────────────────────────────────────────────
-- server_port must be 5433.
-- connected_db  must be 'postgres'.
SELECT
    current_setting('port')::int              AS server_port,
    current_database()                        AS connected_db,
    current_user                              AS connected_as,
    version()                                 AS pg_version;

-- ── 2. Version gate ──────────────────────────────────────────────────────────
-- security_invoker on views was introduced in PostgreSQL 15.
-- version_ok must be true before proceeding.
SELECT
    current_setting('server_version_num')::int   AS version_num,
    current_setting('server_version_num')::int >= 150000 AS version_ok;

-- ── 3. Target database existence ─────────────────────────────────────────────
-- Expected: 0 rows. If 1 row is returned, mostar_cognition already exists —
-- stop and investigate before re-running 002.
SELECT datname, datdba::regrole::text AS owner
FROM   pg_database
WHERE  datname = 'mostar_cognition';

-- ── 4. Role conflict check ───────────────────────────────────────────────────
-- Expected: 0 rows. If either role already exists, resolve before running 002.
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolbypassrls
FROM   pg_roles
WHERE  rolname IN ('cognition_owner', 'cognition_app');

-- ── 5. Confirm trading database mostar is present and will not be touched ─────
-- Expected: 1 row. Confirms mostar exists and reminds that this migration
-- targets a different database entirely.
SELECT datname, datdba::regrole::text AS owner
FROM   pg_database
WHERE  datname = 'mostar';

-- ── 6. Sovereign timezone generated-column probe ─────────────────────────────
-- Empirically tests what PostgreSQL accepts as IMMUTABLE for GENERATED columns.
-- TEMP tables are session-scoped and drop automatically.
--
-- Probe A: (t + INTERVAL '3 hours')::date
--   Expected: REJECTED — interval arithmetic on timestamptz is not IMMUTABLE.
--
-- Probe B: (t AT TIME ZONE 'Africa/Nairobi')::date
--   Expected: ACCEPTED.
--   Africa/Nairobi = UTC+3, no DST. The named timezone is the governance rule.
--
-- If Probe B fails: STOP. Report pg_version and the error. Do not proceed to
-- 002 and do not silently substitute a trigger or a numeric offset expression.
DO $$
DECLARE
    bad_works  BOOLEAN := FALSE;
    good_works BOOLEAN := FALSE;
    bad_err    TEXT;
    good_err   TEXT;
BEGIN
    -- Probe A: interval arithmetic (expected to fail as non-immutable)
    BEGIN
        EXECUTE '
            CREATE TEMP TABLE _preflight_tz_bad (
                t TIMESTAMPTZ,
                d DATE GENERATED ALWAYS AS (
                    (t + INTERVAL ''3 hours'')::date
                ) STORED
            )';
        bad_works := TRUE;
        -- Clean up if it somehow succeeded
        EXECUTE 'DROP TABLE IF EXISTS _preflight_tz_bad';
    EXCEPTION WHEN OTHERS THEN
        bad_err := SQLERRM;
    END;

    -- Probe B: named timezone (expected to succeed)
    BEGIN
        EXECUTE '
            CREATE TEMP TABLE _preflight_tz_good (
                t TIMESTAMPTZ,
                d DATE GENERATED ALWAYS AS (
                    (t AT TIME ZONE ''Africa/Nairobi'')::date
                ) STORED
            )';
        good_works := TRUE;
        EXECUTE 'DROP TABLE IF EXISTS _preflight_tz_good';
    EXCEPTION WHEN OTHERS THEN
        good_err := SQLERRM;
    END;

    RAISE NOTICE '────────────────────────────────────────────────';
    RAISE NOTICE 'Timezone probe results:';
    RAISE NOTICE '  Probe A (interval +3h)         works=% error=%',
        bad_works,  COALESCE(bad_err,  'none');
    RAISE NOTICE '  Probe B (AT TIME ZONE Nairobi)  works=% error=%',
        good_works, COALESCE(good_err, 'none');
    RAISE NOTICE '────────────────────────────────────────────────';

    IF NOT good_works THEN
        RAISE EXCEPTION
            'STOP: AT TIME ZONE ''Africa/Nairobi'' rejected by GENERATED column. '
            'Server version: %. Error: %. '
            'Do not proceed. Do not substitute a trigger.',
            current_setting('server_version'), good_err;
    END IF;

    IF bad_works THEN
        RAISE WARNING
            'Probe A (interval arithmetic) unexpectedly succeeded. '
            'Verify PostgreSQL IMMUTABLE semantics for GENERATED columns '
            'on this version before proceeding.';
    END IF;

    RAISE NOTICE 'Timezone probe: PASSED. Safe to proceed to 002.';
END;
$$;
