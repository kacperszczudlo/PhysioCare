from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin, TherapistPatientQuerysetMixin
from core.permissions import IsEpisodeParticipant, IsPatient, IsTherapist
from notifications.events import publish_document_realtime
from patients.models import PatientProfile
from therapists.medical_devices import catalog_as_list, groups_summary

from .models import (
    BodyAreaPain,
    DeviceOrderStatus,
    DiagnosticRecommendation,
    EpisodeStatus,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
    VisitNote,
)
from .patient_documents import KIND_LABELS, build_clinical_documents_for_patient
from .serializers import (
    BodyAreaPainSerializer,
    DiagnosticRecommendationSerializer,
    MedicalDeviceOrderSerializer,
    PatientEpisodeSerializer,
    PhysicianOrderRefusalSerializer,
    ReceptaNaRuchReferralSerializer,
    TreatmentEpisodeCreateSerializer,
    TreatmentEpisodeSerializer,
    VisitNoteSerializer,
)


def _get_owned_episode(request, episode_id) -> TreatmentEpisode:
    episode = TreatmentEpisode.objects.select_related('patient').filter(
        pk=episode_id,
        patient__therapist=request.user.therapist_profile,
    ).first()
    if episode is None:
        raise NotFound()
    return episode


class PatientEpisodeListCreateView(TherapistPatientQuerysetMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_patient(self):
        try:
            return self.therapist_patients().get(pk=self.kwargs['patient_id'])
        except PatientProfile.DoesNotExist as exc:
            raise NotFound() from exc

    def get_queryset(self):
        return TreatmentEpisode.objects.filter(
            patient=self.get_patient(),
        ).select_related('patient').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TreatmentEpisodeCreateSerializer
        return TreatmentEpisodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        episode = serializer.save(patient=self.get_patient())
        return Response(
            TreatmentEpisodeSerializer(episode).data,
            status=status.HTTP_201_CREATED,
        )


class EpisodeDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TreatmentEpisodeSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsEpisodeParticipant]

    def get_queryset(self):
        return TreatmentEpisode.objects.filter(
            patient__therapist=self.request.user.therapist_profile,
        ).select_related('patient')


class EpisodeBodyPainListCreateView(generics.ListCreateAPIView):
    serializer_class = BodyAreaPainSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self):
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self):
        return BodyAreaPain.objects.filter(episode=self.get_episode())

    def perform_create(self, serializer):
        serializer.save(episode=self.get_episode())


class EpisodeBodyPainDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BodyAreaPainSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return BodyAreaPain.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist=self.request.user.therapist_profile,
        )


class EpisodeNoteListCreateView(generics.ListCreateAPIView):
    serializer_class = VisitNoteSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self):
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self):
        return VisitNote.objects.filter(episode=self.get_episode()).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(episode=self.get_episode())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['episode'] = self.get_episode()
        return context


class EpisodeDiagnosticRecommendationListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosticRecommendationSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self):
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self):
        return DiagnosticRecommendation.objects.filter(
            episode=self.get_episode(),
        ).select_related('therapist')

    def perform_create(self, serializer):
        episode = self.get_episode()
        recommendation = serializer.save(
            episode=episode,
            therapist=self.request.user.therapist_profile,
        )
        if recommendation.red_flags_noted and episode.status == EpisodeStatus.IN_PROGRESS:
            episode.status = EpisodeStatus.REFERRED
            episode.save(update_fields=['status'])
        publish_document_realtime(episode.patient, recommendation.id)


class EpisodeDeviceOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalDeviceOrderSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self):
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self):
        return MedicalDeviceOrder.objects.filter(
            episode=self.get_episode(),
        ).select_related('therapist')

    def perform_create(self, serializer):
        episode = self.get_episode()
        order = serializer.save(
            episode=episode,
            patient=episode.patient,
            therapist=self.request.user.therapist_profile,
        )
        if order.status == DeviceOrderStatus.ISSUED:
            publish_document_realtime(episode.patient, order.id)


class EpisodeOrderRefusalListCreateView(generics.ListCreateAPIView):
    serializer_class = PhysicianOrderRefusalSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self):
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self):
        return PhysicianOrderRefusal.objects.filter(episode=self.get_episode())

    def perform_create(self, serializer):
        episode = self.get_episode()
        refusal = serializer.save(
            episode=episode,
            therapist=self.request.user.therapist_profile,
        )
        publish_document_realtime(episode.patient, refusal.id)


class EpisodeDiagnosticRecommendationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DiagnosticRecommendationSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return DiagnosticRecommendation.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist=self.request.user.therapist_profile,
        ).select_related('episode')

    def perform_update(self, serializer):
        recommendation = serializer.save()
        episode = recommendation.episode
        if recommendation.red_flags_noted and episode.status == EpisodeStatus.IN_PROGRESS:
            episode.status = EpisodeStatus.REFERRED
            episode.save(update_fields=['status'])


class EpisodeDeviceOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalDeviceOrderSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return MedicalDeviceOrder.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist=self.request.user.therapist_profile,
        )


class EpisodeOrderRefusalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PhysicianOrderRefusalSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return PhysicianOrderRefusal.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist=self.request.user.therapist_profile,
        )


class PatientReceptaNaRuchListCreateView(TherapistPatientQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ReceptaNaRuchReferralSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_patient(self):
        try:
            return self.therapist_patients().get(pk=self.kwargs['patient_id'])
        except PatientProfile.DoesNotExist as exc:
            raise NotFound() from exc

    def get_queryset(self):
        return ReceptaNaRuchReferral.objects.filter(
            patient=self.get_patient(),
        ).select_related('therapist', 'episode')

    def perform_create(self, serializer):
        patient = self.get_patient()
        episode = serializer.validated_data.get('episode')
        if episode is not None and episode.patient_id != patient.id:
            raise ValidationError({'episode': 'Epizod nie należy do tego pacjenta.'})
        referral = serializer.save(
            patient=patient,
            therapist=self.request.user.therapist_profile,
        )
        if referral.status == DeviceOrderStatus.ISSUED:
            publish_document_realtime(patient, referral.id)


class PatientReceptaNaRuchDetailView(TherapistPatientQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReceptaNaRuchReferralSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return ReceptaNaRuchReferral.objects.filter(
            patient_id=self.kwargs['patient_id'],
            patient__therapist=self.get_therapist_profile(),
            patient__user__is_active=True,
        )

    def perform_update(self, serializer):
        patient = self.therapist_patients().filter(pk=self.kwargs['patient_id']).first()
        if patient is None:
            raise NotFound()
        episode = serializer.validated_data.get('episode')
        if episode is not None and episode.patient_id != patient.id:
            raise ValidationError({'episode': 'Epizod nie należy do tego pacjenta.'})
        serializer.save()


class MedicalDeviceCatalogView(APIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request):
        therapist = request.user.therapist_profile
        return Response({
            'groups': groups_summary(),
            'items': catalog_as_list(qualification_level=therapist.qualification_level),
            'competences': therapist.competence_snapshot().to_dict(),
            'disclaimer': (
                'PhysioCare modeluje uprawnienia ordynacyjne wyrobów medycznych. '
                'Nie służy do wystawiania recept na leki ani maści farmaceutyczne. '
                'Formalne e-ZWM wymaga podpisu i weryfikacji w systemie P1/NFZ.'
            ),
        })


class MeClinicalDocumentsListView(PatientSelfMixin, APIView):
    """
    Skrzynka dokumentacji pacjenta: kierowanie, wyroby, odmowy,
    Recepta na Ruch, PDF-y oraz podsumowania wizyt — widoczne automatycznie
    po wystawieniu.
    """

    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request):
        kind = request.query_params.get('kind') or None
        if kind is not None and kind not in KIND_LABELS:
            raise ValidationError({
                'kind': (
                    f'Nieznany rodzaj. Dozwolone: {", ".join(sorted(KIND_LABELS))}.'
                ),
            })
        results = build_clinical_documents_for_patient(
            self.get_patient_profile(),
            kind=kind,
        )
        return Response({'count': len(results), 'results': results})


class MeEpisodeListView(PatientSelfMixin, generics.ListAPIView):
    """Pacjent: lista własnych epizodów leczenia (bez notatek klinicznych)."""

    serializer_class = PatientEpisodeSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return TreatmentEpisode.objects.filter(
            patient=self.get_patient_profile(),
        ).order_by('-created_at')


class MeEpisodeDetailView(PatientSelfMixin, generics.RetrieveAPIView):
    serializer_class = PatientEpisodeSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return TreatmentEpisode.objects.filter(
            patient=self.get_patient_profile(),
        )
