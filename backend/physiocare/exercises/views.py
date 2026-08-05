from django.db import transaction
from django.utils import timezone
from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin
from core.permissions import IsPatient, IsTherapist
from core.storage import save_upload

from .models import Exercise, ExerciseAssignment, ExerciseCategory, ExerciseCompletion
from .serializers import (
    ExerciseAssignmentCreateSerializer,
    ExerciseAssignmentSerializer,
    ExerciseCategorySerializer,
    ExerciseCompletionCreateSerializer,
    ExerciseCompletionSerializer,
    ExerciseCreateSerializer,
    ExerciseSerializer,
    TodayExerciseSerializer,
)


class TherapistExerciseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        qs = Exercise.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).prefetch_related('categories')
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(categories__id=category).distinct()
        media_type = self.request.query_params.get('media_type')
        if media_type:
            qs = qs.filter(media_type=media_type)
        search = self.request.query_params.get('q')
        if search:
            qs = qs.filter(title__icontains=search)
        return qs.order_by('-created_at')

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
        serializer = ExerciseCreateSerializer(
            data=request.data,
            context={'therapist': request.user.therapist_profile, 'file_url': file_url},
        )
        serializer.is_valid(raise_exception=True)
        exercise = serializer.save()
        exercise = Exercise.objects.prefetch_related('categories').get(pk=exercise.pk)
        return Response(ExerciseSerializer(exercise).data, status=status.HTTP_201_CREATED)


class TherapistExerciseCategoryListView(generics.ListAPIView):
    serializer_class = ExerciseCategorySerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    pagination_class = None

    def get_queryset(self):
        return ExerciseCategory.objects.all().order_by('name')



class TherapistExerciseAssignmentCreateView(generics.CreateAPIView):
    serializer_class = ExerciseAssignmentCreateSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['therapist'] = self.request.user.therapist_profile
        return context

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
    serializer_class = TodayExerciseSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        from django.db.models import Exists, OuterRef

        today = timezone.localdate()
        completed = ExerciseCompletion.objects.filter(
            assignment_id=OuterRef('pk'),
            completed_on=today,
            done=True,
        )
        return (
            ExerciseAssignment.objects.filter(
                patient=self.get_patient_profile(),
                start_date__lte=today,
                end_date__gte=today,
            )
            .select_related('exercise')
            .annotate(completed_today=Exists(completed))
            .order_by('assigned_at')
        )


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
        completed_on = serializer.validated_data.get('completed_on') or timezone.localdate()
        done = serializer.validated_data.get('done', True)

        with transaction.atomic():
            completion, created = ExerciseCompletion.objects.update_or_create(
                assignment=assignment,
                completed_on=completed_on,
                defaults={'done': done},
            )

        return Response(
            ExerciseCompletionSerializer(completion).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
