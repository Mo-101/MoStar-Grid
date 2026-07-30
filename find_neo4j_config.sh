#!/usr/bin/env bash
set -e
for f in /usr/share/neo4j/conf/neo4j.conf /home/idona/MoStar/_apps/grid/mindgraph/mo-neo4j/conf/neo4j.conf /home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/conf/neo4j.conf; do
  if [ -f "$f" ]; then
    echo "=== $f ==="
    grep -E "server\.bolt\.listen_address|server\.directories\.data|server\.databases\.default_to|dbms\.directories\.data" "$f" | head -10 || true
  fi
done
