from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class TherapistProfile(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='therapist_profile',
    )
    pwzf_number = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    courses = models.JSONField(default=list)
    avatar_url = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        db_table = 'therapist_profiles'

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
