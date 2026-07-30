#!/bin/bash
set -e

append_woo() {
  local file="$1"
  if [ -f "$file" ]; then
    if ! grep -q '^WOO_ENABLED=' "$file" 2>/dev/null; then
      cat >> "$file" <<'EOF'

# Woo shadow mode activation
WOO_ENABLED=true
WOO_MODE=shadow
WOO_EXECUTION_ENABLED=false
WOO_GRAPH_WRITE_ENABLED=false
WOO_DENY_THRESHOLD=0.92
WOO_APPROVE_THRESHOLD=0.95
WOO_GRAPH_RUN_ID=gds-pagerank-kd-sfc-20260712161104
WOO_GRAPH_PROPERTY=pagerank_raw
EOF
      echo "Appended Woo config to $file"
    else
      echo "Woo config already present in $file"
    fi
  else
    echo "File not found: $file"
  fi
}

append_woo /home/idona/MoStar/_apps/grid/.env.local
append_woo /home/idona/MoStar/_apps/grid/front/app/.env.local
