from django.db import models


class NotificationPreferenceKey(models.TextChoices):
    VISIT_REMINDER = 'visit_reminder', 'Przypomnienia o wizytach'
    VISIT_CHANGE = 'visit_change', 'Zmiany terminów'
    WAITLIST = 'waitlist', 'Lista rezerwowa'
    EXERCISE_REMINDER = 'exercise_reminder', 'Przypomnienia o ćwiczeniach'
    NEW_DOCUMENT = 'new_document', 'Nowe dokumenty'


CANONICAL_PREF_KEYS = tuple(NotificationPreferenceKey.values)
