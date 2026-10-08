from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    """Konfiguracja aplikacji administration dla panelu administracyjnego."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'administration'
    verbose_name = 'Zarządzanie i Administracja'
