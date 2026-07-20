from datetime import date
from pathlib import Path

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
