from django.utils import timezone

from notifications.delivery import schedule_notify
from notifications.keys import NotificationPreferenceKey

_VISIT_COPY = {
    'scheduled': ('Nowa wizyta', 'Masz nową wizytę w kalendarzu.'),
    'approved': ('Wizyta zatwierdzona', 'Twoja wizyta została zatwierdzona.'),
    'rejected': ('Wizyta odrzucona', 'Zgłoszenie wizyty nie zostało przyjęte.'),
    'rescheduled': ('Zmiana terminu', 'Termin wizyty został zmieniony.'),
    'cancelled': ('Wizyta odwołana', 'Wizyta została odwołana.'),
}

_REMINDER_COPY = {
    '24h': ('Przypomnienie o wizycie', 'Jutro masz wizytę.'),
    '2h': ('Przypomnienie o wizycie', 'Wkrótce masz wizytę.'),
}


def notify_visit_change(visit, event: str) -> None:
    title, body = _VISIT_COPY[event]
    schedule_notify(
        visit.patient.user,
        NotificationPreferenceKey.VISIT_CHANGE,
        title,
        body,
        data={'type': 'visit', 'id': str(visit.id), 'event': event},
    )


def notify_new_document(document) -> None:
    schedule_notify(
        document.patient.user,
        NotificationPreferenceKey.NEW_DOCUMENT,
        'Nowy dokument',
        'Dodano nowy dokument w Twojej dokumentacji.',
        data={'type': 'document', 'id': str(document.id)},
    )


def notify_exercise_assigned(assignment) -> None:
    schedule_notify(
        assignment.patient.user,
        NotificationPreferenceKey.EXERCISE_REMINDER,
        'Nowe ćwiczenia',
        'Masz nowe zalecenia ćwiczeń.',
        data={'type': 'exercise', 'id': str(assignment.id)},
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
