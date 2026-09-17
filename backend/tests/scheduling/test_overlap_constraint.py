import concurrent.futures
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
import uuid

import pytest
from django.db import connections, transaction
from django.db.utils import IntegrityError, OperationalError
from django.utils import timezone

from scheduling.models import Visit

if TYPE_CHECKING:
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile

pytestmark = pytest.mark.django_db(transaction=True)


def _is_deadlock(exc: OperationalError) -> bool:
    """Sprawdza, czy wyjątek bazodanowy jest rezultatem zakleszczenia (deadlock 40P01).

    Args:
        exc (OperationalError): Wyjątek bazy danych.

    Returns:
        bool: True jeśli kod błędu to 40P01, False w przeciwnym razie.
    """
    cause = exc.__cause__ if hasattr(exc, '__cause__') else None
    pgcode = cause.pgcode if cause is not None and hasattr(cause, 'pgcode') else None
    return pgcode == '40P01'


def _book_visit(
    therapist_id: str | uuid.UUID,
    patient_id: str | uuid.UUID,
    therapy_type_id: str | uuid.UUID,
    start_at: datetime,
    end_at: datetime,
) -> bool:
    """Funkcja pomocnicza do współbieżnego tworzenia wizyty z obsługą zakleszczeń bazy danych."""
    connections.close_all()
    try:
        with transaction.atomic():
            Visit.objects.create(
                therapist_id=therapist_id,
                patient_id=patient_id,
                therapy_type_id=therapy_type_id,
                start_at=start_at,
                end_at=end_at,
                location_address='Gabinet 1',
            )
        return True
    except IntegrityError:
        return False
    except OperationalError as exc:
        if _is_deadlock(exc):
            return False
        raise


def test_concurrent_bookings_reject_overlapping_slot(
    therapist: 'TherapistProfile',
    patient_profiles: list['PatientProfile'],
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie nakładających się rezerwacji w warunkach współbieżności przy użyciu blokady bazy danych."""
    # Arrange
    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)
    workers: int = 10

    # Act
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _book_visit,
                therapist.id,
                patient_profiles[index].id,
                therapy_type.id,
                start_at,
                end_at,
            )
            for index in range(workers)
        ]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    successes: int = sum(1 for result in results if result is True)

    # Assert
    assert successes == 1
    assert Visit.objects.filter(therapist=therapist, status='SCHEDULED').count() == 1


def test_cancelled_visit_does_not_block_slot(
    therapist: 'TherapistProfile',
    patient_profiles: list['PatientProfile'],
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza, że anulowana wizyta nie blokuje ponownego zarezerwowania tego samego slotu czasowego."""
    # Arrange
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=1)

    Visit.objects.create(
        therapist=therapist,
        patient=patient_profiles[0],
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status='CANCELLED',
        location_address='Gabinet 1',
    )

    Visit.objects.create(
        therapist=therapist,
        patient=patient_profiles[1],
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        location_address='Gabinet 1',
    )

    # Assert
    assert Visit.objects.filter(therapist=therapist, status='SCHEDULED').count() == 1

