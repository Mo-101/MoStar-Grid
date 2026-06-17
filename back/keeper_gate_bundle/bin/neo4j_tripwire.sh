#!/usr/bin/env bash
# neo4j_tripwire.sh — Recovery Law, Article 3 (the alarm).
# Cron every minute. If the graph collapses below MIN_NODES:
#   - writers die (pm2 stop all)
#   - Neo4j stays UP, so the wound can be examined and restored
# Respects the truce flag during scheduled dumps.

set -uo pipefail

ENV_FILE="${1:-/home/idona/.neo4j_keeper_gate.env}"
# shellcheck disable=SC1090
source "$ENV_FILE"
: "${NEO4J_URI:?}" "${NEO4J_USER:?}" "${NEO4J_PASSWORD:?}" "${MIN_NODES:?}" "${MAINT_FLAG:?}"

# Truce: scheduled maintenance in progress — stand down.
[ -f "$MAINT_FLAG" ] && exit 0

COUNT_RAW=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
  --format plain "MATCH (n) RETURN count(n);" 2>/dev/null | tail -1 | tr -dc '0-9')

if [ -z "$COUNT_RAW" ]; then
  # Cannot reach the graph and no truce flag — suspicious but not proof of a wound.
  echo "[$(date '+%F %T')] WARN: graph unreachable, no maintenance flag. Investigate." >&2
  exit 1
fi

if [ "$COUNT_RAW" -lt "$MIN_NODES" ]; then
  echo "[$(date '+%F %T')] CRITICAL: node count $COUNT_RAW < $MIN_NODES. Killing writers."
  pm2 stop all 2>/dev/null || true
  # Neo4j stays alive — forensics and restore need it.
  echo "[$(date '+%F %T')] Writers stopped. Graph preserved for examination."
  exit 2
fi

exit 0
