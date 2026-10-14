import contextlib

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPatient, IsTherapist
from scheduling.models import Visit

from .models import Review
from .serializers import (
    RatingSummarySerializer,
    ReviewCreateSerializer,
    ReviewEditSerializer,
    ReviewReadSerializer,
    ReviewReplySerializer,
    TherapistDirectReviewCreateSerializer,
)


class TherapistReviewListView(generics.ListAPIView):
    """Widok publicznej listy opinii fizjoterapeuty z paginacją i filtrowaniem."""

    serializer_class = ReviewReadSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self) -> QuerySet[Review]:
        """Pobiera widoczne opinie danego fizjoterapeuty z opcjonalnym filtrowaniem poprzez selektor.

        Returns:
            QuerySet[Review]: Przefiltrowany zestaw opinii.
        """
        from .selectors import review_list_for_therapist_selector

        therapist_id = self.kwargs['therapist_id']
        rating = self.request.query_params.get('rating')
        parsed_rating = None
        if rating is not None:
            with contextlib.suppress(ValueError, TypeError):
                parsed_rating = int(rating)
        ordering = self.request.query_params.get('ordering', '-created_at')
        return review_list_for_therapist_selector(
            therapist_id=therapist_id,
            rating=parsed_rating,
            ordering=ordering,
        )


class TherapistRatingSummaryView(APIView):
    """Widok podsumowania ocen fizjoterapeuty (średnia, liczba, rozkład)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, therapist_id: str) -> Response:
        """Zwraca zagregowane statystyki ocen dla fizjoterapeuty poprzez selektor.

        Args:
            request (Request): Obiekt żądania HTTP.
            therapist_id (str): UUID fizjoterapeuty.

        Returns:
            Response: Słownik ze średnią, liczbą i rozkładem ocen.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        from .selectors import therapist_rating_summary_selector

        data = therapist_rating_summary_selector(therapist_id)
        serializer = RatingSummarySerializer(data)
        return Response(serializer.data)


class TherapistDirectReviewCreateView(APIView):
    """Widok dodawania opinii bezpośrednio z profilu fizjoterapeuty (także poza wizytą)."""

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request: Request, therapist_id: str) -> Response:
        from therapists.models import TherapistProfile

        patient_profile = getattr(request.user, 'patient_profile', None)
        if patient_profile is None:
            return Response(
                {'detail': 'Profil pacjenta nie istnieje.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        therapist = get_object_or_404(TherapistProfile, pk=therapist_id, user__is_active=True)

        serializer = TherapistDirectReviewCreateSerializer(
            data=request.data,
            context={'request': request, 'therapist': therapist},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            ReviewReadSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class VisitReviewCreateView(APIView):
    """Widok tworzenia opinii przez pacjenta dla zakończonej wizyty."""

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request: Request, visit_id: str) -> Response:
        """Tworzy nową opinię dla wskazanej wizyty.

        Args:
            request (Request): Obiekt żądania HTTP.
            visit_id (str): UUID wizyty, dla której wystawiamy opinię.

        Returns:
            Response: Dane nowo utworzonej opinii (HTTP 201) lub błędy walidacji.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        patient_profile = getattr(request.user, 'patient_profile', None)
        if patient_profile is None:
            return Response(
                {'detail': 'Profil pacjenta nie istnieje.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        visit = get_object_or_404(Visit, pk=visit_id)

        if visit.patient_id != patient_profile.id:
            raise PermissionDenied('Możesz wystawiać opinie tylko do własnych wizyt.')

        serializer = ReviewCreateSerializer(
            data=request.data,
            context={'visit': visit, 'request': request},
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            ReviewReadSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class ReviewEditView(generics.UpdateAPIView):
    """Widok edycji własnej opinii przez pacjenta (okno 14 dni)."""

    serializer_class = ReviewEditSerializer
    permission_classes = [IsAuthenticated, IsPatient]
    http_method_names = ['patch']

    def get_queryset(self) -> QuerySet[Review]:
        """Zwraca opinie należące do zalogowanego pacjenta.

        Returns:
            QuerySet[Review]: Opinie zalogowanego pacjenta.
        """
        patient_profile = getattr(self.request.user, 'patient_profile', None)
        if patient_profile is None:
            return Review.objects.none()
        return Review.objects.filter(patient=patient_profile)

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Aktualizuje opinię i zwraca pełny widok przez ReviewReadSerializer.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Zaktualizowana opinia w pełnym formacie.
        """
        kwargs['partial'] = True
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(ReviewReadSerializer(instance).data, status=status.HTTP_200_OK)


class ReviewDeleteView(generics.DestroyAPIView):
    """Widok usuwania własnej opinii przez pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet[Review]:
        """Zwraca opinie należące do zalogowanego pacjenta.

        Returns:
            QuerySet[Review]: Opinie zalogowanego pacjenta.
        """
        patient_profile = getattr(self.request.user, 'patient_profile', None)
        if patient_profile is None:
            return Review.objects.none()
        return Review.objects.filter(patient=patient_profile)

    def perform_destroy(self, instance: Review) -> None:
        """Usuwa opinię i przelicza statystyki ocen terapeuty za pośrednictwem serwisu."""
        from .services import review_delete_service

        review_delete_service(review=instance)


class ReviewReplyView(APIView):
    """Widok dodawania lub aktualizacji odpowiedzi fizjoterapeuty na opinię."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request: Request, review_id: str) -> Response:
        """Dodaje lub aktualizuje odpowiedź fizjoterapeuty na opinię.

        Args:
            request (Request): Obiekt żądania HTTP.
            review_id (str): UUID opinii, na którą odpowiada terapeuta.

        Returns:
            Response: Zaktualizowana odpowiedź z datą.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        therapist_profile = getattr(request.user, 'therapist_profile', None)
        if therapist_profile is None:
            return Response(
                {'detail': 'Profil fizjoterapeuty nie istnieje.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        review = get_object_or_404(Review, pk=review_id)

        if review.therapist_id != therapist_profile.id:
            raise PermissionDenied('Możesz odpowiadać tylko na opinie dotyczące Twojego profilu.')

        serializer = ReviewReplySerializer(review, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(
            {
                'therapist_reply': updated.therapist_reply,
                'therapist_replied_at': updated.therapist_replied_at,
            },
            status=status.HTTP_200_OK,
        )
