import concurrent.futures
from datetime import timedelta

import pytest
from django.db import IntegrityError, connections, transaction
from django.utils import timezone

from conftest import requires_postgres
from scheduling.models import Visit

pytestmark = [pytest.mark.django_db(transaction=True), requires_postgres]


def _book_visit(therapist_id, patient_id, start_at, end_at):
    connections.close_all()
    try:
        with transaction.atomic():
            Visit.objects.create(
                therapist_id=therapist_id,
                patient_id=patient_id,
                start_at=start_at,
                end_at=end_at,
                location_address='Gabinet 1',
            )
        return None
    except IntegrityError as exc:
        return exc


def test_concurrent_bookings_reject_overlapping_slot(therapist, patient_profiles):
    """
    Symuluje wyścig TOCTOU: wiele równoległych rezerwacji tego samego slotu.
    Baza musi przepuścić dokładnie jedną wizytę i odrzucić resztę IntegrityError.
    """
    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)
    workers = 10

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _book_visit,
                therapist.id,
                patient_profiles[index].id,
                start_at,
                end_at,
            )
            for index in range(workers)
        ]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    integrity_errors = [result for result in results if isinstance(result, IntegrityError)]

    assert len(integrity_errors) == workers - 1
    assert Visit.objects.filter(therapist=therapist, status='SCHEDULED').count() == 1


def test_cancelled_visit_does_not_block_slot(therapist, patient_profiles):
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=1)

    Visit.objects.create(
        therapist=therapist,
        patient=patient_profiles[0],
        start_at=start_at,
        end_at=end_at,
        status='CANCELLED',
        location_address='Gabinet 1',
    )

    Visit.objects.create(
        therapist=therapist,
        patient=patient_profiles[1],
        start_at=start_at,
        end_at=end_at,
        location_address='Gabinet 1',
    )

    assert Visit.objects.filter(therapist=therapist, status='SCHEDULED').count() == 1
