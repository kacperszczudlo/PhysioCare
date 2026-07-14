from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class MedicalDocument(TimestampedModel):
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='medical_documents',
    )
    visit = models.ForeignKey(
        'scheduling.Visit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
    )
    episode = models.ForeignKey(
        'treatment.TreatmentEpisode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_documents',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='uploaded_documents',
    )
    title = models.CharField(max_length=200)
    file_url = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100, default='application/pdf')

    class Meta:
        db_table = 'medical_documents'
        indexes = [
            models.Index(
                fields=['patient', '-created_at'],
                name='idx_med_docs_patient_created',
            ),
        ]

    def __str__(self):
        return self.title
