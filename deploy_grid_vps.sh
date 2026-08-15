#!/usr/bin/env bash
set -euo pipefail

# ======================================================================
# MOSTAR GRID VPS DEPLOYMENT — loopback-only
# Neo4j + mostar-grid + mcp-gateway + voice + frontend + runtime-cockpit
# ======================================================================
# Target: Ubuntu 24.04 VPS at 31.97.180.251
# Run from: WSL (this script SSHes into the VPS)
# All services bind 127.0.0.1 only. No public exposure. Access via SSH tunnel.
# ======================================================================

VPS_HOST="31.97.180.251"
VPS_USER="root"
SSH_KEY="${HOME}/.ssh/id_ed25519"
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i ${SSH_KEY}"
SSH_CMD="ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST}"

GRID_SRC="/home/idona/MoStar/_apps/grid"
RUNTIME_SRC="/home/idona/MoStar/_services/runtime"
NEO4J_DATA_SRC="${GRID_SRC}/back/services/mindgraph/mo-neo4j/data"
NEO4J_CONF_SRC="${GRID_SRC}/back/services/mindgraph/mo-neo4j/conf"

VPS_BASE="/opt/mostar"
VPS_GRID="${VPS_BASE}/grid"
VPS_RUNTIME="${VPS_BASE}/runtime"
VPS_NEO4J_DATA="${VPS_GRID}/back/services/mindgraph/mo-neo4j/data"
VPS_NEO4J_CONF="${VPS_GRID}/back/services/mindgraph/mo-neo4j/conf"

echo "======================================================"
echo "MOSTAR GRID VPS DEPLOYMENT — loopback-only"
echo "======================================================"
echo "Target: ${VPS_USER}@${VPS_HOST}"
echo ""

# ── Step 0: Verify SSH ───────────────────────────────────────
echo "[0/9] Verifying SSH access..."
${SSH_CMD} 'echo OK' >/dev/null
echo "  SSH OK"

# ── Step 1: System packages ─────────────────────────────────
echo "[1/9] Installing system packages on VPS..."
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl wget gnupg lsb-release rsync \
    python3 python3-venv python3-pip \
    postgresql postgresql-contrib \
    openjdk-17-jre-headless ufw 2>/dev/null || true

if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi
if ! command -v pm2 &>/dev/null; then
    npm install -g pm2
fi
echo "  System packages installed"
REMOTE

# ── Step 2: Copy grid codebase ───────────────────────────────
echo "[2/9] Copying grid codebase to VPS..."
${SSH_CMD} "mkdir -p ${VPS_GRID} ${VPS_RUNTIME}"

RSYNC_EXCLUDES="--exclude=.venv --exclude=node_modules --exclude=__pycache__ --exclude=.git --exclude=*.pyc --exclude=.pytest_cache --exclude=back/services/mindgraph/mo-neo4j/data"

rsync -az --delete ${RSYNC_EXCLUDES} \
    -e "ssh ${SSH_OPTS}" \
    "${GRID_SRC}/" "${VPS_USER}@${VPS_HOST}:${VPS_GRID}/"
echo "  Grid codebase copied"

# Runtime cockpit (static console + server.py) — no secrets needed, stdlib only
for d in cockpit-app mostar-runtime mostar-cockpit; do
    rsync -az --delete --exclude=__pycache__ --exclude=.git \
        -e "ssh ${SSH_OPTS}" \
        "${RUNTIME_SRC}/${d}/" "${VPS_USER}@${VPS_HOST}:${VPS_RUNTIME}/${d}/"
done
rsync -az -e "ssh ${SSH_OPTS}" "${RUNTIME_SRC}/index.html" "${VPS_USER}@${VPS_HOST}:${VPS_RUNTIME}/index.html" 2>/dev/null || true
echo "  Runtime cockpit assets copied"

# ── Step 3: Python venv + deps ───────────────────────────────
echo "[3/9] Setting up Python environment..."
${SSH_CMD} "bash -s" <<REMOTE
set -euo pipefail
cd ${VPS_GRID}
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
echo "  Grid venv ready"
REMOTE

# ── Step 4: Frontend deps + production build ─────────────────
echo "[4/9] Installing frontend dependencies and building for production..."
${SSH_CMD} "bash -s" <<REMOTE
set -euo pipefail
cd ${VPS_GRID}/front/app
npm install --include=dev --silent
VITE_GRID_API_BASE=https://api.mostarsystems.com \
VITE_MOSTAR_VOICE_URL=https://voice.mostarsystems.com \
npm run build
echo "  Frontend deps installed and production bundle built"
REMOTE

# ── Step 4b: Postgres — sovereign governance schema ──────────
echo "[4b/9] Configuring Postgres (control-plane schema, port 5433)..."
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
systemctl enable postgresql
systemctl start postgresql

PG_CONF=$(find /etc/postgresql -name "postgresql.conf" | head -1)
sed -i "s/^port = .*/port = 5433/" "$PG_CONF"
grep -q "^port = 5433" "$PG_CONF" || echo "port = 5433" >> "$PG_CONF"
systemctl restart postgresql
sleep 2

sudo -u postgres psql -p 5433 -c "CREATE USER idona SUPERUSER;" 2>/dev/null || true
sudo -u postgres psql -p 5433 -c "CREATE DATABASE idim_ikang OWNER idona;" 2>/dev/null || true
echo "  Postgres ready on port 5433 (local socket only)"
REMOTE

rsync -az -e "ssh ${SSH_OPTS}" \
    "${GRID_SRC}/core/ops/migrations/001_sovereign_governance.sql" \
    "${VPS_USER}@${VPS_HOST}:/tmp/001_sovereign_governance.sql"

${SSH_CMD} "sudo -u postgres psql -p 5433 -d idim_ikang -f /tmp/001_sovereign_governance.sql"
echo "  Sovereign governance schema applied"

# ── Step 5: Install Neo4j ────────────────────────────────────
echo "[5/9] Installing Neo4j on VPS..."
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
if ! command -v neo4j &>/dev/null; then
    wget -qO - https://debian.neo4j.com/neotechnology.gpg.key | gpg --dearmor -o /usr/share/keyrings/neo4j.gpg
    echo 'deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list
    apt-get update -qq
    apt-get install -y -qq neo4j
fi
systemctl stop neo4j 2>/dev/null || true
systemctl disable neo4j 2>/dev/null || true
echo "  Neo4j binary installed (systemd unit disabled — managed by PM2 instead)"
REMOTE

# ── Step 6: Migrate Neo4j graph data (stop local source briefly) ─
echo "[6/9] Migrating Neo4j graph data (stopping local mostar-neo4j)..."
wsl.exe -d Ubuntu-24.04 -- pm2 stop mostar-neo4j >/dev/null 2>&1 || true
sleep 2

rsync -az --progress \
    -e "ssh ${SSH_OPTS}" \
    "${NEO4J_DATA_SRC}/" "${VPS_USER}@${VPS_HOST}:${VPS_NEO4J_DATA}/"

rsync -az --progress \
    -e "ssh ${SSH_OPTS}" \
    "${NEO4J_CONF_SRC}/" "${VPS_USER}@${VPS_HOST}:${VPS_NEO4J_CONF}/"

wsl.exe -d Ubuntu-24.04 -- pm2 start mostar-neo4j >/dev/null 2>&1 || true
echo "  Neo4j data + conf migrated. Local mostar-neo4j restarted."

${SSH_CMD} "chown -R neo4j:neo4j ${VPS_NEO4J_DATA} 2>/dev/null || chown -R \$(id -u):\$(id -g) ${VPS_NEO4J_DATA}"

# ── Step 7: Write VPS PM2 ecosystem file ─────────────────────
echo "[7/9] Writing VPS ecosystem config..."
${SSH_CMD} "bash -s" <<'REMOTE'
cat > /opt/mostar/grid/ecosystem.vps.config.js <<'ECOSYSTEM'
const GRID_ROOT = '/opt/mostar/grid';
const RUNTIME_ROOT = '/opt/mostar/runtime';
const GRID_PYTHONPATH = [
  GRID_ROOT,
  `${GRID_ROOT}/back/services`,
  `${GRID_ROOT}/core/engines`,
  `${GRID_ROOT}/core/sovereignty`,
  `${GRID_ROOT}/core/protocols`,
  `${GRID_ROOT}/core/ops`,
].join(':');

module.exports = {
  apps: [
    {
      name: 'mostar-neo4j',
      script: '/usr/share/neo4j/bin/neo4j',
      args: 'console',
      interpreter: 'none',
      cwd: GRID_ROOT,
      env: {
        NEO4J_HOME: '/usr/share/neo4j',
        NEO4J_CONF: `${GRID_ROOT}/back/services/mindgraph/mo-neo4j/conf`,
      },
      watch: false,
      autorestart: true,
      min_uptime: '60000',
      max_restarts: 3,
      exp_backoff_restart_delay: 5000,
      kill_timeout: 30000,
      out_file: '/tmp/neo4j_pm2_out.log',
      error_file: '/tmp/neo4j_pm2_err.log',
    },
    {
      name: 'mostar-grid',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: '-m uvicorn back.services.grid.api:app --host 127.0.0.1 --port 41010',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        GRID_PORT: '41010',
        DATABASE_URL: "postgresql:///idim_ikang?host=/var/run/postgresql&port=5433&user=idona",
        // Public domain allowlisted for browser CORS once grid.mostarsystems.com is live.
        // Adding it here is a no-op until DNS + nginx (see deploy/setup_domain_grid.sh) point at this host.
        CORS_EXTRA_ORIGINS: 'https://grid.mostarsystems.com',
      },
      watch: false,
      autorestart: true,
      min_uptime: '30s',
      max_restarts: 5,
      restart_delay: 5000,
      exp_backoff_restart_delay: 2000,
      kill_timeout: 10000,
      listen_timeout: 15000,
    },
    {
      name: 'mostar-mcp-gateway',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: '-m uvicorn mcp_gateway.server:app --host 127.0.0.1 --port 41020',
      cwd: `${GRID_ROOT}/back/services`,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        MCP_TRANSPORT: 'sse',
        MCP_HOST: '127.0.0.1',
        MCP_PORT: '41020',
      },
      watch: false,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 3000,
    },
    {
      name: 'mostar-voice',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: '-m uvicorn back.services.voice.voice_api:app --host 127.0.0.1 --port 41071',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: '/tmp/voice_pm2_out.log',
      error_file: '/tmp/voice_pm2_err.log',
    },
    {
      name: 'mostar-frontend',
      script: 'node',
      args: 'serve.mjs',
      interpreter: 'none',
      cwd: `${GRID_ROOT}/front/app`,
      env: {
        NODE_ENV: 'production',
        PORT: '41012',
      },
      watch: false,
      autorestart: true,
      max_restarts: 3,
      restart_delay: 5000,
      out_file: '/tmp/frontend_pm2_out.log',
      error_file: '/tmp/frontend_pm2_err.log',
    },
    {
      name: 'mostar-runtime-cockpit',
      script: 'python3',
      args: `${RUNTIME_ROOT}/cockpit-app/server.py`,
      cwd: `${RUNTIME_ROOT}/cockpit-app`,
      interpreter: 'none',
      env: {
        BIND: '127.0.0.1',
        PORT: '8001',
      },
      watch: false,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 3000,
    },
  ],
};
ECOSYSTEM
echo "  ecosystem.vps.config.js written"
REMOTE

# ── Step 8: Start PM2 ─────────────────────────────────────────
echo "[8/9] Starting PM2 processes on VPS..."
${SSH_CMD} "bash -s" <<REMOTE
set -euo pipefail
cd ${VPS_GRID}
pm2 delete all 2>/dev/null || true
pm2 start ecosystem.vps.config.js
pm2 save
pm2 startup systemd -u root --hp /root 2>/dev/null || true
echo "  PM2 started"
REMOTE

# ── Step 9: Firewall lockdown (loopback-only) ────────────────
echo "[9/9] Locking down firewall (SSH only, all grid services loopback)..."
${SSH_CMD} 'bash -s' <<'REMOTE'
set -euo pipefail
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
echo "y" | ufw enable
ufw status verbose
REMOTE

# ── Done ───────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo "DEPLOYMENT COMPLETE"
echo "======================================================"
${SSH_CMD} "pm2 list"
echo ""
echo "Health checks (loopback, from VPS):"
${SSH_CMD} "sleep 8; curl -s http://127.0.0.1:47474 -o /dev/null -w 'neo4j: %{http_code}\n'; curl -s http://127.0.0.1:41010/ -o /dev/null -w 'grid: %{http_code}\n'; curl -s http://127.0.0.1:41071/health -o /dev/null -w 'voice: %{http_code}\n'; curl -s http://127.0.0.1:8001/ -o /dev/null -w 'cockpit: %{http_code}\n'"
echo ""
echo "Access via SSH tunnel, e.g.:"
echo "  ssh -L 41010:127.0.0.1:41010 -L 41012:127.0.0.1:41012 -L 47474:127.0.0.1:47474 root@${VPS_HOST}"
