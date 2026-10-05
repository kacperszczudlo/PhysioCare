"""Testy systemu opinii i ocen fizjoterapeutów w PhysioCare.

Pokrycie:
- Happy path (tworzenie, odczyt, podsumowanie)
- Walidacja (złe statusy wizyty, duplikat, zakres oceny)
- BOLA/IDOR (pacjent A vs wizyta B, terapeuta A vs opinia B)
- Agregacja (przeliczanie rating_avg/rating_count, ukryte opinie)
- Odpowiedź terapeuty (dodanie, aktualizacja, pusta odpowiedź)
- Edycja opinii przez pacjenta (okno 14 dni)
"""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from patients.models import PatientProfile
from reviews.models import Review
from scheduling.models import TherapyType, Visit, VisitStatus
from therapists.models import TherapistProfile

User = get_user_model()

# ---------------------------------------------------------------------------
# Fixtures pomocnicze
# ---------------------------------------------------------------------------


@pytest.fixture
def patient_b(db: object, therapist: TherapistProfile) -> PatientProfile:
    """Tworzy drugi profil pacjenta do testów BOLA/IDOR."""
    user = User.objects.create_user(
        email='patientb@physiocare.test',
        password='test-pass',
        role='PATIENT',
        first_name='Drugi',
        last_name='Pacjent',
        email_verified_at=timezone.now(),
    )
    return PatientProfile.objects.create(user=user, therapist=therapist)


@pytest.fixture
def completed_visit(db: object, patient: PatientProfile, therapist: TherapistProfile, therapy_type: TherapyType) -> Visit:
    """Tworzy zakończoną wizytę (COMPLETED) pacjenta u fizjoterapeuty."""
    return Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() - timedelta(hours=2),
        end_at=timezone.now() - timedelta(hours=1),
        status=VisitStatus.COMPLETED,
    )


@pytest.fixture
def completed_visit_b(db: object, patient_b: PatientProfile, therapist: TherapistProfile, therapy_type: TherapyType) -> Visit:
    """Tworzy zakończoną wizytę dla drugiego pacjenta."""
    return Visit.objects.create(
        patient=patient_b,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() - timedelta(hours=4),
        end_at=timezone.now() - timedelta(hours=3),
        status=VisitStatus.COMPLETED,
    )


@pytest.fixture
def scheduled_visit(db: object, patient: PatientProfile, therapist: TherapistProfile, therapy_type: TherapyType) -> Visit:
    """Tworzy zaplanowaną wizytę (SCHEDULED)."""
    return Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() + timedelta(hours=2),
        end_at=timezone.now() + timedelta(hours=3),
        status=VisitStatus.SCHEDULED,
    )


@pytest.fixture
def cancelled_visit(db: object, patient: PatientProfile, therapist: TherapistProfile, therapy_type: TherapyType) -> Visit:
    """Tworzy anulowaną wizytę (CANCELLED)."""
    return Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() - timedelta(hours=5),
        end_at=timezone.now() - timedelta(hours=4),
        status=VisitStatus.CANCELLED,
    )


@pytest.fixture
def no_show_visit(db: object, patient: PatientProfile, therapist: TherapistProfile, therapy_type: TherapyType) -> Visit:
    """Tworzy wizytę z nieobecnością pacjenta (NO_SHOW)."""
    return Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() - timedelta(hours=6),
        end_at=timezone.now() - timedelta(hours=5),
        status=VisitStatus.NO_SHOW,
    )


@pytest.fixture
def review(db: object, patient: PatientProfile, therapist: TherapistProfile, completed_visit: Visit) -> Review:
    """Tworzy opinię 5★ od pacjenta do zakończonej wizyty."""
    return Review.objects.create(
        patient=patient,
        therapist=therapist,
        visit=completed_visit,
        rating=5,
        comment='Świetny fizjoterapeuta!',
        is_anonymous=False,
    )


@pytest.fixture
def patient_client(patient: PatientProfile) -> APIClient:
    """APIClient zalogowany jako pacjent."""
    client = APIClient()
    client.force_authenticate(user=patient.user)
    return client


@pytest.fixture
def patient_b_client(patient_b: PatientProfile) -> APIClient:
    """APIClient zalogowany jako drugi pacjent."""
    client = APIClient()
    client.force_authenticate(user=patient_b.user)
    return client


@pytest.fixture
def therapist_client(therapist: TherapistProfile) -> APIClient:
    """APIClient zalogowany jako fizjoterapeuta."""
    client = APIClient()
    client.force_authenticate(user=therapist.user)
    return client


@pytest.fixture
def therapist_b_client(therapist_b: TherapistProfile) -> APIClient:
    """APIClient zalogowany jako drugi fizjoterapeuta."""
    client = APIClient()
    client.force_authenticate(user=therapist_b.user)
    return client


# ---------------------------------------------------------------------------
# 1. Happy path — tworzenie opinii
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_patient_can_review_completed_visit(patient_client: APIClient, completed_visit: Visit) -> None:
    """Pacjent może wystawić opinię dla zakończonej wizyty → HTTP 201."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    payload = {'rating': 5, 'comment': 'Doskonały terapeuta.', 'is_anonymous': False}

    response = patient_client.post(url, payload, format='json')

    assert response.status_code == 201
    assert response.data['rating'] == 5
    assert response.data['is_verified'] is True


@pytest.mark.django_db
def test_review_creates_verified_flag(patient_client: APIClient, completed_visit: Visit) -> None:
    """Opinia powiązana z wizytą ma is_verified=True."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_client.post(url, {'rating': 4, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 201
    assert response.data['is_verified'] is True


@pytest.mark.django_db
def test_anonymous_review_hides_name(patient_client: APIClient, completed_visit: Visit) -> None:
    """Opinia z is_anonymous=True → author_name='Pacjent PhysioCare'."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_client.post(url, {'rating': 3, 'comment': 'OK', 'is_anonymous': True}, format='json')

    assert response.status_code == 201
    assert response.data['author_name'] == 'Pacjent PhysioCare'


@pytest.mark.django_db
def test_non_anonymous_review_shows_abbreviated_name(
    patient_client: APIClient, completed_visit: Visit, patient: PatientProfile
) -> None:
    """Opinia z is_anonymous=False → author_name = 'Imię P.' (skrócone nazwisko)."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_client.post(url, {'rating': 5, 'comment': 'Super!', 'is_anonymous': False}, format='json')

    assert response.status_code == 201
    first = patient.user.first_name
    last_initial = patient.user.last_name[0]
    assert response.data['author_name'] == f'{first} {last_initial}.'


# ---------------------------------------------------------------------------
# 2. Walidacja — złe statusy wizyty
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cannot_review_scheduled_visit(patient_client: APIClient, scheduled_visit: Visit) -> None:
    """Wizyta SCHEDULED → 400."""
    url = f'/api/v1/visits/{scheduled_visit.id}/review/'
    response = patient_client.post(url, {'rating': 5, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_cannot_review_cancelled_visit(patient_client: APIClient, cancelled_visit: Visit) -> None:
    """Wizyta CANCELLED → 400."""
    url = f'/api/v1/visits/{cancelled_visit.id}/review/'
    response = patient_client.post(url, {'rating': 5, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_cannot_review_no_show_visit(patient_client: APIClient, no_show_visit: Visit) -> None:
    """Wizyta NO_SHOW → 400."""
    url = f'/api/v1/visits/{no_show_visit.id}/review/'
    response = patient_client.post(url, {'rating': 5, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_cannot_review_same_visit_twice(patient_client: APIClient, review: Review) -> None:
    """Próba wystawienia drugiej opinii do tej samej wizyty → 400."""
    url = f'/api/v1/visits/{review.visit.id}/review/'
    response = patient_client.post(url, {'rating': 4, 'comment': 'Drugie', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_rating_zero_is_invalid(patient_client: APIClient, completed_visit: Visit) -> None:
    """rating=0 → 400."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_client.post(url, {'rating': 0, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_rating_six_is_invalid(patient_client: APIClient, completed_visit: Visit) -> None:
    """rating=6 → 400."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_client.post(url, {'rating': 6, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_rating_required(patient_client: APIClient, completed_visit: Visit) -> None:
    """Brak pola rating → 400."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_client.post(url, {'comment': 'Bez oceny', 'is_anonymous': False}, format='json')

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# 3. BOLA / IDOR — bezpieczeństwo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_patient_cannot_review_other_patients_visit(
    patient_b_client: APIClient, completed_visit: Visit
) -> None:
    """Pacjent B nie może wystawić opinii do wizyty pacjenta A → 403."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = patient_b_client.post(url, {'rating': 1, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_therapist_cannot_create_review(therapist_client: APIClient, completed_visit: Visit) -> None:
    """Zalogowany terapeuta nie może wystawiać opinii (rola THERAPIST) → 403."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = therapist_client.post(url, {'rating': 5, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_cannot_create_review(api_client: APIClient, completed_visit: Visit) -> None:
    """Niezalogowany użytkownik → 401."""
    url = f'/api/v1/visits/{completed_visit.id}/review/'
    response = api_client.post(url, {'rating': 5, 'comment': '', 'is_anonymous': False}, format='json')

    assert response.status_code == 401


@pytest.mark.django_db
def test_therapist_a_cannot_reply_to_therapist_b_review(
    therapist_b_client: APIClient, review: Review
) -> None:
    """Terapeuta B nie może odpowiedzieć na opinię terapeuty A → 403."""
    url = f'/api/v1/reviews/{review.id}/reply/'
    response = therapist_b_client.post(url, {'therapist_reply': 'Próba odpowiedzi'}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_cannot_edit_other_patients_review(
    patient_b_client: APIClient, review: Review
) -> None:
    """Pacjent B nie może edytować opinii pacjenta A → 404 (queryset filtruje po owner)."""
    url = f'/api/v1/reviews/{review.id}/edit/'
    response = patient_b_client.patch(url, {'rating': 1}, format='json')

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 4. Agregacja — denormalizacja rating_avg / rating_count
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rating_avg_updated_on_new_review(
    patient: PatientProfile, therapist: TherapistProfile, completed_visit: Visit
) -> None:
    """Po dodaniu opinii rating_avg i rating_count są przeliczane przez sygnał."""
    therapist.refresh_from_db()
    assert therapist.rating_count == 0

    Review.objects.create(
        patient=patient, therapist=therapist, visit=completed_visit, rating=5, comment='',
    )

    therapist.refresh_from_db()
    assert therapist.rating_count == 1
    assert float(therapist.rating_avg) == 5.0


@pytest.mark.django_db
def test_rating_avg_updated_on_delete(
    patient: PatientProfile, therapist: TherapistProfile, completed_visit: Visit
) -> None:
    """Po usunięciu jedynej opinii rating_avg wraca do 0."""
    r = Review.objects.create(
        patient=patient, therapist=therapist, visit=completed_visit, rating=4, comment='',
    )
    r.delete()

    therapist.refresh_from_db()
    assert therapist.rating_count == 0
    assert float(therapist.rating_avg) == 0.0


@pytest.mark.django_db
def test_rating_avg_excludes_hidden_reviews(
    patient: PatientProfile, patient_b: PatientProfile,
    therapist: TherapistProfile, completed_visit: Visit, completed_visit_b: Visit,
) -> None:
    """Ukryta opinia (is_visible=False) nie wlicza się do rating_avg."""
    Review.objects.create(
        patient=patient, therapist=therapist, visit=completed_visit, rating=5, comment='',
    )
    hidden = Review.objects.create(
        patient=patient_b, therapist=therapist, visit=completed_visit_b,
        rating=1, comment='', is_visible=False,
    )
    # Ręcznie odpalamy sygnał przez save (is_visible=False → nie wliczane)
    hidden.save()

    therapist.refresh_from_db()
    assert therapist.rating_count == 1
    assert float(therapist.rating_avg) == 5.0


@pytest.mark.django_db
def test_rating_avg_zero_when_no_reviews(therapist: TherapistProfile) -> None:
    """Terapeuta bez opinii → rating_avg=0.00, rating_count=0."""
    therapist.refresh_from_db()
    assert therapist.rating_count == 0
    assert float(therapist.rating_avg) == 0.0


@pytest.mark.django_db
def test_rating_avg_multiple_reviews(
    patient: PatientProfile, patient_b: PatientProfile,
    therapist: TherapistProfile, completed_visit: Visit, completed_visit_b: Visit,
) -> None:
    """Średnia z 5★ i 3★ = 4.00."""
    Review.objects.create(patient=patient, therapist=therapist, visit=completed_visit, rating=5)
    Review.objects.create(patient=patient_b, therapist=therapist, visit=completed_visit_b, rating=3)

    therapist.refresh_from_db()
    assert therapist.rating_count == 2
    assert float(therapist.rating_avg) == 4.0


# ---------------------------------------------------------------------------
# 5. Publiczne endpointy — lista i podsumowanie
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_reviews_returns_visible_only(
    patient_client: APIClient, therapist: TherapistProfile,
    patient: PatientProfile, completed_visit: Visit,
    patient_b: PatientProfile, completed_visit_b: Visit,
) -> None:
    """GET /therapists/<id>/reviews/ zwraca tylko is_visible=True."""
    Review.objects.create(patient=patient, therapist=therapist, visit=completed_visit, rating=5)
    Review.objects.create(
        patient=patient_b, therapist=therapist, visit=completed_visit_b, rating=2, is_visible=False,
    )

    url = f'/api/v1/therapists/{therapist.id}/reviews/'
    response = patient_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['rating'] == 5


@pytest.mark.django_db
def test_list_reviews_filterable_by_rating(
    patient_client: APIClient, therapist: TherapistProfile,
    patient: PatientProfile, completed_visit: Visit,
    patient_b: PatientProfile, completed_visit_b: Visit,
) -> None:
    """?rating=5 zwraca tylko pięciogwiazdkowe opinie."""
    Review.objects.create(patient=patient, therapist=therapist, visit=completed_visit, rating=5)
    Review.objects.create(patient=patient_b, therapist=therapist, visit=completed_visit_b, rating=3)

    url = f'/api/v1/therapists/{therapist.id}/reviews/?rating=5'
    response = patient_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_rating_summary_correct_breakdown(
    patient_client: APIClient, therapist: TherapistProfile,
    patient: PatientProfile, completed_visit: Visit,
    patient_b: PatientProfile, completed_visit_b: Visit,
) -> None:
    """GET /therapists/<id>/rating-summary/ zwraca poprawny breakdown."""
    Review.objects.create(patient=patient, therapist=therapist, visit=completed_visit, rating=5)
    Review.objects.create(patient=patient_b, therapist=therapist, visit=completed_visit_b, rating=3)

    therapist.refresh_from_db()

    url = f'/api/v1/therapists/{therapist.id}/rating-summary/'
    response = patient_client.get(url)

    assert response.status_code == 200
    assert response.data['total_reviews'] == 2
    assert response.data['rating_breakdown']['5'] == 1
    assert response.data['rating_breakdown']['3'] == 1
    assert response.data['rating_breakdown']['1'] == 0


@pytest.mark.django_db
def test_unauthenticated_cannot_list_reviews(api_client: APIClient, therapist: TherapistProfile) -> None:
    """Niezalogowany → 401 na liście opinii."""
    url = f'/api/v1/therapists/{therapist.id}/reviews/'
    response = api_client.get(url)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 6. Odpowiedź fizjoterapeuty
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_therapist_can_reply_to_own_review(therapist_client: APIClient, review: Review) -> None:
    """Terapeuta może odpowiedzieć na własną opinię → 200, therapist_replied_at ustawiony."""
    url = f'/api/v1/reviews/{review.id}/reply/'
    response = therapist_client.post(url, {'therapist_reply': 'Dziękuję za opinię!'}, format='json')

    assert response.status_code == 200
    assert response.data['therapist_reply'] == 'Dziękuję za opinię!'
    assert response.data['therapist_replied_at'] is not None


@pytest.mark.django_db
def test_therapist_reply_empty_fails(therapist_client: APIClient, review: Review) -> None:
    """Pusta odpowiedź → 400."""
    url = f'/api/v1/reviews/{review.id}/reply/'
    response = therapist_client.post(url, {'therapist_reply': '   '}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_therapist_can_update_reply(therapist_client: APIClient, review: Review) -> None:
    """Terapeuta może zaktualizować istniejącą odpowiedź → 200."""
    url = f'/api/v1/reviews/{review.id}/reply/'
    therapist_client.post(url, {'therapist_reply': 'Pierwsza odpowiedź'}, format='json')
    response = therapist_client.post(url, {'therapist_reply': 'Zaktualizowana odpowiedź'}, format='json')

    assert response.status_code == 200
    assert response.data['therapist_reply'] == 'Zaktualizowana odpowiedź'


@pytest.mark.django_db
def test_patient_cannot_reply(patient_client: APIClient, review: Review) -> None:
    """Pacjent nie może dodać odpowiedzi fizjoterapeuty → 403."""
    url = f'/api/v1/reviews/{review.id}/reply/'
    response = patient_client.post(url, {'therapist_reply': 'Próba'}, format='json')

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 7. Edycja opinii przez pacjenta (okno 14 dni)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_patient_can_edit_review_within_14_days(patient_client: APIClient, review: Review) -> None:
    """Edycja opinii w oknie 14 dni → 200, rating zmieniony."""
    url = f'/api/v1/reviews/{review.id}/edit/'
    response = patient_client.patch(url, {'rating': 3}, format='json')

    assert response.status_code == 200
    assert response.data['rating'] == 3


@pytest.mark.django_db
def test_patient_cannot_edit_review_after_14_days(patient_client: APIClient, review: Review) -> None:
    """Edycja po 14 dniach → 400."""
    # Cofamy created_at o 15 dni
    Review.objects.filter(pk=review.pk).update(created_at=timezone.now() - timedelta(days=15))
    review.refresh_from_db()

    url = f'/api/v1/reviews/{review.id}/edit/'
    response = patient_client.patch(url, {'rating': 1}, format='json')

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# 8. TherapistPublicSerializer — pola rating
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_therapist_public_list_includes_rating_fields(
    patient_client: APIClient, therapist: TherapistProfile
) -> None:
    """GET /therapists/public/ → wynik zawiera rating_avg i rating_count."""
    url = '/api/v1/therapists/public/'
    response = patient_client.get(url)

    assert response.status_code == 200
    assert len(response.data['results']) >= 1
    first = response.data['results'][0]
    assert 'rating_avg' in first
    assert 'rating_count' in first


@pytest.mark.django_db
def test_therapist_public_detail_includes_rating_fields(
    patient_client: APIClient, therapist: TherapistProfile
) -> None:
    """GET /therapists/<id>/public/ → wynik zawiera rating_avg i rating_count."""
    url = f'/api/v1/therapists/{therapist.id}/public/'
    response = patient_client.get(url)

    assert response.status_code == 200
    assert 'rating_avg' in response.data
    assert 'rating_count' in response.data


# ---------------------------------------------------------------------------
# 9. Dodawanie opinii bezpośrednio z profilu fizjoterapeuty (z i bez wizyty)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_direct_review_without_visit_success(
    patient_client: APIClient, therapist: TherapistProfile
) -> None:
    """Pacjent dodaje opinię z profilu terapeuty bez ukończonej wizyty."""
    url = f'/api/v1/therapists/{therapist.id}/reviews/create/'
    payload = {'rating': 5, 'comment': 'Świetny specjalista, kontakt telefoniczny.', 'is_anonymous': False}
    response = patient_client.post(url, payload, format='json')

    assert response.status_code == 201
    assert response.data['rating'] == 5
    assert response.data['is_verified'] is False
    assert response.data['is_own'] is True


@pytest.mark.django_db
def test_direct_review_auto_links_completed_visit(
    patient_client: APIClient, therapist: TherapistProfile, completed_visit: Visit
) -> None:
    """Pacjent dodaje opinię z profilu fizjoterapeuty i automatycznie wiąże się ona z ukończoną wizytą."""
    url = f'/api/v1/therapists/{therapist.id}/reviews/create/'
    payload = {'rating': 5, 'comment': 'Byliśmy na wizycie, bardzo polecam.', 'is_anonymous': False}
    response = patient_client.post(url, payload, format='json')

    assert response.status_code == 201
    assert response.data['rating'] == 5
    assert response.data['is_verified'] is True


@pytest.mark.django_db
def test_direct_review_duplicate_fails(
    patient_client: APIClient, therapist: TherapistProfile
) -> None:
    """Pacjent nie może dodać drugiej recenzji z profilu tego samego fizjoterapeuty."""
    url = f'/api/v1/therapists/{therapist.id}/reviews/create/'
    patient_client.post(url, {'rating': 5, 'comment': 'Pierwsza'}, format='json')
    response = patient_client.post(url, {'rating': 4, 'comment': 'Druga'}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_therapist_dashboard_stats_includes_ratings(
    therapist_client: APIClient, review: Review
) -> None:
    """Sprawdza, czy endpoint pulpitu terapeuty zwraca zagregowane dane o ocenach."""
    response = therapist_client.get('/api/v1/therapist/dashboard/stats/')

    assert response.status_code == 200
    assert response.data['rating_avg'] == 5.0
    assert response.data['rating_count'] == 1

