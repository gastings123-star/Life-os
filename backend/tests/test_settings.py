from src.config import Settings, get_default_database_url


def test_settings_have_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("LIFE_OS_DATABASE_URL", raising=False)
    monkeypatch.delenv("LIFE_OS_API_PREFIX", raising=False)
    monkeypatch.delenv("LIFE_OS_CORS_ORIGINS", raising=False)

    settings = Settings()

    assert settings.database_url == get_default_database_url()
    assert settings.api_prefix == "/api/v1"
    assert settings.cors_origins == ["http://localhost:5173"]


def test_settings_load_life_os_environment(monkeypatch) -> None:
    monkeypatch.setenv("LIFE_OS_DATABASE_URL", "sqlite:////tmp/life-os.sqlite3")
    monkeypatch.setenv("LIFE_OS_API_PREFIX", "/custom-api")
    monkeypatch.setenv(
        "LIFE_OS_CORS_ORIGINS",
        '["http://localhost:3000", "http://localhost:5173"]',
    )

    settings = Settings()

    assert settings.database_url == "sqlite:////tmp/life-os.sqlite3"
    assert settings.api_prefix == "/custom-api"
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]
