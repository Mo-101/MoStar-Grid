#!/usr/bin/env bash
set -e
PID=$(pgrep -f 'org.neo4j.server.startup.NeoBoot' | head -1 || true)
if [ -n "$PID" ]; then
  ls -l "/proc/$PID/fd" | grep -E 'neo4j|conf|\.conf' | head -30 || true
  echo "=== cwd ==="
  ls -l "/proc/$PID/cwd"
  echo "=== maps ==="
  grep -E 'neo4j|conf' "/proc/$PID/maps" | head -10 || true
else
  echo "Neo4j process not found"
fi
