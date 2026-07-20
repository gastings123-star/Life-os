from datetime import date

import pytest

from src.domain.daily_planning import Day, EmptyActionTitleError


def test_action_title_is_normalized() -> None:
    day = Day(date=date(2026, 7, 20))

    action = day.add_action("  Prepare   meeting plan  ")

    assert action.title == "Prepare meeting plan"
    assert action.day_id == day.id


def test_empty_action_title_is_rejected() -> None:
    day = Day(date=date(2026, 7, 20))

    with pytest.raises(EmptyActionTitleError):
        day.add_action("   \n  ")
