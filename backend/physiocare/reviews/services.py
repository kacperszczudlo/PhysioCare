from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone

from patients.models import PatientProfile
from scheduling.models import Visit
from therapists.models import TherapistProfile

from .models import Review


def refresh_therapist_rating(therapist: TherapistProfile) -> None:
    """Jawnie przelicza i zapisuje denormalizowane statystyki ocen fizjoterapeuty.

    Args:
        therapist: Instancja TherapistProfile do aktualizacji.
    """
    agg = Review.objects.filter(
        therapist=therapist,
        is_visible=True,
    ).aggregate(avg=Avg('rating'), count=Count('id'))
    therapist.rating_avg = agg['avg'] or 0
    therapist.rating_count = agg['count'] or 0
    therapist.save(update_fields=['rating_avg', 'rating_count'])


@transaction.atomic
def review_create_service(
    *,
    patient: PatientProfile,
    therapist: TherapistProfile,
    rating: int,
    comment: str = '',
    is_anonymous: bool = False,
    visit: Visit | None = None,
) -> Review:
    """Tworzy nową opinię, wymusza pełną walidację (full_clean) i odświeża statystyki terapeuty.

    Args:
        patient: Profil pacjenta wystawiającego opinię.
        therapist: Profil ocenianego fizjoterapeuty.
        rating: Ocena w skali 1-5.
        comment: Opcjonalna treść opinii.
        is_anonymous: Czy opinia ma być anonimowa.
        visit: Opcjonalna zakończona wizyta (verified review).

    Returns:
        Review: Nowo utworzona instancja opinii.
    """
    review = Review(
        patient=patient,
        therapist=therapist,
        visit=visit,
        rating=rating,
        comment=comment,
        is_anonymous=is_anonymous,
    )
    review.full_clean()
    review.save()
    refresh_therapist_rating(therapist)
    return review


@transaction.atomic
def review_edit_service(
    *,
    review: Review,
    rating: int | None = None,
    comment: str | None = None,
    is_anonymous: bool | None = None,
) -> Review:
    """Modyfikuje opinię, wymusza walidację i aktualizuje średnią ocenę terapeuty.

    Args:
        review: Instancja edytowanej opinii.
        rating: Nowa ocena (1-5).
        comment: Nowy komentarz.
        is_anonymous: Nowy status anonimowości.

    Returns:
        Review: Zaktualizowana opinia.
    """
    if rating is not None:
        review.rating = rating
    if comment is not None:
        review.comment = comment
    if is_anonymous is not None:
        review.is_anonymous = is_anonymous

    review.full_clean()
    review.save()
    refresh_therapist_rating(review.therapist)
    return review


@transaction.atomic
def review_delete_service(*, review: Review) -> None:
    """Usuwa opinię i przelicza statystyki ocen terapeuty.

    Args:
        review: Instancja usuwanej opinii.
    """
    therapist = review.therapist
    review.delete()
    refresh_therapist_rating(therapist)


@transaction.atomic
def review_reply_service(*, review: Review, therapist_reply: str) -> Review:
    """Zapisuje odpowiedź fizjoterapeuty na opinię pacjenta.

    Args:
        review: Instancja opinii.
        therapist_reply: Tekst odpowiedzi fizjoterapeuty.

    Returns:
        Review: Zaktualizowana opinia z odpowiedzią i znacznikiem czasu.
    """
    review.therapist_reply = therapist_reply
    review.therapist_replied_at = timezone.now()
    review.full_clean()
    review.save(update_fields=['therapist_reply', 'therapist_replied_at'])
    return review
