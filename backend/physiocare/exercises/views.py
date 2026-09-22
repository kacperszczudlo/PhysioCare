from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import generics, parsers, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin
from core.permissions import IsPatient, IsTherapist
from core.storage import delete_media_url, save_upload
from notifications.events import notify_exercise_assigned

from .filters import filter_exercises_queryset
from .models import CategoryKind, Exercise, ExerciseAssignment, ExerciseCategory, ExerciseCompletion
from .serializers import (
    OVERLAPPING_ASSIGNMENT_MESSAGE,
    ExerciseAssignmentCreateSerializer,
    ExerciseAssignmentSerializer,
    ExerciseAssignmentUpdateSerializer,
    ExerciseCategorySerializer,
    ExerciseCompletionCreateSerializer,
    ExerciseCompletionSerializer,
    ExerciseCreateSerializer,
    ExerciseSerializer,
    ExerciseUpdateSerializer,
    PatientExerciseAssignmentSerializer,
    TodayExerciseSerializer,
)


def _assignment_integrity_error(exc: Exception) -> ValidationError:
    """Przekształca wyjątek IntegrityError bazy danych na ValidationError DRF.

    Args:
        exc (Exception): Wyjątek bazodanowy IntegrityError.

    Returns:
        ValidationError: Wyjątek walidacji DRF z odpowiednim komunikatem.
    """
    if not isinstance(exc, Exception):
        return ValidationError({'detail': 'Nie udało się zapisać zalecenia.'})
    message = str(exc).lower()
    if 'exclude_overlapping_exercise_assignments' in message:
        return ValidationError({'exercise_id': OVERLAPPING_ASSIGNMENT_MESSAGE})
    if 'chk_exercise_assignment_dates' in message:
        return ValidationError(
            {'end_date': 'Data końcowa nie może być wcześniejsza niż początkowa.'}
        )
    return ValidationError({'detail': 'Nie udało się zapisać zalecenia.'})


class TherapistExerciseListCreateView(generics.ListCreateAPIView):
    """Widok listy i tworzenia ćwiczeń dla fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self) -> QuerySet[Exercise]:
        """Zwraca przefiltrowaną listę ćwiczeń należących do zalogowanego fizjoterapeuty.

        Returns:
            QuerySet[Exercise]: Przefiltrowany zestaw ćwiczeń.
        """
        qs = Exercise.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).prefetch_related('categories')
        return filter_exercises_queryset(qs, self.request.query_params).order_by('-created_at')

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca odpowiednią klasę serializatora w zależności od metody HTTP.

        Returns:
            type[serializers.Serializer]: Klasa serializatora do użycia.
        """
        if self.request.method == 'POST':
            return ExerciseCreateSerializer
        return ExerciseSerializer

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Obsługuje tworzenie nowego ćwiczenia wraz z wgrywaniem pliku media.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź HTTP z danymi utworzonego ćwiczenia.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        uploaded = request.FILES.get('file')
        if uploaded is None:
            return Response(
                {
                    'error': {
                        'code': 'VALIDATION',
                        'message': 'Plik ćwiczenia jest wymagany.',
                        'details': {'file': ['To pole jest wymagane.']},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_url = save_upload(uploaded, subfolder='exercises')
        exercise = serializer.save(
            therapist=request.user.therapist_profile,
            file_url=file_url,
        )
        return Response(ExerciseSerializer(exercise).data, status=status.HTTP_201_CREATED)


class TherapistExerciseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, edycji oraz usuwania ćwiczenia."""

    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self) -> QuerySet[Exercise]:
        """Zwraca listę ćwiczeń należących do zalogowanego fizjoterapeuty.

        Returns:
            QuerySet[Exercise]: Przefiltrowany zestaw ćwiczeń.
        """
        return Exercise.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).prefetch_related('categories')

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca serializator do odczytu lub aktualizacji ćwiczenia.

        Returns:
            type[serializers.Serializer]: Klasa serializatora.
        """
        if self.request.method in ('PATCH', 'PUT'):
            return ExerciseUpdateSerializer
        return ExerciseSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Aktualizuje ćwiczenie oraz opcjonalnie plik lub kategorie.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Zaktualizowane dane ćwiczenia.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        uploaded = request.FILES.get('file')
        previous_url = instance.file_url
        file_url = None
        if uploaded is not None:
            file_url, _sniffed = save_upload(uploaded, subdir='exercises')

        context = {'therapist': request.user.therapist_profile}
        if file_url:
            context['file_url'] = file_url

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

    def perform_destroy(self, instance: Exercise) -> None:
        """Usuwa instancję ćwiczenia oraz powiązany plik z magazynu.

        Args:
            instance (Exercise): Usuwany obiekt ćwiczenia.

        Raises:
            TypeError: Gdy parametr instance nie jest instancją Exercise.
        """
        if not isinstance(instance, Exercise):
            raise TypeError('Argument instance musi być instancją Exercise.')

        file_url = instance.file_url
        instance.delete()
        delete_media_url(file_url)


class TherapistExerciseCategoryListView(generics.ListAPIView):
    """Widok listy kategorii ćwiczeń dla fizjoterapeuty z obsługą pamięci podręcznej (Cache)."""

    serializer_class = ExerciseCategorySerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    pagination_class = None

    def get_queryset(self) -> QuerySet[ExerciseCategory]:
        """Zwraca listę kategorii z opcjonalnym filtrowaniem po rodzaju (kind).

        Returns:
            QuerySet[ExerciseCategory]: Zestaw kategorii ćwiczeń.
        """
        qs = ExerciseCategory.objects.all()
        kind = self.request.query_params.get('kind')
        if kind:
            kind = kind.upper()
            if kind not in CategoryKind.values:
                return qs.none()
            qs = qs.filter(kind=kind)
        return qs.order_by('kind', 'name')

    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Zwraca listę kategorii ćwiczeń z pamięci podręcznej lub z bazy danych.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź zawierająca wybuforowaną lub pobraną listę kategorii.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        kind = (request.query_params.get('kind') or 'all').upper()
        cache_key = f'exercise_categories:{kind}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)
        return Response(data, status=status.HTTP_200_OK)


class TherapistExerciseAssignmentListCreateView(generics.ListCreateAPIView):
    """Widok listy i przypisywania ćwiczeń pacjentom przez fizjoterapeutę."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self) -> QuerySet[ExerciseAssignment]:
        """Zwraca przypisania ćwiczeń dla aktywnych pacjentów fizjoterapeuty.

        Returns:
            QuerySet[ExerciseAssignment]: Przefiltrowany zestaw przypisań.
        """
        qs = ExerciseAssignment.objects.filter(
            patient__therapist_links__therapist=self.request.user.therapist_profile,
            patient__therapist_links__status='ACTIVE',
        ).select_related('exercise', 'patient').distinct()
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        active = self.request.query_params.get('active')
        if active == '1':
            today = timezone.localdate()
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
        return qs.order_by('-assigned_at')

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca odpowiedni serializator dla metody GET lub POST.

        Returns:
            type[serializers.Serializer]: Klasa serializatora.
        """
        if self.request.method == 'POST':
            return ExerciseAssignmentCreateSerializer
        return ExerciseAssignmentSerializer

    def get_serializer_context(self) -> dict[str, object]:
        """Rozszerza kontekst serializatora o profil fizjoterapeuty.

        Returns:
            dict[str, object]: Kontekst z profilem terapeuty.
        """
        context = super().get_serializer_context()
        context['therapist'] = self.request.user.therapist_profile
        return context

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Tworzy nowe przypisanie ćwiczenia i wysyła powiadomienie do pacjenta.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź HTTP z danymi przypisanego ćwiczenia.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
            ValidationError: Gdy zapis spowoduje błąd spójności danych.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = serializer.save()
        except IntegrityError as exc:
            raise _assignment_integrity_error(exc) from None
        assignment = ExerciseAssignment.objects.select_related(
            'exercise',
            'patient',
            'patient__user',
        ).get(pk=assignment.pk)
        notify_exercise_assigned(assignment)
        return Response(
            ExerciseAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )


class TherapistExerciseAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, aktualizacji i usuwania przypisania ćwiczenia."""

    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'patch', 'put', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet[ExerciseAssignment]:
        """Zwraca przypisanie ćwiczenia należące do pacjenta terapeuty.

        Returns:
            QuerySet[ExerciseAssignment]: Zestaw przypisań ćwiczeń.
        """
        return ExerciseAssignment.objects.filter(
            patient__therapist_links__therapist=self.request.user.therapist_profile,
            patient__therapist_links__status='ACTIVE',
        ).select_related('exercise', 'patient').distinct()

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Zwraca serializator do odczytu lub aktualizacji przypisania.

        Returns:
            type[serializers.Serializer]: Klasa serializatora.
        """
        if self.request.method in ('PATCH', 'PUT'):
            return ExerciseAssignmentUpdateSerializer
        return ExerciseAssignmentSerializer

    def get_serializer_context(self) -> dict[str, object]:
        """Uzupełnia kontekst serializatora o dane fizjoterapeuty.

        Returns:
            dict[str, object]: Kontekst z profilem terapeuty.
        """
        context = super().get_serializer_context()
        context['therapist'] = self.request.user.therapist_profile
        return context

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Aktualizuje szczegóły przypisania ćwiczenia.

        Args:
            request (Request): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź ze zaktualizowanym przypisaniem.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
            ValidationError: Gdy aktualizacja narusza spójność danych.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = serializer.save()
        except IntegrityError as exc:
            raise _assignment_integrity_error(exc) from None
        assignment = ExerciseAssignment.objects.select_related('exercise').get(pk=assignment.pk)
        return Response(ExerciseAssignmentSerializer(assignment).data)


class MeExercisesTodayView(PatientSelfMixin, generics.ListAPIView):
    """Widok listy ćwiczeń zaplanowanych dla zalogowanego pacjenta na dzisiejszy dzień."""

    serializer_class = TodayExerciseSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet[ExerciseAssignment]:
        """Zwraca aktywne dzisiaj ćwiczenia pacjenta wraz z informacją o ich wykonaniu.

        Returns:
            QuerySet[ExerciseAssignment]: Zestaw ćwiczeń zaplanowanych na dziś.
        """
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
            .prefetch_related('exercise__categories')
            .annotate(completed_today=Exists(completed))
            .order_by('assigned_at')
        )


class MeExercisesListView(PatientSelfMixin, generics.ListAPIView):
    """Pełny plan ćwiczeń pacjenta (HEP) z historią odhaczeń.

    Filtrowanie parametrem `scope`:
    - active: tylko aktywne ćwiczenia
    - past: archiwalne ćwiczenia
    - all: wszystkie ćwiczenia (domyślnie)
    """

    serializer_class = PatientExerciseAssignmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet[ExerciseAssignment]:
        """Zwraca przypisane ćwiczenia pacjenta z opcjonalnym zakresem (active/past/all).

        Returns:
            QuerySet[ExerciseAssignment]: Zestaw przypisanych ćwiczeń pacjenta.
        """
        from django.db.models import Exists, OuterRef, Prefetch

        today = timezone.localdate()
        completed = ExerciseCompletion.objects.filter(
            assignment_id=OuterRef('pk'),
            completed_on=today,
            done=True,
        )
        qs = (
            ExerciseAssignment.objects.filter(patient=self.get_patient_profile())
            .select_related('exercise')
            .prefetch_related(
                'exercise__categories',
                Prefetch(
                    'completions',
                    queryset=ExerciseCompletion.objects.order_by('-completed_on'),
                ),
            )
            .annotate(completed_today=Exists(completed))
        )
        scope = (self.request.query_params.get('scope') or 'all').lower()
        if scope == 'active':
            qs = qs.filter(start_date__lte=today, end_date__gte=today)
        elif scope == 'past':
            qs = qs.filter(end_date__lt=today)
        return qs.order_by('-assigned_at')


class MeExerciseCompletionCreateView(PatientSelfMixin, APIView):
    """Widok do oznaczania wykonania ćwiczenia przez pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Rejestruje wykonanie ćwiczenia w danym dniu.

        Args:
            request (Request): Obiekt żądania HTTP z `assignment_id` oraz flaga `done`.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Obiekt odpowiedzi z utworzonym lub zaktualizowanym wpisem wykonania.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

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
        completed_on = timezone.localdate()
        done = serializer.validated_data.get('done', True)

        with transaction.atomic():
            completion, created = ExerciseCompletion.objects.update_or_create(
                assignment=assignment,
                completed_on=completed_on,
                defaults={'done': done},
            )

        return Response(
            ExerciseCompletionSerializer(completion).data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )

