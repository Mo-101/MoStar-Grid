#!/usr/bin/env bash
set -Eeuo pipefail
set -a

ROOT=/home/idona/MoStar/_apps/grid
cd "$ROOT"
. ./.env.local
set +a

: "${NEO4J_URI:?NEO4J_URI is missing}"
: "${NEO4J_ADMIN_USER:?NEO4J_ADMIN_USER is missing}"
: "${NEO4J_ADMIN_PASSWORD:?NEO4J_ADMIN_PASSWORD is missing}"
: "${NEO4J_USER:?NEO4J_USER is missing}"
: "${NEO4J_PASSWORD:?NEO4J_PASSWORD is missing}"

TMP_CYPHER=$(mktemp /tmp/bootstrap_user.XXXXXX.cypher)
trap 'rm -f "$TMP_CYPHER"' EXIT

cat > "$TMP_CYPHER" <<EOF
CREATE USER $NEO4J_USER IF NOT EXISTS SET PASSWORD '$NEO4J_PASSWORD' CHANGE NOT REQUIRED;
ALTER USER $NEO4J_USER SET PASSWORD '$NEO4J_PASSWORD' CHANGE NOT REQUIRED;
ALTER USER $NEO4J_ADMIN_USER SET PASSWORD '$NEO4J_ADMIN_PASSWORD' CHANGE NOT REQUIRED;
DROP USER grid_builder_test IF EXISTS;
EOF

cypher-shell \
  -a "$NEO4J_URI" \
  -u "$NEO4J_ADMIN_USER" \
  -p "$NEO4J_ADMIN_PASSWORD" \
  --database system \
  --history disable \
  --fail-fast \
  -f "$TMP_CYPHER"

echo "User bootstrap executed on system database."
