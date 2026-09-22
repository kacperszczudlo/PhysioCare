import pytest

from notifications.events import (
    notify_exercise_assigned,
    notify_new_document,
    notify_today_exercises,
    notify_visit_change,
    notify_visit_reminder,
    publish_document_realtime,
    publish_visit_realtime,
)


def test_events_type_errors() -> None:
    """Sprawdza rzucanie TypeError przy przekazaniu nieprawidłowych typów argumentów w events.py."""
    # Act
    with pytest.raises(TypeError, match="Argument 'visit' nie może być None."):
        publish_visit_realtime(None, "scheduled")

    with pytest.raises(TypeError, match="Argument event musi być typu str."):
        publish_visit_realtime(object(), 123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Argument 'visit' nie może być None."):
        notify_visit_change(None, "scheduled")

    with pytest.raises(TypeError, match="Argument 'document' nie może być None."):
        notify_new_document(None)

    with pytest.raises(TypeError, match="Argument 'patient' nie może być None."):
        publish_document_realtime(None, "doc-123")

    with pytest.raises(TypeError, match="Argument 'assignment' nie może być None."):
        notify_exercise_assigned(None)

    with pytest.raises(TypeError, match="Argument 'visit' nie może być None."):
        notify_visit_reminder(None, "24h")

    with pytest.raises(TypeError, match="Argument window musi być typu str."):
        notify_visit_reminder(object(), 100)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Argument 'user' nie może być None."):
        notify_today_exercises(None, 2)

    with pytest.raises(TypeError, match="Argument assignment_count musi być liczbą całkowitą."):
        notify_today_exercises(object(), "invalid")  # type: ignore[arg-type]

