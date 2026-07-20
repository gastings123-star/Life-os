from datetime import date

import pytest

from src.domain.daily_planning import Day, EmptyActionTitleError


def test_action_title_is_normalized() -> None:
    day = Day(date=date(2026, 7, 20))

    action = day.add_action("  Prepare   meeting plan  ")

    assert action.title == "Prepare meeting plan"
    assert action.day_id == day.id
    assert action.completed is False


def test_empty_action_title_is_rejected() -> None:
    day = Day(date=date(2026, 7, 20))

    with pytest.raises(EmptyActionTitleError):
        day.add_action("   \n  ")


def test_action_can_be_renamed_with_normalization() -> None:
    action = Day(date=date(2026, 7, 20)).add_action("Initial title")

    action.rename("  Updated   title ")

    assert action.title == "Updated title"

    with pytest.raises(EmptyActionTitleError):
        action.rename("  \n ")


def test_action_can_be_completed_and_returned_to_work() -> None:
    action = Day(date=date(2026, 7, 20)).add_action("Prepare meeting plan")

    action.set_completed(True)
    assert action.completed is True

    action.set_completed(False)
    assert action.completed is False
