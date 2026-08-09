from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import Func, Q

from core.models import TimestampedModel


class TsTzRange(Func):
    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


class VisitStatus(models.TextChoices):
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Oczekuje na zatwierdzenie'
    SCHEDULED = 'SCHEDULED', 'Zaplanowana'
    COMPLETED = 'COMPLETED', 'Zakończona'
    CANCELLED = 'CANCELLED', 'Anulowana'
    NO_SHOW = 'NO_SHOW', 'Nieobecność'


class TherapyType(TimestampedModel):
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.CASCADE,
        related_name='therapy_types',
    )
    name = models.CharField(max_length=100)
    color_hex = models.CharField(max_length=7, default='#3B82F6')
    duration_min = models.PositiveSmallIntegerField(default=45)

    class Meta:
        db_table = 'therapy_types'
        constraints = [
            models.UniqueConstraint(
                fields=['therapist', 'name'],
                name='uniq_therapy_type_therapist_name',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.therapist})'


class Visit(TimestampedModel):
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='visits',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.CASCADE,
        related_name='visits',
    )
    episode = models.ForeignKey(
        'treatment.TreatmentEpisode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits',
    )
    therapy_type = models.ForeignKey(
        TherapyType,
        on_delete=models.RESTRICT,
        related_name='visits',
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=VisitStatus.choices,
        default=VisitStatus.SCHEDULED,
    )
    location_address = models.CharField(max_length=300, blank=True, default='')
    prep_instructions = models.TextField(blank=True, default='')
    patient_note = models.TextField(blank=True, default='')
    cancel_reason = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'visits'
        indexes = [
            models.Index(
                fields=['therapist', 'start_at'],
                name='idx_visits_therapist_start',
            ),
            models.Index(
                fields=['patient', 'start_at'],
                name='idx_visits_patient_start',
            ),
            models.Index(
                fields=['patient', 'status', 'start_at'],
                name='idx_visits_pt_status_start',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F('start_at')),
                name='chk_visits_end_after_start',
            ),
            ExclusionConstraint(
                name='exclude_overlapping_visits',
                expressions=[
                    ('therapist', RangeOperators.EQUAL),
                    (TsTzRange('start_at', 'end_at', RangeBoundary()), RangeOperators.OVERLAPS),
                ],
                condition=~Q(status='CANCELLED'),
            ),
        ]

    def __str__(self):
        return f'Wizyta {self.start_at} - {self.patient}'
