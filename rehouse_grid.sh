#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/idona/MoStar/_apps/grid"
cd "$ROOT"

echo "=== MoStar Grid Rehouse: market -> house ==="

# Clean up any empty folders created by the first run that prevented moves
rmdir front/app 2>/dev/null || true
rmdir back/data 2>/dev/null || true
rmdir back/logs 2>/dev/null || true
rmdir core/ops/config 2>/dev/null || true
rmdir core/ops/docs 2>/dev/null || true
rmdir core/ops/architecture 2>/dev/null || true
rmdir core/ops/scripts 2>/dev/null || true
rmdir core/ops/tests 2>/dev/null || true
rmdir core/ops/approval_queue 2>/dev/null || true
rmdir core/ops/scratch 2>/dev/null || true

# Pre-create parent structures ONLY, not the actual target names of the moved dirs
mkdir -p \
  front \
  back/services \
  back \
  core/engines \
  core/sovereignty \
  core/protocols \
  core/ops/proofs \
  core/ops/status

move_dir() {
  src="$1"
  dst="$2"

  if [ -d "$src" ]; then
    if [ ! -e "$dst" ]; then
      echo "MOVE DIR  $src -> $dst"
      mkdir -p "$(dirname "$dst")"
      git mv "$src" "$dst" 2>/dev/null || mv "$src" "$dst"
    else
      echo "TARGET EXISTS ($dst), MERGING CONTENTS..."
      # Move files individually or clean up
      git mv "$src"/* "$dst"/ 2>/dev/null || mv "$src"/* "$dst"/
      rmdir "$src" || true
    fi
  else
    echo "SKIP DIR  $src (not found)"
  fi
}

move_file() {
  src="$1"
  dst="$2"

  if [ -f "$src" ]; then
    if [ ! -e "$dst" ]; then
      echo "MOVE FILE $src -> $dst"
      mkdir -p "$(dirname "$dst")"
      git mv "$src" "$dst" 2>/dev/null || mv "$src" "$dst"
    else
      echo "SKIP FILE $src (target exists)"
    fi
  else
    echo "SKIP FILE $src (not found)"
  fi
}

# front
move_dir "frontend" "front/app"

# back/services
move_dir "grid" "back/services/grid"
move_dir "mindgraph" "back/services/mindgraph"
move_dir "mcp_gateway" "back/services/mcp_gateway"
move_dir "federation" "back/services/federation"
move_dir "density_telemetry" "back/services/density_telemetry"

# back/state
move_dir "data" "back/data"
move_dir "logs" "back/logs"

# core engines
move_dir "woo" "core/engines/woo"
move_dir "truth_engine" "core/engines/truth_engine"
move_dir "decision_engine" "core/engines/decision_engine"

# core sovereignty
move_dir "provenance" "core/sovereignty/provenance"
move_dir "security" "core/sovereignty/security"
move_dir "soul" "core/sovereignty/soul"

# core protocols
move_dir "dcx" "core/protocols/dcx"
move_dir "moscript" "core/protocols/moscript"
move_dir "rcf" "core/protocols/rcf"
move_dir "rfcs" "core/protocols/rfcs"

# core ops
move_dir "config" "core/ops/config"
move_dir "docs" "core/ops/docs"
move_dir "architecture" "core/ops/architecture"
move_dir "scripts" "core/ops/scripts"
move_dir "tests" "core/ops/tests"
move_dir "approval_queue" "core/ops/approval_queue"
move_dir "scratch" "core/ops/scratch"

# proof/status files
move_file "FEDERATION_EXCHANGE_PROOF.json" "core/ops/proofs/FEDERATION_EXCHANGE_PROOF.json"
move_file "NEO4J_CHECKPOINT_STATUS.md" "core/ops/status/NEO4J_CHECKPOINT_STATUS.md"
move_file "PHASE_4A_IMPLEMENTATION_SEAL.md" "core/ops/status/PHASE_4A_IMPLEMENTATION_SEAL.md"

echo
echo "=== New top-level house ==="
find . -maxdepth 2 -type d | sort

echo
echo "Done. Now run import/path checks."
