from pathlib import Path

from fastapi.testclient import TestClient

from src.api.dependencies import daily_planning as dependencies
from src.api.dependencies import get_engine
from src.api.main import app
from src.config import Settings
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.metadata import metadata


def test_dependency_chain_builds_service_and_repository(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'dependencies.sqlite3'}")
    metadata.create_all(engine)
    app.dependency_overrides[get_engine] = lambda: engine
    client = TestClient(app)

    response = client.get("/api/v1/days/2026-07-20")

    assert response.status_code == 200
    assert response.json()["date"] == "2026-07-20"
    app.dependency_overrides.clear()
    engine.dispose()


def test_engine_dependency_disposes_created_engine(monkeypatch) -> None:
    engine = create_database_engine("sqlite:///:memory:")
    disposed = False

    def dispose() -> None:
        nonlocal disposed
        disposed = True

    monkeypatch.setattr(engine, "dispose", dispose)
    monkeypatch.setattr(dependencies, "create_database_engine", lambda _: engine)
    generator = get_engine(Settings(database_url="sqlite:///:memory:"))

    assert next(generator) is engine
    generator.close()

    assert disposed is True
