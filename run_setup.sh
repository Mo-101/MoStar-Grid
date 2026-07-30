#!/usr/bin/env bash
set -Eeuo pipefail
set -a

cd /home/idona/MoStar/_apps/grid
. .env.local
set +a

: "${NEO4J_URI:?NEO4J_URI is missing}"
: "${NEO4J_ADMIN_USER:?NEO4J_ADMIN_USER is missing}"
: "${NEO4J_ADMIN_PASSWORD:?NEO4J_ADMIN_PASSWORD is missing}"
: "${NEO4J_DATABASE:?NEO4J_DATABASE is missing}"

TMP_SCHEMA=$(mktemp /tmp/setup_schema.XXXXXX.cypher)
trap 'rm -f "$TMP_SCHEMA"' EXIT

cat > "$TMP_SCHEMA" <<EOF
// Create constraints (idempotent)
CREATE CONSTRAINT unique_mostar_id IF NOT EXISTS
FOR (m:MoStarMoment)
REQUIRE (m.id) IS UNIQUE;

CREATE CONSTRAINT unique_analysisreport_id IF NOT EXISTS
FOR (r:AnalysisReport)
REQUIRE (r.id) IS UNIQUE;

CREATE CONSTRAINT unique_retentionpolicy_id IF NOT EXISTS
FOR (p:RetentionPolicy)
REQUIRE (p.id) IS UNIQUE;

CREATE CONSTRAINT unique_storagebackend_id IF NOT EXISTS
FOR (s:StorageBackend)
REQUIRE (s.id) IS UNIQUE;

// Create index (idempotent)
CREATE INDEX domain_name_index IF NOT EXISTS
FOR (d:Domain)
ON (d.name);

// Starter nodes (idempotent)
MERGE (d:Domain {id:'Domain_MoStarMoment', name:'MoStarMoment'})
  ON CREATE SET d.description = 'Domain node representing MoStarMoment entities';

MERGE (p:RetentionPolicy {id:'RP_MoStarMoment_v1'})
  ON CREATE SET p.domain='MoStarMoment', p.max_age_days=365, p.archive_after_days=365, p.immutable_flag=false, p.reason='Default metadata retention';

MERGE (r:AnalysisReport {id:'AR_20260707_001'})
  ON CREATE SET r.title='MoStarMoment Retention and Storage Recommendations', r.author='ExternalAnalysisBot', r.created_at=datetime(), r.summary='Added retention and storage metadata', r.status='draft';

// Link report -> policy -> domain (idempotent)
MATCH (r:AnalysisReport {id:'AR_20260707_001'}), (p:RetentionPolicy {id:'RP_MoStarMoment_v1'}), (d:Domain {name:'MoStarMoment'})
MERGE (r)-[:RECOMMENDS]->(p)
MERGE (p)-[:APPLIES_TO]->(d);

// Final verification
RETURN 'Schema setup executed. Community edition: roles/privileges skipped. Run SHOW CONSTRAINTS; SHOW INDEXES; to verify.' AS next_steps;
EOF

cypher-shell \
  -a "$NEO4J_URI" \
  -u "$NEO4J_ADMIN_USER" \
  -p "$NEO4J_ADMIN_PASSWORD" \
  --database "$NEO4J_DATABASE" \
  --history disable \
  --fail-fast \
  --file "$TMP_SCHEMA" \
  --format plain
