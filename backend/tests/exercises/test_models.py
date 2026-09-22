from datetime import date, timedelta

import pytest

from exercises.models import CategoryKind, ExerciseAssignment, ExerciseCategory


@pytest.mark.django_db
def test_exercise_category_matches_kind() -> None:
    """Sprawdza działanie metody matches_kind oraz weryfikację typów."""
    # Arrange
    cat: ExerciseCategory = ExerciseCategory(name="Wzmacnianie", kind=CategoryKind.TYPE, slug="wzmacnianie")
    # Assert
    assert cat.matches_kind("TYPE") is True
    assert cat.matches_kind("REGION") is False
    # Act

    with pytest.raises(TypeError, match="Argument 'target_kind' musi być typu str."):
        cat.matches_kind(123)  # type: ignore[arg-type]


@pytest.mark.django_db
def test_exercise_assignment_is_active_on() -> None:
    """Sprawdza działanie metody is_active_on oraz rzucanie TypeError."""
    # Arrange
    today: date = date.today()
    assignment: ExerciseAssignment = ExerciseAssignment(
        start_date=today - timedelta(days=2),
        end_date=today + timedelta(days=2),
    )

    # Assert
    assert assignment.is_active_on(today) is True
    assert assignment.is_active_on(today - timedelta(days=5)) is False
    # Act

    with pytest.raises(TypeError, match="Argument 'target_date' musi być instancją datetime.date."):
        assignment.is_active_on("2026-09-17")  # type: ignore[arg-type]

