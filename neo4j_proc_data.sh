#!/usr/bin/env bash
set -e
PID=$(ss -tlnp 2>/dev/null | grep ':47687' | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1)
if [ -z "$PID" ]; then
  PID=$(pgrep -f 'org.neo4j.server.startup.NeoBoot' | head -1)
fi
echo "Neo4j PID: $PID"
if [ -n "$PID" ] && [ -d "/proc/$PID" ]; then
  echo "=== cwd ==="
  ls -l "/proc/$PID/cwd"
  echo "=== data files ==="
  ls -l "/proc/$PID/fd" | grep -E 'databases|transactions|neostore|data' | head -50 || true
  echo "=== environ ==="
  cat "/proc/$PID/environ" | tr '\0' '\n' | grep -E 'NEO4J|CONF|DATA|HOME' | sort || true
fi
