import os
from pathlib import Path

DATABASE_URL_ENVIRONMENT_VARIABLE = "LIFE_OS_DATABASE_URL"
DEFAULT_SQLITE_FILENAME = "life-os.sqlite3"


def get_default_database_path() -> Path:
    project_root = Path(__file__).resolve().parents[4]
    return project_root / "data" / DEFAULT_SQLITE_FILENAME


def get_database_url() -> str:
    configured_url = os.getenv(DATABASE_URL_ENVIRONMENT_VARIABLE)
    if configured_url:
        return configured_url

    return f"sqlite:///{get_default_database_path()}"
