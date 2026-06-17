#!/usr/bin/env bash
# Build and deploy the MoStar frontend
set -e
cd /home/idona/MoStar/_apps/grid/front/app

echo '→ Building...'
/home/idona/.nvm/versions/node/v22.22.3/bin/node node_modules/vite/bin/vite.js build

echo '→ Syncing assets to public/'
rm -rf public/assets
cp -r dist/client/assets public/assets

echo '→ Restarting PM2...'
pm2 restart ecosystem.prod.config.cjs --update-env

echo '✓ Done. Frontend live at http://localhost:41012'
