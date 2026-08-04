from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.mixins import TherapistPatientQuerysetMixin
from core.permissions import IsEpisodeParticipant, IsTherapist
from patients.models import PatientProfile

from .models import TreatmentEpisode, VisitNote
from .serializers import (
    BodyAreaPainSerializer,
    TreatmentEpisodeCreateSerializer,
    TreatmentEpisodeSerializer,
    VisitNoteSerializer,
)


class PatientEpisodeListCreateView(TherapistPatientQuerysetMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_patient(self):
        try:
            return PatientProfile.objects.get(
                pk=self.kwargs['patient_id'],
                therapist=self.get_therapist_profile(),
            )
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
        episode = TreatmentEpisode.objects.select_related('patient').get(
            pk=self.kwargs['episode_id'],
        )
        if episode.patient.therapist_id != self.request.user.therapist_profile.id:
            raise NotFound()
        return episode

    def get_queryset(self):
        return BodyAreaPain.objects.filter(episode=self.get_episode())

    def perform_create(self, serializer):
        serializer.save(episode=self.get_episode())


class EpisodeBodyPainDetailView(generics.UpdateAPIView):
    serializer_class = BodyAreaPainSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['put', 'patch']

    def get_queryset(self):
        return BodyAreaPain.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist=self.request.user.therapist_profile,
        )


class EpisodeNoteListCreateView(generics.ListCreateAPIView):
    serializer_class = VisitNoteSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self):
        episode = TreatmentEpisode.objects.select_related('patient').filter(
            pk=self.kwargs['episode_id'],
            patient__therapist=self.request.user.therapist_profile,
        ).first()
        if episode is None:
            raise NotFound()
        return episode

    def get_queryset(self):
        return VisitNote.objects.filter(episode=self.get_episode()).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(episode=self.get_episode())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['episode'] = self.get_episode()
        return context

