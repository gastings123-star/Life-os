from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, delete, func, insert, select, update

from src.application.commitment_day import ResolutionCommand
from src.application.repositories import CommitmentDayRepository
from src.domain.commitment_day import (
    Capacity,
    CommitmentKind,
    CommitmentStatus,
    DailyCommitment,
    DailyPlan,
    PlanStatus,
)
from src.infrastructure.database.metadata import (
    commitment_resolutions,
    daily_commitments,
    daily_plans,
)


def _utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _load_plan(connection, plan_row) -> DailyPlan:
    rows = connection.execute(
        select(daily_commitments)
        .where(daily_commitments.c.daily_plan_id == plan_row["id"])
        .order_by(daily_commitments.c.position, daily_commitments.c.id)
    ).mappings()
    return DailyPlan(
        id=UUID(plan_row["id"]),
        date=plan_row["date"],
        capacity=Capacity(plan_row["capacity"]),
        status=PlanStatus(plan_row["status"]),
        created_at=_utc(plan_row["created_at"]),
        closed_at=_utc(plan_row["closed_at"]),
        commitments=[
            DailyCommitment(
                id=UUID(row["id"]),
                daily_plan_id=UUID(row["daily_plan_id"]),
                text=row["text"],
                kind=CommitmentKind(row["kind"]),
                status=CommitmentStatus(row["status"]),
                position=row["position"],
                created_at=_utc(row["created_at"]),
                updated_at=_utc(row["updated_at"]),
            )
            for row in rows
        ],
    )


class SqlAlchemyCommitmentDayRepository(CommitmentDayRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_date(self, day_date: date) -> DailyPlan | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(daily_plans).where(daily_plans.c.date == day_date))
                .mappings()
                .one_or_none()
            )
            return None if row is None else _load_plan(connection, row)

    def get_by_commitment_id(self, commitment_id: UUID) -> DailyPlan | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(daily_plans)
                    .join(daily_commitments)
                    .where(daily_commitments.c.id == str(commitment_id))
                )
                .mappings()
                .one_or_none()
            )
            return None if row is None else _load_plan(connection, row)

    def save_draft(self, plan: DailyPlan) -> None:
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(daily_plans.c.id).where(daily_plans.c.date == plan.date)
            ).scalar_one_or_none()
            if existing is None:
                connection.execute(
                    insert(daily_plans).values(
                        id=str(plan.id),
                        date=plan.date,
                        capacity=plan.capacity.value,
                        status=plan.status.value,
                        created_at=plan.created_at,
                        closed_at=None,
                    )
                )
            else:
                connection.execute(
                    update(daily_plans)
                    .where(daily_plans.c.id == existing)
                    .values(capacity=plan.capacity.value)
                )
                connection.execute(
                    delete(daily_commitments).where(daily_commitments.c.daily_plan_id == existing)
                )
            connection.execute(
                insert(daily_commitments),
                [self._commitment_values(item) for item in plan.commitments],
            )

    def activate(self, plan: DailyPlan) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                update(daily_plans)
                .where(daily_plans.c.id == str(plan.id))
                .values(status=plan.status.value)
            )

    def complete(self, commitment: DailyCommitment) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                update(daily_commitments)
                .where(daily_commitments.c.id == str(commitment.id))
                .values(status=commitment.status.value, updated_at=commitment.updated_at)
            )

    def close(self, plan: DailyPlan, commands: list[ResolutionCommand]) -> DailyPlan:
        now = datetime.now(UTC)
        by_id = {item.id: item for item in plan.commitments}
        with self._engine.begin() as connection:
            current_status = connection.execute(
                select(daily_plans.c.status).where(daily_plans.c.id == str(plan.id))
            ).scalar_one()
            if current_status == PlanStatus.CLOSED.value:
                row = (
                    connection.execute(select(daily_plans).where(daily_plans.c.id == str(plan.id)))
                    .mappings()
                    .one()
                )
                return _load_plan(connection, row)

            for command in commands:
                commitment = by_id[command.commitment_id]
                successor_id = None
                if command.outcome is CommitmentStatus.RENEGOTIATED:
                    successor_plan = self._get_or_create_draft(connection, command.target_date, now)
                    position = connection.execute(
                        select(func.count())
                        .select_from(daily_commitments)
                        .where(daily_commitments.c.daily_plan_id == successor_plan)
                    ).scalar_one()
                    if position >= 3:
                        from src.domain.commitment_day import InvalidCommitmentPlanError

                        raise InvalidCommitmentPlanError("Целевой день уже содержит три результата")
                    successor_id = str(uuid4())
                    successor_kind = (
                        CommitmentKind.PRIMARY if position == 0 else CommitmentKind.SECONDARY
                    )
                    connection.execute(
                        insert(daily_commitments).values(
                            id=successor_id,
                            daily_plan_id=successor_plan,
                            text=commitment.text,
                            kind=successor_kind.value,
                            status=CommitmentStatus.ACTIVE.value,
                            position=position,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                connection.execute(
                    update(daily_commitments)
                    .where(daily_commitments.c.id == str(commitment.id))
                    .values(status=command.outcome.value, updated_at=now)
                )
                connection.execute(
                    insert(commitment_resolutions).values(
                        id=str(uuid4()),
                        commitment_id=str(commitment.id),
                        outcome=command.outcome.value,
                        reason=command.reason.value if command.reason else None,
                        comment=command.comment.strip() if command.comment else None,
                        target_date=command.target_date,
                        successor_commitment_id=successor_id,
                        created_at=now,
                    )
                )
            connection.execute(
                update(daily_plans)
                .where(daily_plans.c.id == str(plan.id))
                .values(status=PlanStatus.CLOSED.value, closed_at=now)
            )
        closed = self.get_by_date(plan.date)
        assert closed is not None
        return closed

    def get_unclosed_before(self, before: date) -> list[DailyPlan]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(daily_plans)
                .where(
                    daily_plans.c.date < before,
                    daily_plans.c.status != PlanStatus.CLOSED.value,
                )
                .order_by(daily_plans.c.date)
            ).mappings()
            return [_load_plan(connection, row) for row in rows]

    def get_summary(self, date_from: date | None, date_to: date | None) -> dict:
        filters = []
        if date_from is not None:
            filters.append(daily_plans.c.date >= date_from)
        if date_to is not None:
            filters.append(daily_plans.c.date <= date_to)
        with self._engine.connect() as connection:
            plan_rows = list(connection.execute(select(daily_plans).where(*filters)).mappings())
            plan_ids = [row["id"] for row in plan_rows]
            resolution_rows = []
            if plan_ids:
                resolution_rows = list(
                    connection.execute(
                        select(commitment_resolutions)
                        .join(
                            daily_commitments,
                            commitment_resolutions.c.commitment_id == daily_commitments.c.id,
                        )
                        .where(daily_commitments.c.daily_plan_id.in_(plan_ids))
                    ).mappings()
                )
        outcomes = {
            value.value: 0
            for value in (
                CommitmentStatus.COMPLETED,
                CommitmentStatus.DROPPED,
                CommitmentStatus.RENEGOTIATED,
            )
        }
        reasons: dict[str, int] = {}
        for row in resolution_rows:
            outcomes[row["outcome"]] += 1
            if row["reason"]:
                reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
        closed = sum(row["status"] == PlanStatus.CLOSED.value for row in plan_rows)
        return {
            "date_from": min((row["date"] for row in plan_rows), default=date_from),
            "date_to": max((row["date"] for row in plan_rows), default=date_to),
            "total_planned_days": len(plan_rows),
            "total_closed_days": closed,
            "close_rate": closed / len(plan_rows) if plan_rows else 0.0,
            "commitments_by_outcome": outcomes,
            "reasons": reasons,
        }

    @staticmethod
    def _commitment_values(item: DailyCommitment) -> dict:
        return {
            "id": str(item.id),
            "daily_plan_id": str(item.daily_plan_id),
            "text": item.text,
            "kind": item.kind.value,
            "status": item.status.value,
            "position": item.position,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    @staticmethod
    def _get_or_create_draft(connection, target_date: date, now: datetime) -> str:
        plan_row = (
            connection.execute(select(daily_plans).where(daily_plans.c.date == target_date))
            .mappings()
            .one_or_none()
        )
        if plan_row is not None:
            if plan_row["status"] == PlanStatus.CLOSED.value:
                from src.domain.commitment_day import ClosedPlanError

                raise ClosedPlanError("Нельзя перенести результат в закрытый день")
            return plan_row["id"]
        plan_id = str(uuid4())
        connection.execute(
            insert(daily_plans).values(
                id=plan_id,
                date=target_date,
                capacity=Capacity.NORMAL.value,
                status=PlanStatus.DRAFT.value,
                created_at=now,
                closed_at=None,
            )
        )
        return plan_id
