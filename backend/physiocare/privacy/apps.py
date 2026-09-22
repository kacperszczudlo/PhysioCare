from django.apps import AppConfig


class PrivacyConfig(AppConfig):
    """Konfiguracja aplikacji Django privacy."""

    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'privacy'

