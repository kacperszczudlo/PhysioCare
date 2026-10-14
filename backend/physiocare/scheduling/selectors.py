import datetime

from django.db.models import QuerySet
from django.utils import timezone

from patients.models import PatientProfile
from therapists.models import TherapistProfile

from .models import TherapistAvailabilitySlot, Visit, VisitStatus


def visit_related_fields() -> tuple[str, ...]:
    """Zwraca relacje do wstępnego dociągnięcia (select_related) dla wizyty."""
    return (
        'patient',
        'patient__user',
        'therapist',
        'therapist__user',
        'therapy_type',
        'episode',
        'review',
    )


def visit_list_for_therapist_selector(
    therapist: TherapistProfile,
    *,
    date_param: str | None = None,
    upcoming: bool = False,
    pending: bool = False,
    limit: int | None = None,
) -> QuerySet[Visit]:
    """Pobiera i optymalizuje listę wizyt fizjoterapeuty.

    Args:
        therapist: Profil fizjoterapeuty.
        date_param: Opcjonalny filtr daty w formacie ISO (YYYY-MM-DD).
        upcoming: Czy filtrować tylko nadchodzące zaplanowane wizyty.
        pending: Czy filtrować wizyty oczekujące na zatwierdzenie.
        limit: Opcjonalny limit liczby wizyt.

    Returns:
        QuerySet[Visit]: Zestaw wizyt z prewencją N+1.
    """
    qs = Visit.objects.filter(therapist=therapist).select_related(*visit_related_fields())

    if date_param:
        try:
            parsed_date = datetime.date.fromisoformat(date_param)
            tz = timezone.get_current_timezone()
            day_start = timezone.make_aware(
                datetime.datetime.combine(parsed_date, datetime.time.min),
                tz,
            )
            day_end = timezone.make_aware(
                datetime.datetime.combine(
                    parsed_date + datetime.timedelta(days=1), datetime.time.min
                ),
                tz,
            )
            qs = qs.filter(start_at__gte=day_start, start_at__lt=day_end)
        except (ValueError, TypeError):
            qs = qs.filter(start_at__date=date_param)

    if upcoming:
        qs = qs.filter(
            status=VisitStatus.SCHEDULED,
            end_at__gte=timezone.now(),
        )

    if pending:
        qs = qs.filter(status=VisitStatus.PENDING_APPROVAL)

    qs = qs.order_by('start_at')

    if limit is not None and limit > 0:
        return qs[:limit]

    return qs


def visit_list_for_patient_selector(
    patient: PatientProfile,
    *,
    upcoming: bool = False,
    limit: int | None = None,
) -> QuerySet[Visit]:
    """Pobiera i optymalizuje listę wizyt pacjenta.

    Args:
        patient: Profil pacjenta.
        upcoming: Czy filtrować tylko nadchodzące wizyty.
        limit: Opcjonalny limit liczby wizyt.

    Returns:
        QuerySet[Visit]: Zestaw wizyt pacjenta.
    """
    qs = Visit.objects.filter(patient=patient).select_related(*visit_related_fields())

    if upcoming:
        qs = qs.filter(
            status=VisitStatus.SCHEDULED,
            end_at__gte=timezone.now(),
        )

    qs = qs.order_by('start_at')

    if limit is not None and limit > 0:
        return qs[:limit]

    return qs


def therapist_availability_slots_selector(
    therapist: TherapistProfile,
) -> QuerySet[TherapistAvailabilitySlot]:
    """Pobiera sloty dostępności danego fizjoterapeuty.

    Args:
        therapist: Profil fizjoterapeuty.

    Returns:
        QuerySet[TherapistAvailabilitySlot]: Zbiór slotów posortowanych po czasie.
    """
    return (
        TherapistAvailabilitySlot.objects.filter(therapist=therapist)
        .select_related('therapist__user')
        .order_by('day_of_week', 'start_time', 'start_at')
    )
