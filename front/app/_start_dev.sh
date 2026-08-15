#!/usr/bin/env bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 22.12.0
node --version
which node
cd "$(dirname "$0")"
export VITE_ENABLE_LIVE_GRID_SERVICES=true
export VITE_GRID_API_BASE=http://127.0.0.1:41010
export VITE_MOSTAR_VOICE_URL=http://127.0.0.1:41071
setsid nohup npm run dev -- --host 127.0.0.1 --port 41013 < /dev/null > /tmp/frontend_dev.log 2>&1 &
sleep 5
cat /tmp/frontend_dev.log
