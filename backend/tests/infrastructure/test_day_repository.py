from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.application.daily_planning import DailyPlanningService
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.day_repository import SqlAlchemyDayRepository
from src.infrastructure.database.metadata import metadata


def test_action_is_persisted_and_returned_after_reloading(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'daily-planning.sqlite3'}")
    metadata.create_all(engine)
    service = DailyPlanningService(SqlAlchemyDayRepository(engine))
    day_date = date(2026, 7, 20)

    created_day, created_action = service.add_action(day_date, "Prepare meeting plan")
    reloaded_day = service.get_or_create_day(day_date)

    assert reloaded_day.id == created_day.id
    assert [action.id for action in reloaded_day.actions] == [created_action.id]
    assert [action.title for action in reloaded_day.actions] == ["Prepare meeting plan"]
    assert reloaded_day.actions[0].completed is False
    engine.dispose()


def test_action_lifecycle_is_persisted(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'action-lifecycle.sqlite3'}")
    metadata.create_all(engine)
    service = DailyPlanningService(SqlAlchemyDayRepository(engine))
    day_date = date(2026, 7, 20)
    _, action = service.add_action(day_date, "Initial title")

    service.update_action(
        action.id,
        title="  Updated   title ",
        completed=True,
    )
    updated_day = service.get_or_create_day(day_date)

    assert updated_day.actions[0].title == "Updated title"
    assert updated_day.actions[0].completed is True

    service.delete_action(action.id)
    reloaded_day = service.get_or_create_day(day_date)

    assert reloaded_day.actions == []
    engine.dispose()


def test_action_moves_between_days_without_changing_identity_or_creation_time(
    tmp_path: Path,
) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'move-action.sqlite3'}")
    metadata.create_all(engine)
    service = DailyPlanningService(SqlAlchemyDayRepository(engine))
    source_date = date(2026, 7, 20)
    target_date = date(2026, 7, 28)
    source_day, action = service.add_action(source_date, "Перенести")
    original_created_at = action.created_at

    moved = service.move_action(action.id, target_date)
    reloaded_source = service.get_or_create_day(source_date)
    reloaded_target = service.get_or_create_day(target_date)

    assert moved.id == action.id
    assert moved.created_at == original_created_at
    assert moved.day_id == reloaded_target.id
    assert reloaded_source.id == source_day.id
    assert reloaded_source.actions == []
    assert [target_action.id for target_action in reloaded_target.actions] == [action.id]
    assert reloaded_target.actions[0].created_at == original_created_at
    engine.dispose()


def test_failed_action_move_rolls_back_target_day_creation(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'move-rollback.sqlite3'}")
    metadata.create_all(engine)
    service = DailyPlanningService(SqlAlchemyDayRepository(engine))
    source_date = date(2026, 7, 20)
    target_date = date(2026, 7, 28)
    _, action = service.add_action(source_date, "Остаться в исходном дне")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER reject_action_move BEFORE UPDATE OF day_id ON actions "
                "BEGIN SELECT RAISE(ABORT, 'rejected'); END"
            )
        )

    with pytest.raises(DBAPIError):
        service.move_action(action.id, target_date)

    assert [item.id for item in service.get_or_create_day(source_date).actions] == [action.id]
    repository = SqlAlchemyDayRepository(engine)
    assert repository.get_by_date(target_date) is None
    engine.dispose()
