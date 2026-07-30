#!/usr/bin/env bash
set -e
PID=$(pgrep -f 'org.neo4j.server.startup.NeoBoot' | head -1 || true)
if [ -n "$PID" ]; then
  ls -l "/proc/$PID/fd" | grep -E 'data|databases|transactions|neostore' | head -30 || true
fi
