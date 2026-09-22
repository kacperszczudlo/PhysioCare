from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Konfiguracja aplikacji Django documents."""

    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'documents'

