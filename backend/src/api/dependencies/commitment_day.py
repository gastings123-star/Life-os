from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine

from src.api.dependencies.daily_planning import get_engine
from src.application.commitment_day import CommitmentDayService
from src.application.repositories import CommitmentDayRepository
from src.infrastructure.database.commitment_day_repository import (
    SqlAlchemyCommitmentDayRepository,
)


def get_commitment_day_repository(
    engine: Annotated[Engine, Depends(get_engine)],
) -> CommitmentDayRepository:
    return SqlAlchemyCommitmentDayRepository(engine)


def get_commitment_day_service(
    repository: Annotated[CommitmentDayRepository, Depends(get_commitment_day_repository)],
) -> CommitmentDayService:
    return CommitmentDayService(repository)
