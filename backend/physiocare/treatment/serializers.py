from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    NOTE_REQUIRED,
    NOTE_TOO_LONG,
    SUMMARY_TOO_LONG,
    normalize_and_validate_icd10,
    normalize_optional_text,
)

from .models import BodyAreaPain, TreatmentEpisode, VisitNote


class TreatmentEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentEpisode
        fields = [
            'id', 'patient', 'icd10_code', 'status', 'summary_note',
            'started_at', 'ended_at', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'created_at']

    def validate_icd10_code(self, value):
        try:
            return normalize_and_validate_icd10(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_summary_note(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=SUMMARY_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class TreatmentEpisodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentEpisode
        fields = ['id', 'icd10_code', 'status', 'summary_note', 'started_at']
        read_only_fields = ['id']

    def validate_icd10_code(self, value):
        try:
            return normalize_and_validate_icd10(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_summary_note(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=SUMMARY_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class BodyAreaPainSerializer(serializers.ModelSerializer):
    vas_score = serializers.IntegerField(
        min_value=0,
        max_value=10,
        error_messages={
            'min_value': 'Skala VAS musi być liczbą od 0 do 10.',
            'max_value': 'Skala VAS musi być liczbą od 0 do 10.',
            'invalid': 'Skala VAS musi być liczbą od 0 do 10.',
            'required': 'Podaj natężenie bólu (VAS 0–10).',
        },
    )
    body_region = serializers.CharField(
        max_length=50,
        error_messages={
            'blank': 'Wskaż obszar ciała.',
            'required': 'Wskaż obszar ciała.',
            'max_length': 'Nazwa obszaru ciała może mieć co najwyżej 50 znaków.',
        },
    )

    class Meta:
        model = BodyAreaPain
        fields = [
            'id', 'episode', 'body_region', 'view_side',
            'vas_score', 'pain_character', 'treatment_targets', 'recorded_at',
        ]
        read_only_fields = ['id', 'episode', 'recorded_at']

    def validate_body_region(self, value):
        region = ' '.join(str(value).split())
        if not region:
            raise serializers.ValidationError('Wskaż obszar ciała.')
        return region

    def validate_pain_character(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Charakter bólu musi być listą.')
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise serializers.ValidationError(
                    'Każdy charakter bólu musi być niepustym tekstem.'
                )
            cleaned.append(item.strip())
        return cleaned

    def validate_treatment_targets(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Cele terapii muszą być listą.')
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise serializers.ValidationError(
                    'Każdy cel terapii musi być niepustym tekstem.'
                )
            cleaned.append(item.strip())
        return cleaned


class VisitNoteSerializer(serializers.ModelSerializer):
    content = serializers.CharField(
        error_messages={
            'blank': NOTE_REQUIRED,
            'required': NOTE_REQUIRED,
        },
    )

    class Meta:
        model = VisitNote
        fields = ['id', 'episode', 'visit', 'content', 'created_at']
        read_only_fields = ['id', 'episode', 'created_at']

    def validate_content(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
                allow_blank=False,
                required_message=NOTE_REQUIRED,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_visit(self, visit):
        if visit is None:
            return visit
        episode = self.context.get('episode')
        if episode is None:
            return visit
        if visit.patient_id != episode.patient_id:
            raise serializers.ValidationError(
                'Wizyta nie należy do pacjenta tego epizodu.'
            )
        if visit.episode_id is not None and visit.episode_id != episode.id:
            raise serializers.ValidationError(
                'Wizyta nie należy do tego epizodu.'
            )
        return visit
