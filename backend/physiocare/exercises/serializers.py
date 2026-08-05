from django.utils import timezone
from rest_framework import serializers

from patients.models import PatientProfile
from treatment.models import TreatmentEpisode

from .models import Exercise, ExerciseAssignment, ExerciseCategory, ExerciseCompletion


class ExerciseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCategory
        fields = ['id', 'name']


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

    class Meta:
        model = Exercise
        fields = ['title', 'media_type', 'instruction', 'categories']

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


class ExerciseAssignmentSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)

    class Meta:
        model = ExerciseAssignment
        fields = [
            'id', 'exercise', 'exercise_title', 'patient', 'episode',
            'dosage', 'start_date', 'end_date', 'assigned_at',
        ]
        read_only_fields = ['id', 'assigned_at']


class ExerciseAssignmentCreateSerializer(serializers.ModelSerializer):
    exercise_id = serializers.UUIDField(write_only=True)
    patient_id = serializers.UUIDField(write_only=True)
    episode_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = ExerciseAssignment
        fields = [
            'exercise_id', 'patient_id', 'episode_id',
            'dosage', 'start_date', 'end_date',
        ]

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

        return attrs

    def create(self, validated_data):
        return ExerciseAssignment.objects.create(
            exercise_id=validated_data.pop('exercise_id'),
            patient_id=validated_data.pop('patient_id'),
            episode_id=validated_data.pop('episode_id', None),
            **validated_data,
        )


class TodayExerciseSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_instruction = serializers.CharField(source='exercise.instruction', read_only=True)
    exercise_file_url = serializers.CharField(source='exercise.file_url', read_only=True)
    exercise_media_type = serializers.CharField(source='exercise.media_type', read_only=True)
    completed_today = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExerciseAssignment
        fields = [
            'id', 'exercise', 'exercise_title', 'exercise_instruction',
            'exercise_file_url', 'exercise_media_type', 'patient', 'episode',
            'dosage', 'start_date', 'end_date', 'assigned_at', 'completed_today',
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
