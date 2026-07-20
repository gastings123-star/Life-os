from datetime import date
from uuid import UUID

from src.application.repositories import DayRepository
from src.domain.daily_planning import Action, Day


class ActionNotFoundError(LookupError):
    """Raised when an action cannot be found by its identifier."""


class DailyPlanningService:
    def __init__(self, repository: DayRepository) -> None:
        self._repository = repository

    def get_or_create_day(self, day_date: date) -> Day:
        day = self._repository.get_day_by_date(day_date)
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

    def update_action(
        self,
        action_id: UUID,
        *,
        title: str | None = None,
        completed: bool | None = None,
    ) -> Action:
        action = self._get_action(action_id)
        if title is not None:
            action.rename(title)
        if completed is not None:
            action.set_completed(completed)
        self._repository.update_action(action)
        return action

    def delete_action(self, action_id: UUID) -> None:
        if not self._repository.delete_action(action_id):
            raise ActionNotFoundError(f"Action {action_id} was not found")

    def _get_action(self, action_id: UUID) -> Action:
        action = self._repository.get_action(action_id)
        if action is None:
            raise ActionNotFoundError(f"Action {action_id} was not found")
        return action
