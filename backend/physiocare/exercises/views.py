from django.utils import timezone
from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin
from core.permissions import IsPatient, IsTherapist
from core.storage import save_upload

from .models import Exercise, ExerciseAssignment, ExerciseCompletion, MediaType
from .serializers import (
    ExerciseAssignmentCreateSerializer,
    ExerciseAssignmentSerializer,
    ExerciseCompletionCreateSerializer,
    ExerciseCompletionSerializer,
    ExerciseCreateSerializer,
    ExerciseSerializer,
)


class TherapistExerciseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return Exercise.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).prefetch_related('categories')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExerciseCreateSerializer
        return ExerciseSerializer

    def create(self, request, *args, **kwargs):
        uploaded = request.FILES.get('file')
        if uploaded is None:
            return Response(
                {'error': {'code': 'FILE_REQUIRED', 'message': 'Wymagany plik.', 'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_url = save_upload(uploaded, subdir='exercises')
        media_type = request.data.get('media_type', MediaType.VIDEO)
        serializer = ExerciseCreateSerializer(
            data=request.data,
            context={'therapist': request.user.therapist_profile, 'file_url': file_url},
        )
        serializer.is_valid(raise_exception=True)
        exercise = serializer.save()
        return Response(ExerciseSerializer(exercise).data, status=status.HTTP_201_CREATED)


class TherapistExerciseAssignmentCreateView(generics.CreateAPIView):
    serializer_class = ExerciseAssignmentCreateSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        assignment = ExerciseAssignment.objects.select_related('exercise').get(pk=assignment.pk)
        return Response(
            ExerciseAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )


class MeExercisesTodayView(PatientSelfMixin, generics.ListAPIView):
    serializer_class = ExerciseAssignmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        today = timezone.localdate()
        return ExerciseAssignment.objects.filter(
            patient=self.get_patient_profile(),
            start_date__lte=today,
            end_date__gte=today,
        ).select_related('exercise')


class MeExerciseCompletionCreateView(PatientSelfMixin, APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request, *args, **kwargs):
        assignment_id = request.data.get('assignment_id')
        assignment = ExerciseAssignment.objects.filter(
            pk=assignment_id,
            patient=self.get_patient_profile(),
        ).first()
        if assignment is None:
            return Response(
                {'error': {'code': 'VALIDATION', 'message': 'Nieprawidłowe przypisanie.', 'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ExerciseCompletionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        completion = ExerciseCompletion.objects.create(
            assignment=assignment,
            completed_on=serializer.validated_data.get('completed_on') or timezone.localdate(),
            done=serializer.validated_data.get('done', True),
        )
        return Response(
            ExerciseCompletionSerializer(completion).data,
            status=status.HTTP_201_CREATED,
        )
