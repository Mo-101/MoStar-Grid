#!/usr/bin/env bash
# neo4j_golden_dump.sh — Recovery Law, Article 1.
# Usage:
#   bash neo4j_golden_dump.sh /home/idona/.neo4j_keeper_gate.env            # golden dump
#   bash neo4j_golden_dump.sh /home/idona/.neo4j_keeper_gate.env --daily    # nightly cron mode
#
# LAW: detects the true process manager (systemd or pm2). If it cannot PROVE
# the manager, it refuses to stop anything. Raises the truce flag so the
# tripwire stands down. Restarts Neo4j and lowers the flag even on failure.

set -euo pipefail

ENV_FILE="${1:?Usage: neo4j_golden_dump.sh <env_file> [--daily]}"
MODE="${2:-golden}"
# shellcheck disable=SC1090
source "$ENV_FILE"

: "${NEO4J_DATABASE:?}" "${GOLDEN_DIR:?}" "${DUMP_DIR:?}" "${MAINT_FLAG:?}"

log() { echo "[$(date '+%F %T')] $*"; }

# ── 1. Prove the process manager. No proof, no stop. ─────────────────────
MANAGER=""
NEO4J_PM2_NAME=""

if command -v systemctl >/dev/null 2>&1 \
   && systemctl is-system-running >/dev/null 2>&1 \
   && systemctl list-unit-files 2>/dev/null | grep -q '^neo4j'; then
  MANAGER="systemd"
elif command -v pm2 >/dev/null 2>&1; then
  NEO4J_PM2_NAME=$(pm2 jlist 2>/dev/null | python3 -c '
import sys, json
try:
    for p in json.load(sys.stdin):
        if "neo4j" in p.get("name","").lower():
            print(p["name"]); break
except Exception:
    pass')
  [ -n "$NEO4J_PM2_NAME" ] && MANAGER="pm2"
fi

if [ -z "$MANAGER" ]; then
  log "REFUSING: cannot prove who manages Neo4j (no systemd unit, no pm2 process)."
  log "If Neo4j runs as 'neo4j console' in a terminal, stop it by hand, then run:"
  log "  neo4j-admin database dump $NEO4J_DATABASE --to-path=$GOLDEN_DIR --overwrite-destination=true"
  exit 3
fi
log "Process manager proven: $MANAGER ${NEO4J_PM2_NAME:+($NEO4J_PM2_NAME)}"

stop_neo4j() {
  case "$MANAGER" in
    systemd) sudo systemctl stop neo4j ;;
    pm2)     pm2 stop "$NEO4J_PM2_NAME" ;;
  esac
}
start_neo4j() {
  case "$MANAGER" in
    systemd) sudo systemctl start neo4j ;;
    pm2)     pm2 start "$NEO4J_PM2_NAME" ;;
  esac
}

# ── 2. Truce flag up. Tripwire stands down. Always cleaned up. ───────────
cleanup() {
  start_neo4j || log "WARNING: Neo4j failed to restart — intervene NOW."
  rm -f "$MAINT_FLAG"
  log "Truce flag lowered."
}
trap cleanup EXIT
touch "$MAINT_FLAG"
log "Truce flag raised: $MAINT_FLAG"

# ── 3. Destination ────────────────────────────────────────────────────────
if [ "$MODE" = "--daily" ]; then
  DEST="$DUMP_DIR/$(date +%Y%m%d_%H%M%S)"
else
  DEST="$GOLDEN_DIR"
fi
mkdir -p "$DEST"

# ── 4. Stop, dump, checksum ───────────────────────────────────────────────
log "Stopping Neo4j via $MANAGER ..."
stop_neo4j
sleep 5

log "Dumping database '$NEO4J_DATABASE' → $DEST"
neo4j-admin database dump "$NEO4J_DATABASE" \
  --to-path="$DEST" \
  --overwrite-destination=true

DUMP_FILE="$DEST/$NEO4J_DATABASE.dump"
[ -s "$DUMP_FILE" ] || { log "FATAL: dump file missing or empty."; exit 4; }

sha256sum "$DUMP_FILE" > "$DUMP_FILE.sha256"
log "Dump $(du -h "$DUMP_FILE" | cut -f1), checksum written."

# ── 5. Golden dumps become immutable. Daily dumps rotate. ────────────────
if [ "$MODE" != "--daily" ]; then
  chmod 444 "$DUMP_FILE" "$DUMP_FILE.sha256"
  log "Golden dump sealed read-only. The crown jewel is in the vault."
else
  find "$DUMP_DIR" -maxdepth 1 -type d -mtime +"${DUMP_RETENTION_DAYS:-14}" -print -exec rm -rf {} \;
  log "Daily dump complete. Rotation enforced (${DUMP_RETENTION_DAYS:-14} days)."
fi
# trap restarts Neo4j and lowers the flag.
