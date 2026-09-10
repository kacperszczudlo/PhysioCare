from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin, user_can_access_visit
from core.permissions import IsPatient, IsTherapist, IsVisitParticipant
from notifications.events import notify_visit_change, publish_document_realtime, publish_visit_realtime

from .models import TherapyType, Visit, VisitStatus
from .serializers import (
    PatientVisitRequestSerializer,
    TherapyTypeSerializer,
    VisitApproveSerializer,
    VisitCancelSerializer,
    VisitCreateSerializer,
    VisitRescheduleSerializer,
    VisitSerializer,
)
from .therapy_type_presets import ensure_therapy_type_presets, preset_payloads


def _maybe_publish_patient_summary(visit, previous_summary: str) -> None:
    summary = (visit.patient_summary or '').strip()
    previous = (previous_summary or '').strip()
    if summary and summary != previous:
        publish_document_realtime(visit.patient, visit.id)


def _visit_integrity_error(exc, *, overlap_message='Termin koliduje z inną wizytą tego terapeuty.'):
    message = str(exc).lower()
    if 'exclude_overlapping_visits' in message:
        return ValidationError({'start_at': overlap_message})
    if 'chk_visits_end_after_start' in message:
        return ValidationError({'end_at': 'Koniec wizyty musi być po rozpoczęciu.'})
    return ValidationError({'detail': 'Nie udało się zapisać wizyty.'})


def _save_visit(save_fn, *, overlap_message='Termin koliduje z inną wizytą tego terapeuty.'):
    try:
        with transaction.atomic():
            return save_fn()
    except IntegrityError as exc:
        raise _visit_integrity_error(exc, overlap_message=overlap_message) from None


def _visit_related():
    return (
        'patient',
        'patient__user',
        'therapist',
        'therapist__user',
        'therapy_type',
        'episode',
    )


class TherapistVisitListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def _upcoming_limit(self):
        """Optional ?limit=N for dashboard preview (upcoming=1 only). Clamped 1-50."""
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

    def get_queryset(self):
        therapist = self.request.user.therapist_profile
        qs = Visit.objects.filter(therapist=therapist).select_related(*_visit_related())
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(start_at__date=date_param)
        if self.request.query_params.get('upcoming') == '1':
            qs = qs.filter(
                status=VisitStatus.SCHEDULED,
                end_at__gte=timezone.now(),
            )
        if self.request.query_params.get('pending') == '1':
            qs = qs.filter(status=VisitStatus.PENDING_APPROVAL)
        qs = qs.order_by('start_at')
        limit = self._upcoming_limit()
        if limit is not None:
            return qs[:limit]
        return qs

    def paginate_queryset(self, queryset):
        if self._upcoming_limit() is not None:
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VisitCreateSerializer
        return VisitSerializer

    def create(self, request, *args, **kwargs):
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
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsVisitParticipant]

    def get_queryset(self):
        return Visit.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).select_related(*_visit_related())

    def update(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request, pk):
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
    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request, pk):
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
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        qs = (
            Visit.objects.filter(
                patient=self.get_patient_profile(),
            )
            .select_related(
                'therapist',
                'therapist__user',
                'therapy_type',
                'episode',
            )
            .order_by('start_at')
        )

        status_filter = self.request.query_params.get('status')
        now = timezone.now()
        active_statuses = (VisitStatus.SCHEDULED, VisitStatus.PENDING_APPROVAL)
        if status_filter == 'upcoming':
            qs = qs.filter(start_at__gte=now, status__in=active_statuses)
        elif status_filter == 'past':
            qs = qs.filter(
                Q(start_at__lt=now) | ~Q(status__in=active_statuses),
            )
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientVisitRequestSerializer
        return VisitSerializer

    def create(self, request, *args, **kwargs):
        patient = self.get_patient_profile()
        ensure_therapy_type_presets(patient.therapist)
        serializer = self.get_serializer(
            data=request.data,
            context={'patient': patient},
        )
        serializer.is_valid(raise_exception=True)
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
        # Pacjent sam zgłasza termin - bez push/e-mail do siebie; SSE dla obu stron (live UI).
        publish_visit_realtime(visit, 'scheduled')
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)


class MeTherapyTypeListView(PatientSelfMixin, generics.ListAPIView):
    serializer_class = TherapyTypeSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        therapist = self.get_patient_profile().therapist
        ensure_therapy_type_presets(therapist)
        return TherapyType.objects.filter(therapist=therapist).order_by('name')


class VisitDetailView(generics.RetrieveAPIView):
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsVisitParticipant]

    def get_queryset(self):
        user = self.request.user
        related = _visit_related()
        if user.role == 'PATIENT':
            return Visit.objects.filter(patient=user.patient_profile).select_related(*related)
        if user.role == 'THERAPIST':
            return Visit.objects.filter(therapist=user.therapist_profile).select_related(*related)
        return Visit.objects.none()


class VisitRescheduleView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def patch(self, request, pk):
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
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
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
            # Pacjent odwołuje - push/e-mail do pacjenta zbędny; SSE dla terapeuty (i pacjenta).
            publish_visit_realtime(visit, 'cancelled')
        return Response(VisitSerializer(visit).data)


class TherapyTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = TherapyTypeSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self):
        return TherapyType.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).order_by('name')

    def list(self, request, *args, **kwargs):
        ensure_therapy_type_presets(request.user.therapist_profile)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request):
        therapist = request.user.therapist_profile
        existing = set(
            TherapyType.objects.filter(therapist=therapist).values_list('name', flat=True),
        )
        presets = [
            {**preset, 'already_added': preset['name'] in existing} for preset in preset_payloads()
        ]
        return Response({'results': presets})


class TherapyTypeSeedPresetsView(APIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def post(self, request):
        therapist = request.user.therapist_profile
        types = ensure_therapy_type_presets(therapist)
        return Response(
            {'results': TherapyTypeSerializer(types, many=True).data},
            status=status.HTTP_200_OK,
        )
