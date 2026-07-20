#!/usr/bin/env sh

set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
backend_pid=""
frontend_pid=""

cleanup() {
  if [ -n "$backend_pid" ]; then
    kill "$backend_pid" 2>/dev/null || true
  fi
  if [ -n "$frontend_pid" ]; then
    kill "$frontend_pid" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

cd "$root_dir/backend"
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &
backend_pid=$!

cd "$root_dir/frontend"
npm run dev &
frontend_pid=$!

wait
