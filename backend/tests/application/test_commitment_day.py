from datetime import date
from pathlib import Path

import pytest

from src.application.commitment_day import CommitmentDayService
from src.domain.commitment_day import Capacity, ClosedPlanError
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.commitment_day_repository import SqlAlchemyCommitmentDayRepository
from src.infrastructure.database.metadata import metadata


def test_service_prevents_editing_active_and_closed_shapes(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'service.sqlite3'}")
    metadata.create_all(engine)
    service = CommitmentDayService(SqlAlchemyCommitmentDayRepository(engine))
    service.save_plan(date(2026, 7, 20), capacity=Capacity.NORMAL, primary="Главный", secondary=[])
    service.activate(date(2026, 7, 20))

    with pytest.raises(ClosedPlanError):
        service.save_plan(
            date(2026, 7, 20), capacity=Capacity.HIGH, primary="Изменить", secondary=[]
        )
    engine.dispose()
