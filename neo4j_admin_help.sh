#!/usr/bin/env bash
set -e
NEO4J_HOME=/usr/share/neo4j
NEO4J_CONF=/home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/conf
"$NEO4J_HOME/bin/neo4j-admin" database dump --help 2>&1 | head -60 || true
