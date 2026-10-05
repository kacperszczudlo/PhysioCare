from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsTherapist
from exercises.models import ExerciseAssignment
from scheduling.models import Visit, VisitStatus

from .models import TherapistProfile
from .serializers import (
    TherapistProfileSerializer,
    TherapistProfileUpdateSerializer,
    TherapistPublicSerializer,
)


class TherapistProfileView(generics.RetrieveUpdateAPIView):
    """Widok pobierania i edycji własnego profilu fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get_object(self) -> TherapistProfile:
        """Pobiera profil fizjoterapeuty przypisany do zalogowanego użytkownika.

        Returns:
            TherapistProfile: Obiekt profilu fizjoterapeuty.
        """
        return self.request.user.therapist_profile

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca odpowiednią klasę serializera zależnie od metody żądania.

        Returns:
            type[serializers.Serializer]: Klasa serializera do użycia.
        """
        if self.request.method in ('PUT', 'PATCH'):
            return TherapistProfileUpdateSerializer
        return TherapistProfileSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Aktualizuje dane profilu fizjoterapeuty.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź zawierająca zaktualizowane dane profilu.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(TherapistProfileSerializer(instance).data)


class TherapistCompetencesView(APIView):
    """Widok pobierania kompetencji zalogowanego fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request: Request) -> Response:
        """Pobiera migawkę kompetencji zawodowych fizjoterapeuty.

        Args:
            request (Request): Obiekt żądania HTTP.

        Returns:
            Response: Słownik reprezentujący migawkę kompetencji.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        therapist = request.user.therapist_profile
        return Response(therapist.competence_snapshot().to_dict())


class TherapistDashboardStatsView(APIView):
    """Widok statystyk pulpitów fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request: Request) -> Response:
        """Pobiera zbiorcze statystyki wizyt, pacjentów i aktywnych zadań dla fizjoterapeuty.

        Args:
            request (Request): Obiekt żądania HTTP.

        Returns:
            Response: Słownik zawierający zagregowane statystyki.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        therapist = request.user.therapist_profile
        today = timezone.localdate()
        upcoming = Visit.objects.filter(
            therapist=therapist,
            start_at__date=today,
            status=VisitStatus.SCHEDULED,
        ).count()
        patients_count = therapist.patient_links.filter(status='ACTIVE', patient__user__is_active=True).count()
        assignments_active = ExerciseAssignment.objects.filter(
            patient__therapist_links__therapist=therapist,
            patient__therapist_links__status='ACTIVE',
            patient__user__is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        ).count()
        return Response({
            'visits_today': upcoming,
            'patients_total': patients_count,
            'assignments_active': assignments_active,
            'rating_avg': float(therapist.rating_avg),
            'rating_count': therapist.rating_count,
        })


class TherapistPublicView(generics.RetrieveAPIView):
    """Widok szczegółowy publicznego profilu fizjoterapeuty."""

    serializer_class = TherapistPublicSerializer
    permission_classes = [IsAuthenticated]
    queryset = TherapistProfile.objects.select_related('user')


class TherapistPublicListView(generics.ListAPIView):
    """Widok wyszukiwania i pobierania publicznej listy fizjoterapeutów."""

    serializer_class = TherapistPublicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[TherapistProfile]:
        """Pobiera przefiltrowaną listę aktywnych profilów fizjoterapeutów.

        Returns:
            QuerySet[TherapistProfile]: Zestaw przefiltrowanych obiektów TherapistProfile.
        """
        qs = TherapistProfile.objects.select_related('user').filter(user__is_active=True)
        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q, Value
            from django.db.models.functions import Concat
            qs = qs.annotate(
                full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            )
            query = (
                Q(full_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(location_address__icontains=search)
                | Q(pwzf_number__icontains=search)
            )
            for term in search.split():
                query |= Q(user__first_name__icontains=term)
                query |= Q(user__last_name__icontains=term)
            qs = qs.filter(query)
        return qs
