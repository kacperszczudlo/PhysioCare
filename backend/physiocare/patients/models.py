from django.conf import settings
from django.db import models

from core.fields import EncryptedCharField
from core.models import TimestampedModel, TimestampedUpdatedModel


class PatientProfileQuerySet(models.QuerySet):
    def active(self):
        """Exclude soft-deleted / anonymized accounts (user.is_active=False)."""
        return self.filter(user__is_active=True)


class LinkStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Aktywny'
    ARCHIVED = 'ARCHIVED', 'Zarchiwizowany'


class PatientTherapistLink(TimestampedUpdatedModel):
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='therapist_links',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.CASCADE,
        related_name='patient_links',
    )
    status = models.CharField(
        max_length=20,
        choices=LinkStatus.choices,
        default=LinkStatus.ACTIVE,
    )

    class Meta:
        db_table = 'patient_therapist_links'
        constraints = [
            models.UniqueConstraint(
                fields=['patient', 'therapist'],
                name='uniq_patient_therapist_link',
            ),
        ]
        indexes = [
            models.Index(fields=['patient', 'status'], name='idx_pt_link_patient_status'),
            models.Index(fields=['therapist', 'status'], name='idx_pt_link_therapist_status'),
        ]

    def __str__(self):
        return f'{self.patient} <-> {self.therapist} ({self.status})'


class PatientProfileManager(models.Manager.from_queryset(PatientProfileQuerySet)):
    def create(self, **kwargs):
        therapist = kwargs.pop('therapist', None)
        therapist_id = kwargs.pop('therapist_id', None)
        patient_profile = super().create(**kwargs)
        if therapist:
            PatientTherapistLink.objects.get_or_create(
                patient=patient_profile,
                therapist=therapist,
                defaults={'status': LinkStatus.ACTIVE},
            )
        elif therapist_id:
            PatientTherapistLink.objects.get_or_create(
                patient=patient_profile,
                therapist_id=therapist_id,
                defaults={'status': LinkStatus.ACTIVE},
            )
        return patient_profile


class PatientProfile(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile',
    )
    therapists = models.ManyToManyField(
        'therapists.TherapistProfile',
        through='PatientTherapistLink',
        related_name='patients',
    )
    pesel = EncryptedCharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    avatar_url = models.CharField(max_length=500, blank=True, default='')

    objects = PatientProfileManager()

    class Meta:
        db_table = 'patient_profiles'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def therapist(self):
        return self.therapists.filter(patient_links__status=LinkStatus.ACTIVE).first()

    @property
    def therapist_id(self):
        t = self.therapist
        return t.id if t else None
