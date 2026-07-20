from datetime import date
from pathlib import Path
from uuid import uuid4

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
    assert created_day.json()["actions"][0]["completed"] is False
    assert reloaded_day.json() == created_day.json()
    engine.dispose()


def test_update_and_delete_action_through_api(tmp_path: Path, monkeypatch) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'action-lifecycle-api.sqlite3'}")
    metadata.create_all(engine)
    monkeypatch.setattr(
        daily_planning,
        "service",
        DailyPlanningService(SqlAlchemyDayRepository(engine)),
    )
    client = TestClient(app)
    day_date = date(2026, 7, 20).isoformat()
    created = client.post(
        f"/api/v1/days/{day_date}/actions",
        json={"title": "Initial title"},
    ).json()["actions"][0]
    action_url = f"/api/v1/actions/{created['id']}"

    renamed = client.patch(action_url, json={"title": "  Updated   title "})
    completed = client.patch(action_url, json={"completed": True})
    updated_together = client.patch(
        action_url,
        json={"title": "Final title", "completed": False},
    )
    deleted = client.delete(action_url)
    reloaded_day = client.get(f"/api/v1/days/{day_date}")

    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Updated title"
    assert completed.json()["completed"] is True
    assert updated_together.json()["title"] == "Final title"
    assert updated_together.json()["completed"] is False
    assert deleted.status_code == 204
    assert reloaded_day.json()["actions"] == []
    engine.dispose()


def test_action_lifecycle_returns_consistent_not_found_error(tmp_path: Path, monkeypatch) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'missing-action-api.sqlite3'}")
    metadata.create_all(engine)
    monkeypatch.setattr(
        daily_planning,
        "service",
        DailyPlanningService(SqlAlchemyDayRepository(engine)),
    )
    client = TestClient(app)
    action_url = f"/api/v1/actions/{uuid4()}"

    patch_response = client.patch(action_url, json={"completed": True})
    delete_response = client.delete(action_url)

    expected_detail = {
        "detail": {
            "code": "action_not_found",
            "message": "Действие не найдено",
        }
    }
    assert patch_response.status_code == 404
    assert delete_response.status_code == 404
    assert patch_response.json() == expected_detail
    assert delete_response.json() == expected_detail
    engine.dispose()
