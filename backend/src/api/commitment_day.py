from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.dependencies import get_commitment_day_service
from src.application.commitment_day import CommitmentDayService, ResolutionCommand
from src.domain.commitment_day import (
    Capacity,
    CommitmentKind,
    CommitmentStatus,
    DailyPlan,
    PlanStatus,
    ResolutionReason,
)

router = APIRouter(prefix="/commitment-days", tags=["commitment-day-experiment"])
commitments_router = APIRouter(prefix="/commitments", tags=["commitment-day-experiment"])
experiments_router = APIRouter(prefix="/experiments/commitment-day", tags=["experiments"])
ServiceDependency = Annotated[CommitmentDayService, Depends(get_commitment_day_service)]


class CommitmentResponse(BaseModel):
    id: UUID
    text: str
    kind: CommitmentKind
    status: CommitmentStatus
    position: int
    created_at: str
    updated_at: str


class CommitmentDayResponse(BaseModel):
    date: date
    status: PlanStatus | Literal["empty"]
    capacity: Capacity | None
    commitments: list[CommitmentResponse]
    closed_at: str | None = None


class PlanRequest(BaseModel):
    capacity: Capacity
    primary: str = Field(min_length=1, max_length=500)
    secondary: list[str] = Field(default_factory=list, max_length=2)


class ResolutionRequest(BaseModel):
    commitment_id: UUID
    outcome: CommitmentStatus
    reason: ResolutionReason | None = None
    comment: str | None = Field(default=None, max_length=1000)
    target_date: date | None = None


class CloseRequest(BaseModel):
    resolutions: list[ResolutionRequest]


class SummaryResponse(BaseModel):
    date_from: date | None
    date_to: date | None
    total_planned_days: int
    total_closed_days: int
    close_rate: float
    commitments_by_outcome: dict[str, int]
    reasons: dict[str, int]


def serialize_plan(plan: DailyPlan | None, day_date: date) -> CommitmentDayResponse:
    if plan is None:
        return CommitmentDayResponse(
            date=day_date, status="empty", capacity=None, commitments=[], closed_at=None
        )
    return CommitmentDayResponse(
        date=plan.date,
        status=plan.status,
        capacity=plan.capacity,
        commitments=[
            CommitmentResponse(
                id=item.id,
                text=item.text,
                kind=item.kind,
                status=item.status,
                position=item.position,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat(),
            )
            for item in plan.commitments
        ],
        closed_at=plan.closed_at.isoformat() if plan.closed_at else None,
    )


@router.get("/unclosed", response_model=list[CommitmentDayResponse])
def get_unclosed(before: date, service: ServiceDependency) -> list[CommitmentDayResponse]:
    return [serialize_plan(plan, plan.date) for plan in service.get_unclosed(before)]


@router.get("/{day_date}", response_model=CommitmentDayResponse)
def get_commitment_day(day_date: date, service: ServiceDependency) -> CommitmentDayResponse:
    return serialize_plan(service.get_day(day_date), day_date)


@router.put("/{day_date}/plan", response_model=CommitmentDayResponse)
def save_plan(
    day_date: date, request: PlanRequest, service: ServiceDependency
) -> CommitmentDayResponse:
    plan = service.save_plan(
        day_date,
        capacity=request.capacity,
        primary=request.primary,
        secondary=request.secondary,
    )
    return serialize_plan(plan, day_date)


@router.post("/{day_date}/activate", response_model=CommitmentDayResponse)
def activate_plan(day_date: date, service: ServiceDependency) -> CommitmentDayResponse:
    return serialize_plan(service.activate(day_date), day_date)


@commitments_router.post("/{commitment_id}/complete", response_model=CommitmentDayResponse)
def complete_commitment(commitment_id: UUID, service: ServiceDependency) -> CommitmentDayResponse:
    plan = service.complete(commitment_id)
    return serialize_plan(plan, plan.date)


@router.post("/{day_date}/close", response_model=CommitmentDayResponse)
def close_day(
    day_date: date, request: CloseRequest, service: ServiceDependency
) -> CommitmentDayResponse:
    commands = [
        ResolutionCommand(
            commitment_id=item.commitment_id,
            outcome=item.outcome,
            reason=item.reason,
            comment=item.comment,
            target_date=item.target_date,
        )
        for item in request.resolutions
    ]
    return serialize_plan(service.close(day_date, commands), day_date)


@experiments_router.get("/summary", response_model=SummaryResponse)
def get_summary(
    service: ServiceDependency,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    return service.get_summary(date_from, date_to)
