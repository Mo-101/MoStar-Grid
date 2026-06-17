#!/usr/bin/env bash
export NVM_DIR=/home/idona/.nvm
. /home/idona/.nvm/nvm.sh
nvm use 22
cd /home/idona/MoStar/_apps/grid/front/app
export PORT=41012
exec node dist/server/server.js
