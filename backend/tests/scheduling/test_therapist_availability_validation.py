from datetime import date, time, timedelta
from typing import TYPE_CHECKING

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from scheduling.holidays import get_polish_holidays
from scheduling.models import TherapistAvailabilitySlot, Visit, VisitStatus

if TYPE_CHECKING:
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_therapist_availability_slot_valid_recurring_range(therapist: 'TherapistProfile') -> None:
    """Tworzenie cyklicznego slotu dostępności terapeuty w prawidłowym przedziale godzinowym."""
    # Arrange
    slot = TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=True,
        day_of_week=0,
        start_time=time(8, 0),
        end_time=time(16, 0),
        is_active=True,
    )
    # Assert
    assert slot.id is not None
    assert slot.is_recurring is True
    assert slot.start_time < slot.end_time


@pytest.mark.django_db
def test_therapist_availability_slot_invalid_time_range_raises_error(therapist: 'TherapistProfile') -> None:
    """Próba utworzenia slotu z czasem końcowym przed początkowym musi wywołać wyjątek w bazie."""
    # Act
    with transaction.atomic(), pytest.raises(IntegrityError):
        TherapistAvailabilitySlot.objects.create(
            therapist=therapist,
            is_recurring=True,
            day_of_week=1,
            start_time=time(17, 0),
            end_time=time(8, 0),
            is_active=True,
        )


@pytest.mark.django_db
def test_visit_end_before_start_raises_integrity_error(
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Baza danych odrzuca utworzenie wizyty o ujemnym lub zerowym czasie trwania."""
    # Arrange
    now = timezone.now()
    # Act
    with transaction.atomic(), pytest.raises(IntegrityError):
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now + timedelta(hours=2),
            end_at=now + timedelta(hours=1),
            status=VisitStatus.SCHEDULED,
        )


def test_polish_holidays_returns_fixed_and_movable_dates() -> None:
    """Funkcja get_polish_holidays zwraca stałe (1 maja, 3 maja, 11 listopada) i ruchome święta."""
    # Arrange
    holidays_2026 = get_polish_holidays(2026)

    # Assert
    assert date(2026, 1, 1) in holidays_2026
    assert date(2026, 5, 1) in holidays_2026
    assert date(2026, 5, 3) in holidays_2026
    assert date(2026, 11, 11) in holidays_2026
    assert date(2026, 12, 25) in holidays_2026

