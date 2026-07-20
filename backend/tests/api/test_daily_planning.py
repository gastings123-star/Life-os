from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import daily_planning
from src.api.main import app
from src.application.daily_planning import DailyPlanningService
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.day_repository import SqlAlchemyDayRepository
from src.infrastructure.database.metadata import metadata


def test_create_and_read_action_through_api(tmp_path: Path, monkeypatch) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'api.sqlite3'}")
    metadata.create_all(engine)
    monkeypatch.setattr(
        daily_planning,
        "service",
        DailyPlanningService(SqlAlchemyDayRepository(engine)),
    )
    client = TestClient(app)
    day_date = date(2026, 7, 20).isoformat()

    empty_day = client.get(f"/api/v1/days/{day_date}")
    created_day = client.post(
        f"/api/v1/days/{day_date}/actions",
        json={"title": "  Prepare   meeting plan  "},
    )
    reloaded_day = client.get(f"/api/v1/days/{day_date}")

    assert empty_day.status_code == 200
    assert empty_day.json()["actions"] == []
    assert created_day.status_code == 201
    assert created_day.json()["actions"][0]["title"] == "Prepare meeting plan"
    assert reloaded_day.json() == created_day.json()
    engine.dispose()
