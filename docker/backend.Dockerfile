FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock backend/alembic.ini ./
RUN uv sync --frozen --no-dev

COPY backend/src ./src
COPY backend/migrations ./migrations
COPY docker/backend-entrypoint.sh /usr/local/bin/life-os-backend
RUN chmod +x /usr/local/bin/life-os-backend

EXPOSE 8000

CMD ["life-os-backend"]
