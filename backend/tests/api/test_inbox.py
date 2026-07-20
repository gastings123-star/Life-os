from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.dependencies import get_engine
from src.api.main import app
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.metadata import metadata


def test_inbox_api_lifecycle_and_schedule_integration(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'inbox-api.sqlite3'}")
    metadata.create_all(engine)
    app.dependency_overrides[get_engine] = lambda: engine
    client = TestClient(app)

    assert client.get("/api/v1/inbox").json() == []
    created = client.post("/api/v1/inbox", json={"title": "  Купить   молоко "})
    item_id = created.json()["id"]
    renamed = client.patch(
        f"/api/v1/inbox/{item_id}",
        json={"title": "Купить овсяное молоко"},
    )
    scheduled = client.post(
        f"/api/v1/inbox/{item_id}/schedule",
        json={"date": "2026-07-25"},
    )
    inbox = client.get("/api/v1/inbox")
    day = client.get("/api/v1/days/2026-07-25")

    assert created.status_code == 201
    assert renamed.json()["title"] == "Купить овсяное молоко"
    assert scheduled.status_code == 200
    assert scheduled.json()["title"] == "Купить овсяное молоко"
    assert inbox.json() == []
    assert [action["title"] for action in day.json()["actions"]] == ["Купить овсяное молоко"]
    app.dependency_overrides.clear()
    engine.dispose()


def test_inbox_api_deletes_item_and_standardizes_not_found(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'inbox-delete-api.sqlite3'}")
    metadata.create_all(engine)
    app.dependency_overrides[get_engine] = lambda: engine
    client = TestClient(app)
    created = client.post("/api/v1/inbox", json={"title": "Удалить"}).json()

    deleted = client.delete(f"/api/v1/inbox/{created['id']}")
    missing = client.patch(f"/api/v1/inbox/{uuid4()}", json={"title": "Нет"})

    assert deleted.status_code == 204
    assert missing.status_code == 404
    assert missing.json() == {
        "code": "inbox_item_not_found",
        "message": "Элемент Inbox не найден",
    }
    app.dependency_overrides.clear()
    engine.dispose()
