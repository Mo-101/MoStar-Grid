#!/usr/bin/env bash
set -e
PID=$(pgrep -f 'org.neo4j.server' | head -1 || true)
if [ -n "$PID" ]; then
  echo "=== Neo4j process $PID ==="
  cat "/proc/$PID/environ" | tr '\0' '\n' | grep -E 'NEO4J|CONF|HOME|DATA' | sort || true
  echo "=== CWD ==="
  ls -l "/proc/$PID/cwd"
else
  echo "Neo4j process not found"
fi

echo "=== pm2 env ==="
pm2 env 21 | grep -E 'NEO4J|CONF|HOME|DATA' || true
