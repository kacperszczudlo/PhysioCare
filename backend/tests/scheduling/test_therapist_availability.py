from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from scheduling.models import TherapistAvailabilitySlot, VisitStatus


@pytest.mark.django_db
def test_therapist_can_create_and_list_availability_slots(api_client, therapist):
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=4)

    # Act - Specific date slot
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

    # Act - Recurring slot
    res_rec = api_client.post(
        '/api/v1/therapist/availabilities/',
        {
            'is_recurring': True,
            'day_of_week': 0,  # Poniedziałek
            'start_time': '08:00:00',
            'end_time': '16:00:00',
        },
        format='json',
    )
    assert res_rec.status_code == status.HTTP_201_CREATED
    assert res_rec.data['is_recurring'] is True

    # List slots
    res_list = api_client.get('/api/v1/therapist/availabilities/')
    assert res_list.status_code == status.HTTP_200_OK
    assert len(res_list.data['results']) == 2


@pytest.mark.django_db
def test_patient_can_book_visit_only_within_availability_slot(
    api_client, therapist, patient, therapy_type,
):
    # Arrange
    now = timezone.now()
    start_at = now + timedelta(days=3)
    # Align to full hours
    start_at = start_at.replace(minute=0, second=0, microsecond=0)
    end_at = start_at + timedelta(minutes=45)

    # Create slot covering start_at to end_at
    slot_start = start_at - timedelta(hours=1)
    slot_end = end_at + timedelta(hours=1)
    TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=False,
        start_at=slot_start,
        end_at=slot_end,
    )

    # Act - Valid booking within slot
    api_client.force_authenticate(user=patient.user)
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

    # Act - Invalid booking outside slot (next day without slot)
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

    # Assert 400 Bad Request
    assert res_fail.status_code == status.HTTP_400_BAD_REQUEST
    details = res_fail.data.get('error', {}).get('details', res_fail.data)
    assert 'start_at' in details
    assert 'nie mieści się w godzinach przyjęć' in details['start_at'][0]


@pytest.mark.django_db
def test_other_therapist_cannot_access_or_modify_availability_slot(
    api_client, therapist, therapist_b,
):
    # Arrange
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=3)
    slot = TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=False,
        start_at=start_at,
        end_at=end_at,
    )

    # Act - Therapist B attempts to delete Therapist A's slot (BOLA isolation)
    api_client.force_authenticate(user=therapist_b.user)
    res_del = api_client.delete(f'/api/v1/therapist/availabilities/{slot.id}/')

    # Assert - 404 Not Found due to queryset isolation
    assert res_del.status_code == status.HTTP_404_NOT_FOUND
    assert TherapistAvailabilitySlot.objects.filter(id=slot.id).exists()


@pytest.mark.django_db
def test_public_available_slots_endpoint(api_client, therapist, patient):
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
    date_param = start_at.strftime('%Y-%m-%d')
    res = api_client.get(
        f'/api/v1/therapists/{therapist.id}/available-slots/?date={date_param}',
    )

    assert res.status_code == status.HTTP_200_OK
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == str(slot.id)
