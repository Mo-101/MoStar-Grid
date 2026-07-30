#!/usr/bin/env bash
set -Eeuo pipefail

NEO4J_HOME=/usr/share/neo4j
NEO4J_CONF=/home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/conf
BACKUP_DIR="/home/idona/MoStar/_backups/neo4j/$(date +%Y%m%d-%H%M%S)"
PING_FILE=/home/idona/MoStar/_apps/grid/ping.cypher

mkdir -p "$BACKUP_DIR"
chmod 0700 "$BACKUP_DIR"

echo "Stopping mostar-neo4j..."
pm2 stop mostar-neo4j

# Wait for process to stop
for i in {1..30}; do
  if ! pgrep -f 'org.neo4j.server.startup.NeoBoot' >/dev/null; then
    break
  fi
  sleep 1
done

if pgrep -f 'org.neo4j.server.startup.NeoBoot' >/dev/null; then
  echo "Neo4j did not stop in time" >&2
  exit 1
fi

echo "Dumping system database..."
NEO4J_HOME="$NEO4J_HOME" NEO4J_CONF="$NEO4J_CONF" \
  "$NEO4J_HOME/bin/neo4j-admin" database dump system --to-path="$BACKUP_DIR"

echo "Dumping neo4j database..."
NEO4J_HOME="$NEO4J_HOME" NEO4J_CONF="$NEO4J_CONF" \
  "$NEO4J_HOME/bin/neo4j-admin" database dump neo4j --to-path="$BACKUP_DIR"

echo "Starting mostar-neo4j..."
pm2 start mostar-neo4j

# Wait for bolt port to come up
for i in {1..60}; do
  if ss -tlnp 2>/dev/null | grep -q ':47687'; then
    break
  fi
  sleep 2
done

if ! ss -tlnp 2>/dev/null | grep -q ':47687'; then
  echo "Neo4j bolt port not listening after start" >&2
  exit 1
fi

# Create a ping cypher file if needed
if [ ! -f "$PING_FILE" ]; then
  echo 'RETURN 1 AS online;' > "$PING_FILE"
fi

echo "Verifying connectivity..."
/home/idona/MoStar/_apps/grid/run_admin_cypher.sh "$PING_FILE"

echo "Backup complete: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
