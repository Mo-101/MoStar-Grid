#!/bin/bash
# MoStar Grid — start the Grid's Neo4j (bolt:47687, http:47474)
# Uses system Neo4j 2026.04.0 JARs. NEO4J_HOME must never point at the
# bundled mo-neo4j lib/ — it is 2025.10.1 and cannot read 2026.04.0 tx logs.
export NEO4J_HOME="/usr/share/neo4j"
export NEO4J_CONF="/home/idona/MoStar/_apps/grid/back/services/mindgraph/mo-neo4j/conf"
exec /usr/share/neo4j/bin/neo4j console
