from django.conf import settings
from django.db import models

from core.models import UUIDModel


class NotificationPreference(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    pref_key = models.CharField(max_length=50)
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
        return f'{self.user.email} — {self.pref_key}'
