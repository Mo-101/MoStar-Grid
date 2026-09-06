// ============================================================
// MoStar Grid — Sovereign PM2 Ecosystem
// The Flame Architect · MoStar Intelligent Systems
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
//    4317  mostar-vokal          (MoVoKaL bundle default, outside range)
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
// The Neo4j each app talks to is resolved from that app's OWN env_file.
// This file sets no NEO4J_* values — see the policy note below the path
// constants for why the shared Aura block was removed.
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

// ── Neo4j configuration policy: ONE SOURCE PER APP ───────────
// There is deliberately no shared NEO4J_* block here any more.
//
// What was here: a hardcoded Aura Free Tier block
// (neo4j+s://2f88895b.databases.neo4j.io, user and database '2f88895b')
// spread into every app's `env`. PM2 merges `env` ON TOP of `env_file`, so
// that block silently overrode each app's own .env values.
//
// Measured on this box 2026-09-05: 2f88895b.databases.neo4j.io does not
// resolve — the Aura instance is gone. Every worker that inherited the block
// was addressing a dead hostname, and CrypSide's own .env (bolt://127.0.0.1:47687,
// correct) was being overridden by it. grid-api only stayed up because its
// start command unset the whole block again immediately after loading it.
//
// The live graph is the PM2-managed local Neo4j below (bolt 47687, http
// 47474). It holds the Genesis constitution chain bootstrapped 2026-08-31.
// Each app now resolves Neo4j from its own env_file, and nothing here
// overrides that.

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
      IDIM_DATABASE_URL: `postgresql://idona:${process.env.IDIM_DB_PASSWORD || ''}@127.0.0.1:5433/${process.env.IDIM_DB_NAME || 'idimikang'}`,
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

    // ══════════════════════════════════════════════════════
    // TIER 1 — GRID CORE
    // ══════════════════════════════════════════════════════

    {
      name: 'mostar-grid',
      script: '/bin/bash',
      // Loopback-only: reachability, not just authorization (First Wound
      // doctrine, mostar-doorman/README.md). Only the cockpit-app aggregator
      // and other local processes on this box need this port; the doorman
      // tunnel never proxies directly to it.
      // runtime/.env supplies the cross-service values (attestor, session
      // token, conduit ingest). Neo4j comes from grid/.env via
      // back/services/grid/config.py — the dead Aura block that used to be
      // loaded here and then unset again line-by-line is gone from both ends.
      args: [
        '-lc',
        `exec ${GRID_ROOT}/.venv/bin/dotenv -f /home/idona/MoStar/_services/runtime/.env run -- ${GRID_ROOT}/.venv/bin/python -m uvicorn back.services.grid.api:app --host 127.0.0.1 --port 41010`,
      ],
      cwd: GRID_ROOT,
      env_file: '/home/idona/MoStar/_services/runtime/.env',
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        GRID_PORT: '41010',
        NO_PROXY: 'localhost,127.0.0.1',
        no_proxy: 'localhost,127.0.0.1',
        // Windows-hosted Ollama, reached over WSL2 mirrored networking.
        // A previous comment here claimed 127.0.0.1 could not cross that
        // boundary and routed through ollama.mostarsystems.com instead.
        // Measured on this box: localhost:11434 answers /api/tags in ~20ms
        // with the full trinity pulled, and BOTH tunnel hostnames
        // (mostarsystems / mostarindustries) are NXDOMAIN with no
        // cloudflared running. The remote hop was the outage, not the cure.
        OLLAMA_BASE_URL: 'http://localhost:11434',
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
      // Pre-existing bug fixed: this was 'voice_api:app' (bare, no package
      // path), which only worked historically because PM2 was restarting
      // from its own cached args rather than re-reading this file. The
      // actual module lives at back/services/voice/voice_api.py.
      args: `-m dotenv -f /home/idona/MoStar/_services/runtime/.env run -- ${GRID_ROOT}/.venv/bin/python -m uvicorn back.services.voice.voice_api:app --host 127.0.0.1 --port 41071`,
      interpreter: 'none',
      cwd: GRID_ROOT,
      env: {
        PYTHONPATH: GRID_PYTHONPATH,
        GRID_API_URL: 'http://127.0.0.1:41010',
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
      args: ['-lc', 'export NVM_DIR=/home/idona/.nvm; . /home/idona/.nvm/nvm.sh; nvm use 20; npm run dev -- --host 0.0.0.0 --port 41012'],
      interpreter: 'none',
      cwd: `${GRID_ROOT}/front/app`,
      env: {
        NODE_ENV: 'development',
        VITE_PORT: '41012',
        // The app reads VITE_GRID_API_BASE (front/app/src/config/gridServices.ts).
        // This was VITE_GRID_API_URL, which nothing reads — the dev server only
        // worked because front/app/.env supplies the correct name. Dropped
        // alongside it: VITE_NEO4J_BOLT_URL, read by no source file, and a bolt
        // endpoint the browser has no driver for in any case.
        VITE_GRID_API_BASE: 'http://127.0.0.1:41010',
        VITE_MOSTAR_VOICE_URL: 'http://127.0.0.1:41071',
      },
      watch: false,
      autorestart: true,
      max_restarts: 3,
      restart_delay: 5000,
      out_file: '/tmp/frontend_pm2_out.log',
      error_file: '/tmp/frontend_pm2_err.log',
    },

    {
      // mostar-vokal — the MoVoKaL voice box, served from the Grid package on
      // 4317. Started through `npm start` rather than `script: server.mjs`:
      // server.mjs only listens when process.argv[1] equals its own path, and
      // under PM2's fork wrapper that guard never fires — the process sits
      // online, holding memory, without ever binding the port.
      //
      // This replaces an unmanaged copy that was running from
      // _apps/financial/crypside/MoStar-Vokal, whose lib/grid.mjs still cut
      // replies at 4000 characters mid-word.
      name: 'mostar-vokal',
      script: '/bin/bash',
      args: ['-lc', 'npm start'],
      interpreter: 'none',
      cwd: `${GRID_ROOT}/core/MoVoKaL-Grid-Package`,
      env: {
        PORT: '4317',
        HOST: '127.0.0.1',
        GRID_API_URL: 'http://127.0.0.1:41010',
        VOICE_API_URL: 'http://127.0.0.1:41071',
        VOICE_DEFAULT: 'mostar-clear-v1',
        VOICE_MOOD: 'conversational',
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      out_file: '/tmp/vokal_pm2_out.log',
      error_file: '/tmp/vokal_pm2_err.log',
    },

    // ══════════════════════════════════════════════════════
    // TIER 3 — IDIM IKANG (Signal Intelligence / Evidence River)
    // Boot order: collectors → api → scanner → tracker → executor
    // Telemetry targets come from IDIM_ENV. Note: that file still points at
    // the retired Aura instance (NEO4J_BOLT_URL=neo4j+s://2f88895b…), which no
    // longer resolves — repoint it at bolt://127.0.0.1:47687 in Idim's own
    // .env. PM2 no longer masks this by overriding it from here.
    // ══════════════════════════════════════════════════════

    idimWorker('idim-funding-collector', 'funding_collector.py'),
    idimWorker('idim-oi-collector', 'oi_collector.py'),
    idimWorker('idim-ls-ratio-collector', 'ls_ratio_collector.py'),

    {
      // idim-api — sovereign port 41050
      name: 'idim-api',
      script: IDIM_PYTHON,
      args: '-m uvicorn api:app --host 127.0.0.1 --port 41050',
      cwd: IDIM_OBS,
      interpreter: 'none',
      env_file: IDIM_ENV,
      env: {
        PYTHONUNBUFFERED: '1',
        IDIM_API_PORT: '41050',
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
