-- ═══════════════════════════════════════════════════════════════════════════════
-- 005_yolo_dataset_schema.sql
-- YOLO image/annotation dataset schema inside mostar_cognition.
--
-- Prerequisite: 002_create_db_and_role.sql and 003_mostar_cognition_schema.sql
--               applied. Run as a superuser or as cognition_owner.
--
-- Connection: psql -U postgres -d mostar_cognition -h 127.0.0.1 -p 5433 -f 005_yolo_dataset_schema.sql
--
-- Rationale: YOLO training data is not sealed cognition. It is kept in its own
--            `yolo` schema so it lives inside mostar_cognition without blurring
--            the governance boundary around mo_moments, neo4j_synthesis, or
--            rt_manifestations.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. Schema ─────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS yolo;

COMMENT ON SCHEMA yolo IS
'YOLO image and bounding-box dataset tables. Training data, not sovereign cognition.';

-- ── 2. Images table ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS yolo.images (
    id              SERIAL PRIMARY KEY,
    image_filename  TEXT NOT NULL UNIQUE,
    image_path      TEXT,
    image_hash      TEXT,
    image_width     INTEGER,
    image_height    INTEGER,
    split_type      TEXT CHECK (split_type IN ('train', 'val', 'test')),
    capture_date    TEXT,
    location        TEXT,
    camera_sensor   TEXT,
    weather         TEXT,
    model_version   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE yolo.images IS
'YOLO dataset image records. image_path is the filesystem path; image_hash is sha256(image_path). Pixel dimensions are required to export normalized .txt labels.';

-- ── 3. Annotations table ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS yolo.annotations (
    id              SERIAL PRIMARY KEY,
    image_id        INTEGER NOT NULL REFERENCES yolo.images(id) ON DELETE CASCADE,
    label_class     INTEGER NOT NULL,
    bbox_xmin       REAL NOT NULL,
    bbox_ymin       REAL NOT NULL,
    bbox_xmax       REAL NOT NULL,
    bbox_ymax       REAL NOT NULL,
    model_version   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE yolo.annotations IS
'YOLO bounding-box annotations in pixel coordinates. Exported to normalized class xc yc w h .txt labels.';

-- ── 4. Models table ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS yolo.models (
    id              SERIAL PRIMARY KEY,
    version         TEXT NOT NULL,
    source_dataset  TEXT,
    mAP50           REAL,
    mAP50_95        REAL,
    weights_blob    BYTEA,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE yolo.models IS
'Stored YOLO .pt model weights and their metrics. Keep the filesystem copy canonical; the blob is a durable backup.';

-- ── 5. Indexes ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_yolo_images_filename  ON yolo.images (image_filename);
CREATE INDEX IF NOT EXISTS idx_yolo_annotations_image ON yolo.annotations (image_id);

-- ── 5. Privileges ─────────────────────────────────────────────────────────────
-- cognition_app is the runtime login. It needs read/write on yolo tables.
GRANT USAGE ON SCHEMA yolo TO cognition_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA yolo TO cognition_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA yolo TO cognition_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA yolo
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cognition_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA yolo
    GRANT USAGE, SELECT ON SEQUENCES TO cognition_app;

-- No DELETE is not enforced here: training labels are mutable, unlike sovereign moments.

COMMIT;
