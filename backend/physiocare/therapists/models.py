from django.conf import settings
from django.db import models

from core.models import TimestampedModel
from therapists.competence import QualificationLevel, snapshot_for_therapist


class TherapistProfile(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='therapist_profile',
    )
    pwzf_number = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    location_address = models.CharField(max_length=300, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    courses = models.JSONField(default=list)
    avatar_url = models.CharField(max_length=500, blank=True, default='')
    qualification_level = models.CharField(
        max_length=20,
        choices=QualificationLevel.CHOICES,
        default=QualificationLevel.MAGISTER,
    )
    experience_years = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'therapist_profiles'

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def competence_snapshot(self):
        return snapshot_for_therapist(self)
