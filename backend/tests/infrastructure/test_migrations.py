from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

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

    assert script.get_heads() == ["20260720_01"]
    command.current(config)
    assert database_path.exists()
