#!/usr/bin/env bash
set -e
PID=${1:-34073}
if [ -f "/proc/$PID/cmdline" ]; then
  cat "/proc/$PID/cmdline" | tr '\0' ' '
  echo
fi
