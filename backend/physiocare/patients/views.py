from uuid import UUID

from django.db.models import QuerySet
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.token_ops import blacklist_user_refresh_tokens
from core.mixins import PatientSelfMixin, TherapistPatientQuerysetMixin
from core.permissions import IsOwnerPatientProfile, IsPatient, IsTherapist
from privacy.account_deletion import submit_account_deletion
from privacy.export import build_patient_export
from privacy.models import Consent, ConsentType

from .models import PatientProfile
from .serializers import (
    ConsentSerializer,
    MeProfileSerializer,
    MeProfileUpdateSerializer,
    OptionalConsentsUpdateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
)


class PatientListView(TherapistPatientQuerysetMixin, generics.ListAPIView):
    """Widok listy pacjentów przypisanych do fizjoterapeuty."""

    serializer_class = PatientListSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self) -> QuerySet[PatientProfile]:
        """Pobiera zestaw pacjentów powiązanych z zalogowanym fizjoterapeutą.

        Returns:
            QuerySet[PatientProfile]: Zestaw profilów pacjentów fizjoterapeuty.
        """
        return self.therapist_patients()


class PatientDetailView(TherapistPatientQuerysetMixin, generics.RetrieveAPIView):
    """Widok szczegółów pacjenta dostępny dla fizjoterapeuty."""

    serializer_class = PatientDetailSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsOwnerPatientProfile]

    def get_queryset(self) -> QuerySet[PatientProfile]:
        """Pobiera zestaw pacjentów powiązanych z zalogowanym fizjoterapeutą.

        Returns:
            QuerySet[PatientProfile]: Zestaw profilów pacjentów fizjoterapeuty.
        """
        return self.therapist_patients()


class MeProfileView(PatientSelfMixin, generics.RetrieveUpdateAPIView):
    """Widok pobierania i edycji własnego profilu pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get_object(self) -> PatientProfile:
        """Pobiera profil pacjenta dla zalogowanego użytkownika.

        Returns:
            PatientProfile: Instancja profilu pacjenta.
        """
        return self.get_patient_profile()

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Dobiera odpowiednią klasę serializera w zależności od metody HTTP.

        Returns:
            type[serializers.Serializer]: Klasa serializera.
        """
        if self.request.method in ('PUT', 'PATCH'):
            return MeProfileUpdateSerializer
        return MeProfileSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Aktualizuje profil zalogowanego pacjenta.

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
        serializer.save()
        return Response(MeProfileSerializer(instance).data)


class MeConsentsView(PatientSelfMixin, generics.ListAPIView):
    """Widok pobierania listy zgód RODO zalogowanego pacjenta."""

    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet[Consent]:
        """Pobiera zgody przypisane do zalogowanego pacjenta.

        Returns:
            QuerySet[Consent]: Zestaw zgód użytkownika.
        """
        return Consent.objects.filter(user=self.request.user)


class MeOptionalConsentsView(PatientSelfMixin, APIView):
    """Widok aktualizacji opcjonalnych zgód RODO pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Aktualizuje stan opcjonalnych zgód (marketingowych, badawczych).

        Args:
            request (Request): Obiekt żądania HTTP z danymi zgód.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź ze zaktualizowaną listą zgód pacjenta.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        serializer = OptionalConsentsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'marketing' in data:
            Consent.objects.update_or_create(
                user=request.user,
                consent_type=ConsentType.MARKETING_OPTIONAL,
                defaults={'granted': data['marketing']},
            )
        if 'research' in data:
            Consent.objects.update_or_create(
                user=request.user,
                consent_type=ConsentType.RESEARCH_OPTIONAL,
                defaults={'granted': data['research']},
            )

        consents = Consent.objects.filter(user=request.user)
        return Response(ConsentSerializer(consents, many=True).data)


class MeDataExportView(PatientSelfMixin, APIView):
    """Widok eksportu danych osobowych pacjenta (zgodnie z RODO)."""

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Generuje paczkę eksportową danych pacjenta.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź zawierająca zaktualizowany zbiór wyeksportowanych danych.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        profile = self.get_patient_profile()
        payload = build_patient_export(request.user, profile)
        return Response(payload, status=status.HTTP_200_OK)


class MeAccountDeletionRequestView(PatientSelfMixin, APIView):
    """Widok zgłoszenia żądania usunięcia konta pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Przetwarza wniosek o usunięcie konta pacjenta i unieważnia tokeny.

        Args:
            request (Request): Obiekt żądania HTTP (może zawierać powód w body).
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Komunikat potwierdzający dezaktywację konta.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        reason = ''
        if isinstance(request.data, dict):
            raw = request.data.get('reason')
            if raw is not None:
                reason = str(raw)
        user = request.user
        submit_account_deletion(user, reason=reason)
        blacklist_user_refresh_tokens(user)
        return Response(
            {
                'detail': (
                    'Konto zostało wyłączone. Adres e-mail jest wolny - '
                    'możesz założyć nowe konto tym samym adresem.'
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class MeTherapistsView(PatientSelfMixin, APIView):
    """Widok listy fizjoterapeutów powiązanych z zalogowanym pacjentem."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Pobiera aktywnych fizjoterapeutów przypisanych do pacjenta.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Lista zserializowanych profili fizjoterapeutów.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        patient = self.get_patient_profile()
        active_therapists = patient.therapists.filter(patient_links__status='ACTIVE')
        from therapists.serializers import TherapistPublicSerializer
        return Response(TherapistPublicSerializer(active_therapists, many=True).data)


class MeTherapistLinkView(PatientSelfMixin, APIView):
    """Widok nawiązywania powiązania pacjenta z fizjoterapeutą."""

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Tworzy lub reaktywuje powiązanie z fizjoterapeutą po ID lub kodzie/PWZF.

        Args:
            request (Request): Obiekt żądania HTTP zawierający ID lub kod fizjoterapeuty.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź zawierająca publiczne dane fizjoterapeuty lub błąd 404.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        patient = self.get_patient_profile()
        therapist_id = request.data.get('therapist_id') if isinstance(request.data, dict) else None
        therapist_code = request.data.get('therapist_code') if isinstance(request.data, dict) else None

        from django.db.models import Q

        from patients.models import LinkStatus, PatientTherapistLink
        from therapists.models import TherapistProfile

        therapist = None
        if therapist_id:
            therapist = TherapistProfile.objects.filter(id=therapist_id).first()
        elif therapist_code:
            code = str(therapist_code).strip()
            therapist = TherapistProfile.objects.filter(
                Q(pwzf_number__iexact=code) | Q(id=code if len(code) == 36 else None)
            ).first()

        if not therapist:
            return Response({'detail': 'Nie znaleziono fizjoterapeuty.'}, status=status.HTTP_404_NOT_FOUND)

        link, created = PatientTherapistLink.objects.get_or_create(
            patient=patient,
            therapist=therapist,
            defaults={'status': LinkStatus.ACTIVE},
        )
        if not created and link.status != LinkStatus.ACTIVE:
            link.status = LinkStatus.ACTIVE
            link.save(update_fields=['status', 'updated_at'])

        from therapists.serializers import TherapistPublicSerializer
        return Response(
            TherapistPublicSerializer(therapist).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MeTherapistUnlinkView(PatientSelfMixin, APIView):

    """Widok archiwizacji powiązania z fizjoterapeutą."""

    permission_classes = [IsAuthenticated, IsPatient]

    def delete(self, request: Request, therapist_id: str | UUID, *args: object, **kwargs: object) -> Response:
        """Archiwizuje relację pomiędzy pacjentem a wskazanym fizjoterapeutą.

        Args:
            request (Request): Obiekt żądania HTTP.
            therapist_id (str | UUID): Identyfikator fizjoterapeuty.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Potwierdzenie usunięcia z listy.

        Raises:
            TypeError: Gdy request nie jest instancją Request lub therapist_id nie jest napisem/UUID.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')
        if not isinstance(therapist_id, (str, UUID)):
            raise TypeError('Argument therapist_id musi być typu str lub UUID.')

        patient = self.get_patient_profile()
        from patients.models import LinkStatus, PatientTherapistLink
        link = PatientTherapistLink.objects.filter(patient=patient, therapist_id=therapist_id).first()
        if link:
            link.status = LinkStatus.ARCHIVED
            link.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Fizjoterapeuta został usunięty z listy.'}, status=status.HTTP_200_OK)


