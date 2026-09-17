from django.apps import AppConfig


class ExercisesConfig(AppConfig):
    """Konfiguracja aplikacji ćwiczeń dla Django."""

    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'exercises'

