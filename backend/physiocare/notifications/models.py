from django.conf import settings
from django.db import models

from core.models import TimestampedModel, TimestampedUpdatedModel, UUIDModel
from notifications.keys import NotificationPreferenceKey


class DevicePlatform(models.TextChoices):
    IOS = 'ios', 'iOS'
    ANDROID = 'android', 'Android'
    UNKNOWN = 'unknown', 'Nieznana'


class DeliveryChannel(models.TextChoices):
    PUSH = 'push', 'Push'
    EMAIL = 'email', 'E-mail'
    NONE = 'none', 'Brak'


class DeliveryStatus(models.TextChoices):
    SENT = 'sent', 'Wysłane'
    SKIPPED = 'skipped', 'Pominięte'
    FAILED = 'failed', 'Błąd'


class NotificationPreference(UUIDModel):
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
        db_table = 'notification_preferences'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'pref_key'],
                name='uniq_notification_pref_user_key',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.pref_key}'


class DeviceToken(TimestampedUpdatedModel):
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
        db_table = 'device_tokens'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_device_token_user_active'),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.platform}'


class NotificationDelivery(TimestampedModel):
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
        db_table = 'notification_deliveries'
        indexes = [
            models.Index(
                fields=['user', 'dedupe_key'],
                name='idx_notif_delivery_user_dedupe',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.pref_key} - {self.status}'
