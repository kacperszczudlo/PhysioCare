from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.token_ops import blacklist_user_refresh_tokens
from core.mixins import PatientSelfMixin, TherapistPatientQuerysetMixin
from core.permissions import IsOwnerPatientProfile, IsPatient, IsTherapist
from privacy.account_deletion import submit_account_deletion
from privacy.export import build_patient_export
from privacy.models import Consent, ConsentType

from .serializers import (
    ConsentSerializer,
    MeProfileSerializer,
    MeProfileUpdateSerializer,
    OptionalConsentsUpdateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
)


class PatientListView(TherapistPatientQuerysetMixin, generics.ListAPIView):
    serializer_class = PatientListSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self):
        return self.therapist_patients()


class PatientDetailView(TherapistPatientQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = PatientDetailSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsOwnerPatientProfile]

    def get_queryset(self):
        return self.therapist_patients()


class MeProfileView(PatientSelfMixin, generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def get_object(self):
        return self.get_patient_profile()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return MeProfileUpdateSerializer
        return MeProfileSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeProfileSerializer(instance).data)


class MeConsentsView(PatientSelfMixin, generics.ListAPIView):
    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Consent.objects.filter(user=self.request.user)


class MeOptionalConsentsView(PatientSelfMixin, APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def patch(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request, *args, **kwargs):
        profile = self.get_patient_profile()
        payload = build_patient_export(request.user, profile)
        return Response(payload, status=status.HTTP_200_OK)


class MeAccountDeletionRequestView(PatientSelfMixin, APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request, *args, **kwargs):
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
                    'Konto zostało wyłączone. Adres e-mail jest wolny — '
                    'możesz założyć nowe konto tym samym adresem.'
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )
