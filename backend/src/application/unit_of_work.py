from typing import Protocol

from src.application.repositories import DayRepository


class UnitOfWork(Protocol):
    """Preparation point for future transaction boundaries.

    The current application service continues to use a repository directly.
    Transaction management is intentionally outside this iteration.
    """

    @property
    def day_repository(self) -> DayRepository: ...
