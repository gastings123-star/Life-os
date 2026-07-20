from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.application.daily_planning import DailyPlanningService
from src.domain.daily_planning import Day, EmptyActionTitleError
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.day_repository import SqlAlchemyDayRepository

router = APIRouter(prefix="/api/v1/days", tags=["daily-planning"])
service = DailyPlanningService(SqlAlchemyDayRepository(create_database_engine()))


class ActionResponse(BaseModel):
    id: UUID
    title: str
    created_at: str


class DayResponse(BaseModel):
    id: UUID
    date: date
    actions: list[ActionResponse]


class CreateActionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)


def serialize_day(day: Day) -> DayResponse:
    return DayResponse(
        id=day.id,
        date=day.date,
        actions=[
            ActionResponse(
                id=action.id,
                title=action.title,
                created_at=action.created_at.isoformat(),
            )
            for action in day.actions
        ],
    )


@router.get("/{day_date}", response_model=DayResponse)
def get_day(day_date: date) -> DayResponse:
    return serialize_day(service.get_or_create_day(day_date))


@router.post("/{day_date}/actions", response_model=DayResponse, status_code=status.HTTP_201_CREATED)
def add_action(day_date: date, request: CreateActionRequest) -> DayResponse:
    try:
        day, _ = service.add_action(day_date, request.title)
    except EmptyActionTitleError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "empty_action_title", "message": str(error)},
        ) from error
    return serialize_day(day)
