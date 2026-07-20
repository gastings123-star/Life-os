from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_daily_planning_service
from src.application.daily_planning import DailyPlanningService
from src.domain.daily_planning import Action, Day

router = APIRouter(prefix="/days", tags=["daily-planning"])
actions_router = APIRouter(prefix="/actions", tags=["daily-planning"])
ServiceDependency = Annotated[DailyPlanningService, Depends(get_daily_planning_service)]


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
def get_day(day_date: date, service: ServiceDependency) -> DayResponse:
    return serialize_day(service.get_or_create_day(day_date))


@router.post("/{day_date}/actions", response_model=DayResponse, status_code=status.HTTP_201_CREATED)
def add_action(
    day_date: date,
    request: CreateActionRequest,
    service: ServiceDependency,
) -> DayResponse:
    day, _ = service.add_action(day_date, request.title)
    return serialize_day(day)


def serialize_action(action: Action) -> ActionResponse:
    return ActionResponse(
        id=action.id,
        title=action.title,
        completed=action.completed,
        created_at=action.created_at.isoformat(),
    )


@actions_router.patch("/{action_id}", response_model=ActionResponse)
def update_action(
    action_id: UUID,
    request: UpdateActionRequest,
    service: ServiceDependency,
) -> ActionResponse:
    action = service.update_action(
        action_id,
        title=request.title,
        completed=request.completed,
    )
    return serialize_action(action)


@actions_router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action(action_id: UUID, service: ServiceDependency) -> None:
    service.delete_action(action_id)
