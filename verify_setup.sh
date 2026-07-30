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

echo '--- USERS ---'
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_ADMIN_USER" -p "$NEO4J_ADMIN_PASSWORD" --database system --history disable --fail-fast "SHOW USERS;" --format plain
echo '--- CONSTRAINTS ---'
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_ADMIN_USER" -p "$NEO4J_ADMIN_PASSWORD" --database "$NEO4J_DATABASE" --history disable --fail-fast "SHOW CONSTRAINTS;" --format plain
echo '--- INDEXES ---'
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_ADMIN_USER" -p "$NEO4J_ADMIN_PASSWORD" --database "$NEO4J_DATABASE" --history disable --fail-fast "SHOW INDEXES;" --format plain
