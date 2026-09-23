#!/usr/bin/env bash

set -euo pipefail

export PUBLIC_DEMO_MODE=true

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Starting Engineering Knowledge Copilot public demo..."
echo "Host: ${HOST}"
echo "Port: ${PORT}"
echo "Public demo mode: ${PUBLIC_DEMO_MODE}"

exec uvicorn backend.main:app \
  --host "${HOST}" \
  --port "${PORT}"
