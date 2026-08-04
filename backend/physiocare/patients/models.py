from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class PatientProfile(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.PROTECT,
        related_name='patients',
    )
    pesel = models.CharField(max_length=11, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    avatar_url = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        db_table = 'patient_profiles'
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['therapist'], name='idx_patient_profiles_therapist'),
        ]

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
