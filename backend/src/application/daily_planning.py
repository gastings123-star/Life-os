from datetime import date
from typing import Protocol

from src.domain.daily_planning import Action, Day


class DayRepository(Protocol):
    def get_by_date(self, day_date: date) -> Day | None: ...

    def save(self, day: Day) -> None: ...


class DailyPlanningService:
    def __init__(self, repository: DayRepository) -> None:
        self._repository = repository

    def get_or_create_day(self, day_date: date) -> Day:
        day = self._repository.get_by_date(day_date)
        if day is not None:
            return day

        day = Day(date=day_date)
        self._repository.save(day)
        return day

    def add_action(self, day_date: date, title: str) -> tuple[Day, Action]:
        day = self.get_or_create_day(day_date)
        action = day.add_action(title)
        self._repository.save(day)
        return day, action
