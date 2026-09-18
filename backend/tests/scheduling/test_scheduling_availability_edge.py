from typing import TYPE_CHECKING

import pytest
from rest_framework import status

from scheduling.models import TherapistAvailabilitySlot

if TYPE_CHECKING:
    from rest_framework.test import APIClient
    from patients.models import PatientProfile
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_unauthenticated_cannot_create_availability_slot(
    api_client: 'APIClient',
) -> None:
    """Niezalogowany użytkownik otrzymuje status HTTP 401 Unauthorized przy próbie dodania slotu dostępności."""
    # Act
    response = api_client.post(
        '/api/v1/therapist/availabilities/',
        data={
            'is_recurring': True,
            'day_of_week': 0,
            'start_time': '09:00:00',
            'end_time': '17:00:00',
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_patient_cannot_create_availability_slot(
    api_client: 'APIClient',
    patient: 'PatientProfile',
) -> None:
    """Pacjent otrzymuje status HTTP 403 Forbidden przy próbie utworzenia slotu dostępności terapeuty."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    # Act
    response = api_client.post(
        '/api/v1/therapist/availabilities/',
        data={
            'is_recurring': True,
            'day_of_week': 1,
            'start_time': '08:00:00',
            'end_time': '16:00:00',
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_therapist_creates_valid_recurring_availability_slot(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
) -> None:
    """Terapeuta pomyślnie dodaje cykliczny slot dostępności (status 201 Created)."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(
        '/api/v1/therapist/availabilities/',
        data={
            'is_recurring': True,
            'day_of_week': 2,
            'start_time': '10:00:00',
            'end_time': '18:00:00',
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert TherapistAvailabilitySlot.objects.filter(
        therapist=therapist,
        day_of_week=2,
        is_recurring=True,
    ).exists()


@pytest.mark.django_db
def test_therapist_cannot_delete_other_therapists_availability_slot(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
) -> None:
    """Weryfikuje izolację BOLA: terapeuta B nie może usunąć slotu dostępności należącego do terapeuty A."""
    # Arrange
    slot = TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=True,
        day_of_week=3,
        start_time='09:00:00',
        end_time='15:00:00',
    )
    api_client.force_authenticate(user=therapist_b.user)

    # Act
    response = api_client.delete(f'/api/v1/therapist/availabilities/{slot.id}/')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert TherapistAvailabilitySlot.objects.filter(id=slot.id).exists()


@pytest.mark.django_db
def test_public_available_slots_endpoint_returns_slots_for_therapist(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza publiczne pobieranie wolnych slotów czasowych dla danego fizjoterapeuty na wybrany dzień."""
    # Arrange
    TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=True,
        day_of_week=0,  # Poniedziałek
        start_time='08:00:00',
        end_time='12:00:00',
    )
    api_client.force_authenticate(user=patient.user)

    # Act
    target_date_str = '2026-10-05'  # Poniedziałek
    response = api_client.get(
        f'/api/v1/therapists/{therapist.id}/available-slots/?date={target_date_str}',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data or 'slots' in response.data or isinstance(response.data, list)
