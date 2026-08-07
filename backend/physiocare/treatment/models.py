from django.db import models

from core.models import TimestampedModel, UUIDModel


class EpisodeStatus(models.TextChoices):
    IN_PROGRESS = 'IN_PROGRESS', 'W trakcie'
    COMPLETED_SUCCESS = 'COMPLETED_SUCCESS', 'Zakończony sukcesem'
    REFERRED = 'REFERRED', 'Skierowany'
    INTERRUPTED = 'INTERRUPTED', 'Przerwany'


class BodyViewSide(models.TextChoices):
    FRONT = 'FRONT', 'Przód'
    BACK = 'BACK', 'Tył'


class TreatmentEpisode(TimestampedModel):
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='episodes',
    )
    icd10_code = models.CharField(max_length=10, blank=True, default='')
    status = models.CharField(
        max_length=30,
        choices=EpisodeStatus.choices,
        default=EpisodeStatus.IN_PROGRESS,
    )
    summary_note = models.TextField(blank=True, default='')
    started_at = models.DateField(auto_now_add=True)
    ended_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'treatment_episodes'
        indexes = [
            models.Index(
                fields=['patient', 'status'],
                name='idx_episodes_patient_status',
            ),
        ]

    def __str__(self):
        return f'Epizod {self.id} - {self.patient}'


class BodyAreaPain(UUIDModel):
    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='body_pain_entries',
    )
    body_region = models.CharField(max_length=50)
    view_side = models.CharField(max_length=10, choices=BodyViewSide.choices)
    vas_score = models.PositiveSmallIntegerField()
    pain_character = models.JSONField(default=list)
    treatment_targets = models.JSONField(default=list, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'body_area_pain'
        constraints = [
            models.UniqueConstraint(
                fields=['episode', 'body_region', 'view_side'],
                name='uniq_body_pain_episode_region_side',
            ),
            models.CheckConstraint(
                condition=models.Q(vas_score__gte=0, vas_score__lte=10),
                name='chk_body_pain_vas_score',
            ),
        ]

    def __str__(self):
        return f'{self.body_region} ({self.view_side}) VAS={self.vas_score}'


class VisitNote(TimestampedModel):
    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='visit_notes',
    )
    visit = models.ForeignKey(
        'scheduling.Visit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes',
    )
    content = models.TextField()

    class Meta:
        db_table = 'visit_notes'

    def __str__(self):
        return f'Notatka epizodu {self.episode_id}'
