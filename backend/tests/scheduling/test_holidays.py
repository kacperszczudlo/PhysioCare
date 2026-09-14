from datetime import date, datetime, timezone, timedelta
import pytest

from scheduling.holidays import get_easter_date, get_polish_holidays, is_polish_holiday
from scheduling.models import TherapistAvailabilitySlot
from scheduling.serializers import is_visit_within_therapist_availability


def test_easter_date_calculation():
    # Known Easter Sunday dates
    assert get_easter_date(2024) == date(2024, 3, 31)
    assert get_easter_date(2025) == date(2025, 4, 20)
    assert get_easter_date(2026) == date(2026, 4, 5)
    assert get_easter_date(2028) == date(2028, 4, 16)  # Przestępny rok


def test_polish_holidays_2026():
    holidays = get_polish_holidays(2026)
    assert holidays[date(2026, 1, 1)] == 'Nowy Rok'
    assert holidays[date(2026, 1, 6)] == 'Święto Trzech Króli'
    assert holidays[date(2026, 4, 5)] == 'Wielkanoc (Pierwszy Dzień)'
    assert holidays[date(2026, 4, 6)] == 'Poniedziałek Wielkanocny'
    assert holidays[date(2026, 5, 1)] == 'Święto Pracy'
    assert holidays[date(2026, 5, 3)] == 'Święto Konstytucji 3 Maja'
    assert holidays[date(2026, 5, 24)] == 'Zielone Świątki'
    assert holidays[date(2026, 6, 4)] == 'Boże Ciało'
    assert holidays[date(2026, 8, 15)] == 'Wniebowzięcie Najświętszej Maryi Panny'
    assert holidays[date(2026, 11, 1)] == 'Wszystkich Świętych'
    assert holidays[date(2026, 11, 11)] == 'Święto Niepodległości'
    assert holidays[date(2026, 12, 25)] == 'Boże Narodzenie (Pierwszy Dzień)'
    assert holidays[date(2026, 12, 26)] == 'Boże Narodzenie (Drugi Dzień)'

    is_hol, name = is_polish_holiday(date(2026, 11, 11))
    assert is_hol is True
    assert name == 'Święto Niepodległości'

    is_workday, name_none = is_polish_holiday(date(2026, 11, 12))
    assert is_workday is False
    assert name_none is None


@pytest.mark.django_db
def test_no_availability_slots_blocks_booking(therapist):
    # Therapist has 0 slots configured
    from django.utils import timezone as django_tz
    now = django_tz.now().replace(hour=10, minute=0, second=0, microsecond=0)
    start_at = now + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)

    # Must return False (no booking without configured grafik)
    assert is_visit_within_therapist_availability(therapist, start_at, end_at) is False


@pytest.mark.django_db
def test_recurring_slot_suppressed_on_statutory_holiday(therapist):
    # Mon Apr 6, 2026 is Easter Monday (Drugi Dzień Wielkanocy)
    # Recurring slot for Monday (day_of_week=0)
    TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=True,
        day_of_week=0,
        start_time='08:00:00',
        end_time='16:00:00',
    )

    # April 6, 2026 10:00 - Monday
    easter_monday_start = datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)
    easter_monday_end = easter_monday_start + timedelta(minutes=45)

    # Recurring slot alone DOES NOT allow booking on Easter Monday
    assert is_visit_within_therapist_availability(therapist, easter_monday_start, easter_monday_end) is False

    # Normal Monday (Apr 13, 2026) DOES allow booking
    normal_monday_start = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
    normal_monday_end = normal_monday_start + timedelta(minutes=45)
    assert is_visit_within_therapist_availability(therapist, normal_monday_start, normal_monday_end) is True


@pytest.mark.django_db
def test_therapist_holiday_override_slot_allows_booking(therapist):
    # Explicit single-date slot on Easter Monday
    easter_monday_start = datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc)
    easter_monday_end = easter_monday_start + timedelta(minutes=45)

    TherapistAvailabilitySlot.objects.create(
        therapist=therapist,
        is_recurring=False,
        start_at=easter_monday_start - timedelta(hours=1),
        end_at=easter_monday_end + timedelta(hours=1),
    )

    # Explicit override allows booking on holiday
    assert is_visit_within_therapist_availability(therapist, easter_monday_start, easter_monday_end) is True

