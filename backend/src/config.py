from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SQLITE_FILENAME = "life-os.sqlite3"


def get_default_database_url() -> str:
    project_root = Path(__file__).resolve().parents[2]
    return f"sqlite:///{project_root / 'data' / DEFAULT_SQLITE_FILENAME}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIFE_OS_", case_sensitive=False)

    database_url: str = get_default_database_url()
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
