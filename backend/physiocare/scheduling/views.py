from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin, user_can_access_visit
from core.permissions import IsPatient, IsTherapist, IsVisitParticipant

from .models import TherapyType, Visit, VisitStatus
from .serializers import (
    TherapyTypeSerializer,
    VisitCancelSerializer,
    VisitCreateSerializer,
    VisitRescheduleSerializer,
    VisitSerializer,
)


class TherapistVisitListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self):
        therapist = self.request.user.therapist_profile
        qs = Visit.objects.filter(therapist=therapist).select_related(
            'patient', 'patient__user', 'therapy_type', 'episode',
        )
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(start_at__date=date_param)
        return qs.order_by('start_at')

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
        try:
            visit = serializer.save()
        except IntegrityError:
            raise ValidationError(
                {'start_at': 'Termin koliduje z inną wizytą tego terapeuty.'}
            ) from None
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)


class TherapistVisitDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsVisitParticipant]

    def get_queryset(self):
        return Visit.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).select_related('patient', 'therapy_type', 'episode')


class MeVisitListView(PatientSelfMixin, generics.ListAPIView):
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        qs = Visit.objects.filter(
            patient=self.get_patient_profile(),
        ).select_related('therapist', 'therapy_type', 'episode').order_by('start_at')

        status_filter = self.request.query_params.get('status')
        now = timezone.now()
        if status_filter == 'upcoming':
            qs = qs.filter(start_at__gte=now, status=VisitStatus.SCHEDULED)
        elif status_filter == 'past':
            qs = qs.filter(Q(start_at__lt=now) | ~Q(status=VisitStatus.SCHEDULED))
        return qs


class VisitDetailView(generics.RetrieveAPIView):
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated, IsVisitParticipant]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return Visit.objects.filter(patient=user.patient_profile)
        if user.role == 'THERAPIST':
            return Visit.objects.filter(therapist=user.therapist_profile)
        return Visit.objects.all()


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
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError(
                {'start_at': 'Termin koliduje z inną wizytą.'}
            ) from None
        return Response(VisitSerializer(visit).data)


class VisitCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        visit = Visit.objects.select_related('patient', 'therapist').filter(pk=pk).first()
        if visit is None or not user_can_access_visit(request.user, visit):
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = VisitCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visit.status = VisitStatus.CANCELLED
        visit.cancel_reason = serializer.validated_data.get('cancel_reason', '')
        visit.save(update_fields=['status', 'cancel_reason'])
        return Response(VisitSerializer(visit).data)


class TherapyTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = TherapyTypeSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self):
        return TherapyType.objects.filter(
            therapist=self.request.user.therapist_profile,
        )

    def perform_create(self, serializer):
        serializer.save(therapist=self.request.user.therapist_profile)
