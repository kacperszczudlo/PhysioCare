from typing import TYPE_CHECKING
import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from scheduling.models import Visit, VisitStatus
from scheduling.serializers import (
    PatientVisitRequestSerializer,
    TherapyTypeSerializer,
    VisitCancelSerializer,
    VisitCreateSerializer,
    VisitRescheduleSerializer,
)

if TYPE_CHECKING:
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_therapy_type_serializer_validations() -> None:
    """Sprawdza walidację koloru szesnastkowego oraz czasu trwania w serializatorze typu terapii."""
    # Arrange
    ser = TherapyTypeSerializer(data={'name': 'Terapia', 'color_hex': 'invalid', 'duration_min': 45})
    # Assert
    assert ser.is_valid() is False
    assert 'color_hex' in ser.errors

    ser = TherapyTypeSerializer(data={'name': 'Terapia', 'color_hex': '#123456', 'duration_min': 0})
    assert ser.is_valid() is False
    assert 'duration_min' in ser.errors


@pytest.mark.django_db
def test_visit_create_serializer_validations(
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    therapist_b: 'TherapistProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie pacjenta lub typu terapii nienależącego do wybranego fizjoterapeuty."""
    # Arrange
    ser = VisitCreateSerializer(
        data={
            'patient_id': str(uuid.uuid4()),
            'therapy_type_id': str(therapy_type.id),
            'start_at': timezone.now().isoformat(),
            'end_at': (timezone.now() + timedelta(hours=1)).isoformat(),
        },
        context={'therapist': therapist},
    )
    # Assert
    assert ser.is_valid() is False
    assert 'patient_id' in ser.errors

    other_therapy_type = TherapyTypeSerializer().create({
        'therapist': therapist_b,
        'name': 'Inna terapia',
        'color_hex': '#FFFFFF',
        'duration_min': 30,
    })
    ser = VisitCreateSerializer(
        data={
            'patient_id': str(patient.id),
            'therapy_type_id': str(other_therapy_type.id),
            'start_at': timezone.now().isoformat(),
            'end_at': (timezone.now() + timedelta(hours=1)).isoformat(),
        },
        context={'therapist': therapist},
    )
    assert ser.is_valid() is False
    assert 'therapy_type_id' in ser.errors


@pytest.mark.django_db
def test_patient_visit_request_in_past_raises(
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie wniosku pacjenta o wizytę z datą z przeszłości."""
    # Arrange
    past_time = timezone.now() - timedelta(hours=2)
    ser = PatientVisitRequestSerializer(
        data={
            'therapy_type_id': str(therapy_type.id),
            'start_at': past_time.isoformat(),
            'end_at': (past_time + timedelta(minutes=45)).isoformat(),
        },
        context={'patient': patient},
    )
    # Assert
    assert ser.is_valid() is False
    assert 'start_at' in ser.errors


@pytest.mark.django_db
def test_visit_reschedule_completed_visit_raises(
    patient: 'PatientProfile',
    therapist: 'TherapistProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie próby przełożenia wizyty, która została już zakończona."""
    # Arrange
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now(),
        end_at=timezone.now() + timedelta(minutes=45),
        status=VisitStatus.COMPLETED,
    )
    new_start = timezone.now() + timedelta(days=1)
    ser = VisitRescheduleSerializer(
        instance=visit,
        data={
            'start_at': new_start.isoformat(),
            'end_at': (new_start + timedelta(minutes=45)).isoformat(),
        },
    )
    # Assert
    assert ser.is_valid() is False
    assert 'detail' in ser.errors


def test_visit_cancel_serializer_reason_too_long() -> None:
    """Sprawdza odrzucenie zbyt długiego powodu odwołania wizyty w serializatorze."""
    # Arrange
    ser = VisitCancelSerializer(data={'cancel_reason': 'X' * 501})
    # Assert
    assert ser.is_valid() is False
    assert 'cancel_reason' in ser.errors

