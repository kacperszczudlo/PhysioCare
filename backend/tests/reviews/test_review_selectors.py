import pytest

from accounts.models import CustomUser, RoleChoices
from patients.models import PatientProfile
from reviews.models import Review
from reviews.selectors import (
    review_list_for_therapist_selector,
    therapist_rating_summary_selector,
)
from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_review_list_for_therapist_selector_filters_and_prefetches():
    u_t = CustomUser.objects.create_user(
        email='t_sel@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='T',
        last_name='S',
    )
    t = TherapistProfile.objects.create(user=u_t)
    u_p = CustomUser.objects.create_user(
        email='p_sel@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='P',
        last_name='S',
    )
    p = PatientProfile.objects.create(user=u_p)

    Review.objects.create(therapist=t, patient=p, rating=5, is_visible=True)
    Review.objects.create(therapist=t, patient=p, rating=3, is_visible=True)
    Review.objects.create(therapist=t, patient=p, rating=1, is_visible=False)

    qs = review_list_for_therapist_selector(str(t.id), rating=5)
    assert qs.count() == 1
    assert qs.first().rating == 5


@pytest.mark.django_db
def test_therapist_rating_summary_selector_breakdown():
    u_t = CustomUser.objects.create_user(
        email='t_sum@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='T',
        last_name='Sum',
    )
    t = TherapistProfile.objects.create(user=u_t, rating_avg=4.5, rating_count=2)
    u_p = CustomUser.objects.create_user(
        email='p_sum@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='P',
        last_name='Sum',
    )
    p = PatientProfile.objects.create(user=u_p)

    Review.objects.create(therapist=t, patient=p, rating=5, is_visible=True)
    Review.objects.create(therapist=t, patient=p, rating=4, is_visible=True)

    summary = therapist_rating_summary_selector(str(t.id))
    assert summary['total_reviews'] == 2
    assert summary['rating_breakdown']['5'] == 1
    assert summary['rating_breakdown']['4'] == 1
