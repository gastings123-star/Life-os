from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from src.infrastructure.database import create_database_engine
from src.infrastructure.database.config import DATABASE_URL_ENVIRONMENT_VARIABLE


def test_alembic_current_supports_empty_database_with_daily_planning_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    database_path = tmp_path / "alembic.sqlite3"
    monkeypatch.setenv(DATABASE_URL_ENVIRONMENT_VARIABLE, f"sqlite:///{database_path}")

    config = Config(backend_root / "alembic.ini")
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["20260720_02"]
    command.current(config)
    assert database_path.exists()


def test_action_completed_column_is_created_by_migrations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    database_path = tmp_path / "migrations.sqlite3"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv(DATABASE_URL_ENVIRONMENT_VARIABLE, database_url)
    config = Config(backend_root / "alembic.ini")

    command.upgrade(config, "head")

    engine = create_database_engine(database_url)
    completed_column = next(
        column for column in inspect(engine).get_columns("actions") if column["name"] == "completed"
    )
    assert completed_column["nullable"] is False
    engine.dispose()
