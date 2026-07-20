from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.application.daily_planning import ActionNotFoundError
from src.domain.daily_planning import EmptyActionTitleError


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "message": message})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ActionNotFoundError)
    async def action_not_found_handler(_: Request, __: ActionNotFoundError) -> JSONResponse:
        return error_response(status.HTTP_404_NOT_FOUND, "action_not_found", "Действие не найдено")

    @app.exception_handler(EmptyActionTitleError)
    async def empty_action_title_handler(_: Request, error: EmptyActionTitleError) -> JSONResponse:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "empty_action_title",
            str(error),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "request_validation_error",
            "Некорректные данные запроса",
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, error: StarletteHTTPException) -> JSONResponse:
        message = error.detail if isinstance(error.detail, str) else "Ошибка HTTP-запроса"
        return error_response(error.status_code, "http_error", message)

    @app.exception_handler(Exception)
    async def internal_error_handler(_: Request, __: Exception) -> JSONResponse:
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "Внутренняя ошибка сервера",
        )
