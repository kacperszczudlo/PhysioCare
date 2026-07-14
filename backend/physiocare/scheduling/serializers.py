from rest_framework import serializers

from .models import TherapyType, Visit


class TherapyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapyType
        fields = ['id', 'name', 'color_hex', 'duration_min', 'created_at']
        read_only_fields = ['id', 'created_at']


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type',
            'start_at', 'end_at', 'status', 'location_address',
            'prep_instructions', 'cancel_reason', 'created_at',
        ]
        read_only_fields = ['id', 'therapist', 'created_at']


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
