from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url

from src.infrastructure.database.config import get_database_url

DEFAULT_SQLITE_TIMEOUT_SECONDS = 5.0


def create_database_engine(
    database_url: str | None = None,
    *,
    timeout_seconds: float = DEFAULT_SQLITE_TIMEOUT_SECONDS,
) -> Engine:
    resolved_url = database_url or get_database_url()
    url = make_url(resolved_url)

    if url.get_backend_name() != "sqlite":
        raise ValueError("Life OS storage foundation currently supports SQLite only")

    engine = create_engine(resolved_url, connect_args={"timeout": timeout_seconds})

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine
