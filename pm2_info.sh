#!/usr/bin/env bash
set -e
cd /home/idona/MoStar/_apps/grid/mindgraph/mo-neo4j
pm2 describe mostar-neo4j | cat
