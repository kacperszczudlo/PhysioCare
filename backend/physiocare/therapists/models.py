from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

from core.models import TimestampedModel
from therapists.competence import CompetenceSnapshot, QualificationLevel, snapshot_for_therapist


class TherapistProfile(TimestampedModel):
    """Model profilu fizjoterapeuty w systemie PhysioCare."""

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
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(60)],
    )
    rating_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Denormalizowana średnia ocena (przeliczana przez sygnały reviews).',
    )
    rating_count = models.PositiveIntegerField(
        default=0,
        help_text='Denormalizowana liczba widocznych opinii (przeliczana przez sygnały reviews).',
    )

    class Meta:
        """Metadane modelu profilu fizjoterapeuty."""

        db_table: str = 'therapist_profiles'


    def __str__(self) -> str:
        """Reprezentacja tekstowa profilu fizjoterapeuty.

        Returns:
            str: Imię i nazwisko fizjoterapeuty.
        """
        return f'{self.user.first_name} {self.user.last_name}'

    def competence_snapshot(self) -> CompetenceSnapshot:
        """Pobiera migawkę kompetencji dla fizjoterapeuty.

        Returns:
            CompetenceSnapshot: Migawka kompetencji wygenerowana na podstawie profilu.
        """
        return snapshot_for_therapist(self)

