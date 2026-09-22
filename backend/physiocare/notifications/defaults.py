from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import NotificationPreference


def ensure_default_preferences(user) -> None:
    """Zapewnia obecność domyślnych preferencji powiadomień dla podanego użytkownika.

    Args:
        user: Obiekt użytkownika, dla którego tworzone są brakujące preferencje.
    """
    existing = set(
        NotificationPreference.objects.filter(user=user).values_list(
            'pref_key',
            flat=True,
        )
    )
    missing = [
        NotificationPreference(user=user, pref_key=key, enabled=True)
        for key in CANONICAL_PREF_KEYS
        if key not in existing
    ]
    if missing:
        NotificationPreference.objects.bulk_create(missing)
