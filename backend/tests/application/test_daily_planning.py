from datetime import date
from uuid import UUID

import pytest

from src.application.daily_planning import ActionNotFoundError, DailyPlanningService
from src.domain.daily_planning import Action, Day


class MoveActionRepository:
    def __init__(self, action: Action | None) -> None:
        self.action = action
        self.target_date: date | None = None

    def move_action(self, action_id: UUID, target_date: date) -> Action | None:
        self.target_date = target_date
        if self.action is None or self.action.id != action_id:
            return None
        self.action.move_to_day(UUID(int=2))
        return self.action


def test_service_moves_existing_action() -> None:
    action = Day(date=date(2026, 7, 20)).add_action("Перенести")
    repository = MoveActionRepository(action)
    service = DailyPlanningService(repository)  # type: ignore[arg-type]
    target_date = date(2026, 7, 28)

    moved = service.move_action(action.id, target_date)

    assert moved is action
    assert moved.id == action.id
    assert repository.target_date == target_date


def test_service_reports_missing_action_during_move() -> None:
    repository = MoveActionRepository(None)
    service = DailyPlanningService(repository)  # type: ignore[arg-type]

    with pytest.raises(ActionNotFoundError):
        service.move_action(UUID(int=1), date(2026, 7, 28))
