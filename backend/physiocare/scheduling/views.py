from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin, user_can_access_visit
from core.permissions import IsPatient, IsTherapist, IsVisitParticipant
from core.throttling import VisitBookingRateThrottle
from notifications.events import (
    notify_visit_change,
    publish_visit_realtime,
)

from .holidays import get_polish_holidays, is_polish_holiday
from .models import TherapistAvailabilitySlot, TherapyType, Visit, VisitStatus
from .selectors import (
    visit_list_for_patient_selector,
    visit_list_for_therapist_selector,
)
from .selectors import (
    visit_related_fields as _visit_related,
)
from .serializers import (
    PatientVisitRequestSerializer,
    TherapistAvailabilitySlotSerializer,
    TherapyTypeSerializer,
    VisitApproveSerializer,
    VisitCancelSerializer,
    VisitCreateSerializer,
    VisitRescheduleSerializer,
    VisitSerializer,
)
from .services import (
    maybe_publish_patient_summary as _maybe_publish_patient_summary,
)
from .services import (
    translate_visit_integrity_error as _visit_integrity_error,
)
from .therapy_type_presets import ensure_therapy_type_presets, preset_payloads


def _save_visit(
    save_fn: object,
    *,
    overlap_message: str = 'Termin koliduje z inną wizytą tego terapeuty.',
) -> Visit:
    """Zapisuje wizytę w transakcji atomowej z obsługą błędów spójności bazy danych.

    Args:
        save_fn (object): Funkcja wywoływalna wykonująca zapis wizyty.
        overlap_message (str, optional): Komunikat błędu nakładania się terminów.

    Returns:
        Visit: Zapisany obiekt wizyty.

    Raises:
        TypeError: Gdy parametr save_fn nie jest funkcją wywoływalną lub overlap_message nie jest ciągiem znaków.
        ValidationError: Gdy wystąpi naruszenie ograniczeń spójności wizyty.
    """
    if not callable(save_fn):
        raise TypeError('Parametr save_fn musi być funkcją wywoływalną (callable).')
    if not isinstance(overlap_message, str):
        raise TypeError('Parametr overlap_message musi być ciągiem znaków.')
    try:
        with transaction.atomic():
            return save_fn()
    except IntegrityError as exc:
        raise _visit_integrity_error(exc, overlap_message=overlap_message) from None


class TherapistVisitListCreateView(generics.ListCreateAPIView):
    """Widok listy oraz tworzenia wizyt z poziomu fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def _upcoming_limit(self) -> int | None:
        """Pobiera i waliduje opcjonalny limit nadchodzących wizyt z parametrów zapytania URL.

        Returns:
            int | None: Wartość limitu z przedziału 1-50 lub None.
        """
        if self.request.query_params.get('upcoming') != '1':
            return None
        raw = self.request.query_params.get('limit')
        if raw is None:
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        if value < 1:
            return None
        return min(value, 50)

    def get_queryset(self) -> QuerySet:
        """Zwraca przefiltrowany zestaw wizyt należących do zalogowanego fizjoterapeuty za pośrednictwem selektora.

        Returns:
            QuerySet: Zbiór wizyt fizjoterapeuty z prewencją N+1.
        """
        therapist = self.request.user.therapist_profile
        return visit_list_for_therapist_selector(
            therapist,
            date_param=self.request.query_params.get('date'),
            upcoming=(self.request.query_params.get('upcoming') == '1'),
            pending=(self.request.query_params.get('pending') == '1'),
            limit=self._upcoming_limit(),
        )

    def paginate_queryset(self, queryset: object) -> list[object] | None:
        """Pojedyncza paginacja wyłączana w przypadku żądania limitu nadchodzących wizyt.

        Args:
            queryset (object): Zbiór danych do spaginowania.

        Returns:
            list[object] | None: Wynik paginacji lub None przy limicie.
        """
        if self._upcoming_limit() is not None:
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca odpowiednią klasę serializatora w zależności od metody HTTP.

        Returns:
            type[serializers.Serializer]: Klasa serializatora.
        """
        if self.request.method == 'POST':
            return VisitCreateSerializer
        return VisitSerializer

    def create(self, request: object, *args: object, **kwargs: object) -> Response:
        """Tworzy nową wizytę w grafiku fizjoterapeuty i wysyła powiadomienie.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź z danymi nowo utworzonej wizyty (201 CREATED).

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        serializer = self.get_serializer(
            data=request.data,
            context={'therapist': request.user.therapist_profile},
        )
        serializer.is_valid(raise_exception=True)
        visit = _save_visit(serializer.save)
        visit = self.get_queryset().get(pk=visit.pk)
        notify_visit_change(visit, 'scheduled')
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)


class TherapistVisitDetailView(generics.RetrieveUpdateAPIView):
    """Widok pobierania i edycji szczegółów wizyty z poziomu fizjoterapeuty."""

    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsVisitParticipant]

    def get_queryset(self) -> QuerySet:
        """Zwraca zestaw wizyt powiązanych z zalogowanym fizjoterapeutą za pośrednictwem selektora.

        Returns:
            QuerySet: Zbiór wizyt fizjoterapeuty z prewencją N+1.
        """
        return visit_list_for_therapist_selector(self.request.user.therapist_profile)

    def update(self, request: object, *args: object, **kwargs: object) -> Response:
        """Aktualizuje dane wizyty, powiadamia o zmianach oraz aktualizuje podsumowanie.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź z aktualnymi danymi wizyty.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        previous_start = instance.start_at
        previous_end = instance.end_at
        previous_status = instance.status
        previous_summary = instance.patient_summary
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        _save_visit(lambda: self.perform_update(serializer))
        visit = self.get_queryset().get(pk=instance.pk)
        if visit.status == VisitStatus.CANCELLED and previous_status != VisitStatus.CANCELLED:
            notify_visit_change(visit, 'cancelled')
        elif visit.start_at != previous_start or visit.end_at != previous_end:
            notify_visit_change(visit, 'rescheduled')
        _maybe_publish_patient_summary(visit, previous_summary)
        return Response(VisitSerializer(visit).data)


class VisitApproveView(APIView):
    """Widok zatwierdzania zgłoszenia wizyty przez fizjoterapeutę."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request: object, pk: object) -> Response:
        """Zatwierdza oczekujące zgłoszenie wizyty i ustawia status SCHEDULED.

        Args:
            request (object): Obiekt żądania HTTP.
            pk (object): Identyfikator wizyty (UUID).

        Returns:
            Response: Odpowiedź zawierająca dane zatwierdzonej wizyty lub błąd.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        visit = (
            Visit.objects.filter(
                pk=pk,
                therapist=request.user.therapist_profile,
            )
            .select_related(*_visit_related())
            .first()
        )
        if visit is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if visit.status != VisitStatus.PENDING_APPROVAL:
            return Response(
                {
                    'error': {
                        'code': 'VISIT_NOT_PENDING',
                        'message': 'Można zatwierdzić tylko zgłoszenie oczekujące.',
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VisitApproveSerializer(
            data=request.data,
            context={'visit': visit},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if 'therapy_type_id' in data:
            visit.therapy_type_id = data['therapy_type_id']
        if 'start_at' in data:
            visit.start_at = data['start_at']
        if 'end_at' in data:
            visit.end_at = data['end_at']
        if 'prep_instructions' in data:
            visit.prep_instructions = data['prep_instructions']
        if 'location_address' in data:
            visit.location_address = data['location_address']

        visit.status = VisitStatus.SCHEDULED
        _save_visit(visit.save)

        visit = Visit.objects.select_related(*_visit_related()).get(pk=visit.pk)
        notify_visit_change(visit, 'approved')
        return Response(VisitSerializer(visit).data)


class VisitRejectView(APIView):
    """Widok odrzucania zgłoszenia wizyty przez fizjoterapeutę."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request: object, pk: object) -> Response:
        """Odrzuca oczekujące zgłoszenie wizyty i zmienia jej status na CANCELLED.

        Args:
            request (object): Obiekt żądania HTTP.
            pk (object): Identyfikator wizyty (UUID).

        Returns:
            Response: Odpowiedź zawierająca dane odrzuconej wizyty.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        visit = (
            Visit.objects.filter(
                pk=pk,
                therapist=request.user.therapist_profile,
            )
            .select_related(*_visit_related())
            .first()
        )
        if visit is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if visit.status != VisitStatus.PENDING_APPROVAL:
            return Response(
                {
                    'error': {
                        'code': 'VISIT_NOT_PENDING',
                        'message': 'Można odrzucić tylko zgłoszenie oczekujące.',
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VisitCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visit.status = VisitStatus.CANCELLED
        visit.cancel_reason = (
            serializer.validated_data.get('cancel_reason', '') or 'Odrzucone przez terapeutę'
        )
        visit.save(update_fields=['status', 'cancel_reason'])
        notify_visit_change(visit, 'rejected')
        return Response(VisitSerializer(visit).data)


class MeVisitListCreateView(PatientSelfMixin, generics.ListCreateAPIView):
    """Widok przeglądania i tworzenia zgłoszeń wizyt dla zalogowanego pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get_throttles(self) -> list[object]:
        """Aplikuje dedykowany limiter zapytań dla tworzenia nowych wizyt (POST).

        Returns:
            list[object]: Lista klas dławiących ruch HTTP dla żądania.
        """
        if self.request and self.request.method == 'POST':
            return [VisitBookingRateThrottle()]
        return super().get_throttles()

    def get_queryset(self) -> QuerySet:
        """Zwraca zestaw wizyt należących do zalogowanego pacjenta za pośrednictwem selektora.

        Returns:
            QuerySet: Przefiltrowany zbiór wizyt pacjenta.
        """
        patient = self.get_patient_profile()
        status_filter = self.request.query_params.get('status')
        qs = visit_list_for_patient_selector(patient)

        now = timezone.now()
        active_statuses = (VisitStatus.SCHEDULED, VisitStatus.PENDING_APPROVAL)
        if status_filter == 'upcoming':
            qs = qs.filter(start_at__gte=now, status__in=active_statuses)
        elif status_filter == 'past':
            qs = qs.filter(
                Q(start_at__lt=now) | ~Q(status__in=active_statuses),
            )
        return qs

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca odpowiednią klasę serializatora w zależności od metody HTTP.

        Returns:
            type[serializers.Serializer]: Klasa serializatora.
        """
        if self.request.method == 'POST':
            return PatientVisitRequestSerializer
        return VisitSerializer

    def create(self, request: object, *args: object, **kwargs: object) -> Response:
        """Tworzy nowe zgłoszenie rezerwacji wizyty przez pacjenta.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź z danymi zgłoszonej wizyty (201 CREATED).

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        patient = self.get_patient_profile()
        serializer = self.get_serializer(
            data=request.data,
            context={'patient': patient},
        )
        serializer.is_valid(raise_exception=True)
        therapist = serializer.validated_data.get('therapist')
        if therapist:
            ensure_therapy_type_presets(therapist)
        visit = _save_visit(
            serializer.save,
            overlap_message='Termin koliduje z inną wizytą. Wybierz inny slot.',
        )
        visit = Visit.objects.select_related(
            'therapist',
            'therapist__user',
            'therapy_type',
            'episode',
            'patient',
            'patient__user',
        ).get(pk=visit.pk)
        publish_visit_realtime(visit, 'scheduled')
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)


class MeTherapyTypeListView(PatientSelfMixin, generics.ListAPIView):
    """Widok pobierania listy dostępnych typów terapii dla pacjenta."""

    serializer_class = TherapyTypeSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet:
        """Zwraca listę typów terapii oferowanych przez fizjoterapeutę pacjenta.

        Returns:
            QuerySet: Zbiór typów terapii.
        """
        patient = self.get_patient_profile()
        therapist_id = self.request.query_params.get('therapist_id')
        therapist = None
        if therapist_id:
            from therapists.models import TherapistProfile

            therapist = TherapistProfile.objects.filter(pk=therapist_id).first()
        if not therapist:
            therapist = patient.therapists.filter(patient_links__status='ACTIVE').first()

        if therapist:
            ensure_therapy_type_presets(therapist)
            return TherapyType.objects.filter(therapist=therapist).order_by('name')
        return TherapyType.objects.none()


class VisitDetailView(generics.RetrieveAPIView):
    """Widok podglądu szczegółów wizyty dla uczestnika wizyty (pacjenta lub terapeuty)."""

    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsVisitParticipant]

    def get_queryset(self) -> QuerySet:
        """Zwraca wizyty dostępne dla zalogowanego użytkownika (pacjenta lub terapeuty).

        Returns:
            QuerySet: Zbiór dostępnych wizyt.
        """
        user = self.request.user
        related = _visit_related()
        if user.role == 'PATIENT':
            return Visit.objects.filter(patient=user.patient_profile).select_related(*related)
        if user.role == 'THERAPIST':
            return Visit.objects.filter(therapist=user.therapist_profile).select_related(*related)
        return Visit.objects.none()


class VisitRescheduleView(APIView):
    """Widok przekładania terminu wizyty przez pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def patch(self, request: object, pk: object) -> Response:
        """Zmienia termin wizyty pacjenta po walidacji dostępności.

        Args:
            request (object): Obiekt żądania HTTP.
            pk (object): Identyfikator wizyty (UUID).

        Returns:
            Response: Odpowiedź ze zaktualizowanymi danymi wizyty.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        visit = Visit.objects.filter(
            pk=pk,
            patient=request.user.patient_profile,
        ).first()
        if visit is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = VisitRescheduleSerializer(visit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        _save_visit(
            serializer.save,
            overlap_message='Termin koliduje z inną wizytą.',
        )
        visit = Visit.objects.select_related(
            'patient',
            'patient__user',
            'therapist',
            'therapist__user',
            'therapy_type',
        ).get(pk=visit.pk)
        publish_visit_realtime(visit, 'rescheduled')
        return Response(VisitSerializer(visit).data)


class VisitCancelView(APIView):
    """Widok odwoływania wizyty przez pacjenta lub fizjoterapeutę."""

    permission_classes = [IsAuthenticated]

    def post(self, request: object, pk: object) -> Response:
        """Anuluje wizytę i rozsyła odpowiednie powiadomienia.

        Args:
            request (object): Obiekt żądania HTTP.
            pk (object): Identyfikator wizyty (UUID).

        Returns:
            Response: Odpowiedź zawierająca dane odwołanej wizyty.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        visit = (
            Visit.objects.select_related('patient', 'patient__user', 'therapist')
            .filter(pk=pk)
            .first()
        )
        if visit is None or not user_can_access_visit(request.user, visit):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if visit.status not in (VisitStatus.SCHEDULED, VisitStatus.PENDING_APPROVAL):
            return Response(
                {
                    'error': {
                        'code': 'VISIT_NOT_CANCELLABLE',
                        'message': 'Tej wizyty nie można odwołać.',
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VisitCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visit.status = VisitStatus.CANCELLED
        visit.cancel_reason = serializer.validated_data.get('cancel_reason', '')
        visit.save(update_fields=['status', 'cancel_reason'])
        if request.user.role == 'THERAPIST':
            notify_visit_change(visit, 'cancelled')
        else:
            publish_visit_realtime(visit, 'cancelled')
        return Response(VisitSerializer(visit).data)


class TherapyTypeListCreateView(generics.ListCreateAPIView):
    """Widok pobierania listy oraz obsługi tworzenia typów terapii fizjoterapeuty."""

    serializer_class = TherapyTypeSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self) -> QuerySet:
        """Zwraca typy terapii przypisane do fizjoterapeuty.

        Returns:
            QuerySet: Lista typów terapii.
        """
        return TherapyType.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).order_by('name')

    def list(self, request: object, *args: object, **kwargs: object) -> Response:
        """Zapewnia obecność domyślnych szablonów typów terapii i zwraca ich listę.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź zawierająca listę typów terapii.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        ensure_therapy_type_presets(request.user.therapist_profile)
        return super().list(request, *args, **kwargs)

    def create(self, request: object, *args: object, **kwargs: object) -> Response:
        """Zwraca informację, że typy terapii są stałe (HTTP 405).

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź błędu 405 Method Not Allowed.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        return Response(
            {
                'error': {
                    'code': 'THERAPY_TYPES_FIXED',
                    'message': 'Typy wizyt są stałe - wybierz z proponowanej listy.',
                },
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class TherapyTypePresetListView(APIView):
    """Widok listy predefiniowanych szablonów typów terapii."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request: object) -> Response:
        """Zwraca dostępną listę szablonów typów terapii wraz z informacją czy zostały już dodane.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Wynik z listą predefiniowanych szablonów.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        therapist = request.user.therapist_profile
        existing = set(
            TherapyType.objects.filter(therapist=therapist).values_list('name', flat=True),
        )
        presets = [
            {**preset, 'already_added': preset['name'] in existing} for preset in preset_payloads()
        ]
        return Response({'results': presets})


class TherapyTypeSeedPresetsView(APIView):
    """Widok automatycznego generowania wstępnych typów terapii dla fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request: object) -> Response:
        """Inicjalizuje domyślne szablony typów terapii dla profilu fizjoterapeuty.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Lista zainicjalizowanych typów terapii.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        therapist = request.user.therapist_profile
        types = ensure_therapy_type_presets(therapist)
        return Response(
            {'results': TherapyTypeSerializer(types, many=True).data},
            status=status.HTTP_200_OK,
        )


class TherapistAvailabilityListCreateView(generics.ListCreateAPIView):
    """Widok przeglądania i dodawania slotów dostępności przez fizjoterapeutę."""

    serializer_class = TherapistAvailabilitySlotSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self) -> QuerySet:
        """Zwraca sloty dostępności zalogowanego fizjoterapeuty.

        Returns:
            QuerySet: Zbiór slotów dostępności.
        """
        return TherapistAvailabilitySlot.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).order_by('is_recurring', 'start_at', 'day_of_week', 'start_time')

    def perform_create(self, serializer: object) -> None:
        """Zapisuje slot dostępności z przypisanym profilem fizjoterapeuty.

        Args:
            serializer (object): Serializator z danymi slotu.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        serializer.save(therapist=self.request.user.therapist_profile)


class TherapistAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, edycji i usuwania slotu dostępności fizjoterapeuty."""

    serializer_class = TherapistAvailabilitySlotSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self) -> QuerySet:
        """Zwraca sloty dostępności należące do zalogowanego fizjoterapeuty.

        Returns:
            QuerySet: Zbiór slotów dostępności.
        """
        return TherapistAvailabilitySlot.objects.filter(
            therapist=self.request.user.therapist_profile,
        )


class PublicTherapistAvailableSlotsView(APIView):
    """Widok publicznej dostępności slotów danego fizjoterapeuty."""

    permission_classes = [IsAuthenticated]

    def get(self, request: object, therapist_id: object) -> Response:
        """Pobiera wolne/dostępne sloty przyjęć dla wskazanego terapeuty z uwzględnieniem dni wolnych od pracy.

        Args:
            request (object): Obiekt żądania HTTP.
            therapist_id (object): Identyfikator fizjoterapeuty (UUID).

        Returns:
            Response: Lista dostępnych slotów i informacja o ew. święcie.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        from therapists.models import TherapistProfile

        try:
            therapist = TherapistProfile.objects.get(pk=therapist_id)
        except TherapistProfile.DoesNotExist:
            return Response(
                {'detail': 'Nie znaleziono profilu fizjoterapeuty.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        date_str = request.query_params.get('date')
        slots = TherapistAvailabilitySlot.objects.filter(
            therapist=therapist,
            is_active=True,
        )
        is_holiday = False
        holiday_name = None

        if date_str:
            try:
                target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                dow = target_date.weekday()
                is_holiday, holiday_name = is_polish_holiday(target_date)

                has_specific_slot = slots.filter(
                    is_recurring=False, start_at__date=target_date
                ).exists()

                if is_holiday and not has_specific_slot:
                    slots = slots.none()
                else:
                    slots = slots.filter(
                        Q(is_recurring=False, start_at__date=target_date)
                        | Q(is_recurring=True, day_of_week=dow)
                    )
            except ValueError:
                return Response(
                    {'date': 'Nieprawidłowy format daty (wymagany YYYY-MM-DD).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = TherapistAvailabilitySlotSerializer(slots, many=True)
        return Response(
            {
                'results': serializer.data,
                'is_holiday': is_holiday,
                'holiday_name': holiday_name,
            }
        )


class PolishHolidaysView(APIView):
    """Widok listy polskich świąt państwowych w danym roku."""

    permission_classes = [IsAuthenticated]

    def get(self, request: object) -> Response:
        """Zwraca słownik polskich świąt państwowych dla wskazanego lub bieżącego roku.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Lista obiektów ze zdefiniowanymi datami i nazwami świąt.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        raw_year = request.query_params.get('year')
        try:
            year = int(raw_year) if raw_year else timezone.now().year
        except (TypeError, ValueError):
            return Response(
                {'error': 'Nieprawidłowy rok.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        holidays_dict = get_polish_holidays(year)
        results = [
            {'date': h_date.isoformat(), 'name': h_name}
            for h_date, h_name in sorted(holidays_dict.items())
        ]
        return Response({'results': results})
