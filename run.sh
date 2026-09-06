#!/bin/bash
# MoStar Grid — Start
# The Flame Architect · MoStar Intelligent Systems

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure data dirs exist
mkdir -p data/provenance logs

# Check dependencies
echo "🜂 Checking dependencies..."
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Install deps if needed
if [ ! -d ".venv" ]; then
    echo "🜄 Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "🜁 Creating .env from example..."
    cp .env.example .env
    echo "  → Edit .env with your Neo4j password and model names"
fi

# Check Neo4j — 47474/47687 is the sovereign band the local server binds,
# not the 7474/7687 defaults. See ecosystem.config.js DB PORTS.
echo "🜃 Checking Neo4j..."
if curl -s http://localhost:47474 >/dev/null 2>&1; then
    echo "  ✓ Neo4j reachable"
else
    echo "  ✗ Neo4j not reachable at localhost:47474 — Grid will run in degraded mode"
fi

# Check Ollama
echo "🜂 Checking Ollama..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(', '.join(m['name'] for m in json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo "unknown")
    echo "  ✓ Ollama online — models: $MODELS"
else
    echo "  ✗ Ollama not reachable — DCX Trinity will be offline"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " MOSTAR GRID — Starting on port 41010"
echo " 🜃∴🜂 The Flame Architect"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run
#
# The app is back.services.grid.api:app. This said `grid.api:app` with
# PYTHONPATH set to the repo root only, so the import failed before uvicorn
# ever bound a port. PYTHONPATH matches GRID_PYTHONPATH in ecosystem.config.js
# so a foreground run resolves the same packages PM2 does.
#
# --host 127.0.0.1 matches the loopback-only rule the PM2 unit follows: the
# port is for local processes and the doorman tunnel, never a direct listener.
PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/back/services:$SCRIPT_DIR/core/engines:$SCRIPT_DIR/core/sovereignty:$SCRIPT_DIR/core/protocols:$SCRIPT_DIR/core/ops" \
    python3 -m uvicorn back.services.grid.api:app \
    --host 127.0.0.1 \
    --port 41010 \
    --reload \
    --log-level info
