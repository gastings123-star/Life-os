from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID, uuid4


class EmptyActionTitleError(ValueError):
    """Raised when an action title is empty after whitespace normalization."""


def normalize_action_title(title: str) -> str:
    normalized = " ".join(title.split())
    if not normalized:
        raise EmptyActionTitleError("Action title must not be empty")
    return normalized


@dataclass(slots=True)
class Action:
    day_id: UUID
    title: str
    completed: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", normalize_action_title(self.title))
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must include timezone information")

    def rename(self, title: str) -> None:
        self.title = normalize_action_title(title)

    def set_completed(self, completed: bool) -> None:
        self.completed = completed

    def move_to_day(self, day_id: UUID) -> None:
        self.day_id = day_id


@dataclass(slots=True)
class Day:
    date: date
    id: UUID = field(default_factory=uuid4)
    actions: list[Action] = field(default_factory=list)

    def add_action(self, title: str) -> Action:
        action = Action(day_id=self.id, title=title)
        self.actions.append(action)
        self.actions.sort(key=lambda item: (item.created_at, item.id.hex))
        return action
