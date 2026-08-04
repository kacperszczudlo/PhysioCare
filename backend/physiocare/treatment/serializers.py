from rest_framework import serializers

from .models import BodyAreaPain, TreatmentEpisode, VisitNote


class TreatmentEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentEpisode
        fields = [
            'id', 'patient', 'icd10_code', 'status', 'summary_note',
            'started_at', 'ended_at', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'created_at']


class TreatmentEpisodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentEpisode
        fields = ['id', 'icd10_code', 'status', 'summary_note', 'started_at']
        read_only_fields = ['id']


class BodyAreaPainSerializer(serializers.ModelSerializer):
    vas_score = serializers.IntegerField(min_value=0, max_value=10)

    class Meta:
        model = BodyAreaPain
        fields = [
            'id', 'episode', 'body_region', 'view_side',
            'vas_score', 'pain_character', 'recorded_at',
        ]
        read_only_fields = ['id', 'episode', 'recorded_at']


class VisitNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitNote
        fields = ['id', 'episode', 'visit', 'content', 'created_at']
        read_only_fields = ['id', 'episode', 'created_at']
