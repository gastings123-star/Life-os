import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from src.infrastructure.database import create_database_engine
from src.infrastructure.database.config import DATABASE_URL_ENVIRONMENT_VARIABLE


def sqlite_url(database_path: Path) -> str:
    return f"sqlite:///{database_path}"


def test_engine_does_not_create_database_before_connection(tmp_path: Path) -> None:
    database_path = tmp_path / "lazy.sqlite3"

    engine = create_database_engine(sqlite_url(database_path))

    assert not database_path.exists()
    engine.dispose()


def test_connection_executes_select_and_creates_database_in_temporary_directory(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "connection.sqlite3"
    engine = create_database_engine(sqlite_url(database_path))

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1
    assert database_path.exists()
    assert database_path.parent == tmp_path
    engine.dispose()


def test_foreign_keys_are_enabled_for_every_connection(tmp_path: Path) -> None:
    engine = create_database_engine(sqlite_url(tmp_path / "foreign-keys.sqlite3"))

    with engine.connect() as first_connection:
        assert first_connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1

    with engine.connect() as second_connection:
        assert second_connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1

    engine.dispose()


def test_sqlite_timeout_is_configured(tmp_path: Path) -> None:
    engine = create_database_engine(
        sqlite_url(tmp_path / "timeout.sqlite3"),
        timeout_seconds=2.5,
    )

    with engine.connect() as connection:
        timeout_milliseconds = connection.execute(text("PRAGMA busy_timeout")).scalar_one()

    assert timeout_milliseconds == 2500
    engine.dispose()


def test_importing_database_modules_has_no_storage_side_effects(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "import.sqlite3"
    backend_root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    environment[DATABASE_URL_ENVIRONMENT_VARIABLE] = sqlite_url(database_path)
    environment["PYTHONPATH"] = str(backend_root)

    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import src.infrastructure.database.config; "
                "import src.infrastructure.database.engine; "
                "import src.infrastructure.database.metadata"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
    )

    assert not database_path.parent.exists()
    assert not database_path.exists()
