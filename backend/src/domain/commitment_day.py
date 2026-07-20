from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class Capacity(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class CommitmentKind(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class CommitmentStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    RENEGOTIATED = "renegotiated"


class ResolutionReason(StrEnum):
    OVERESTIMATED_CAPACITY = "overestimated_capacity"
    NOT_ENOUGH_TIME = "not_enough_time"
    HIGHER_PRIORITY_APPEARED = "higher_priority_appeared"
    SCOPE_WAS_TOO_LARGE = "scope_was_too_large"
    LOST_RELEVANCE = "lost_relevance"
    BLOCKED_BY_EXTERNAL_DEPENDENCY = "blocked_by_external_dependency"
    OTHER = "other"


class CommitmentDayError(ValueError):
    code = "commitment_day_invalid"


class InvalidCommitmentPlanError(CommitmentDayError):
    code = "invalid_commitment_plan"


class ClosedPlanError(CommitmentDayError):
    code = "commitment_day_closed"


class InvalidResolutionError(CommitmentDayError):
    code = "invalid_commitment_resolution"


def normalize_commitment_text(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise InvalidCommitmentPlanError("Результат не может быть пустым")
    return normalized


@dataclass(slots=True)
class DailyCommitment:
    daily_plan_id: UUID
    text: str
    kind: CommitmentKind
    position: int
    id: UUID = field(default_factory=uuid4)
    status: CommitmentStatus = CommitmentStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.text = normalize_commitment_text(self.text)
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("Commitment timestamps must include timezone information")

    def complete(self, *, now: datetime | None = None) -> None:
        if self.status not in (CommitmentStatus.ACTIVE, CommitmentStatus.COMPLETED):
            raise InvalidResolutionError("Завершённое обязательство нельзя изменить")
        self.status = CommitmentStatus.COMPLETED
        self.updated_at = now or datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class CommitmentResolution:
    commitment_id: UUID
    outcome: CommitmentStatus
    reason: ResolutionReason | None = None
    comment: str | None = None
    target_date: date | None = None
    successor_commitment_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class DailyPlan:
    date: date
    capacity: Capacity
    id: UUID = field(default_factory=uuid4)
    status: PlanStatus = PlanStatus.DRAFT
    commitments: list[DailyCommitment] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None

    @classmethod
    def draft(
        cls,
        *,
        day_date: date,
        capacity: Capacity,
        primary: str,
        secondary: list[str] | None = None,
    ) -> "DailyPlan":
        plan = cls(date=day_date, capacity=capacity)
        plan.replace_commitments(primary=primary, secondary=secondary or [])
        return plan

    def replace_commitments(self, *, primary: str, secondary: list[str]) -> None:
        if self.status is not PlanStatus.DRAFT:
            raise ClosedPlanError("Изменять можно только черновик плана")
        if len(secondary) > 2:
            raise InvalidCommitmentPlanError("Допустимо не более двух дополнительных результатов")
        primary_text = normalize_commitment_text(primary)
        secondary_texts = [normalize_commitment_text(value) for value in secondary]
        self.commitments = [
            DailyCommitment(
                daily_plan_id=self.id,
                text=primary_text,
                kind=CommitmentKind.PRIMARY,
                position=0,
            ),
            *[
                DailyCommitment(
                    daily_plan_id=self.id,
                    text=text,
                    kind=CommitmentKind.SECONDARY,
                    position=index,
                )
                for index, text in enumerate(secondary_texts, start=1)
            ],
        ]
        self.validate_shape()

    def validate_shape(self) -> None:
        primary_count = sum(item.kind is CommitmentKind.PRIMARY for item in self.commitments)
        secondary_count = sum(item.kind is CommitmentKind.SECONDARY for item in self.commitments)
        if primary_count != 1:
            raise InvalidCommitmentPlanError("План должен содержать один главный результат")
        if secondary_count > 2:
            raise InvalidCommitmentPlanError("Допустимо не более двух дополнительных результатов")

    def activate(self) -> None:
        if self.status is not PlanStatus.DRAFT:
            raise InvalidCommitmentPlanError("Активировать можно только черновик плана")
        self.validate_shape()
        self.status = PlanStatus.ACTIVE


def validate_resolution(
    *,
    plan_date: date,
    commitment: DailyCommitment,
    outcome: CommitmentStatus,
    reason: ResolutionReason | None,
    comment: str | None,
    target_date: date | None,
) -> None:
    if outcome not in (
        CommitmentStatus.COMPLETED,
        CommitmentStatus.DROPPED,
        CommitmentStatus.RENEGOTIATED,
    ):
        raise InvalidResolutionError("Недопустимый итог обязательства")
    if outcome is CommitmentStatus.COMPLETED:
        if reason is not None or comment is not None or target_date is not None:
            raise InvalidResolutionError(
                "Для выполненного результата не нужны причина или новая дата"
            )
        return
    if reason is None:
        raise InvalidResolutionError("Для снятия или пересмотра обязательна причина")
    if reason is ResolutionReason.OTHER and not (comment and comment.strip()):
        raise InvalidResolutionError("Для причины other обязателен комментарий")
    if outcome is CommitmentStatus.RENEGOTIATED:
        if target_date is None:
            raise InvalidResolutionError("Для пересмотра обязательна новая дата")
        if target_date < plan_date:
            raise InvalidResolutionError("Новая дата не может быть раньше исходной")
    elif target_date is not None:
        raise InvalidResolutionError("Новая дата допустима только при пересмотре")
