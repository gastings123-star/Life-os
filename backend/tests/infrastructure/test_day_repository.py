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
    engine.dispose()
