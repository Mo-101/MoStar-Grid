#!/usr/bin/env bash
set -e
F=/home/idona/MoStar/_apps/grid/data/mem/12_archived_misc/neo4j.conf
if [ -f "$F" ]; then
  echo "=== $F ==="
  grep -E "server\.bolt\.listen_address|server\.directories\.data|server\.databases\.default_to" "$F" | head -20 || true
else
  echo "$F not found"
fi
