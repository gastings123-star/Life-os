from datetime import date
from uuid import UUID

from src.application.repositories import InboxRepository
from src.domain.daily_planning import Action
from src.domain.inbox import InboxItem


class InboxItemNotFoundError(LookupError):
    """Raised when an inbox item cannot be found by its identifier."""


class InboxService:
    def __init__(self, repository: InboxRepository) -> None:
        self._repository = repository

    def get_inbox(self) -> list[InboxItem]:
        return self._repository.get_all()

    def add_item(self, title: str) -> InboxItem:
        item = InboxItem(title=title)
        self._repository.add(item)
        return item

    def rename_item(self, item_id: UUID, title: str) -> InboxItem:
        item = self._get_item(item_id)
        item.rename(title)
        self._repository.update(item)
        return item

    def delete_item(self, item_id: UUID) -> None:
        if not self._repository.delete(item_id):
            raise InboxItemNotFoundError(f"Inbox item {item_id} was not found")

    def schedule_item(self, item_id: UUID, day_date: date) -> Action:
        action = self._repository.schedule(item_id, day_date)
        if action is None:
            raise InboxItemNotFoundError(f"Inbox item {item_id} was not found")
        return action

    def _get_item(self, item_id: UUID) -> InboxItem:
        item = self._repository.get(item_id)
        if item is None:
            raise InboxItemNotFoundError(f"Inbox item {item_id} was not found")
        return item
