from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.domain.inbox import InboxItem
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.day_repository import SqlAlchemyDayRepository
from src.infrastructure.database.inbox_repository import SqlAlchemyInboxRepository
from src.infrastructure.database.metadata import metadata


def test_inbox_repository_persists_renames_and_deletes(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'inbox.sqlite3'}")
    metadata.create_all(engine)
    repository = SqlAlchemyInboxRepository(engine)
    first = InboxItem(title="Первый")
    second = InboxItem(title="Второй")

    repository.add(first)
    repository.add(second)
    first.rename("Обновлённый")
    repository.update(first)

    assert [item.title for item in repository.get_all()] == ["Обновлённый", "Второй"]
    assert repository.get(first.id).title == "Обновлённый"
    assert repository.delete(second.id) is True
    assert repository.delete(second.id) is False
    engine.dispose()


def test_inbox_repository_schedules_item_into_day_atomically(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'schedule.sqlite3'}")
    metadata.create_all(engine)
    inbox_repository = SqlAlchemyInboxRepository(engine)
    day_repository = SqlAlchemyDayRepository(engine)
    item = InboxItem(title="Запланировать встречу")
    target_date = date(2026, 7, 25)
    inbox_repository.add(item)

    action = inbox_repository.schedule(item.id, target_date)
    day = day_repository.get_by_date(target_date)

    assert action is not None
    assert action.title == item.title
    assert inbox_repository.get_all() == []
    assert day is not None
    assert [day_action.title for day_action in day.actions] == [item.title]
    engine.dispose()


def test_failed_schedule_keeps_inbox_item_and_does_not_create_day(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'schedule-rollback.sqlite3'}")
    metadata.create_all(engine)
    inbox_repository = SqlAlchemyInboxRepository(engine)
    day_repository = SqlAlchemyDayRepository(engine)
    item = InboxItem(title="Остаться в Inbox")
    target_date = date(2026, 7, 25)
    inbox_repository.add(item)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER reject_scheduled_action BEFORE INSERT ON actions "
                "BEGIN SELECT RAISE(ABORT, 'rejected'); END"
            )
        )

    with pytest.raises(DBAPIError):
        inbox_repository.schedule(item.id, target_date)

    assert inbox_repository.get(item.id) is not None
    assert day_repository.get_by_date(target_date) is None
    engine.dispose()
