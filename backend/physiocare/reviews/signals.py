from django.db import models
from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


def _refresh_therapist_rating(therapist: object) -> None:
    """Przelicza i zapisuje denormalizowane pola ocen na profilu fizjoterapeuty.

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


@receiver(post_save, sender=Review)
def on_review_save(sender: type, instance: Review, **kwargs: object) -> None:
    """Aktualizuje statystyki ocen fizjoterapeuty po zapisaniu opinii.

    Args:
        sender (type): Klasa modelu wysyłającego sygnał.
        instance (Review): Zapisana instancja opinii.
        **kwargs (object): Dodatkowe argumenty sygnału.
    """
    _refresh_therapist_rating(instance.therapist)


@receiver(post_delete, sender=Review)
def on_review_delete(sender: type, instance: Review, **kwargs: object) -> None:
    """Aktualizuje statystyki ocen fizjoterapeuty po usunięciu opinii.

    Args:
        sender (type): Klasa modelu wysyłającego sygnał.
        instance (Review): Usunięta instancja opinii.
        **kwargs (object): Dodatkowe argumenty sygnału.
    """
    _refresh_therapist_rating(instance.therapist)
