import pytest
from django.db import IntegrityError

from accounts.models import CustomUser, RoleChoices
from patients.models import PatientProfile
from reviews.models import Review
from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_review_rating_check_constraint_rejects_out_of_range():
    user1 = CustomUser.objects.create_user(
        email='p_c@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='A',
        last_name='B',
    )
    patient = PatientProfile.objects.create(user=user1)
    user2 = CustomUser.objects.create_user(
        email='t_c@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='C',
        last_name='D',
    )
    therapist = TherapistProfile.objects.create(user=user2)

    from django.db import transaction

    with transaction.atomic(), pytest.raises(IntegrityError):
        Review.objects.create(
            patient=patient,
            therapist=therapist,
            rating=6,
        )
