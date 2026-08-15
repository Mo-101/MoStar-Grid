#!/usr/bin/env bash
# Rotates the local governance Postgres password (VPS-native, port 5433,
# db idim_ikang, user idona) and rewrites the VPS-only secrets file that
# grid-api/mcp-gateway load via docker-compose.yml's `.env.pg.local`
# env_file entry. Run this ON THE VPS (it needs `sudo -u postgres psql`).
# After running, recreate the containers so they pick up the new password:
#   docker compose up -d grid-api mcp-gateway
set -euo pipefail
PGPASS=$(openssl rand -hex 24)
if [ -z "$PGPASS" ]; then echo "GENERATION_FAILED"; exit 1; fi

SQLFILE=$(mktemp)
trap 'rm -f "$SQLFILE"' EXIT
printf "ALTER USER idona WITH PASSWORD '%s';\n" "$PGPASS" > "$SQLFILE"
sudo -u postgres psql -p 5433 < "$SQLFILE" >/dev/null

printf 'DATABASE_URL=postgresql://idona:%s@127.0.0.1:5433/idim_ikang\n' "$PGPASS" > /opt/mostar/grid/.env.pg.local
chmod 600 /opt/mostar/grid/.env.pg.local
echo WROTE_OK
