from django.apps import AppConfig


class TreatmentConfig(AppConfig):
    """Konfiguracja aplikacji Django treatment odpowiadającej za leczenie i dokumentację medyczną."""

    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'treatment'

