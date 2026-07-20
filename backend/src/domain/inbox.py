from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


class EmptyInboxItemTitleError(ValueError):
    """Raised when an inbox item title is empty after normalization."""


def normalize_inbox_item_title(title: str) -> str:
    normalized = " ".join(title.split())
    if not normalized:
        raise EmptyInboxItemTitleError("Inbox item title must not be empty")
    return normalized


@dataclass(slots=True)
class InboxItem:
    title: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.title = normalize_inbox_item_title(self.title)
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must include timezone information")

    def rename(self, title: str) -> None:
        self.title = normalize_inbox_item_title(title)
