from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers


from core.field_policies import (
    DOSAGE_TOO_LONG,
    INSTRUCTION_TOO_LONG,
    normalize_and_validate_dosage,
    normalize_and_validate_exercise_title,
    normalize_optional_text,
)
from patients.models import PatientProfile
from treatment.models import TreatmentEpisode

from .models import Exercise, ExerciseAssignment, ExerciseCategory, ExerciseCompletion

OVERLAPPING_ASSIGNMENT_MESSAGE = (
    'To ćwiczenie jest już przypisane temu pacjentowi w nakładającym się okresie.'
)


def assert_no_overlapping_assignment(
    *,
    exercise_id: object,
    patient_id: object,
    start_date: object,
    end_date: object,
    exclude_id: object = None,
    error_field: str = 'exercise_id',
) -> None:
    """Odrzuca nakładające się przypisania tego samego ćwiczenia dla pacjenta w nakładającym się okresie.

    Args:
        exercise_id (object): Identyfikator ćwiczenia (UUID lub string).
        patient_id (object): Identyfikator pacjenta (UUID lub string).
        start_date (object): Data początkowa przypisania.
        end_date (object): Data końcowa przypisania.
        exclude_id (object): Identyfikator przypisania do wykluczenia (np. przy edycji).
        error_field (str): Pole słownika błędów walidacji. Domyślnie 'exercise_id'.

    Raises:
        TypeError: Gdy error_field nie jest napisem.
        serializers.ValidationError: Gdy istnieje nakładające się przypisanie.
    """
    if not isinstance(error_field, str):
        raise TypeError('Argument error_field musi być typu str.')
    if not start_date or not end_date:
        return
    qs = ExerciseAssignment.objects.filter(
        exercise_id=exercise_id,
        patient_id=patient_id,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    if qs.exists():
        raise serializers.ValidationError({error_field: OVERLAPPING_ASSIGNMENT_MESSAGE})


class ExerciseCategorySerializer(serializers.ModelSerializer):
    """Serializator dla kategorii ćwiczeń."""

    class Meta:
        """Metadane serializatora ExerciseCategorySerializer."""

        model = ExerciseCategory
        fields = ['id', 'name', 'kind', 'slug']
        read_only_fields = fields


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializator odczytu ćwiczenia."""

    categories = ExerciseCategorySerializer(many=True, read_only=True)

    class Meta:
        """Metadane serializatora ExerciseSerializer."""

        model = Exercise
        fields = [
            'id', 'title', 'media_type', 'file_url',
            'instruction', 'created_at', 'categories',
        ]
        read_only_fields = ['id', 'file_url', 'created_at']


class ExerciseCreateSerializer(serializers.ModelSerializer):
    """Serializator do tworzenia nowego ćwiczenia przez fizjoterapeutę."""

    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ExerciseCategory.objects.all(),
        required=False,
    )
    title = serializers.CharField(max_length=200)
    instruction = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        """Metadane serializatora ExerciseCreateSerializer."""

        model = Exercise
        fields = ['title', 'media_type', 'instruction', 'categories']

    def validate_title(self, value: str) -> str:
        """Waliduje oraz normalizuje tytuł ćwiczenia.

        Args:
            value (str): Wprowadzony tytuł ćwiczenia.

        Returns:
            str: Znormalizowany tytuł.

        Raises:
            serializers.ValidationError: Gdy tytuł jest niepoprawny.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Tytuł musi być ciągiem znaków.')
        try:
            return normalize_and_validate_exercise_title(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_instruction(self, value: str | None) -> str | None:
        """Waliduje oraz normalizuje opcjonalne instrukcje do ćwiczenia.

        Args:
            value (str | None): Wprowadzona treść instrukcji.

        Returns:
            str | None: Znormalizowana treść instrukcji.

        Raises:
            serializers.ValidationError: Gdy instrukcja przekracza dozwoloną długość.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Instrukcja musi być ciągiem znaków.')
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=INSTRUCTION_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def create(self, validated_data: dict[str, object]) -> Exercise:
        """Tworzy instancję ćwiczenia wraz z przypisanymi kategoriami.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane z formularza.

        Returns:
            Exercise: Utworzony obiekt ćwiczenia.
        """
        if not isinstance(validated_data, dict):
            raise serializers.ValidationError('Nieprawidłowe dane wejściowe.')
        categories = validated_data.pop('categories', [])
        exercise = Exercise.objects.create(
            therapist=self.context['therapist'],
            file_url=self.context['file_url'],
            **validated_data,
        )
        if categories:
            exercise.categories.set(categories)
        return exercise


class ExerciseUpdateSerializer(serializers.ModelSerializer):
    """Serializator do aktualizacji istniejącego ćwiczenia."""

    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ExerciseCategory.objects.all(),
        required=False,
    )
    title = serializers.CharField(max_length=200, required=False)
    instruction = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        """Metadane serializatora ExerciseUpdateSerializer."""

        model = Exercise
        fields = ['title', 'media_type', 'instruction', 'categories']

    def validate_title(self, value: str) -> str:
        """Waliduje i normalizuje tytuł ćwiczenia podczas edycji.

        Args:
            value (str): Nowy tytuł ćwiczenia.

        Returns:
            str: Znormalizowany tytuł.

        Raises:
            serializers.ValidationError: Gdy tytuł jest niepoprawny.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Tytuł musi być ciągiem znaków.')
        try:
            return normalize_and_validate_exercise_title(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_instruction(self, value: str | None) -> str | None:
        """Waliduje i normalizuje instrukcję do ćwiczenia podczas edycji.

        Args:
            value (str | None): Treść instrukcji.

        Returns:
            str | None: Znormalizowana treść instrukcji.

        Raises:
            serializers.ValidationError: Gdy instrukcja jest zbyt długa.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Instrukcja musi być ciągiem znaków.')
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=INSTRUCTION_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def update(self, instance: Exercise, validated_data: dict[str, object]) -> Exercise:
        """Aktualizuje instancję ćwiczenia.

        Args:
            instance (Exercise): Edytowany obiekt ćwiczenia.
            validated_data (dict[str, object]): Zwalidowane dane do aktualizacji.

        Returns:
            Exercise: Zaktualizowany obiekt ćwiczenia.
        """
        if not isinstance(instance, Exercise) or not isinstance(validated_data, dict):
            raise serializers.ValidationError('Nieprawidłowe dane wejściowe.')
        categories = validated_data.pop('categories', serializers.empty)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        file_url = self.context.get('file_url')
        if file_url:
            instance.file_url = file_url
        instance.save()
        if categories is not serializers.empty:
            instance.categories.set(categories)
        return instance


class ExerciseAssignmentSerializer(serializers.ModelSerializer):
    """Serializator odczytu przypisania ćwiczenia pacjentowi."""

    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_instruction = serializers.CharField(source='exercise.instruction', read_only=True)
    exercise_file_url = serializers.CharField(source='exercise.file_url', read_only=True)
    exercise_media_type = serializers.CharField(source='exercise.media_type', read_only=True)

    class Meta:
        """Metadane serializatora ExerciseAssignmentSerializer."""

        model = ExerciseAssignment
        fields = [
            'id', 'exercise', 'exercise_title', 'exercise_instruction',
            'exercise_file_url', 'exercise_media_type', 'patient', 'episode',
            'dosage', 'start_date', 'end_date', 'assigned_at',
        ]
        read_only_fields = [
            'id', 'exercise', 'exercise_title', 'exercise_instruction',
            'exercise_file_url', 'exercise_media_type', 'patient', 'assigned_at',
        ]


class ExerciseAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializator tworzenia przypisania ćwiczenia pacjentowi przez terapeutę."""

    exercise_id = serializers.UUIDField(write_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    episode_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    dosage = serializers.CharField(
        max_length=100,
        error_messages={'max_length': DOSAGE_TOO_LONG},
    )

    class Meta:
        """Metadane serializatora ExerciseAssignmentCreateSerializer."""

        model = ExerciseAssignment
        fields = [
            'exercise_id', 'patient_id', 'episode_id',
            'dosage', 'start_date', 'end_date',
        ]

    def validate_dosage(self, value: str) -> str:
        """Waliduje i normalizuje dawkowanie ćwiczenia.

        Args:
            value (str): Wprowadzony opis dawkowania (np. "3x10 powtórzeń").

        Returns:
            str: Znormalizowane dawkowanie.

        Raises:
            serializers.ValidationError: Gdy dawkowanie jest niepoprawne.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Dawkowanie musi być ciągiem znaków.')
        try:
            return normalize_and_validate_dosage(value, allow_blank=False)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje powiązanie pacjenta, epizodu oraz potencjalne nakładanie się przypisań.

        Args:
            attrs (dict[str, object]): Dane do walidacji.

        Returns:
            dict[str, object]: Zwalidowane dane.

        Raises:
            serializers.ValidationError: Gdy walidacja relacji lub dat zakończy się niepowodzeniem.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane walidowane muszą być słownikiem.')
        therapist = self.context['therapist']
        exercise_id = attrs['exercise_id']
        patient_id = attrs['patient_id']
        episode_id = attrs.get('episode_id')

        if not Exercise.objects.filter(pk=exercise_id, therapist=therapist).exists():
            raise serializers.ValidationError(
                {'exercise_id': 'Ćwiczenie nie należy do tego terapeuty.'}
            )

        if not PatientProfile.objects.active().filter(
            pk=patient_id,
            therapist_links__therapist=therapist,
            therapist_links__status='ACTIVE',
        ).exists():
            raise serializers.ValidationError(
                {'patient_id': 'Pacjent nie należy do tego terapeuty.'}
            )

        if episode_id is not None and not TreatmentEpisode.objects.filter(
            pk=episode_id,
            patient_id=patient_id,
        ).exists():
            raise serializers.ValidationError(
                {'episode_id': 'Epizod nie należy do wskazanego pacjenta.'}
            )

        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and end < start:
            raise serializers.ValidationError(
                {'end_date': 'Data końcowa nie może być wcześniejsza niż początkowa.'}
            )

        assert_no_overlapping_assignment(
            exercise_id=exercise_id,
            patient_id=patient_id,
            start_date=start,
            end_date=end,
        )

        return attrs

    def create(self, validated_data: dict[str, object]) -> ExerciseAssignment:
        """Tworzy nowe przypisanie ćwiczenia w bazie danych.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane przypisania.

        Returns:
            ExerciseAssignment: Nowo utworzone przypisanie ćwiczenia.
        """
        if not isinstance(validated_data, dict):
            raise serializers.ValidationError('Nieprawidłowe dane wejściowe.')
        return ExerciseAssignment.objects.create(
            exercise_id=validated_data.pop('exercise_id'),
            patient_id=validated_data.pop('patient_id'),
            episode_id=validated_data.pop('episode_id', None),
            **validated_data,
        )


class ExerciseAssignmentUpdateSerializer(serializers.ModelSerializer):
    """Serializator edycji istniejącego przypisania ćwiczenia pacjentowi."""

    episode_id = serializers.UUIDField(required=False, allow_null=True)
    dosage = serializers.CharField(
        max_length=100,
        required=False,
        error_messages={'max_length': DOSAGE_TOO_LONG},
    )

    class Meta:
        """Metadane serializatora ExerciseAssignmentUpdateSerializer."""

        model = ExerciseAssignment
        fields = ['dosage', 'start_date', 'end_date', 'episode_id']

    def validate_dosage(self, value: str) -> str:
        """Waliduje i normalizuje zaktualizowane dawkowanie.

        Args:
            value (str): Dawkowanie ćwiczenia.

        Returns:
            str: Znormalizowany opis dawkowania.

        Raises:
            serializers.ValidationError: Gdy dawkowanie jest niepoprawne.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Dawkowanie musi być ciągiem znaków.')
        try:
            return normalize_and_validate_dosage(value, allow_blank=False)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje poprawność zakresu dat przypisania ćwiczenia oraz powiązanego epizodu.

        Args:
            attrs (dict[str, object]): Walidowane atrybuty.

        Returns:
            dict[str, object]: Przetestowane i zwalidowane atrybuty.

        Raises:
            serializers.ValidationError: Gdy data końcowa wyprzedza początkową lub epizod jest niepoprawny.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane walidowane muszą być słownikiem.')
        instance_start = self.instance.start_date if self.instance and hasattr(self.instance, 'start_date') else None
        instance_end = self.instance.end_date if self.instance and hasattr(self.instance, 'end_date') else None
        start = attrs.get('start_date', instance_start)
        end = attrs.get('end_date', instance_end)
        if start and end and end < start:
            raise serializers.ValidationError(
                {'end_date': 'Data końcowa nie może być wcześniejsza niż początkowa.'}
            )

        if 'episode_id' in attrs:
            episode_id = attrs['episode_id']
            patient_id = self.instance.patient_id
            if episode_id is not None and not TreatmentEpisode.objects.filter(
                pk=episode_id,
                patient_id=patient_id,
            ).exists():
                raise serializers.ValidationError(
                    {'episode_id': 'Epizod nie należy do wskazanego pacjenta.'}
                )

        assert_no_overlapping_assignment(
            exercise_id=self.instance.exercise_id,
            patient_id=self.instance.patient_id,
            start_date=start,
            end_date=end,
            exclude_id=self.instance.pk,
            error_field='start_date',
        )

        return attrs

    def update(self, instance: ExerciseAssignment, validated_data: dict[str, object]) -> ExerciseAssignment:
        """Zapisuje zmiany w przypisaniu ćwiczenia.

        Args:
            instance (ExerciseAssignment): Edytowane przypisanie ćwiczenia.
            validated_data (dict[str, object]): Zwalidowane dane do aktualizacji.

        Returns:
            ExerciseAssignment: Zaktualizowany obiekt przypisania ćwiczenia.
        """
        if not isinstance(instance, ExerciseAssignment) or not isinstance(validated_data, dict):
            raise serializers.ValidationError('Nieprawidłowe dane wejściowe.')
        if 'episode_id' in validated_data:
            instance.episode_id = validated_data.pop('episode_id')
        return super().update(instance, validated_data)


class TodayExerciseSerializer(serializers.ModelSerializer):
    """Serializator ćwiczeń zaplanowanych na dzisiejszy dzień dla pacjenta."""

    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_instruction = serializers.CharField(source='exercise.instruction', read_only=True)
    exercise_file_url = serializers.CharField(source='exercise.file_url', read_only=True)
    exercise_media_type = serializers.CharField(source='exercise.media_type', read_only=True)
    categories = ExerciseCategorySerializer(source='exercise.categories', many=True, read_only=True)
    completed_today = serializers.BooleanField(read_only=True)

    class Meta:
        """Metadane serializatora TodayExerciseSerializer."""

        model = ExerciseAssignment
        fields = [
            'id', 'exercise', 'exercise_title', 'exercise_instruction',
            'exercise_file_url', 'exercise_media_type', 'categories',
            'patient', 'episode', 'dosage', 'start_date', 'end_date',
            'assigned_at', 'completed_today',
        ]
        read_only_fields = fields


class ExerciseCompletionSerializer(serializers.ModelSerializer):
    """Serializator odczytu historii wykonania ćwiczeń."""

    class Meta:
        """Metadane serializatora ExerciseCompletionSerializer."""

        model = ExerciseCompletion
        fields = ['id', 'assignment', 'completed_on', 'done', 'completed_at']
        read_only_fields = ['id', 'completed_at']


class PatientExerciseAssignmentSerializer(serializers.ModelSerializer):
    """Pełne przypisanie ćwiczeń HEP dla pacjenta wraz z historią odhaczeń."""

    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_instruction = serializers.CharField(source='exercise.instruction', read_only=True)
    exercise_file_url = serializers.CharField(source='exercise.file_url', read_only=True)
    exercise_media_type = serializers.CharField(source='exercise.media_type', read_only=True)
    categories = ExerciseCategorySerializer(source='exercise.categories', many=True, read_only=True)
    completed_today = serializers.BooleanField(read_only=True)
    completions = ExerciseCompletionSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora PatientExerciseAssignmentSerializer."""

        model = ExerciseAssignment
        fields = [
            'id', 'exercise', 'exercise_title', 'exercise_instruction',
            'exercise_file_url', 'exercise_media_type', 'categories',
            'patient', 'episode', 'dosage', 'start_date', 'end_date',
            'assigned_at', 'completed_today', 'completions', 'is_active',
        ]
        read_only_fields = fields

    def get_is_active(self, obj: ExerciseAssignment) -> bool:
        """Sprawdza, czy dzisiejsza data mieści się w przedziale czasowym przypisania.

        Args:
            obj (ExerciseAssignment): Obiekt przypisania ćwiczenia.

        Returns:
            bool: True jeśli przypisanie jest aktywne dzisiaj, False w przeciwnym razie.
        """
        if not isinstance(obj, ExerciseAssignment):
            return False
        today = timezone.localdate()
        return obj.start_date <= today <= obj.end_date


class ExerciseCompletionCreateSerializer(serializers.ModelSerializer):
    """Serializator tworzenia wpisu o wykonaniu ćwiczenia przez pacjenta."""

    assignment_id = serializers.UUIDField(write_only=True)
    completed_on = serializers.DateField(required=False, allow_null=True)
    done = serializers.BooleanField(required=False, default=True)

    class Meta:
        """Metadane serializatora ExerciseCompletionCreateSerializer."""

        model = ExerciseCompletion
        fields = ['assignment_id', 'completed_on', 'done']

    def create(self, validated_data: dict[str, object]) -> ExerciseCompletion:
        """Tworzy obiekt wykonania ćwiczenia.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane wykonania.

        Returns:
            ExerciseCompletion: Utworzona instancja wykonania ćwiczenia.
        """
        if not isinstance(validated_data, dict):
            raise serializers.ValidationError('Nieprawidłowe dane wejściowe.')
        return ExerciseCompletion.objects.create(
            assignment_id=validated_data.pop('assignment_id'),
            completed_on=validated_data.get('completed_on') or timezone.localdate(),
            done=validated_data.get('done', True),
        )

