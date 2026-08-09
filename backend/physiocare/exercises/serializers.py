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
    exercise_id,
    patient_id,
    start_date,
    end_date,
    exclude_id=None,
    error_field='exercise_id',
):
    """Reject same exercise + patient when date ranges overlap (inclusive)."""
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
    class Meta:
        model = ExerciseCategory
        fields = ['id', 'name', 'kind', 'slug']
        read_only_fields = fields


class ExerciseSerializer(serializers.ModelSerializer):
    categories = ExerciseCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'media_type', 'file_url',
            'instruction', 'created_at', 'categories',
        ]
        read_only_fields = ['id', 'file_url', 'created_at']


class ExerciseCreateSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ExerciseCategory.objects.all(),
        required=False,
    )
    title = serializers.CharField(max_length=200)
    instruction = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Exercise
        fields = ['title', 'media_type', 'instruction', 'categories']

    def validate_title(self, value):
        try:
            return normalize_and_validate_exercise_title(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_instruction(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=INSTRUCTION_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def create(self, validated_data):
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
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ExerciseCategory.objects.all(),
        required=False,
    )
    title = serializers.CharField(max_length=200, required=False)
    instruction = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Exercise
        fields = ['title', 'media_type', 'instruction', 'categories']

    def validate_title(self, value):
        try:
            return normalize_and_validate_exercise_title(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_instruction(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=INSTRUCTION_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def update(self, instance, validated_data):
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
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_instruction = serializers.CharField(source='exercise.instruction', read_only=True)
    exercise_file_url = serializers.CharField(source='exercise.file_url', read_only=True)
    exercise_media_type = serializers.CharField(source='exercise.media_type', read_only=True)

    class Meta:
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
    exercise_id = serializers.UUIDField(write_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    episode_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    dosage = serializers.CharField(
        max_length=100,
        error_messages={'max_length': DOSAGE_TOO_LONG},
    )

    class Meta:
        model = ExerciseAssignment
        fields = [
            'exercise_id', 'patient_id', 'episode_id',
            'dosage', 'start_date', 'end_date',
        ]

    def validate_dosage(self, value):
        try:
            return normalize_and_validate_dosage(value, allow_blank=False)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        therapist = self.context['therapist']
        exercise_id = attrs['exercise_id']
        patient_id = attrs['patient_id']
        episode_id = attrs.get('episode_id')

        if not Exercise.objects.filter(pk=exercise_id, therapist=therapist).exists():
            raise serializers.ValidationError(
                {'exercise_id': 'Ćwiczenie nie należy do tego terapeuty.'}
            )

        if not PatientProfile.objects.filter(pk=patient_id, therapist=therapist).exists():
            raise serializers.ValidationError(
                {'patient_id': 'Pacjent nie należy do tego terapeuty.'}
            )

        if episode_id is not None and not TreatmentEpisode.objects.filter(
            pk=episode_id,
            patient_id=patient_id,
            patient__therapist=therapist,
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

    def create(self, validated_data):
        return ExerciseAssignment.objects.create(
            exercise_id=validated_data.pop('exercise_id'),
            patient_id=validated_data.pop('patient_id'),
            episode_id=validated_data.pop('episode_id', None),
            **validated_data,
        )


class ExerciseAssignmentUpdateSerializer(serializers.ModelSerializer):
    episode_id = serializers.UUIDField(required=False, allow_null=True)
    dosage = serializers.CharField(
        max_length=100,
        required=False,
        error_messages={'max_length': DOSAGE_TOO_LONG},
    )

    class Meta:
        model = ExerciseAssignment
        fields = ['dosage', 'start_date', 'end_date', 'episode_id']

    def validate_dosage(self, value):
        try:
            return normalize_and_validate_dosage(value, allow_blank=False)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end < start:
            raise serializers.ValidationError(
                {'end_date': 'Data końcowa nie może być wcześniejsza niż początkowa.'}
            )

        if 'episode_id' in attrs:
            episode_id = attrs['episode_id']
            therapist = self.context['therapist']
            patient_id = self.instance.patient_id
            if episode_id is not None and not TreatmentEpisode.objects.filter(
                pk=episode_id,
                patient_id=patient_id,
                patient__therapist=therapist,
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

    def update(self, instance, validated_data):
        if 'episode_id' in validated_data:
            instance.episode_id = validated_data.pop('episode_id')
        return super().update(instance, validated_data)


class TodayExerciseSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_instruction = serializers.CharField(source='exercise.instruction', read_only=True)
    exercise_file_url = serializers.CharField(source='exercise.file_url', read_only=True)
    exercise_media_type = serializers.CharField(source='exercise.media_type', read_only=True)
    categories = ExerciseCategorySerializer(source='exercise.categories', many=True, read_only=True)
    completed_today = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExerciseAssignment
        fields = [
            'id', 'exercise', 'exercise_title', 'exercise_instruction',
            'exercise_file_url', 'exercise_media_type', 'categories',
            'patient', 'episode', 'dosage', 'start_date', 'end_date',
            'assigned_at', 'completed_today',
        ]
        read_only_fields = fields


class ExerciseCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCompletion
        fields = ['id', 'assignment', 'completed_on', 'done', 'completed_at']
        read_only_fields = ['id', 'completed_at']


class ExerciseCompletionCreateSerializer(serializers.ModelSerializer):
    assignment_id = serializers.UUIDField(write_only=True)
    completed_on = serializers.DateField(required=False, allow_null=True)
    done = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = ExerciseCompletion
        fields = ['assignment_id', 'completed_on', 'done']

    def create(self, validated_data):
        return ExerciseCompletion.objects.create(
            assignment_id=validated_data.pop('assignment_id'),
            completed_on=validated_data.get('completed_on') or timezone.localdate(),
            done=validated_data.get('done', True),
        )
