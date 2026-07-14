from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin, TherapistPatientQuerysetMixin
from core.permissions import IsOwnerPatientProfile, IsPatient, IsTherapist
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
        payload = MeProfileSerializer(profile).data
        consents = ConsentSerializer(
            Consent.objects.filter(user=request.user), many=True
        ).data
        return Response(
            {'profile': payload, 'consents': consents},
            status=status.HTTP_200_OK,
        )


class MeAccountDeletionRequestView(PatientSelfMixin, APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Wniosek o usunięcie konta został zarejestrowany.'},
            status=status.HTTP_202_ACCEPTED,
        )
