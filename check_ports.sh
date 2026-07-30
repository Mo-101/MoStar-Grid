#!/usr/bin/env bash
set -e
if command -v ss >/dev/null 2>&1; then
  ss -tlnp 2>/dev/null | grep -E '47687|7687|7474' || true
else
  netstat -tlnp 2>/dev/null | grep -E '47687|7687|7474' || true
fi
