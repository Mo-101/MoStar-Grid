#!/usr/bin/env bash
set -e
echo "=== /etc/neo4j/neo4j.conf ==="
if [ -f /etc/neo4j/neo4j.conf ]; then
  grep -E "server\.bolt\.listen_address|server\.directories\.data|server\.databases\.default_to|dbms\.directories\.data" /etc/neo4j/neo4j.conf | head -20 || true
else
  echo "not found"
fi

echo "=== /etc/neo4j/neo4j-admin.conf ==="
if [ -f /etc/neo4j/neo4j-admin.conf ]; then
  grep -E "server\.directories\.data|dbms\.directories\.data" /etc/neo4j/neo4j-admin.conf | head -20 || true
fi

echo "=== /usr/share/neo4j/conf ==="
ls -la /usr/share/neo4j/conf 2>&1 || true
