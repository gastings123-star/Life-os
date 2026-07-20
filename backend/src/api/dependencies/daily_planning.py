from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine

from src.application.daily_planning import DailyPlanningService
from src.application.repositories import DayRepository
from src.config import Settings, get_settings
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.day_repository import SqlAlchemyDayRepository


def get_engine(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[Engine]:
    engine = create_database_engine(settings.database_url)
    try:
        yield engine
    finally:
        engine.dispose()


def get_day_repository(
    engine: Annotated[Engine, Depends(get_engine)],
) -> DayRepository:
    return SqlAlchemyDayRepository(engine)


def get_daily_planning_service(
    repository: Annotated[DayRepository, Depends(get_day_repository)],
) -> DailyPlanningService:
    return DailyPlanningService(repository)
