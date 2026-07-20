from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine

from src.api.dependencies.daily_planning import get_engine
from src.application.inbox import InboxService
from src.application.repositories import InboxRepository
from src.infrastructure.database.inbox_repository import SqlAlchemyInboxRepository


def get_inbox_repository(
    engine: Annotated[Engine, Depends(get_engine)],
) -> InboxRepository:
    return SqlAlchemyInboxRepository(engine)


def get_inbox_service(
    repository: Annotated[InboxRepository, Depends(get_inbox_repository)],
) -> InboxService:
    return InboxService(repository)
