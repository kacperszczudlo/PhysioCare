from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Konfiguracja aplikacji reviews."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'

    def ready(self) -> None:
        """Rejestruje sygnały aplikacji reviews po jej załadowaniu."""
        import reviews.signals  # noqa: F401
