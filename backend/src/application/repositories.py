from datetime import date
from typing import Protocol
from uuid import UUID

from src.domain.daily_planning import Action, Day


class DayRepository(Protocol):
    def get_by_date(self, day_date: date) -> Day | None: ...

    def save(self, day: Day) -> None: ...

    def get_action(self, action_id: UUID) -> Action | None: ...

    def update_action(self, action: Action) -> None: ...

    def delete_action(self, action_id: UUID) -> bool: ...
