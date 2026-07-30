#!/usr/bin/env bash
set -e
echo "=== backup log ==="
cat /tmp/backup_neo4j.log 2>&1 || true
echo "=== pm2 status ==="
pm2 status | grep -E 'mostar-neo4j|status' || true
echo "=== backup dir ==="
ls -la /home/idona/MoStar/_backups/neo4j/ 2>/dev/null | tail -5 || true
