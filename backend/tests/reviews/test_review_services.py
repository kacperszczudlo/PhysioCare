import pytest

from accounts.models import CustomUser, RoleChoices
from patients.models import PatientProfile
from reviews.models import Review
from reviews.services import (
    review_create_service,
    review_delete_service,
    review_edit_service,
    review_reply_service,
)
from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_review_create_and_delete_updates_therapist_rating_explicitly():
    u_t = CustomUser.objects.create_user(
        email='t_srv@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='T',
        last_name='Srv',
    )
    t = TherapistProfile.objects.create(user=u_t)
    u_p = CustomUser.objects.create_user(
        email='p_srv@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='P',
        last_name='Srv',
    )
    p = PatientProfile.objects.create(user=u_p)

    # 1. Utworzenie opinii 5
    rev = review_create_service(patient=p, therapist=t, rating=5, comment='Super')
    assert isinstance(rev, Review)
    t.refresh_from_db()
    assert t.rating_count == 1
    assert t.rating_avg == 5.0

    # 2. Edycja opinii na 3
    review_edit_service(review=rev, rating=3)
    t.refresh_from_db()
    assert t.rating_count == 1
    assert t.rating_avg == 3.0

    # 3. Odpowiedź terapeuty
    review_reply_service(review=rev, therapist_reply='Dziękuję za opinię!')
    rev.refresh_from_db()
    assert rev.therapist_reply == 'Dziękuję za opinię!'
    assert rev.therapist_replied_at is not None

    # 4. Usunięcie opinii
    review_delete_service(review=rev)
    t.refresh_from_db()
    assert t.rating_count == 0
    assert t.rating_avg == 0.0
