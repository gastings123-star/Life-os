FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock backend/alembic.ini ./
RUN uv sync --frozen --no-dev

COPY backend/src ./src
COPY backend/migrations ./migrations

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
