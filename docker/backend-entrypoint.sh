#!/usr/bin/env sh

set -eu

uv run --no-dev alembic upgrade head
exec uv run --no-dev uvicorn src.api.main:app --host 0.0.0.0 --port 8000
