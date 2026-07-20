from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.inbox import EmptyInboxItemTitleError, InboxItem


def test_inbox_item_normalizes_title_and_keeps_identity() -> None:
    item_id = uuid4()
    created_at = datetime(2026, 7, 20, 10, 0, tzinfo=UTC)

    item = InboxItem(id=item_id, title="  Купить   молоко ", created_at=created_at)

    assert item.id == item_id
    assert item.title == "Купить молоко"
    assert item.created_at == created_at


def test_inbox_item_can_be_renamed_but_not_to_empty_title() -> None:
    item = InboxItem(title="Позвонить")

    item.rename("  Позвонить   врачу ")

    assert item.title == "Позвонить врачу"
    with pytest.raises(EmptyInboxItemTitleError):
        item.rename("   ")
