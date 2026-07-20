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

    assert script.get_heads() == ["20260720_04"]
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


def test_inbox_items_table_is_created_by_migrations(tmp_path: Path, monkeypatch) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    database_path = tmp_path / "inbox-migration.sqlite3"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv(DATABASE_URL_ENVIRONMENT_VARIABLE, database_url)
    config = Config(backend_root / "alembic.ini")

    command.upgrade(config, "head")

    engine = create_database_engine(database_url)
    inspector = inspect(engine)
    assert "inbox_items" in inspector.get_table_names()
    assert [column["name"] for column in inspector.get_columns("inbox_items")] == [
        "id",
        "title",
        "created_at",
    ]
    engine.dispose()


def test_commitment_migration_preserves_existing_data(tmp_path: Path, monkeypatch) -> None:
    from sqlalchemy import text

    backend_root = Path(__file__).resolve().parents[2]
    database_url = f"sqlite:///{tmp_path / 'existing.sqlite3'}"
    monkeypatch.setenv(DATABASE_URL_ENVIRONMENT_VARIABLE, database_url)
    config = Config(backend_root / "alembic.ini")
    command.upgrade(config, "20260720_03")
    engine = create_database_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO inbox_items VALUES ('existing', 'Сохранить', CURRENT_TIMESTAMP)")
        )
    engine.dispose()

    command.upgrade(config, "head")

    engine = create_database_engine(database_url)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT title FROM inbox_items")).scalar_one() == "Сохранить"
    assert {"daily_plans", "daily_commitments", "commitment_resolutions"}.issubset(
        inspect(engine).get_table_names()
    )
    engine.dispose()

    command.downgrade(config, "20260720_03")
    engine = create_database_engine(database_url)
    inspector = inspect(engine)
    assert "daily_plans" not in inspector.get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT title FROM inbox_items")).scalar_one() == "Сохранить"
    engine.dispose()
