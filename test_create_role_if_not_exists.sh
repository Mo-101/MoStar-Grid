#!/usr/bin/env bash
set -e
set -a
cd /home/idona/MoStar/_apps/grid
. .env.local
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_ADMIN_USER" -p "$NEO4J_ADMIN_PASSWORD" --database system --file test_create_role_if_not_exists.cypher --format plain
