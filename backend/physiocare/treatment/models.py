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


class RecommendationType(models.TextChoices):
    SPECIALIST_CONSULTATION = 'SPECIALIST_CONSULTATION', 'Konsultacja lekarza specjalisty'
    IMAGING_MRI = 'IMAGING_MRI', 'Sugestia MRI'
    IMAGING_CT = 'IMAGING_CT', 'Sugestia TK'
    IMAGING_RTG = 'IMAGING_RTG', 'Sugestia RTG (wymaga lekarza)'
    IMAGING_USG = 'IMAGING_USG', 'Sugestia USG'
    OTHER = 'OTHER', 'Inne'


class FundingHint(models.TextChoices):
    NFZ_VIA_DOCTOR = 'NFZ_VIA_DOCTOR', 'NFZ - formalne skierowanie wystawia lekarz'
    PRIVATE = 'PRIVATE', 'Ścieżka prywatna'
    NOT_APPLICABLE = 'NOT_APPLICABLE', 'Nie dotyczy'


class DeviceOrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Szkic'
    ISSUED = 'ISSUED', 'Wystawione'
    CANCELLED = 'CANCELLED', 'Anulowane'


# Tekst prawny / produktowy - wspólny dla katalogu, API pacjenta i UI.
DEVICE_ORDER_DISCLAIMER = (
    'PhysioCare modeluje uprawnienia ordynacyjne wyrobów medycznych. '
    'Nie służy do wystawiania recept na leki ani maści farmaceutyczne. '
    'Formalne e-ZWM wymaga podpisu i weryfikacji w systemie P1/NFZ.'
)

DEVICE_PICKUP_HINT = (
    'W aptece lub sklepie medycznym z umową NFZ podaj PESEL oraz ten 4-cyfrowy kod dostępu. '
    'Kod pochodzi z systemu NFZ (SMS, e-mail, druk lub IKP) - PhysioCare go tylko pokazuje.'
)


class BodySide(models.TextChoices):
    LEFT = 'LEFT', 'Lewa'
    RIGHT = 'RIGHT', 'Prawa'
    BOTH = 'BOTH', 'Obustronnie'
    NA = 'NA', 'Nie dotyczy'


class TreatmentEpisode(TimestampedModel):
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='episodes',
    )
    # Kod roboczy / z dokumentacji lekarskiej - nie jest samodzielną diagnozą nozologiczną.
    icd10_code = models.CharField(max_length=10, blank=True, default='')
    # Diagnoza funkcjonalna - domena fizjoterapeuty (art. 4 u.o.z.f.).
    functional_diagnosis = models.TextField(blank=True, default='')
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


class DiagnosticRecommendation(TimestampedModel):
    """
    Kierowanie pośrednie: opinia fizjoterapeuty ułatwiająca diagnostykę lekarską.
    Nie jest formalnym e-skierowaniem NFZ na badania obrazowe.
    """

    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='diagnostic_recommendations',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.PROTECT,
        related_name='diagnostic_recommendations',
    )
    recommendation_type = models.CharField(
        max_length=40,
        choices=RecommendationType.choices,
    )
    target_specialty = models.CharField(max_length=120, blank=True, default='')
    body_area = models.CharField(max_length=120, blank=True, default='')
    justification = models.TextField()
    red_flags_noted = models.BooleanField(default=False)
    funding_hint = models.CharField(
        max_length=30,
        choices=FundingHint.choices,
        default=FundingHint.NFZ_VIA_DOCTOR,
    )

    class Meta:
        db_table = 'diagnostic_recommendations'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recommendation_type} @ {self.episode_id}'


class MedicalDeviceOrder(TimestampedModel):
    """Zlecenie na wyrób medyczny (model e-ZWM w aplikacji - bez integracji P1)."""

    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='device_orders',
    )
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='device_orders',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.PROTECT,
        related_name='device_orders',
    )
    device_code = models.CharField(max_length=40)
    device_group = models.CharField(max_length=5)
    device_name = models.CharField(max_length=255)
    side = models.CharField(
        max_length=10,
        choices=BodySide.choices,
        default=BodySide.NA,
    )
    quantity = models.PositiveSmallIntegerField(default=1)
    icd10_code = models.CharField(max_length=10)
    access_code = models.CharField(
        max_length=4,
        blank=True,
        default='',
        help_text='Opcjonalny 4-cyfrowy kod dostępu e-ZWM z NFZ (nie generowany lokalnie).',
    )
    status = models.CharField(
        max_length=20,
        choices=DeviceOrderStatus.choices,
        default=DeviceOrderStatus.ISSUED,
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'medical_device_orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.device_code} → {self.patient_id}'


class PhysicianOrderRefusal(TimestampedModel):
    """Odmowa wykonania zlecenia lekarskiego - art. 6 ust. 2 u.o.z.f."""

    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='order_refusals',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.PROTECT,
        related_name='order_refusals',
    )
    physician_order_description = models.TextField()
    refusal_reason = models.TextField()
    physician_notified = models.BooleanField(default=False)

    class Meta:
        db_table = 'physician_order_refusals'
        ordering = ['-created_at']

    def __str__(self):
        return f'Odmowa @ {self.episode_id}'


class ReceptaNaRuchReferral(TimestampedModel):
    """Skierowanie do programu Recepta na Ruch (mojeIKP) - model dokumentacyjny."""

    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='recepta_na_ruch_referrals',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.PROTECT,
        related_name='recepta_na_ruch_referrals',
    )
    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recepta_na_ruch_referrals',
    )
    readiness_confirmed = models.BooleanField(default=False)
    activity_notes = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=DeviceOrderStatus.choices,
        default=DeviceOrderStatus.ISSUED,
    )

    class Meta:
        db_table = 'recepta_na_ruch_referrals'
        ordering = ['-created_at']

    def __str__(self):
        return f'Recepta na Ruch → {self.patient_id}'
