from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import event, func, select

from src.application.commitment_day import CommitmentDayService, ResolutionCommand
from src.domain.commitment_day import Capacity, CommitmentStatus, ResolutionReason
from src.infrastructure.database import create_database_engine
from src.infrastructure.database.commitment_day_repository import SqlAlchemyCommitmentDayRepository
from src.infrastructure.database.metadata import commitment_resolutions, daily_commitments, metadata


def make_service(tmp_path: Path) -> tuple[CommitmentDayService, object]:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'commitments.sqlite3'}")
    metadata.create_all(engine)
    return CommitmentDayService(SqlAlchemyCommitmentDayRepository(engine)), engine


def test_full_close_creates_audited_successor_and_is_idempotent(tmp_path: Path) -> None:
    service, engine = make_service(tmp_path)
    source_date, target_date = date(2026, 7, 20), date(2026, 7, 22)
    plan = service.save_plan(
        source_date, capacity=Capacity.NORMAL, primary="Главный", secondary=["Снять", "Перенести"]
    )
    service.activate(source_date)
    service.complete(plan.commitments[0].id)
    commands = [
        ResolutionCommand(plan.commitments[0].id, CommitmentStatus.COMPLETED),
        ResolutionCommand(
            plan.commitments[1].id, CommitmentStatus.DROPPED, ResolutionReason.LOST_RELEVANCE
        ),
        ResolutionCommand(
            plan.commitments[2].id,
            CommitmentStatus.RENEGOTIATED,
            ResolutionReason.NOT_ENOUGH_TIME,
            target_date=target_date,
        ),
    ]
    closed = service.close(source_date, commands)
    again = service.close(source_date, commands)
    successor = service.get_day(target_date)

    assert closed.status.value == "closed"
    assert [item.status for item in closed.commitments] == [
        CommitmentStatus.COMPLETED,
        CommitmentStatus.DROPPED,
        CommitmentStatus.RENEGOTIATED,
    ]
    assert again.status.value == "closed"
    assert successor is not None and successor.commitments[0].text == "Перенести"
    with engine.connect() as connection:
        assert (
            connection.execute(
                select(func.count()).select_from(commitment_resolutions)
            ).scalar_one()
            == 3
        )
        link = connection.execute(
            select(commitment_resolutions.c.successor_commitment_id).where(
                commitment_resolutions.c.commitment_id == str(plan.commitments[2].id)
            )
        ).scalar_one()
        assert link == str(successor.commitments[0].id)
    engine.dispose()


def test_close_rolls_back_everything_on_database_error(tmp_path: Path) -> None:
    service, engine = make_service(tmp_path)
    source_date = date(2026, 7, 20)
    plan = service.save_plan(
        source_date, capacity=Capacity.NORMAL, primary="Главный", secondary=["Перенести"]
    )
    service.activate(source_date)
    commands = [
        ResolutionCommand(plan.commitments[0].id, CommitmentStatus.COMPLETED),
        ResolutionCommand(
            plan.commitments[1].id,
            CommitmentStatus.RENEGOTIATED,
            ResolutionReason.NOT_ENOUGH_TIME,
            target_date=date(2026, 7, 22),
        ),
    ]

    @event.listens_for(engine, "before_cursor_execute")
    def fail_resolution(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith("INSERT INTO commitment_resolutions"):
            raise RuntimeError("simulated failure")

    with pytest.raises(RuntimeError):
        service.close(source_date, commands)
    event.remove(engine, "before_cursor_execute", fail_resolution)
    reloaded = service.get_day(source_date)
    assert reloaded is not None and reloaded.status.value == "active"
    assert service.get_day(date(2026, 7, 22)) is None
    with engine.connect() as connection:
        assert (
            connection.execute(select(func.count()).select_from(daily_commitments)).scalar_one()
            == 2
        )
    engine.dispose()
