from django.utils import timezone

from notifications.delivery import schedule_notify
from notifications.keys import NotificationPreferenceKey
from notifications.sse import publish_user_event

_VISIT_COPY: dict[str, tuple[str, str]] = {
    'scheduled': ('Nowa wizyta', 'Masz nową wizytę w kalendarzu.'),
    'approved': ('Wizyta zatwierdzona', 'Twoja wizyta została zatwierdzona.'),
    'rejected': ('Wizyta odrzucona', 'Zgłoszenie wizyty nie zostało przyjęte.'),
    'rescheduled': ('Zmiana terminu', 'Termin wizyty został zmieniony.'),
    'cancelled': ('Wizyta odwołana', 'Wizyta została odwołana.'),
}

_VISIT_SSE_TYPE: dict[str, str] = {
    'scheduled': 'visit.scheduled',
    'approved': 'visit.approved',
    'rejected': 'visit.rejected',
    'rescheduled': 'visit.rescheduled',
    'cancelled': 'visit.cancelled',
}

_REMINDER_COPY: dict[str, tuple[str, str]] = {
    '24h': ('Przypomnienie o wizycie', 'Jutro masz wizytę.'),
    '2h': ('Przypomnienie o wizycie', 'Wkrótce masz wizytę.'),
}


def publish_visit_realtime(visit: object, event: str) -> None:
    """Publikuje zdarzenie wizyty w czasie rzeczywistym (SSE) dla pacjenta i terapeuty.

    Args:
        visit (object): Obiekt wizyty.
        event (str): Nazwa zdarzenia dotyczącego wizyty (np. 'scheduled', 'approved').

    Raises:
        TypeError: Gdy visit jest None lub event nie jest napisem.
    """
    if visit is None:
        raise TypeError("Argument 'visit' nie może być None.")
    if not isinstance(event, str):
        raise TypeError('Argument event musi być typu str.')

    sse_type: str = _VISIT_SSE_TYPE[event]
    resource_id: object = visit.id
    publish_user_event(visit.patient.user_id, sse_type, resource_id=resource_id)
    publish_user_event(visit.therapist.user_id, sse_type, resource_id=resource_id)


def notify_visit_change(visit: object, event: str) -> None:
    """Wysyła powiadomienie o zmianie statusu wizyty do pacjenta oraz powiadomienie SSE.

    Args:
        visit (object): Obiekt wizyty.
        event (str): Nazwa zdarzenia (np. 'scheduled', 'cancelled').

    Raises:
        TypeError: Gdy visit jest None lub event nie jest napisem.
    """
    if visit is None:
        raise TypeError("Argument 'visit' nie może być None.")
    if not isinstance(event, str):
        raise TypeError('Argument event musi być typu str.')

    title: str
    body: str
    title, body = _VISIT_COPY[event]
    schedule_notify(
        visit.patient.user,
        NotificationPreferenceKey.VISIT_CHANGE,
        title,
        body,
        data={'type': 'visit', 'id': str(visit.id), 'event': event},
    )
    publish_visit_realtime(visit, event)


def notify_new_document(document: object) -> None:
    """Wysyła powiadomienie do pacjenta o dodaniu nowego dokumentu medycznego.

    Args:
        document (object): Obiekt dokumentu medycznego.

    Raises:
        TypeError: Gdy document jest None.
    """
    if document is None:
        raise TypeError("Argument 'document' nie może być None.")

    schedule_notify(
        document.patient.user,
        NotificationPreferenceKey.NEW_DOCUMENT,
        'Nowy dokument',
        'Dodano nowy dokument w Twojej dokumentacji.',
        data={'type': 'document', 'id': str(document.id)},
    )
    publish_document_realtime(document.patient, document.id)


def publish_document_realtime(patient: object, resource_id: object) -> None:
    """Publikuje zdarzenie w czasie rzeczywistym (SSE) o utworzeniu dokumentu dla pacjenta.

    Args:
        patient (object): Obiekt pacjenta.
        resource_id (object): Identyfikator dokumentu.

    Raises:
        TypeError: Gdy patient jest None.
    """
    if patient is None:
        raise TypeError("Argument 'patient' nie może być None.")

    publish_user_event(
        patient.user_id,
        'document.created',
        resource_id=resource_id,
    )


def notify_exercise_assigned(assignment: object) -> None:
    """Wysyła powiadomienie do pacjenta o przypisaniu nowego zestawu ćwiczeń.

    Args:
        assignment (object): Obiekt przypisania ćwiczenia.

    Raises:
        TypeError: Gdy assignment jest None.
    """
    if assignment is None:
        raise TypeError("Argument 'assignment' nie może być None.")

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


def notify_visit_reminder(visit: object, window: str) -> None:
    """Wysyła przypomnienie o nadchodzącej wizycie w określonym oknie czasowym.

    Args:
        visit (object): Obiekt wizyty.
        window (str): Okno czasowe przypomnienia ('24h' lub '2h').

    Raises:
        TypeError: Gdy visit jest None lub window nie jest napisem.
    """
    if visit is None:
        raise TypeError("Argument 'visit' nie może być None.")
    if not isinstance(window, str):
        raise TypeError('Argument window musi być typu str.')

    title: str
    body: str
    title, body = _REMINDER_COPY[window]
    schedule_notify(
        visit.patient.user,
        NotificationPreferenceKey.VISIT_REMINDER,
        title,
        body,
        data={'type': 'visit', 'id': str(visit.id), 'window': window},
        dedupe_key=f'visit-reminder:{visit.id}:{window}',
    )


def notify_today_exercises(user: object, assignment_count: int) -> None:
    """Wysyła powiadomienie przypominające o ćwiczeniach zaplanowanych na dzisiejszy dzień.

    Args:
        user (object): Obiekt użytkownika.
        assignment_count (int): Liczba przypisanych zestawów ćwiczeń na dziś.

    Raises:
        TypeError: Gdy user jest None lub assignment_count nie jest liczbą całkowitą.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(assignment_count, int):
        raise TypeError('Argument assignment_count musi być liczbą całkowitą.')

    schedule_notify(
        user,
        NotificationPreferenceKey.EXERCISE_REMINDER,
        'Ćwiczenia na dziś',
        'Masz zalecenia ćwiczeń na dziś.',
        data={'type': 'exercise', 'count': assignment_count},
        dedupe_key=f'exercise-today:{user.pk}:{timezone.localdate().isoformat()}',
    )
