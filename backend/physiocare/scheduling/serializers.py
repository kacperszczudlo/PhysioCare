from rest_framework import serializers

from patients.models import PatientProfile
from treatment.models import TreatmentEpisode

from .models import TherapyType, Visit


class TherapyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapyType
        fields = ['id', 'name', 'color_hex', 'duration_min', 'created_at']
        read_only_fields = ['id', 'created_at']


class VisitSerializer(serializers.ModelSerializer):
    patient_first_name = serializers.CharField(
        source='patient.user.first_name',
        read_only=True,
    )
    patient_last_name = serializers.CharField(
        source='patient.user.last_name',
        read_only=True,
    )
    therapy_type_name = serializers.CharField(
        source='therapy_type.name',
        read_only=True,
    )
    therapy_type_color = serializers.CharField(
        source='therapy_type.color_hex',
        read_only=True,
    )
    therapy_type_duration_min = serializers.IntegerField(
        source='therapy_type.duration_min',
        read_only=True,
    )

    class Meta:
        model = Visit
        fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type',
            'patient_first_name', 'patient_last_name',
            'therapy_type_name', 'therapy_type_color', 'therapy_type_duration_min',
            'start_at', 'end_at', 'status', 'location_address',
            'prep_instructions', 'cancel_reason', 'created_at',
        ]
        read_only_fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type',
            'patient_first_name', 'patient_last_name',
            'therapy_type_name', 'therapy_type_color', 'therapy_type_duration_min',
            'created_at',
        ]


class VisitCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.UUIDField(write_only=True)
    episode_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    therapy_type_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Visit
        fields = [
            'patient_id', 'episode_id', 'therapy_type_id',
            'start_at', 'end_at', 'location_address', 'prep_instructions',
        ]

    def validate(self, attrs):
        therapist = self.context['therapist']
        patient_id = attrs['patient_id']
        therapy_type_id = attrs['therapy_type_id']
        episode_id = attrs.get('episode_id')

        if not PatientProfile.objects.filter(pk=patient_id, therapist=therapist).exists():
            raise serializers.ValidationError(
                {'patient_id': 'Pacjent nie należy do tego terapeuty.'}
            )

        if not TherapyType.objects.filter(pk=therapy_type_id, therapist=therapist).exists():
            raise serializers.ValidationError(
                {'therapy_type_id': 'Typ terapii nie należy do tego terapeuty.'}
            )

        if episode_id is not None:
            if not TreatmentEpisode.objects.filter(
                pk=episode_id,
                patient_id=patient_id,
                patient__therapist=therapist,
            ).exists():
                raise serializers.ValidationError(
                    {'episode_id': 'Epizod nie należy do wskazanego pacjenta.'}
                )

        return attrs

    def create(self, validated_data):
        patient_id = validated_data.pop('patient_id')
        episode_id = validated_data.pop('episode_id', None)
        therapy_type_id = validated_data.pop('therapy_type_id')
        therapist = self.context['therapist']
        return Visit.objects.create(
            patient_id=patient_id,
            therapist=therapist,
            episode_id=episode_id,
            therapy_type_id=therapy_type_id,
            **validated_data,
        )


class VisitRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ['start_at', 'end_at']


class VisitCancelSerializer(serializers.Serializer):
    cancel_reason = serializers.CharField(required=False, allow_blank=True)
