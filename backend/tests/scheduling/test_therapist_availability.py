from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.utils import timezone
from rest_framework import status

from scheduling.models import TherapistAvailabilitySlot, VisitStatus

if TYPE_CHECKING:
    from rest_framework.test import APIClient
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_therapist_can_create_and_list_availability_slots(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
) -> None:
    """Sprawdza możliwość tworzenia i pobierania listy slotów dostępności przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=4)

    # Act
    res_date = api_client.post(
        '/api/v1/therapist/availabilities/',
        {
            'is_recurring': False,
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )

    # Assert
    assert res_date.status_code == status.HTTP_201_CREATED
    assert res_date.data['is_recurring'] is False
    assert TherapistAvailabilitySlot.objects.filter(therapist=therapist).count() == 1

    res_rec = api_client.post(
        '/api/v1/therapist/availabilities/',
        {
            'is_recurring': True,
            'day_of_week': 0,
            'start_time': '08:00:00',
            'end_time': '16:00:00',
        },
        format='json',
    )
    assert res_rec.status_code == status.HTTP_201_CREATED
    assert res_rec.data['is_recurring'] is True

    res_list = api_client.get('/api/v1/therapist/availabilities/')
    assert res_list.status_code == status.HTTP_200_OK
    assert len(res_list.data['results']) == 2


@pytest.mark.django_db
def test_patient_can_book_visit_only_within_availability_slot(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza blokadę rezerwacji wizyty poza ustalonymi godzinami dostępności fizjoterapeuty."""
    # Arrange
    now = timezone.now()
    start_at = now + timedelta(days=3)
    start_at = start_at.replace(minute=0, second=0, microsecond=0)
    end_at = start_at + timedelta(minutes=45)

    slot_start = start_at - timedelta(hours=1)
    slot_end = end_at + timedelta(hours=1)
    TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=False,
        start_at=slot_start,
        end_at=slot_end,
    )

    api_client.force_authenticate(user=patient.user)
    # Act
    res_ok = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
            'patient_note': 'Rezerwacja wewnątrz slotu',
        },
        format='json',
    )

    # Assert
    assert res_ok.status_code == status.HTTP_201_CREATED
    assert res_ok.data['status'] == VisitStatus.PENDING_APPROVAL

    outside_start = start_at + timedelta(days=1)
    outside_end = outside_start + timedelta(minutes=45)
    res_fail = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': outside_start.isoformat(),
            'end_at': outside_end.isoformat(),
        },
        format='json',
    )

    assert res_fail.status_code == status.HTTP_400_BAD_REQUEST
    details = res_fail.data.get('error', {}).get('details', res_fail.data)
    assert 'start_at' in details
    assert 'nie mieści się w godzinach przyjęć' in details['start_at'][0]


@pytest.mark.django_db
def test_other_therapist_cannot_access_or_modify_availability_slot(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
) -> None:
    """Sprawdza izolację BOLA przy próbie modyfikacji slotu innego fizjoterapeuty."""
    # Arrange
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=3)
    slot = TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=False,
        start_at=start_at,
        end_at=end_at,
    )

    api_client.force_authenticate(user=therapist_b.user)
    # Act
    res_del = api_client.delete(f'/api/v1/therapist/availabilities/{slot.id}/')

    # Assert
    assert res_del.status_code == status.HTTP_404_NOT_FOUND
    assert TherapistAvailabilitySlot.objects.filter(id=slot.id).exists()


@pytest.mark.django_db
def test_public_available_slots_endpoint(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza publiczny endpoint dostępnych slotów dla pacjenta w wybranym dniu."""
    # Arrange
    start_at = timezone.now() + timedelta(days=5)
    end_at = start_at + timedelta(hours=4)
    slot = TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=False,
        start_at=start_at,
        end_at=end_at,
    )

    api_client.force_authenticate(user=patient.user)
    date_param = timezone.localtime(start_at).strftime('%Y-%m-%d')
    # Act
    res = api_client.get(
        f'/api/v1/therapists/{therapist.id}/available-slots/?date={date_param}',
    )

    # Assert
    assert res.status_code == status.HTTP_200_OK
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == str(slot.id)

