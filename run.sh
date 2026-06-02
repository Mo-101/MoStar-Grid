#!/bin/bash
# MoStar Grid — Start
# The Flame Architect · MoStar Industries

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

# Check Neo4j
echo "🜃 Checking Neo4j..."
if curl -s http://localhost:7474 >/dev/null 2>&1; then
    echo "  ✓ Neo4j reachable"
else
    echo "  ✗ Neo4j not reachable at localhost:7474 — Grid will run in degraded mode"
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
PYTHONPATH="$SCRIPT_DIR" python3 -m uvicorn grid.api:app \
    --host 0.0.0.0 \
    --port 41010 \
    --reload \
    --log-level info
