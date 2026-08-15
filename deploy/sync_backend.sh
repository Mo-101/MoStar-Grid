#!/usr/bin/env bash
# Safe ad-hoc sync of back/ and/or core/ to the VPS, for pushing local
# code changes (e.g. WIP not yet worth a full deploy_grid_vps.sh run)
# without hand-rolling an rsync command that might omit protection for
# server-owned state.
#
# Incident 2026-08-15: an ad-hoc `rsync --delete` of back/ run directly
# (not through this script) used a narrower exclude list and overwrote
# the VPS's neo4j.conf with the local dev machine's copy, taking the live
# graph offline. Use this script instead of a hand-written rsync.
#
# Usage: ./deploy/sync_backend.sh [back] [core]   (defaults to both)
set -euo pipefail

VPS_HOST="31.97.180.251"
VPS_USER="root"
SSH_KEY="${HOME}/.ssh/id_ed25519"
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i ${SSH_KEY}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRID_SRC="$(dirname "${SCRIPT_DIR}")"
VPS_GRID="/opt/mostar/grid"
RSYNC_PROTECTED="${SCRIPT_DIR}/rsync-protected.txt"

if [ ! -s "${RSYNC_PROTECTED}" ] || ! grep -q "mo-neo4j/conf/" "${RSYNC_PROTECTED}"; then
    echo "ABORT: ${RSYNC_PROTECTED} is missing, empty, or no longer protects mo-neo4j/conf/." >&2
    exit 1
fi

TARGETS=("$@")
if [ "${#TARGETS[@]}" -eq 0 ]; then
    TARGETS=(back core)
fi

# Always rsync from the repo ROOT (never a subdirectory as its own source
# root) so rsync-protected.txt's paths — which are written relative to the
# repo root, e.g. back/services/mindgraph/mo-neo4j/conf/ — mean what they
# say. Syncing `back/` as its own source root instead makes those relative
# paths resolve to services/mindgraph/... with no `back/` prefix to match,
# silently defeating the exclude list. (This is exactly how the
# 2026-08-15 incident happened — verify with --dry-run before trusting a
# change to this pattern.)
INCLUDE_ARGS=()
for dir in "${TARGETS[@]}"; do
    INCLUDE_ARGS+=(--include="${dir}/***")
done

echo "Syncing [${TARGETS[*]}] -> ${VPS_USER}@${VPS_HOST}:${VPS_GRID}/ (repo-root-relative excludes applied)"
rsync -az --delete \
    --exclude-from="${RSYNC_PROTECTED}" \
    "${INCLUDE_ARGS[@]}" \
    --exclude='*' \
    -e "ssh ${SSH_OPTS}" \
    "${GRID_SRC}/" "${VPS_USER}@${VPS_HOST}:${VPS_GRID}/"

echo "Done. Rebuild affected containers, e.g.: ssh ... 'cd ${VPS_GRID} && docker compose build grid-api && docker compose up -d grid-api mcp-gateway'"
