from django.conf import settings
from django.db import models

from core.models import UUIDModel


class ConsentType(models.TextChoices):
    TERMS_REQUIRED = 'TERMS_REQUIRED', 'Regulamin (wymagany)'
    MEDICAL_DATA_REQUIRED = 'MEDICAL_DATA_REQUIRED', 'Dane medyczne (wymagany)'
    MARKETING_OPTIONAL = 'MARKETING_OPTIONAL', 'Marketing (opcjonalny)'
    RESEARCH_OPTIONAL = 'RESEARCH_OPTIONAL', 'Badania (opcjonalny)'


class Consent(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consents',
    )
    consent_type = models.CharField(max_length=30, choices=ConsentType.choices)
    granted = models.BooleanField()
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'consents'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'consent_type'],
                name='uniq_consent_user_type',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} — {self.consent_type}'
