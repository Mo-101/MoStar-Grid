// MoStar Grid — PM2 Ecosystem
// The Flame Architect · MoStar Industries

module.exports = {
  apps: [
    {
      name: "mostar-grid",
      script: ".venv/bin/python",
      args: "-m uvicorn grid.api:app --host 0.0.0.0 --port 41010",
      cwd: "/home/idona/MoStar/_apps/grid",
      env: {
        PYTHONPATH: "/home/idona/MoStar/_apps/grid",
        GRID_PORT: "41010",
        NO_PROXY: "localhost,127.0.0.1",
        no_proxy: "localhost,127.0.0.1",
      },
      watch: false,
      max_restarts: 5,
      restart_delay: 3000,
    },
    {
      name: "mostar-mcp-gateway",
      script: ".venv/bin/python",
      args: "-m uvicorn mcp_gateway.api:app --host 0.0.0.0 --port 41020",
      cwd: "/home/idona/MoStar/_apps/grid",
      env: {
        PYTHONPATH: "/home/idona/MoStar/_apps/grid",
      },
      watch: false,
      max_restarts: 5,
      restart_delay: 3000,
    },
    {
      name: "mostar-ollama-tunnel",
      script: ".venv/bin/python",
      args: "scripts/wsl_tunnel.py",
      cwd: "/home/idona/MoStar/_apps/grid",
      watch: false,
      max_restarts: 5,
      restart_delay: 3000,
    },
    {
      name: "mostar-voice",
      script: "/home/idona/MoStar/_apps/grid/.venv/bin/python",
      args: "-m uvicorn voice_api:app --host 0.0.0.0 --port 41071",
      cwd: "/home/idona/MoStar/voice",
      env: {
        PYTHONPATH: "/home/idona/MoStar/voice",
      },
      watch: false,
      max_restarts: 5,
      restart_delay: 3000,
    }
  ],
};
