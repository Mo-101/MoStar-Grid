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
        NEO4J_URI: "bolt://localhost:7687",
        NEO4J_USER: "neo4j",
        NEO4J_DATABASE: "neo4j",
        OLLAMA_BASE_URL: "http://localhost:11434",
        GRID_PORT: "41010",
        NO_PROXY: "localhost,127.0.0.1",
        no_proxy: "localhost,127.0.0.1",
      },
      watch: false,
      max_restarts: 5,
      restart_delay: 3000,
    },
  ],
};
