from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.utils import timezone
from rest_framework import status

from scheduling.models import Visit, VisitStatus

if TYPE_CHECKING:
    from rest_framework.test import APIClient
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_cancel_already_completed_visit_returns_400(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Odrzuca próbę odwołania wizyty, która znajduje się już w stanie COMPLETED (zakończona)."""
    # Arrange
    start_at = timezone.now() - timedelta(days=1)
    end_at = start_at + timedelta(hours=1)
    visit = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.COMPLETED,
        location_address='Gabinet 1',
    )
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(f'/api/v1/visits/{visit.id}/cancel/')

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_cancel_already_cancelled_visit_returns_400(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Odrzuca próbę ponownego odwołania wizyty mającej już status CANCELLED."""
    # Arrange
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=1)
    visit = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.CANCELLED,
        location_address='Gabinet 1',
    )
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(f'/api/v1/visits/{visit.id}/cancel/')

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_other_patient_cannot_cancel_visit_returns_404(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    patient_profiles: list['PatientProfile'],
    therapy_type: 'TherapyType',
) -> None:
    """Weryfikuje izolację BOLA: inny pacjent nie może odwołać nie swojej wizyty."""
    # Arrange
    start_at = timezone.now() + timedelta(days=3)
    end_at = start_at + timedelta(hours=1)
    visit = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.SCHEDULED,
        location_address='Gabinet 1',
    )
    other_patient = patient_profiles[1]
    api_client.force_authenticate(user=other_patient.user)

    # Act
    response = api_client.post(f'/api/v1/visits/{visit.id}/cancel/')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_reschedule_visit_to_overlapping_slot_returns_400(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    patient_profiles: list['PatientProfile'],
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie przełożenia wizyty na termin, w którym terapeuta ma już inną zarezerwowaną wizytę."""
    # Arrange
    start_1 = timezone.now() + timedelta(days=4)
    end_1 = start_1 + timedelta(hours=1)
    Visit.objects.create(
        therapist=therapist,
        patient=patient_profiles[0],
        therapy_type=therapy_type,
        start_at=start_1,
        end_at=end_1,
        status=VisitStatus.SCHEDULED,
        location_address='Gabinet 1',
    )

    start_2 = start_1 + timedelta(days=1)
    end_2 = start_2 + timedelta(hours=1)
    visit_to_reschedule = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=therapy_type,
        start_at=start_2,
        end_at=end_2,
        status=VisitStatus.SCHEDULED,
        location_address='Gabinet 1',
    )
    api_client.force_authenticate(user=patient.user)

    # Act
    response = api_client.patch(
        f'/api/v1/visits/{visit_to_reschedule.id}/reschedule/',
        data={
            'start_at': start_1.isoformat(),
            'end_at': end_1.isoformat(),
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_other_therapist_cannot_approve_visit_returns_404(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Weryfikuje izolację BOLA: inny terapeuta nie może zatwierdzić oczekującej wizyty drugiego terapeuty."""
    # Arrange
    start_at = timezone.now() + timedelta(days=5)
    end_at = start_at + timedelta(hours=1)
    visit = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
        location_address='Gabinet 1',
    )
    api_client.force_authenticate(user=therapist_b.user)

    # Act
    response = api_client.post(f'/api/v1/therapist/visits/{visit.id}/approve/')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_other_therapist_cannot_reject_visit_returns_404(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Weryfikuje izolację BOLA: inny terapeuta nie może odrzucić oczekującej wizyty drugiego terapeuty."""
    # Arrange
    start_at = timezone.now() + timedelta(days=5)
    end_at = start_at + timedelta(hours=1)
    visit = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
        location_address='Gabinet 1',
    )
    api_client.force_authenticate(user=therapist_b.user)

    # Act
    response = api_client.post(
        f'/api/v1/therapist/visits/{visit.id}/reject/',
        data={'rejection_reason': 'Brak wolnego terminu w gabinecie.'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
