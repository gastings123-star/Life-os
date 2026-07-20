from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_cors_preflight_allows_action_patch() -> None:
    response = client.options(
        "/api/v1/actions/00000000-0000-0000-0000-000000000000",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
        },
    )

    allowed_methods = {
        method.strip() for method in response.headers["access-control-allow-methods"].split(",")
    }

    assert response.status_code == 200
    assert allowed_methods == {"GET", "POST", "PUT", "PATCH", "DELETE"}
