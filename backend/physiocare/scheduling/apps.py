from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    """Konfiguracja aplikacji scheduling w Django.

    Przechowuje konfigurację modułu harmonogramu i wizyt.
    """

    name: str = 'scheduling'

