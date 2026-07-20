from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.application.daily_planning import ActionNotFoundError, DailyPlanningService
from src.domain.daily_planning import Action, Day, EmptyActionTitleError
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.day_repository import SqlAlchemyDayRepository

router = APIRouter(prefix="/api/v1/days", tags=["daily-planning"])
actions_router = APIRouter(prefix="/api/v1/actions", tags=["daily-planning"])
service = DailyPlanningService(SqlAlchemyDayRepository(create_database_engine()))

ACTION_NOT_FOUND_DETAIL = {
    "code": "action_not_found",
    "message": "Действие не найдено",
}


class ActionResponse(BaseModel):
    id: UUID
    title: str
    completed: bool
    created_at: str


class DayResponse(BaseModel):
    id: UUID
    date: date
    actions: list[ActionResponse]


class CreateActionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class UpdateActionRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    completed: bool | None = None


def serialize_day(day: Day) -> DayResponse:
    return DayResponse(
        id=day.id,
        date=day.date,
        actions=[
            ActionResponse(
                id=action.id,
                title=action.title,
                completed=action.completed,
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


def serialize_action(action: Action) -> ActionResponse:
    return ActionResponse(
        id=action.id,
        title=action.title,
        completed=action.completed,
        created_at=action.created_at.isoformat(),
    )


@actions_router.patch("/{action_id}", response_model=ActionResponse)
def update_action(action_id: UUID, request: UpdateActionRequest) -> ActionResponse:
    try:
        action = service.update_action(
            action_id,
            title=request.title,
            completed=request.completed,
        )
    except ActionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ACTION_NOT_FOUND_DETAIL,
        ) from error
    except EmptyActionTitleError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "empty_action_title", "message": str(error)},
        ) from error
    return serialize_action(action)


@actions_router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action(action_id: UUID) -> None:
    try:
        service.delete_action(action_id)
    except ActionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ACTION_NOT_FOUND_DETAIL,
        ) from error
