from django.conf import settings
from django.db import models

from core.models import TimestampedModel, UUIDModel


class ConsentType(models.TextChoices):
    """Typy zgód udzielanych przez użytkowników."""

    TERMS_REQUIRED = 'TERMS_REQUIRED', 'Regulamin (wymagany)'
    MEDICAL_DATA_REQUIRED = 'MEDICAL_DATA_REQUIRED', 'Dane medyczne (wymagany)'
    MARKETING_OPTIONAL = 'MARKETING_OPTIONAL', 'Marketing (opcjonalny)'
    RESEARCH_OPTIONAL = 'RESEARCH_OPTIONAL', 'Badania (opcjonalny)'


class Consent(UUIDModel):
    """Model rejestrujący zgodę udzieloną przez użytkownika."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consents',
    )
    consent_type = models.CharField(max_length=30, choices=ConsentType.choices)
    granted = models.BooleanField()
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadane modelu zgód RODO."""

        db_table: str = 'consents'
        constraints: list[object] = [
            models.UniqueConstraint(
                fields=['user', 'consent_type'],
                name='uniq_consent_user_type',
            ),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową udzielonej zgody.

        Returns:
            str: Napis w formacie 'email - typ_zgody'.
        """
        return f'{self.user.email} - {self.consent_type}'

    def is_required_consent(self) -> bool:
        """Sprawdza, czy dana zgoda należy do kategorii zgód wymaganych.

        Returns:
            bool: True jeśli zgoda jest wymagana, False w przeciwnym razie.
        """
        return self.consent_type in (
            ConsentType.TERMS_REQUIRED,
            ConsentType.MEDICAL_DATA_REQUIRED,
        )


class AccountDeletionRequest(TimestampedModel):
    """Model zgłoszenia żądania usunięcia konta przez użytkownika (RODO/GDPR)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='account_deletion_request',
    )
    reason = models.TextField(
        blank=True,
        default='',
        help_text='Powód rezygnacji podany przez użytkownika.',
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        """Metadane modelu wniosków o usunięcie konta."""

        db_table: str = 'account_deletion_requests'

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową żądania usunięcia konta.

        Returns:
            str: Opis żądania usunięcia konta z adresem email.
        """
        return f'Deletion request {self.user.email}'

    def is_processed(self) -> bool:
        """Sprawdza, czy wniosek o usunięcie konta został przetworzony.

        Returns:
            bool: True jeśli wniosek został przetworzony, False w przeciwnym razie.
        """
        return self.processed_at is not None

