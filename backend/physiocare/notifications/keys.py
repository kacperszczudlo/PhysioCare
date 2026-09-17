from django.db import models


class NotificationPreferenceKey(models.TextChoices):
    """Klucze typów i kategorii preferencji powiadomień."""

    VISIT_REMINDER: str = 'visit_reminder', 'Przypomnienia o wizytach'
    VISIT_CHANGE: str = 'visit_change', 'Zmiany terminów'
    WAITLIST: str = 'waitlist', 'Lista rezerwowa'
    EXERCISE_REMINDER: str = 'exercise_reminder', 'Przypomnienia o ćwiczeniach'
    NEW_DOCUMENT: str = 'new_document', 'Nowe dokumenty'


CANONICAL_PREF_KEYS: tuple[str, ...] = tuple(NotificationPreferenceKey.values)


def get_canonical_pref_keys() -> tuple[str, ...]:
    """Zwraca krotkę wszystkich kanonicznych kluczy preferencji powiadomień.

    Returns:
        tuple[str, ...]: Krotka z unikalnymi kluczami preferencji.
    """
    return CANONICAL_PREF_KEYS


def is_valid_pref_key(key: str) -> bool:
    """Sprawdza, czy podany ciąg znaków jest prawidłowym kluczem preferencji.

    Args:
        key (str): Klucz do zweryfikowania.

    Returns:
        bool: True jeśli klucz jest prawidłowy, False w przeciwnym razie.

    Raises:
        TypeError: Gdy argument key nie jest napisem.
    """
    if not isinstance(key, str):
        raise TypeError("Argument 'key' musi być typu str.")

    return key in CANONICAL_PREF_KEYS
