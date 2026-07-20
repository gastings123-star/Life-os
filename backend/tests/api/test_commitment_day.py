from pathlib import Path

from fastapi.testclient import TestClient

from src.api.dependencies import get_engine
from src.api.main import app
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.metadata import metadata


def test_commitment_day_api_happy_path_and_summary(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'api.sqlite3'}")
    metadata.create_all(engine)
    app.dependency_overrides[get_engine] = lambda: engine
    client = TestClient(app)
    day_date = "2026-07-20"

    assert client.get(f"/api/v1/commitment-days/{day_date}").json()["status"] == "empty"
    planned = client.put(
        f"/api/v1/commitment-days/{day_date}/plan",
        json={
            "capacity": "normal",
            "primary": "Главный результат готов",
            "secondary": ["Снять", "Пересмотреть"],
        },
    )
    activated = client.post(f"/api/v1/commitment-days/{day_date}/activate")
    commitments = activated.json()["commitments"]
    completed = client.post(f"/api/v1/commitments/{commitments[0]['id']}/complete")
    closed = client.post(
        f"/api/v1/commitment-days/{day_date}/close",
        json={
            "resolutions": [
                {"commitment_id": commitments[0]["id"], "outcome": "completed"},
                {
                    "commitment_id": commitments[1]["id"],
                    "outcome": "dropped",
                    "reason": "lost_relevance",
                },
                {
                    "commitment_id": commitments[2]["id"],
                    "outcome": "renegotiated",
                    "reason": "not_enough_time",
                    "target_date": "2026-07-22",
                },
            ]
        },
    )
    successor = client.get("/api/v1/commitment-days/2026-07-22")
    summary = client.get("/api/v1/experiments/commitment-day/summary")

    assert planned.status_code == 200 and len(planned.json()["commitments"]) == 3
    assert completed.json()["commitments"][0]["status"] == "completed"
    assert closed.status_code == 200 and closed.json()["status"] == "closed"
    assert successor.json()["commitments"][0]["text"] == "Пересмотреть"
    assert summary.json()["total_closed_days"] == 1
    assert summary.json()["commitments_by_outcome"] == {
        "completed": 1,
        "dropped": 1,
        "renegotiated": 1,
    }
    app.dependency_overrides.clear()
    engine.dispose()


def test_commitment_api_validation_and_past_unclosed(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'validation.sqlite3'}")
    metadata.create_all(engine)
    app.dependency_overrides[get_engine] = lambda: engine
    client = TestClient(app)
    client.put(
        "/api/v1/commitment-days/2026-07-19/plan",
        json={"capacity": "low", "primary": "Незакрытый", "secondary": []},
    )
    client.post("/api/v1/commitment-days/2026-07-19/activate")
    item = client.get("/api/v1/commitment-days/2026-07-19").json()["commitments"][0]
    invalid = client.post(
        "/api/v1/commitment-days/2026-07-19/close",
        json={"resolutions": [{"commitment_id": item["id"], "outcome": "dropped"}]},
    )
    unclosed = client.get("/api/v1/commitment-days/unclosed?before=2026-07-20")

    assert invalid.status_code == 422
    assert invalid.json()["code"] == "invalid_commitment_resolution"
    assert [entry["date"] for entry in unclosed.json()] == ["2026-07-19"]
    app.dependency_overrides.clear()
    engine.dispose()
