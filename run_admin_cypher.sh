#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/home/idona/MoStar/_apps/grid
FILE=${1:?Usage: run_admin_cypher.sh FILE}

cd "$ROOT"

set -a
. ./.env.local
set +a

: "${NEO4J_URI:?NEO4J_URI is missing}"
: "${NEO4J_ADMIN_USER:?NEO4J_ADMIN_USER is missing}"
: "${NEO4J_ADMIN_PASSWORD:?NEO4J_ADMIN_PASSWORD is missing}"

export NEO4J_USERNAME="$NEO4J_ADMIN_USER"
export NEO4J_PASSWORD="$NEO4J_ADMIN_PASSWORD"

exec cypher-shell \
  -a "$NEO4J_URI" \
  -d neo4j \
  --history disable \
  --fail-fast \
  -f "$FILE"
