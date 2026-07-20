from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import register_exception_handlers
from src.api.main import app

client = TestClient(app)


def test_request_validation_error_uses_standard_format() -> None:
    response = client.get("/api/v1/days/not-a-date")

    assert response.status_code == 422
    assert response.json() == {
        "code": "request_validation_error",
        "message": "Некорректные данные запроса",
    }


def test_http_not_found_uses_standard_format() -> None:
    response = client.get("/missing-route")

    assert response.status_code == 404
    assert response.json() == {"code": "http_error", "message": "Not Found"}


def test_unexpected_error_uses_standard_format() -> None:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/failure")
    def failure() -> None:
        raise RuntimeError("sensitive detail")

    response = TestClient(test_app, raise_server_exceptions=False).get("/failure")

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "Внутренняя ошибка сервера",
    }
