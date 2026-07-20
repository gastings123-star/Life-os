from dataclasses import dataclass
from datetime import date, timedelta

from src.application.repositories import DayRepository
from src.domain.daily_planning import Action


@dataclass(frozen=True, slots=True)
class WeekDayView:
    date: date
    actions: tuple[Action, ...]


@dataclass(frozen=True, slots=True)
class WeekView:
    week_start: date
    days: tuple[WeekDayView, ...]


def start_of_week(selected_date: date) -> date:
    return selected_date - timedelta(days=selected_date.weekday())


class WeeklyPlanningService:
    def __init__(self, repository: DayRepository) -> None:
        self._repository = repository

    def get_week(self, selected_date: date) -> WeekView:
        week_start = start_of_week(selected_date)
        days = []
        for offset in range(7):
            day_date = week_start + timedelta(days=offset)
            day = self._repository.get_day_by_date(day_date)
            days.append(
                WeekDayView(
                    date=day_date,
                    actions=tuple(day.actions) if day is not None else (),
                )
            )
        return WeekView(week_start=week_start, days=tuple(days))
