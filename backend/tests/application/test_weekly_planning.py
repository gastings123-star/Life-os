from datetime import date

from src.application.weekly_planning import WeeklyPlanningService, start_of_week
from src.domain.daily_planning import Day


class ReadOnlyDayRepository:
    def __init__(self, days: dict[date, Day]) -> None:
        self.days = days
        self.requested_dates: list[date] = []

    def get_day_by_date(self, day_date: date) -> Day | None:
        self.requested_dates.append(day_date)
        return self.days.get(day_date)


def test_start_of_week_returns_monday() -> None:
    assert start_of_week(date(2026, 7, 20)) == date(2026, 7, 20)
    assert start_of_week(date(2026, 7, 26)) == date(2026, 7, 20)


def test_week_always_contains_seven_days_and_empty_views_for_missing_days() -> None:
    monday = date(2026, 7, 20)
    existing_day = Day(date=date(2026, 7, 22))
    existing_day.add_action("Среда")
    repository = ReadOnlyDayRepository({existing_day.date: existing_day})
    service = WeeklyPlanningService(repository)  # type: ignore[arg-type]

    week = service.get_week(date(2026, 7, 24))

    assert week.week_start == monday
    assert len(week.days) == 7
    assert [day.date for day in week.days] == [
        date(2026, 7, 20),
        date(2026, 7, 21),
        date(2026, 7, 22),
        date(2026, 7, 23),
        date(2026, 7, 24),
        date(2026, 7, 25),
        date(2026, 7, 26),
    ]
    assert week.days[0].actions == ()
    assert [action.title for action in week.days[2].actions] == ["Среда"]
    assert repository.requested_dates == [day.date for day in week.days]
