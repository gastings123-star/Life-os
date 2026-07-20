from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.daily_planning import ActionResponse, serialize_action
from src.api.dependencies import get_weekly_planning_service
from src.application.weekly_planning import WeeklyPlanningService

router = APIRouter(prefix="/week", tags=["weekly-planning"])
ServiceDependency = Annotated[WeeklyPlanningService, Depends(get_weekly_planning_service)]


class WeekDayResponse(BaseModel):
    date: date
    actions: list[ActionResponse]


class WeekResponse(BaseModel):
    week_start: date = Field(serialization_alias="weekStart")
    days: list[WeekDayResponse]


@router.get("", response_model=WeekResponse)
def get_week(date: date, service: ServiceDependency) -> WeekResponse:
    week = service.get_week(date)
    return WeekResponse(
        week_start=week.week_start,
        days=[
            WeekDayResponse(
                date=day.date,
                actions=[serialize_action(action) for action in day.actions],
            )
            for day in week.days
        ],
    )
