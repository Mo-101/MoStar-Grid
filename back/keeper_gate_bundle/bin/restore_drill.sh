#!/usr/bin/env bash
# restore_drill.sh — a dump never test-loaded is a prayer, not a backup.
# Community Edition runs ONE database, so the drill loads the golden dump
# into a throwaway Neo4j container and counts what comes back.
#
# Usage: bash restore_drill.sh /home/idona/.neo4j_keeper_gate.env [min_expected_nodes]

set -euo pipefail

ENV_FILE="${1:?Usage: restore_drill.sh <env_file> [min_nodes]}"
MIN_EXPECT="${2:-90000}"
# shellcheck disable=SC1090
source "$ENV_FILE"
: "${GOLDEN_DIR:?}" "${NEO4J_DATABASE:?}"

DUMP="$GOLDEN_DIR/$NEO4J_DATABASE.dump"
log() { echo "[$(date '+%F %T')] $*"; }

# ── 1. Checksum — trust nothing, verify everything ───────────────────────
[ -s "$DUMP" ] || { log "FATAL: no golden dump at $DUMP"; exit 1; }
if [ -f "$DUMP.sha256" ]; then
  (cd "$GOLDEN_DIR" && sha256sum -c "$NEO4J_DATABASE.dump.sha256") \
    || { log "FATAL: checksum mismatch — golden dump is wounded."; exit 2; }
  log "Checksum verified."
else
  log "WARNING: no checksum file beside the dump. Generate one."
fi

# ── 2. Load into a disposable container — never near the real keeper ─────
command -v docker >/dev/null 2>&1 || {
  log "Docker absent. Drill cannot proceed automatically."
  log "Manual drill: install a second Neo4j (different ports), then:"
  log "  neo4j-admin database load $NEO4J_DATABASE --from-path=$GOLDEN_DIR --overwrite-destination=true"
  exit 3
}

DRILL=keeper-restore-drill
docker rm -f "$DRILL" >/dev/null 2>&1 || true

log "Loading golden dump into throwaway container..."
docker run --name "$DRILL" -d \
  -e NEO4J_AUTH=neo4j/drillpass123 \
  -v "$GOLDEN_DIR":/dumps:ro \
  neo4j:5 >/dev/null

sleep 5
docker exec "$DRILL" neo4j stop || true
sleep 3
docker exec "$DRILL" neo4j-admin database load "$NEO4J_DATABASE" \
  --from-path=/dumps --overwrite-destination=true
docker exec -d "$DRILL" neo4j start
log "Waiting for drill instance to come up..."
sleep 25

COUNT=$(docker exec "$DRILL" cypher-shell -u neo4j -p drillpass123 \
  --format plain "MATCH (n) RETURN count(n);" | tail -1 | tr -dc '0-9')

docker rm -f "$DRILL" >/dev/null

if [ -n "$COUNT" ] && [ "$COUNT" -ge "$MIN_EXPECT" ]; then
  log "DRILL PASSED: golden dump restores to $COUNT nodes (≥ $MIN_EXPECT)."
  log "The backup is real. The keeper can always come home."
  exit 0
else
  log "DRILL FAILED: restored count '$COUNT' below $MIN_EXPECT. The dump is NOT trustworthy."
  exit 4
fi
