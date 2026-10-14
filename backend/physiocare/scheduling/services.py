import datetime

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from accounts.models import CustomUser
from notifications.events import (
    notify_visit_change,
    publish_document_realtime,
    publish_visit_realtime,
)
from patients.models import PatientProfile
from therapists.models import TherapistProfile

from .models import TherapyType, Visit, VisitStatus


def translate_visit_integrity_error(
    exc: Exception,
    *,
    overlap_message: str = 'Termin koliduje z inną wizytą tego terapeuty.',
) -> ValidationError:
    """Przekształca błąd spójności bazy danych (IntegrityError) na ValidationError DRF."""
    message = str(exc).lower()
    if 'exclude_overlapping_visits' in message:
        return ValidationError({'start_at': overlap_message})
    if 'chk_visits_end_after_start' in message:
        return ValidationError({'end_at': 'Koniec wizyty musi być po rozpoczęciu.'})
    return ValidationError({'detail': 'Nie udało się zapisać wizyty.'})


def maybe_publish_patient_summary(visit: Visit, previous_summary: str) -> None:
    """Publikuje w czasie rzeczywistym podsumowanie wizyty pacjenta, jeśli uległo zmianie."""
    summary = (visit.patient_summary or '').strip()
    previous = (previous_summary or '').strip()
    if summary and summary != previous:
        publish_document_realtime(visit.patient, visit.id)


@transaction.atomic
def visit_create_service(
    *,
    therapist: TherapistProfile,
    patient: PatientProfile,
    therapy_type: TherapyType,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    patient_note: str = '',
    status: str = VisitStatus.SCHEDULED,
    episode: object = None,
) -> Visit:
    """Tworzy nową wizytę, sprawdza spójność i wysyła powiadomienie."""
    try:
        visit = Visit(
            therapist=therapist,
            patient=patient,
            therapy_type=therapy_type,
            start_at=start_at,
            end_at=end_at,
            patient_note=patient_note,
            status=status,
            episode=episode,
        )
        visit.full_clean()
        visit.save()
        if status == VisitStatus.SCHEDULED:
            notify_visit_change(visit, 'scheduled')
        elif status == VisitStatus.PENDING_APPROVAL:
            publish_visit_realtime(visit, 'scheduled')
        return visit
    except IntegrityError as exc:
        raise translate_visit_integrity_error(exc) from None


@transaction.atomic
def visit_reschedule_service(
    *,
    visit: Visit,
    new_start_at: datetime.datetime,
    new_end_at: datetime.datetime,
    requested_by_user: CustomUser | None = None,
) -> Visit:
    """Przekłada termin wizyty, sprawdza kolizje i emituje zdarzenia SSE."""
    try:
        visit.start_at = new_start_at
        visit.end_at = new_end_at
        visit.full_clean()
        visit.save(update_fields=['start_at', 'end_at'])
        notify_visit_change(visit, 'rescheduled')
        return visit
    except IntegrityError as exc:
        raise translate_visit_integrity_error(exc) from None


@transaction.atomic
def visit_cancel_service(
    *,
    visit: Visit,
    cancelled_by_user: CustomUser | None = None,
    reason: str = '',
) -> Visit:
    """Anuluje wizytę ze wskazaniem powodu i powiadamia uczestników."""
    visit.status = VisitStatus.CANCELLED
    visit.cancel_reason = reason
    visit.full_clean()
    visit.save(update_fields=['status', 'cancel_reason'])
    notify_visit_change(visit, 'cancelled')
    return visit


@transaction.atomic
def visit_approve_service(
    *,
    visit: Visit,
    therapist: TherapistProfile,
) -> Visit:
    """Zatwierdza wizytę w statusie PENDING_APPROVAL przez fizjoterapeutę."""
    try:
        visit.status = VisitStatus.SCHEDULED
        visit.full_clean()
        visit.save(update_fields=['status'])
        notify_visit_change(visit, 'approved')
        return visit
    except IntegrityError as exc:
        raise translate_visit_integrity_error(exc) from None
