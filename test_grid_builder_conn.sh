#!/usr/bin/env bash
set -e
set -a
cd /home/idona/MoStar/_apps/grid
. .env.local
cypher-shell -a "$NEO4J_URI" -u grid_builder -p 'TestPassword123' --database neo4j --file test_grid_builder_conn.cypher --format plain
