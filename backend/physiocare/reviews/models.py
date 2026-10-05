from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimestampedModel


class Review(TimestampedModel):
    """Opinia pacjenta o wizycie fizjoterapeutycznej.

    Każda opinia jest powiązana z konkretną zakończoną wizytą (Verified Review).
    Relacja OneToOneField na visit gwarantuje 1 opinia = 1 wizyta na poziomie bazy danych.
    """

    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='Pacjent wystawiający opinię.',
    )
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='Fizjoterapeuta, którego dotyczy opinia.',
    )
    visit = models.OneToOneField(
        'scheduling.Visit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review',
        help_text='Zakończona wizyta będąca podstawą opinii (Verified Review).',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Ocena w skali 1–5 gwiazdek.',
    )
    comment = models.TextField(
        blank=True,
        default='',
        help_text='Opcjonalny komentarz tekstowy pacjenta.',
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text='Jeśli True, imię i nazwisko pacjenta są ukryte pod opinią.',
    )

    # Odpowiedź fizjoterapeuty
    therapist_reply = models.TextField(
        blank=True,
        default='',
        help_text='Odpowiedź fizjoterapeuty na opinię (jedna odpowiedź).',
    )
    therapist_replied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data i czas dodania odpowiedzi przez fizjoterapeutę.',
    )

    # Moderacja
    is_visible = models.BooleanField(
        default=True,
        help_text='Czy opinia jest widoczna publicznie (może być ukryta przez admina).',
    )

    class Meta:
        """Metadane modelu Review."""

        db_table = 'therapist_reviews'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['patient', 'visit'],
                name='unique_review_per_visit',
            ),
        ]
        indexes = [
            models.Index(
                fields=['therapist', 'is_visible', '-created_at'],
                name='idx_review_therapist_visible',
            ),
            models.Index(fields=['rating'], name='idx_review_rating'),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową opinii.

        Returns:
            str: Skrócony opis opinii z oceną i pacjentem.
        """
        return f'Opinia {self.rating}★ od {self.patient} dla {self.therapist}'
