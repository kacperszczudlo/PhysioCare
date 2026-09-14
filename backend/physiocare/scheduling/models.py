from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import Func, Q

from core.models import TimestampedModel, TimestampedUpdatedModel


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
    # After-visit summary for the patient (plain language) - not the clinical VisitNote.
    patient_summary = models.TextField(blank=True, default='')
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


class TherapistAvailabilitySlot(TimestampedUpdatedModel):
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.CASCADE,
        related_name='availability_slots',
    )
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    day_of_week = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='0=Poniedziałek, 6=Niedziela',
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'therapist_availability_slots'
        indexes = [
            models.Index(
                fields=['therapist', 'is_active', 'start_at'],
                name='idx_avail_therapist_start',
            ),
            models.Index(
                fields=['therapist', 'is_active', 'day_of_week'],
                name='idx_avail_therapist_dow',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    is_recurring=False,
                    start_at__isnull=False,
                    end_at__isnull=False,
                    end_at__gt=models.F('start_at'),
                ) | models.Q(
                    is_recurring=True,
                    day_of_week__isnull=False,
                    start_time__isnull=False,
                    end_time__isnull=False,
                    end_time__gt=models.F('start_time'),
                ),
                name='chk_avail_slot_valid_range',
            ),
        ]

    def __str__(self):
        if self.is_recurring:
            return f'Dostępność cykliczna DOW:{self.day_of_week} ({self.start_time}-{self.end_time}) - {self.therapist}'
        return f'Dostępność {self.start_at} do {self.end_at} - {self.therapist}'

