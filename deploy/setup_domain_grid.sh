#!/usr/bin/env bash
set -euo pipefail

# ======================================================================
# MOSTAR GRID — public domain prep (grid.mostarsystems.com)
# ======================================================================
# Installs nginx on the VPS and deploys the reverse-proxy config that
# will front the loopback-only PM2 services (see deploy_grid_vps.sh)
# once grid.mostarsystems.com / api.mostarsystems.com / voice.mostarsystems.com
# resolve to this host.
#
# This script deliberately does NOT:
#   - touch DNS — the A records live in Truehost DNS, not Hostinger, and are
#     created out of band once you're ready to cut over, then re-run with RUN_CERTBOT=1
#   - request TLS certs — certbot's HTTP-01 challenge needs DNS live first
#
# Run order for go-live:
#   1. ./deploy/setup_domain_grid.sh                 (this script, safe anytime)
#   2. create the A records in Truehost DNS           (out of band)
#   3. wait for DNS propagation (dig grid.mostarsystems.com)
#   4. RUN_CERTBOT=1 ./deploy/setup_domain_grid.sh    (issues TLS, enables :443)
# ======================================================================

VPS_HOST="31.97.180.251"
VPS_USER="root"
SSH_KEY="${HOME}/.ssh/id_ed25519"
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i ${SSH_KEY}"
SSH_CMD="ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_CONF="${SCRIPT_DIR}/nginx/grid.mostarsystems.com.conf"
RUN_CERTBOT="${RUN_CERTBOT:-0}"

echo "======================================================"
echo "MOSTAR GRID — domain prep for grid.mostarsystems.com"
echo "======================================================"

echo "[1/4] Verifying SSH access..."
${SSH_CMD} 'echo OK' >/dev/null
echo "  SSH OK"

echo "[2/4] Installing nginx + certbot on VPS..."
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
if ! command -v nginx &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq nginx certbot python3-certbot-nginx
fi
mkdir -p /var/www/certbot
echo "  nginx + certbot ready"
REMOTE

echo "[3/4] Deploying reverse-proxy config..."
scp ${SSH_OPTS} "${NGINX_CONF}" "${VPS_USER}@${VPS_HOST}:/etc/nginx/sites-available/grid.mostarsystems.com.conf"
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
ln -sf /etc/nginx/sites-available/grid.mostarsystems.com.conf /etc/nginx/sites-enabled/grid.mostarsystems.com.conf
nginx -t
systemctl reload nginx || systemctl start nginx
echo "  nginx config live (HTTP only — no TLS yet)"
REMOTE

echo "[4/4] Opening firewall for HTTP/HTTPS..."
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
ufw allow 80/tcp
ufw allow 443/tcp
ufw status verbose
REMOTE

echo ""
echo "======================================================"
echo "DOMAIN PREP COMPLETE — DNS NOT CHANGED"
echo "======================================================"
echo "nginx is listening on 80 for grid.mostarsystems.com,"
echo "api.mostarsystems.com, voice.mostarsystems.com but those"
echo "hostnames do not resolve to ${VPS_HOST} yet."
echo ""

if [ "${RUN_CERTBOT}" = "1" ]; then
    echo "RUN_CERTBOT=1 set — requesting certificates now."
    echo "This will fail unless DNS already resolves to ${VPS_HOST}."
    ${SSH_CMD} "certbot --nginx -d grid.mostarsystems.com -d api.mostarsystems.com -d voice.mostarsystems.com --non-interactive --agree-tos -m akiniobong10@gmail.com"
else
    echo "Next step (after creating the A records in Truehost DNS):"
    echo "  RUN_CERTBOT=1 ./deploy/setup_domain_grid.sh"
fi
