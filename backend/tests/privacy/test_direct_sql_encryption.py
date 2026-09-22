from typing import TYPE_CHECKING

import pytest
from django.db import connection

from privacy.account_deletion import anonymize_user_for_deletion
from treatment.models import EpisodeStatus, TreatmentEpisode

if TYPE_CHECKING:
    from patients.models import PatientProfile
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_pesel_direct_sql_inspection_proves_fernet_ciphertext(patient: 'PatientProfile') -> None:
    """Direct SQL Inspection: zapytanie SQL do bazy zwraca szyfrogram gAAAAA..., a nie jawny numer PESEL."""
    # Arrange
    patient.pesel = '92071304259'
    patient.save()

    # Act
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT pesel FROM patient_profiles WHERE id = %s',
            [patient.id],
        )
        row = cursor.fetchone()

    raw_db_value = row[0]

    # Assert
    assert raw_db_value is not None
    assert raw_db_value != '92071304259'
    assert raw_db_value.startswith('gAAAAA')


@pytest.mark.django_db
def test_gdpr_anonymization_preserves_clinical_episodes_for_retention(
    patient: 'PatientProfile',
    therapist: 'TherapistProfile',
) -> None:
    """RODO vs Retencja EDM: Anonimizacja usuwa dane osobowe, zachowując zanonimizowaną historię epizodów."""
    # Arrange
    user = patient.user
    original_email: str = user.email

    episode = TreatmentEpisode.objects.create(
        patient=patient,
        therapist=therapist,
        icd10_code='M23.2',
        summary_note='Epizod rehabilitacyjny kolana',
        status=EpisodeStatus.COMPLETED_SUCCESS,
    )

    anonymize_user_for_deletion(user, source='user_request')

    user.refresh_from_db()
    patient.refresh_from_db()

    # Assert
    assert user.is_active is False
    assert user.email != original_email
    assert user.email.endswith('@deleted.invalid')
    assert user.first_name == 'Usunięte'
    assert user.last_name == 'Konto'

    retained_episode = TreatmentEpisode.objects.filter(id=episode.id).first()
    assert retained_episode is not None
    assert retained_episode.icd10_code == 'M23.2'
    assert retained_episode.patient_id == patient.id

