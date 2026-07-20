from datetime import date
from uuid import UUID

import pytest

from src.application.inbox import InboxItemNotFoundError, InboxService
from src.domain.daily_planning import Action
from src.domain.inbox import InboxItem


class InMemoryInboxRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, InboxItem] = {}

    def get_all(self) -> list[InboxItem]:
        return list(self.items.values())

    def add(self, item: InboxItem) -> None:
        self.items[item.id] = item

    def get(self, item_id: UUID) -> InboxItem | None:
        return self.items.get(item_id)

    def update(self, item: InboxItem) -> None:
        self.items[item.id] = item

    def delete(self, item_id: UUID) -> bool:
        return self.items.pop(item_id, None) is not None

    def schedule(self, item_id: UUID, day_date: date) -> Action | None:
        item = self.items.pop(item_id, None)
        if item is None:
            return None
        return Action(day_id=UUID(int=1), title=item.title)


def test_inbox_service_supports_item_lifecycle() -> None:
    repository = InMemoryInboxRepository()
    service = InboxService(repository)

    item = service.add_item("  Купить   молоко ")
    renamed = service.rename_item(item.id, "Купить овсяное молоко")
    action = service.schedule_item(item.id, date(2026, 7, 25))

    deleted_item = service.add_item("Удалить")
    service.delete_item(deleted_item.id)

    assert renamed.title == "Купить овсяное молоко"
    assert action.title == "Купить овсяное молоко"
    assert service.get_inbox() == []


def test_inbox_service_reports_missing_items() -> None:
    service = InboxService(InMemoryInboxRepository())
    missing_id = UUID(int=2)

    with pytest.raises(InboxItemNotFoundError):
        service.rename_item(missing_id, "Название")
    with pytest.raises(InboxItemNotFoundError):
        service.delete_item(missing_id)
    with pytest.raises(InboxItemNotFoundError):
        service.schedule_item(missing_id, date(2026, 7, 25))
