#!/usr/bin/env bash
set -e
LOG=/home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/logs/debug.log
if [ -f "$LOG" ]; then
  # Find the most recent DBMS config dump and print the line
  grep -n "DBMS provided settings" "$LOG" | tail -1 | cut -d: -f1 | head -1
  echo "---"
  grep -n "DBMS provided settings" "$LOG" | tail -1 | sed 's/\\n/\n/g' | head -200
else
  echo "debug.log not found"
fi
