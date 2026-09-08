from django.utils import timezone

from notifications.delivery import schedule_notify
from notifications.keys import NotificationPreferenceKey
from notifications.sse import publish_user_event

_VISIT_COPY = {
    'scheduled': ('Nowa wizyta', 'Masz nową wizytę w kalendarzu.'),
    'approved': ('Wizyta zatwierdzona', 'Twoja wizyta została zatwierdzona.'),
    'rejected': ('Wizyta odrzucona', 'Zgłoszenie wizyty nie zostało przyjęte.'),
    'rescheduled': ('Zmiana terminu', 'Termin wizyty został zmieniony.'),
    'cancelled': ('Wizyta odwołana', 'Wizyta została odwołana.'),
}

_VISIT_SSE_TYPE = {
    'scheduled': 'visit.scheduled',
    'approved': 'visit.approved',
    'rejected': 'visit.rejected',
    'rescheduled': 'visit.rescheduled',
    'cancelled': 'visit.cancelled',
}

_REMINDER_COPY = {
    '24h': ('Przypomnienie o wizycie', 'Jutro masz wizytę.'),
    '2h': ('Przypomnienie o wizycie', 'Wkrótce masz wizytę.'),
}


def publish_visit_realtime(visit, event: str) -> None:
    """SSE to patient + therapist (UI sync). Independent of push/email prefs."""
    sse_type = _VISIT_SSE_TYPE[event]
    resource_id = visit.id
    publish_user_event(visit.patient.user_id, sse_type, resource_id=resource_id)
    publish_user_event(visit.therapist.user_id, sse_type, resource_id=resource_id)


def notify_visit_change(visit, event: str) -> None:
    title, body = _VISIT_COPY[event]
    schedule_notify(
        visit.patient.user,
        NotificationPreferenceKey.VISIT_CHANGE,
        title,
        body,
        data={'type': 'visit', 'id': str(visit.id), 'event': event},
    )
    publish_visit_realtime(visit, event)


def notify_new_document(document) -> None:
    schedule_notify(
        document.patient.user,
        NotificationPreferenceKey.NEW_DOCUMENT,
        'Nowy dokument',
        'Dodano nowy dokument w Twojej dokumentacji.',
        data={'type': 'document', 'id': str(document.id)},
    )
    publish_document_realtime(document.patient, document.id)


def publish_document_realtime(patient, resource_id) -> None:
    """SSE to patient for documentation mailbox (PDF or clinical entry)."""
    publish_user_event(
        patient.user_id,
        'document.created',
        resource_id=resource_id,
    )


def notify_exercise_assigned(assignment) -> None:
    schedule_notify(
        assignment.patient.user,
        NotificationPreferenceKey.EXERCISE_REMINDER,
        'Nowe ćwiczenia',
        'Masz nowe zalecenia ćwiczeń.',
        data={'type': 'exercise', 'id': str(assignment.id)},
    )
    publish_user_event(
        assignment.patient.user_id,
        'exercise.assigned',
        resource_id=assignment.id,
    )


def notify_visit_reminder(visit, window: str) -> None:
    title, body = _REMINDER_COPY[window]
    schedule_notify(
        visit.patient.user,
        NotificationPreferenceKey.VISIT_REMINDER,
        title,
        body,
        data={'type': 'visit', 'id': str(visit.id), 'window': window},
        dedupe_key=f'visit-reminder:{visit.id}:{window}',
    )


def notify_today_exercises(user, assignment_count: int) -> None:
    schedule_notify(
        user,
        NotificationPreferenceKey.EXERCISE_REMINDER,
        'Ćwiczenia na dziś',
        'Masz zalecenia ćwiczeń na dziś.',
        data={'type': 'exercise', 'count': assignment_count},
        dedupe_key=f'exercise-today:{user.pk}:{timezone.localdate().isoformat()}',
    )
