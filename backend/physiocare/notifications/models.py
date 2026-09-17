from django.conf import settings
from django.db import models

from core.models import TimestampedModel, TimestampedUpdatedModel, UUIDModel
from notifications.keys import NotificationPreferenceKey


class DevicePlatform(models.TextChoices):
    """Wybór platformy urządzenia mobilnego."""

    IOS: str = 'ios', 'iOS'
    ANDROID: str = 'android', 'Android'
    UNKNOWN: str = 'unknown', 'Nieznana'


class DeliveryChannel(models.TextChoices):
    """Kanał dostarczenia powiadomienia."""

    PUSH: str = 'push', 'Push'
    EMAIL: str = 'email', 'E-mail'
    NONE: str = 'none', 'Brak'


class DeliveryStatus(models.TextChoices):
    """Status wysyłki powiadomienia."""

    SENT: str = 'sent', 'Wysłane'
    SKIPPED: str = 'skipped', 'Pominięte'
    FAILED: str = 'failed', 'Błąd'


class NotificationPreference(UUIDModel):
    """Model przechowujący indywidualne preferencje powiadomień użytkownika."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    pref_key = models.CharField(
        max_length=50,
        choices=NotificationPreferenceKey.choices,
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        """Metadane modelu NotificationPreference."""

        db_table: str = 'notification_preferences'
        constraints: list[object] = [
            models.UniqueConstraint(
                fields=['user', 'pref_key'],
                name='uniq_notification_pref_user_key',
            ),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową preferencji powiadomienia.

        Returns:
            str: Napis w formacie 'email - klucz_preferencji'.
        """
        return f'{self.user.email} - {self.pref_key}'

    def is_preference_enabled(self) -> bool:
        """Sprawdza czy dana preferencja powiadomień jest aktywna.

        Returns:
            bool: True jeśli powiadomienia są włączone, False w przeciwnym razie.
        """
        return self.enabled


class DeviceToken(TimestampedUpdatedModel):
    """Model rejestrujący tokeny urządzeń mobilnych użytkownika (Expo Push Token)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
    )
    expo_push_token = models.CharField(max_length=200, unique=True)
    platform = models.CharField(
        max_length=20,
        choices=DevicePlatform.choices,
        default=DevicePlatform.UNKNOWN,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        """Metadane modelu DeviceToken."""

        db_table: str = 'device_tokens'
        indexes: list[models.Index] = [
            models.Index(fields=['user', 'is_active'], name='idx_device_token_user_active'),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową tokenu urządzenia.

        Returns:
            str: Napis w formacie 'email - platforma'.
        """
        return f'{self.user.email} - {self.platform}'

    def matches_platform(self, target_platform: str) -> bool:
        """Sprawdza czy urządzenie odpowiada podanej platformie.

        Args:
            target_platform (str): Oczekiwana nazwa platformy (np. 'ios', 'android').

        Returns:
            bool: True jeśli platforma zgadza się, False w przeciwnym razie.

        Raises:
            TypeError: Gdy argument target_platform nie jest napisem.
        """
        if not isinstance(target_platform, str):
            raise TypeError("Argument 'target_platform' musi być typu str.")

        return self.platform == target_platform


class NotificationDelivery(TimestampedModel):
    """Model rejestrujący historię dostarczenia i wysyłki powiadomień."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_deliveries',
    )
    pref_key = models.CharField(max_length=50, choices=NotificationPreferenceKey.choices)
    channel = models.CharField(max_length=10, choices=DeliveryChannel.choices)
    status = models.CharField(max_length=10, choices=DeliveryStatus.choices)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=500)
    data = models.JSONField(default=dict, blank=True)
    dedupe_key = models.CharField(max_length=200, blank=True, default='')
    error_message = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        """Metadane modelu NotificationDelivery."""

        db_table: str = 'notification_deliveries'
        indexes: list[models.Index] = [
            models.Index(
                fields=['user', 'dedupe_key'],
                name='idx_notif_delivery_user_dedupe',
            ),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową rekordu doręczenia powiadomienia.

        Returns:
            str: Napis w formacie 'email - klucz_preferencji - status'.
        """
        return f'{self.user.email} - {self.pref_key} - {self.status}'

    def is_failed(self) -> bool:
        """Sprawdza czy wysyłka powiadomienia zakończyła się błędem.

        Returns:
            bool: True jeśli status to FAILED, False w przeciwnym razie.
        """
        return self.status == DeliveryStatus.FAILED
