from django.db import transaction
from django.utils import timezone
from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin
from core.permissions import IsPatient, IsTherapist
from core.storage import delete_media_url, save_upload

from .models import Exercise, ExerciseAssignment, ExerciseCategory, ExerciseCompletion
from .serializers import (
    ExerciseAssignmentCreateSerializer,
    ExerciseAssignmentSerializer,
    ExerciseAssignmentUpdateSerializer,
    ExerciseCategorySerializer,
    ExerciseCompletionCreateSerializer,
    ExerciseCompletionSerializer,
    ExerciseCreateSerializer,
    ExerciseSerializer,
    ExerciseUpdateSerializer,
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


class TherapistExerciseDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Exercise.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).prefetch_related('categories')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ExerciseUpdateSerializer
        return ExerciseSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        uploaded = request.FILES.get('file')
        previous_url = instance.file_url
        file_url = None
        if uploaded is not None:
            file_url = save_upload(uploaded, subdir='exercises')

        context = {'therapist': request.user.therapist_profile}
        if file_url:
            context['file_url'] = file_url

        # Categories are applied explicitly so an empty selection can clear M2M.
        mutable = request.data.copy()
        if hasattr(mutable, 'pop'):
            mutable.pop('has_categories', None)
            if str(request.data.get('has_categories', '')) == '1':
                mutable.pop('categories', None)

        serializer = ExerciseUpdateSerializer(
            instance,
            data=mutable,
            partial=partial,
            context=context,
        )
        serializer.is_valid(raise_exception=True)
        exercise = serializer.save()

        if str(request.data.get('has_categories', '')) == '1':
            if hasattr(request.data, 'getlist'):
                category_ids = request.data.getlist('categories')
            else:
                raw = request.data.get('categories') or []
                category_ids = raw if isinstance(raw, list) else [raw]
            categories = list(ExerciseCategory.objects.filter(pk__in=category_ids))
            exercise.categories.set(categories)

        if file_url and previous_url and previous_url != file_url:
            delete_media_url(previous_url)

        exercise = Exercise.objects.prefetch_related('categories').get(pk=exercise.pk)
        return Response(ExerciseSerializer(exercise).data)

    def perform_destroy(self, instance):
        file_url = instance.file_url
        instance.delete()
        delete_media_url(file_url)


class TherapistExerciseCategoryListView(generics.ListAPIView):
    serializer_class = ExerciseCategorySerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    pagination_class = None

    def get_queryset(self):
        return ExerciseCategory.objects.all().order_by('name')



class TherapistExerciseAssignmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self):
        qs = ExerciseAssignment.objects.filter(
            patient__therapist=self.request.user.therapist_profile,
        ).select_related('exercise', 'patient')
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        active = self.request.query_params.get('active')
        if active == '1':
            today = timezone.localdate()
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
        return qs.order_by('-assigned_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExerciseAssignmentCreateSerializer
        return ExerciseAssignmentSerializer

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


class TherapistExerciseAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'patch', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        return ExerciseAssignment.objects.filter(
            patient__therapist=self.request.user.therapist_profile,
        ).select_related('exercise', 'patient')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return ExerciseAssignmentUpdateSerializer
        return ExerciseAssignmentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['therapist'] = self.request.user.therapist_profile
        return context

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        assignment = ExerciseAssignment.objects.select_related('exercise').get(pk=assignment.pk)
        return Response(ExerciseAssignmentSerializer(assignment).data)


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
