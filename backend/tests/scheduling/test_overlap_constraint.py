import concurrent.futures
from datetime import timedelta

import pytest
from django.db import connections, transaction
from django.db.utils import IntegrityError, OperationalError
from django.utils import timezone

from scheduling.models import Visit

pytestmark = pytest.mark.django_db(transaction=True)


def _is_deadlock(exc: OperationalError) -> bool:
    cause = getattr(exc, '__cause__', None)
    return getattr(cause, 'pgcode', None) == '40P01'


def _book_visit(therapist_id, patient_id, therapy_type_id, start_at, end_at):
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
    therapist, patient_profiles, therapy_type,
):
    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)
    workers = 10

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

    successes = sum(1 for result in results if result is True)

    assert successes == 1
    assert Visit.objects.filter(therapist=therapist, status='SCHEDULED').count() == 1


def test_cancelled_visit_does_not_block_slot(
    therapist, patient_profiles, therapy_type,
):
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

    assert Visit.objects.filter(therapist=therapist, status='SCHEDULED').count() == 1
