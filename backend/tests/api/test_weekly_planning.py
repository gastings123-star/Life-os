from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src.api.dependencies import get_engine
from src.api.main import app
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.metadata import days, metadata


def test_week_api_serializes_seven_days_without_creating_missing_days(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'week-api.sqlite3'}")
    metadata.create_all(engine)
    app.dependency_overrides[get_engine] = lambda: engine
    client = TestClient(app)
    client.post(
        "/api/v1/days/2026-07-22/actions",
        json={"title": "Задача среды"},
    )

    response = client.get("/api/v1/week", params={"date": "2026-07-24"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["weekStart"] == "2026-07-20"
    assert len(payload["days"]) == 7
    assert [day["date"] for day in payload["days"]] == [
        "2026-07-20",
        "2026-07-21",
        "2026-07-22",
        "2026-07-23",
        "2026-07-24",
        "2026-07-25",
        "2026-07-26",
    ]
    assert payload["days"][0]["actions"] == []
    assert payload["days"][2]["actions"][0]["title"] == "Задача среды"
    with engine.connect() as connection:
        assert connection.execute(select(func.count()).select_from(days)).scalar_one() == 1
    app.dependency_overrides.clear()
    engine.dispose()
