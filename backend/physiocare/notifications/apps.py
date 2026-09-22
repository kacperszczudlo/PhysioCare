from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Konfiguracja aplikacji Django notifications."""

    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'notifications'

