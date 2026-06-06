// ============================================================
// MoStar Grid — Sovereign PM2 Ecosystem
// The Flame Architect · MoStar Industries
//
// BOOT ORDER (dependency-chain, not parallel):
//   [0] Infrastructure  → neo4j, postgres
//   [1] Grid Core       → grid-api, mcp-gateway, ollama-tunnel, voice
//   [2] Grid Frontend   → mostar-frontend
//   [3] Idim Ikang      → collectors → api → scanner → outcome-tracker → auto-executor
//   [4] CrypSide        → collectors → api → scanner → outcome-tracker → frontend
//   [5] Edge            → moedge-sentinel
//
// PORT REGISTRY (41000–41999 = MoStar sovereign range)
//   41010  mostar-grid-api
//   41012  mostar-frontend        (Vite dev)
//   41020  mostar-mcp-gateway
//   41071  mostar-voice
//
//   41050  idim-api
//   41051  (idim-scanner — no public port, internal loop)
//   41052  (idim-outcome-tracker — internal loop)
//   41053  (idim-auto-executor — internal loop)
//   41054  (idim-funding-collector — internal loop)
//   41055  (idim-oi-collector — internal loop)
//   41056  (idim-ls-ratio-collector — internal loop)
//
//   41060  crypside-api
//   41061  crypside-frontend      (Next.js dev)
//   41062  (crypside-scanner — internal loop)
//   41063  (crypside-outcome-tracker — internal loop)
//   41064  (crypside-funding-collector — internal loop)
//   41065  (crypside-oi-collector — internal loop)
//   41066  (crypside-ls-ratio-collector — internal loop)
//   41067  moedge-sentinel
//
// DB PORTS (system-level, outside Grid range)
//   47687  neo4j bolt (mindgraph)
//   47474  neo4j http
//   5433   idim postgres
//
// NEO4J RECEIVES FROM:
//   grid   → agent events, covenant logs, MoStarMoments
//   idim   → signals, candidates, shadow_signals, outcomes
//   crypside → executions, trade outcomes, funding/OI telemetry
//
// AUTOBOOT:
//   Run once after saving this file:
//     npx pm2 start ecosystem.config.js
//     npx pm2 save
//     npx pm2 startup   (follow the printed sudo command)
//   After that: system boot → PM2 resurrect → everything online.
// ============================================================

// ── Path constants ───────────────────────────────────────────
const GRID_ROOT = '/home/idona/MoStar/_apps/grid';
const GRID_PYTHONPATH = [
  GRID_ROOT,
  `${GRID_ROOT}/back/services`,
  `${GRID_ROOT}/core/engines`,
  `${GRID_ROOT}/core/sovereignty`,
  `${GRID_ROOT}/core/protocols`,
  `${GRID_ROOT}/core/ops`,
].join(':');

const IDIM_ROOT = '/home/idona/MoStar/_apps/financial/IdimIkang-main';
const IDIM_OBS = `${IDIM_ROOT}/observer_bundle`;
const IDIM_PYTHON = `${IDIM_OBS}/.venv/bin/python`;
const IDIM_ENV = `${IDIM_OBS}/.env`;

const CRYS_ROOT = '/home/idona/MoStar/_apps/financial/crypside/CrypSide';
const CRYS_OBS = `${CRYS_ROOT}/observer_bundle`;
const CRYS_PYTHON = `${CRYS_ROOT}/.venv/bin/python3.12`;
const CRYS_ENV = `${CRYS_ROOT}/.env`;
const CRYS_LOGS = `${CRYS_ROOT}/logs/pm2`;

// ── Neo4j shared telemetry env (injected into every app) ─────
const NEO4J_ENV = {
  NEO4J_BOLT_URL: 'bolt://127.0.0.1:47687',
  NEO4J_HTTP_URL: 'http://127.0.0.1:47474',
  // Password loaded from each app's own .env — not hardcoded here.
};

// ── Helper: Idim background worker ───────────────────────────
function idimWorker(name, script, extraEnv = {}) {
  return {
    name,
    script: IDIM_PYTHON,
    args: script,
    cwd: IDIM_OBS,
    interpreter: 'none',
    env_file: IDIM_ENV,
    env: {
      PYTHONUNBUFFERED: '1',
      ...NEO4J_ENV,
      ...extraEnv,
    },
    watch: false,
    autorestart: true,
    max_restarts: 20,
    restart_delay: 5000,
    time: true,
    out_file: `/tmp/pm2-${name}-out.log`,
    error_file: `/tmp/pm2-${name}-err.log`,
  };
}

// ── Helper: CrypSide background worker ───────────────────────
function crysWorker(name, script, extraEnv = {}) {
  return {
    name,
    script: CRYS_PYTHON,
    args: script,
    cwd: CRYS_OBS,
    interpreter: 'none',
    env_file: CRYS_ENV,
    env: {
      PYTHONUNBUFFERED: '1',
      IDIM_API_URL: 'http://127.0.0.1:41050',
      IDIM_DATABASE_URL: 'postgresql://idona:${IDIM_DB_PASSWORD}@127.0.0.1:5433/${IDIM_DB_NAME}',
      ...NEO4J_ENV,
      ...extraEnv,
    },
    watch: false,
    autorestart: true,
    max_restarts: 20,
    restart_delay: 5000,
    time: true,
    out_file: `${CRYS_LOGS}/${name}-out.log`,
    error_file: `${CRYS_LOGS}/${name}-err.log`,
  };
}

// ============================================================
module.exports = {
  apps: [

    // ══════════════════════════════════════════════════════
    // TIER 0 — INFRASTRUCTURE
    // ══════════════════════════════════════════════════════

    {
      // Neo4j MindGraph — sovereign cognitive substrate
      // Bolt: 47687  HTTP: 47474
      name: 'mostar-neo4j',
      script: '/usr/share/neo4j/bin/neo4j',
      args: 'console',
      interpreter: 'none',
      cwd: GRID_ROOT,
      env: {
        NEO4J_HOME: `${GRID_ROOT}/back/services/mindgraph/neo4j-mindgraph`,
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

    // ══════════════════════════════════════════════════════
    // TIER 1 — GRID CORE
    // ══════════════════════════════════════════════════════

    {
      name: 'mostar-grid',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: '-m uvicorn back.services.grid.api:app --host 0.0.0.0 --port 41010',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        GRID_PORT: '41010',
        NO_PROXY: 'localhost,127.0.0.1',
        no_proxy: 'localhost,127.0.0.1',
        ...NEO4J_ENV,
      },
      watch: false,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 3000,
    },

    {
      name: 'mostar-mcp-gateway',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: '-m uvicorn mcp_gateway.api:app --host 0.0.0.0 --port 41020',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        ...NEO4J_ENV,
      },
      watch: false,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 3000,
    },

    {
      name: 'mostar-ollama-tunnel',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: 'core/ops/scripts/wsl_tunnel.py',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
      },
      watch: false,
      autorestart: true,
      max_restarts: 5,
      restart_delay: 3000,
    },

    {
      name: 'mostar-voice',
      script: `${GRID_ROOT}/.venv/bin/python`,
      args: '-m uvicorn voice_api:app --host 0.0.0.0 --port 41071',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        ...NEO4J_ENV,
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: '/tmp/voice_pm2_out.log',
      error_file: '/tmp/voice_pm2_err.log',
    },

    // ══════════════════════════════════════════════════════
    // TIER 2 — GRID FRONTEND
    // ══════════════════════════════════════════════════════

    {
      name: 'mostar-frontend',
      script: '/bin/bash',
      args: ['-lc', 'export NVM_DIR=/home/idona/.nvm; . /home/idona/.nvm/nvm.sh; nvm use 20; npm run dev'],
      interpreter: 'none',
      cwd: `${GRID_ROOT}/front/app`,
      env: {
        NODE_ENV: 'development',
        VITE_PORT: '41012',
        VITE_GRID_API_URL: 'http://127.0.0.1:41010',
        VITE_NEO4J_BOLT_URL: 'bolt://127.0.0.1:47687',
      },
      watch: false,
      autorestart: true,
      max_restarts: 3,
      restart_delay: 5000,
      out_file: '/tmp/frontend_pm2_out.log',
      error_file: '/tmp/frontend_pm2_err.log',
    },

    // ══════════════════════════════════════════════════════
    // TIER 3 — IDIM IKANG (Signal Intelligence / Evidence River)
    // Boot order: collectors → api → scanner → tracker → executor
    // All workers receive NEO4J_ENV for telemetry writes.
    // ══════════════════════════════════════════════════════

    idimWorker('idim-funding-collector', 'funding_collector.py'),
    idimWorker('idim-oi-collector', 'oi_collector.py'),
    idimWorker('idim-ls-ratio-collector', 'ls_ratio_collector.py'),

    {
      // idim-api — sovereign port 41050
      name: 'idim-api',
      script: IDIM_PYTHON,
      args: '-m uvicorn api:app --host 0.0.0.0 --port 41050',
      cwd: IDIM_OBS,
      interpreter: 'none',
      env_file: IDIM_ENV,
      env: {
        PYTHONUNBUFFERED: '1',
        IDIM_API_PORT: '41050',
        ...NEO4J_ENV,
      },
      watch: false,
      autorestart: true,
      max_restarts: 20,
      restart_delay: 5000,
      time: true,
      out_file: '/tmp/pm2-idim-api-out.log',
      error_file: '/tmp/pm2-idim-api-err.log',
    },

    idimWorker('idim-scanner', 'scanner.py'),
    idimWorker('idim-outcome-tracker', 'outcome_tracker.py --loop'),
    idimWorker('idim-auto-executor', 'auto_executor.py'),

    // ══════════════════════════════════════════════════════
    // TIER 4 — CRYPSIDE (Execution Layer / Trade Hand)
    // Consumes Idim via IDIM_API_URL=http://127.0.0.1:41050
    // Does NOT run its own scanner — intelligence comes from Idim.
    // ══════════════════════════════════════════════════════

    crysWorker('crypside-funding-collector', 'funding_collector.py'),
    crysWorker('crypside-oi-collector', 'oi_collector.py'),
    crysWorker('crypside-ls-ratio-collector', 'ls_ratio_collector.py'),

    {
      // crypside-api — sovereign port 41060
      name: 'crypside-api',
      script: CRYS_PYTHON,
      args: '-m uvicorn api:app --host 127.0.0.1 --port 41060',
      cwd: CRYS_ROOT,
      interpreter: 'none',
      env_file: CRYS_ENV,
      env: {
        PYTHONUNBUFFERED: '1',
        PORT: '41060',
        IDIM_API_URL: 'http://127.0.0.1:41050',
        ...NEO4J_ENV,
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: `${CRYS_LOGS}/crypside-api-out.log`,
      error_file: `${CRYS_LOGS}/crypside-api-err.log`,
    },

    crysWorker('crypside-scanner', 'scanner.py'),
    crysWorker('crypside-outcome-tracker', 'outcome_tracker.py --loop'),

    {
      // crypside-frontend — sovereign port 41061
      name: 'crypside-frontend',
      script: 'npm',
      args: 'run dev -- --hostname 127.0.0.1 --port 41061',
      cwd: CRYS_ROOT,
      interpreter: 'none',
      env_file: CRYS_ENV,
      env: {
        NODE_ENV: 'development',
        PORT: '41061',
        NEXT_PUBLIC_API_BASE_URL: 'http://127.0.0.1:41060',
        NEXT_PUBLIC_API_WS_URL: 'ws://127.0.0.1:41060/ws',
        NEXT_PUBLIC_IDIM_API_URL: 'http://127.0.0.1:41050',
      },
      watch: false,
      autorestart: true,
      max_restarts: 20,
      restart_delay: 5000,
      time: true,
      out_file: `${CRYS_LOGS}/crypside-frontend-out.log`,
      error_file: `${CRYS_LOGS}/crypside-frontend-err.log`,
    },

    // ══════════════════════════════════════════════════════
    // TIER 5 — EDGE INTELLIGENCE
    // ══════════════════════════════════════════════════════

    {
      // moedge-sentinel — sovereign port 41067
      name: 'moedge-sentinel',
      script: CRYS_PYTHON,
      args: 'moedge_sentinel.py',
      cwd: CRYS_OBS,
      interpreter: 'none',
      env_file: CRYS_ENV,
      env: {
        PYTHONUNBUFFERED: '1',
        MOEDGE_SENTINEL_PORT: '41067',
        MOEDGE_SENTINEL_INTERVAL: '1800',
        ...NEO4J_ENV,
      },
      watch: false,
      autorestart: true,
      max_restarts: 20,
      restart_delay: 5000,
      time: true,
      out_file: `${CRYS_LOGS}/moedge-sentinel-out.log`,
      error_file: `${CRYS_LOGS}/moedge-sentinel-err.log`,
    },

  ],
};