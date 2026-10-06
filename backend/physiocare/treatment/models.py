from django.db import models

from core.fields import EncryptedJSONField, EncryptedTextField
from core.models import TimestampedModel, UUIDModel


class EpisodeStatus(models.TextChoices):
    """Statusy epizodu leczenia fizjoterapeutycznego."""

    IN_PROGRESS = 'IN_PROGRESS', 'W trakcie'
    COMPLETED_SUCCESS = 'COMPLETED_SUCCESS', 'Zakończony sukcesem'
    REFERRED = 'REFERRED', 'Skierowany'
    INTERRUPTED = 'INTERRUPTED', 'Przerwany'


class BodyViewSide(models.TextChoices):
    """Strony widoku ciała na diagramie bólu."""

    FRONT = 'FRONT', 'Przód'
    BACK = 'BACK', 'Tył'


class RecommendationType(models.TextChoices):
    """Typy rekomendacji diagnostycznych wystawianych przez fizjoterapeutę."""

    SPECIALIST_CONSULTATION = 'SPECIALIST_CONSULTATION', 'Konsultacja lekarza specjalisty'
    IMAGING_MRI = 'IMAGING_MRI', 'Sugestia MRI'
    IMAGING_CT = 'IMAGING_CT', 'Sugestia TK'
    IMAGING_RTG = 'IMAGING_RTG', 'Sugestia RTG (wymaga lekarza)'
    IMAGING_USG = 'IMAGING_USG', 'Sugestia USG'
    OTHER = 'OTHER', 'Inne'


class FundingHint(models.TextChoices):
    """Wskazówki dotyczące finansowania zalecanego badania lub konsultacji."""

    NFZ_VIA_DOCTOR = 'NFZ_VIA_DOCTOR', 'NFZ - formalne skierowanie wystawia lekarz'
    PRIVATE = 'PRIVATE', 'Ścieżka prywatna'
    NOT_APPLICABLE = 'NOT_APPLICABLE', 'Nie dotyczy'


class DeviceOrderStatus(models.TextChoices):
    """Statusy zlecenia na wyroby medyczne."""

    DRAFT = 'DRAFT', 'Szkic'
    ISSUED = 'ISSUED', 'Wystawione'
    CANCELLED = 'CANCELLED', 'Anulowane'


DEVICE_ORDER_DISCLAIMER: str = (
    'PhysioCare modeluje uprawnienia ordynacyjne wyrobów medycznych. '
    'Nie służy do wystawiania recept na leki ani maści farmaceutyczne. '
    'Formalne e-ZWM wymaga podpisu i weryfikacji w systemie P1/NFZ.'
)

DEVICE_PICKUP_HINT: str = (
    'W aptece lub sklepie medycznym z umową NFZ podaj PESEL oraz ten 4-cyfrowy kod dostępu. '
    'Kod pochodzi z systemu NFZ (SMS, e-mail, druk lub IKP) - PhysioCare go tylko pokazuje.'
)


class BodySide(models.TextChoices):
    """Strony ciała dotyczące zlecenia na wyrób medyczny."""

    LEFT = 'LEFT', 'Lewa'
    RIGHT = 'RIGHT', 'Prawa'
    BOTH = 'BOTH', 'Obustronnie'
    NA = 'NA', 'Nie dotyczy'


class TreatmentEpisode(TimestampedModel):
    """Reprezentuje epizod leczenia pacjenta pod opieką fizjoterapeuty."""

    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='episodes',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episodes',
    )
    icd10_code = models.CharField(max_length=10, blank=True, default='')
    functional_diagnosis = EncryptedTextField(blank=True, default='')
    status = models.CharField(
        max_length=30,
        choices=EpisodeStatus.choices,
        default=EpisodeStatus.IN_PROGRESS,
    )
    summary_note = EncryptedTextField(blank=True, default='')
    started_at = models.DateField(auto_now_add=True)
    ended_at = models.DateField(null=True, blank=True)

    class Meta:
        """Metadane modelu epizodu leczenia."""

        db_table: str = 'treatment_episodes'
        indexes: list[object] = [
            models.Index(
                fields=['patient', 'status'],
                name='idx_episodes_patient_status',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ended_at__isnull=True) | models.Q(ended_at__gte=models.F('started_at')),
                name='chk_episode_end_on_or_after_start',
            ),
        ]


    def __str__(self) -> str:
        """Zwraca reprezentację tekstową epizodu leczenia.

        Returns:
            str: Tekstowa reprezentacja epizodu leczenia.
        """
        return f'Epizod {self.id} - {self.patient}'


class BodyAreaPain(UUIDModel):
    """Reprezentuje ocenę bólu i cele terapeutyczne dla określonego obszaru ciała."""

    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='body_pain_entries',
    )
    body_region = models.CharField(max_length=50)
    view_side = models.CharField(max_length=10, choices=BodyViewSide.choices)
    vas_score = models.PositiveSmallIntegerField()
    pain_character = EncryptedJSONField(default=list)
    treatment_targets = EncryptedJSONField(default=list, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadane modelu wpisu o bólu obszaru ciała."""

        db_table: str = 'body_area_pain'
        constraints: list[object] = [
            models.UniqueConstraint(
                fields=['episode', 'body_region', 'view_side'],
                name='uniq_body_pain_episode_region_side',
            ),
            models.CheckConstraint(
                condition=models.Q(vas_score__gte=0, vas_score__lte=10),
                name='chk_body_pain_vas_score',
            ),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową wpisu o bólach w danym obszarze ciała.

        Returns:
            str: Tekstowa reprezentacja poziomu bólu VAS i obszaru.
        """
        return f'{self.body_region} ({self.view_side}) VAS={self.vas_score}'


class VisitNote(TimestampedModel):
    """Reprezentuje wpis notatki medycznej z wizyty w ramach epizodu leczenia."""

    episode = models.ForeignKey(
        TreatmentEpisode,
        on_delete=models.CASCADE,
        related_name='visit_notes',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visit_notes',
    )
    visit = models.ForeignKey(
        'scheduling.Visit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes',
    )
    content = EncryptedTextField()

    class Meta:
        """Metadane modelu notatki z wizyty."""

        db_table: str = 'visit_notes'

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową notatki z wizyty.

        Returns:
            str: Tekstowa reprezentacja notatki z wizyty.
        """
        return f'Notatka epizodu {self.episode_id}'


class DiagnosticRecommendation(TimestampedModel):
    """Kierowanie pośrednie: opinia fizjoterapeuty ułatwiająca diagnostykę lekarską.

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
    justification = EncryptedTextField()
    red_flags_noted = models.BooleanField(default=False)
    funding_hint = models.CharField(
        max_length=30,
        choices=FundingHint.choices,
        default=FundingHint.NFZ_VIA_DOCTOR,
    )

    class Meta:
        """Metadane modelu rekomendacji diagnostycznej."""

        db_table: str = 'diagnostic_recommendations'
        ordering: list[str] = ['-created_at']

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową rekomendacji diagnostycznej.

        Returns:
            str: Tekstowa reprezentacja rekomendacji diagnostycznej.
        """
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
    notes = EncryptedTextField(blank=True, default='')

    class Meta:
        """Metadane modelu zlecenia na wyrób medyczny."""

        db_table: str = 'medical_device_orders'
        ordering: list[str] = ['-created_at']

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową zlecenia na wyrób medyczny.

        Returns:
            str: Tekstowa reprezentacja zlecenia na wyrób medyczny.
        """
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
    physician_order_description = EncryptedTextField()
    refusal_reason = EncryptedTextField()
    physician_notified = models.BooleanField(default=False)

    class Meta:
        """Metadane modelu odmowy wykonania zlecenia lekarskiego."""

        db_table: str = 'physician_order_refusals'
        ordering: list[str] = ['-created_at']

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową odmowa wykonania zlecenia lekarskiego.

        Returns:
            str: Tekstowa reprezentacja odmowy wykonania zlecenia.
        """
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
    activity_notes = EncryptedTextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=DeviceOrderStatus.choices,
        default=DeviceOrderStatus.ISSUED,
    )

    class Meta:
        """Metadane modelu skierowania Recepta na Ruch."""

        db_table: str = 'recepta_na_ruch_referrals'
        ordering: list[str] = ['-created_at']


    def __str__(self) -> str:
        """Zwraca reprezentację tekstową skierowania Recepta na Ruch.

        Returns:
            str: Tekstowa reprezentacja skierowania.
        """
        return f'Recepta na Ruch → {self.patient_id}'
