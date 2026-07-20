from datetime import date

import pytest

from src.domain.commitment_day import (
    Capacity,
    CommitmentKind,
    CommitmentStatus,
    DailyCommitment,
    DailyPlan,
    InvalidCommitmentPlanError,
    InvalidResolutionError,
    ResolutionReason,
    validate_resolution,
)


def test_plan_accepts_one_primary_and_two_secondary() -> None:
    plan = DailyPlan.draft(
        day_date=date(2026, 7, 20),
        capacity=Capacity.NORMAL,
        primary="  Результат   готов ",
        secondary=["Дополнительный 1", "Дополнительный 2"],
    )
    assert [item.kind for item in plan.commitments] == [
        CommitmentKind.PRIMARY,
        CommitmentKind.SECONDARY,
        CommitmentKind.SECONDARY,
    ]
    assert plan.commitments[0].text == "Результат готов"


@pytest.mark.parametrize("secondary", [["1", "2", "3"], [" "]])
def test_plan_rejects_invalid_commitments(secondary: list[str]) -> None:
    with pytest.raises(InvalidCommitmentPlanError):
        DailyPlan.draft(
            day_date=date(2026, 7, 20),
            capacity=Capacity.LOW,
            primary="Главный",
            secondary=secondary,
        )


def test_shape_rejects_second_primary() -> None:
    plan = DailyPlan.draft(day_date=date(2026, 7, 20), capacity=Capacity.HIGH, primary="Один")
    plan.commitments.append(
        DailyCommitment(
            daily_plan_id=plan.id,
            text="Два",
            kind=CommitmentKind.PRIMARY,
            position=1,
        )
    )
    with pytest.raises(InvalidCommitmentPlanError):
        plan.validate_shape()


def test_resolution_requires_reason_target_and_other_comment() -> None:
    plan = DailyPlan.draft(day_date=date(2026, 7, 20), capacity=Capacity.NORMAL, primary="Главный")
    item = plan.commitments[0]
    with pytest.raises(InvalidResolutionError):
        validate_resolution(
            plan_date=plan.date,
            commitment=item,
            outcome=CommitmentStatus.DROPPED,
            reason=None,
            comment=None,
            target_date=None,
        )
    with pytest.raises(InvalidResolutionError):
        validate_resolution(
            plan_date=plan.date,
            commitment=item,
            outcome=CommitmentStatus.RENEGOTIATED,
            reason=ResolutionReason.NOT_ENOUGH_TIME,
            comment=None,
            target_date=None,
        )
    with pytest.raises(InvalidResolutionError):
        validate_resolution(
            plan_date=plan.date,
            commitment=item,
            outcome=CommitmentStatus.DROPPED,
            reason=ResolutionReason.OTHER,
            comment=" ",
            target_date=None,
        )
