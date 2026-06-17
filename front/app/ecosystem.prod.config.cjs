module.exports = {
  apps: [
    {
      name: "mostar-frontend",
      script: "node_modules/srvx/bin/srvx.mjs",
      args: "--entry dist/server/server.js --port 41012 --prod --dir /home/idona/MoStar/_apps/grid/front/app",
      cwd: "/home/idona/MoStar/_apps/grid/front/app",
      interpreter: "/home/idona/.nvm/versions/node/v22.22.3/bin/node",
      env: {
        PORT: "41012",
        NODE_ENV: "production",
      },
      restart_delay: 3000,
      max_restarts: 5,
    },
  ],
};
