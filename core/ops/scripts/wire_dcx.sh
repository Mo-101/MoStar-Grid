#!/usr/bin/env bash
# wire_dcx.sh - wire the grid's cognition leg to Ollama, and refuse to
# declare success unless DCX actually thinks.
#
# It cannot lie. WIRED prints only when the readiness probe returns THINKING.
#
#   ./wire_dcx.sh [OLLAMA_URL] [MODEL] [ENV_FILE] [PM2_PROC]
#   ./wire_dcx.sh --check-only [OLLAMA_URL] [MODEL]   # probe only, no writes
#
# Defaults match the grid as last reported.
set -euo pipefail

CHECK_ONLY=0
if [[ "${1:-}" == "--check-only" ]]; then CHECK_ONLY=1; shift; fi

OLLAMA_URL="${1:-http://127.0.0.1:11434}"
MODEL="${2:-Mostar/mostar-ai:dcx0}"
ENV_FILE="${3:-/home/idona/MoStar/_apps/grid/.env}"
PM2_PROC="${4:-mostar-grid}"
PROBE="$(dirname "$0")/dcx_readiness.py"

# Bearer token for auth-gated Ollama endpoints (e.g. behind Cloudflare Tunnel + auth).
# Pass as 5th arg or set OLLAMA_BEARER_TOKEN in env.
# Without this, a gated remote reads DOWN — not proof the gate held.
BEARER_TOKEN="${5:-${OLLAMA_BEARER_TOKEN:-}}"

host="$(echo "$OLLAMA_URL" | sed -E 's#https?://([^:/]+).*#\1#')"
is_local=0; [[ "$host" == "127.0.0.1" || "$host" == "localhost" ]] && is_local=1

say(){ printf '%s\n' "-- $*"; }

# 1. reachable?
say "probing $OLLAMA_URL/api/tags"
_CURL_AUTH=()
[[ -n "$BEARER_TOKEN" ]] && _CURL_AUTH=(-H "Authorization: Bearer $BEARER_TOKEN")
if ! tags="$(curl -fsS --max-time 10 "${_CURL_AUTH[@]}" "$OLLAMA_URL/api/tags" 2>/dev/null)"; then
  echo "DOWN: Ollama unreachable at $OLLAMA_URL"
  if [[ $is_local -eq 1 ]]; then
    echo "  -> local: is 'ollama serve' running?  systemctl status ollama"
  else
    echo "  -> remote: is Ollama bound to 0.0.0.0 (not 127.0.0.1) and reachable"
    echo "     over your tunnel/proxy?  Launch: OLLAMA_HOST=0.0.0.0:11434 ollama serve"
    echo "     Do NOT expose 11434 publicly without TLS + auth."
  fi
  exit 1
fi

# 2. model present?
if echo "$tags" | grep -q "\"${MODEL%%:*}"; then
  say "model present: $MODEL"
else
  if [[ $is_local -eq 1 ]]; then
    say "NAKED: model '$MODEL' not pulled. pulling..."
    [[ $CHECK_ONLY -eq 1 ]] && { echo "(--check-only) skipping pull"; exit 1; }
    ollama pull "$MODEL"
  else
    echo "NAKED: model '$MODEL' not on the remote Ollama. pull it ON that box:"
    echo "  ollama pull $MODEL"
    exit 1
  fi
fi

# 3. acceptance gate FIRST in check-only mode
if [[ $CHECK_ONLY -eq 1 ]]; then
  say "running readiness probe (acceptance gate)"
  python3 "$PROBE" "$OLLAMA_URL" "$MODEL" 20 "$BEARER_TOKEN"
  exit $?
fi

# 4. patch the grid env (idempotent)
say "patching $ENV_FILE"
[[ -f "$ENV_FILE" ]] || { echo "env file not found: $ENV_FILE"; exit 1; }
cp "$ENV_FILE" "$ENV_FILE.bak.$(date +%s)"
grep -q '^OLLAMA_BASE_URL='        "$ENV_FILE" \
  && sed -i "s#^OLLAMA_BASE_URL=.*#OLLAMA_BASE_URL=$OLLAMA_URL#"        "$ENV_FILE" \
  || echo "OLLAMA_BASE_URL=$OLLAMA_URL"        >> "$ENV_FILE"
grep -q '^OLLAMA_REQUEST_TIMEOUT=' "$ENV_FILE" \
  && sed -i "s#^OLLAMA_REQUEST_TIMEOUT=.*#OLLAMA_REQUEST_TIMEOUT=20#"   "$ENV_FILE" \
  || echo "OLLAMA_REQUEST_TIMEOUT=20"          >> "$ENV_FILE"

# 5. restart + acceptance gate
say "restarting $PM2_PROC"
pm2 restart "$PM2_PROC" --update-env >/dev/null
sleep 3

say "acceptance gate: DCX must actually think"
if python3 "$PROBE" "$OLLAMA_URL" "$MODEL" 20 "$BEARER_TOKEN"; then
  echo "WIRED: cognition leg live. grid readiness may now flip true."
else
  echo "NOT WIRED: env patched + restarted, but DCX did not think. grid stays honest-degraded."
  echo "  the wire is in place; the thinking is not. nothing pretended otherwise."
  exit 1
fi
