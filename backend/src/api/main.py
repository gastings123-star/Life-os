from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.daily_planning import actions_router
from src.api.daily_planning import router as daily_planning_router
from src.api.errors import register_exception_handlers
from src.api.inbox import router as inbox_router
from src.api.weekly_planning import router as weekly_planning_router
from src.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="Life OS")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    application.include_router(daily_planning_router, prefix=settings.api_prefix)
    application.include_router(actions_router, prefix=settings.api_prefix)
    application.include_router(inbox_router, prefix=settings.api_prefix)
    application.include_router(weekly_planning_router, prefix=settings.api_prefix)
    register_exception_handlers(application)
    return application


app = create_app()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
