from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.application.repositories import CommitmentDayRepository
from src.domain.commitment_day import (
    Capacity,
    CommitmentStatus,
    DailyPlan,
    PlanStatus,
    ResolutionReason,
    validate_resolution,
)


class CommitmentDayNotFoundError(LookupError):
    pass


class CommitmentNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class ResolutionCommand:
    commitment_id: UUID
    outcome: CommitmentStatus
    reason: ResolutionReason | None = None
    comment: str | None = None
    target_date: date | None = None


class CommitmentDayService:
    def __init__(self, repository: CommitmentDayRepository) -> None:
        self._repository = repository

    def get_day(self, day_date: date) -> DailyPlan | None:
        return self._repository.get_by_date(day_date)

    def save_plan(
        self,
        day_date: date,
        *,
        capacity: Capacity,
        primary: str,
        secondary: list[str],
    ) -> DailyPlan:
        plan = self._repository.get_by_date(day_date)
        if plan is None:
            plan = DailyPlan.draft(
                day_date=day_date,
                capacity=capacity,
                primary=primary,
                secondary=secondary,
            )
        else:
            plan.capacity = capacity
            plan.replace_commitments(primary=primary, secondary=secondary)
        self._repository.save_draft(plan)
        return plan

    def activate(self, day_date: date) -> DailyPlan:
        plan = self._require_day(day_date)
        plan.activate()
        self._repository.activate(plan)
        return plan

    def complete(self, commitment_id: UUID) -> DailyPlan:
        plan = self._repository.get_by_commitment_id(commitment_id)
        if plan is None:
            raise CommitmentNotFoundError(str(commitment_id))
        if plan.status is PlanStatus.CLOSED:
            from src.domain.commitment_day import ClosedPlanError

            raise ClosedPlanError("Закрытый день нельзя изменить")
        if plan.status is not PlanStatus.ACTIVE:
            from src.domain.commitment_day import InvalidCommitmentPlanError

            raise InvalidCommitmentPlanError("Отмечать результат можно только в активном дне")
        commitment = next(item for item in plan.commitments if item.id == commitment_id)
        commitment.complete()
        self._repository.complete(commitment)
        return plan

    def close(self, day_date: date, commands: list[ResolutionCommand]) -> DailyPlan:
        plan = self._require_day(day_date)
        if plan.status is PlanStatus.CLOSED:
            return plan
        if plan.status is not PlanStatus.ACTIVE:
            from src.domain.commitment_day import InvalidResolutionError

            raise InvalidResolutionError("Закрыть можно только активный план")
        by_id = {item.id: item for item in plan.commitments}
        if len(commands) != len(by_id) or {item.commitment_id for item in commands} != set(by_id):
            from src.domain.commitment_day import InvalidResolutionError

            raise InvalidResolutionError("Нужен итог для каждого обязательства")
        for command in commands:
            validate_resolution(
                plan_date=plan.date,
                commitment=by_id[command.commitment_id],
                outcome=command.outcome,
                reason=command.reason,
                comment=command.comment,
                target_date=command.target_date,
            )
        return self._repository.close(plan, commands)

    def get_unclosed(self, before: date) -> list[DailyPlan]:
        return self._repository.get_unclosed_before(before)

    def get_summary(self, date_from: date | None, date_to: date | None) -> dict:
        return self._repository.get_summary(date_from, date_to)

    def _require_day(self, day_date: date) -> DailyPlan:
        plan = self._repository.get_by_date(day_date)
        if plan is None:
            raise CommitmentDayNotFoundError(day_date.isoformat())
        return plan
