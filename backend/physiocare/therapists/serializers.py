from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    ADDRESS_TOO_LONG,
    BIO_TOO_LONG,
    normalize_and_validate_address,
    normalize_and_validate_bio,
    normalize_and_validate_courses,
)
from core.phone_policy import PHONE_FIELD_ERRORS, normalize_and_validate_phone
from therapists.competence import QualificationLevel

from .models import TherapistProfile


class TherapistProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    competences = serializers.SerializerMethodField()

    class Meta:
        model = TherapistProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pwzf_number', 'phone', 'location_address', 'bio', 'courses',
            'avatar_url', 'qualification_level', 'experience_years',
            'competences', 'created_at',
        ]
        read_only_fields = ['id', 'pwzf_number', 'competences', 'created_at']

    def get_competences(self, obj):
        return obj.competence_snapshot().to_dict()


class TherapistProfileUpdateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        error_messages=PHONE_FIELD_ERRORS,
    )
    location_address = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        error_messages={'max_length': ADDRESS_TOO_LONG},
    )
    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': BIO_TOO_LONG},
    )
    courses = serializers.JSONField(required=False)
    qualification_level = serializers.ChoiceField(
        choices=QualificationLevel.CHOICES,
        required=False,
    )
    experience_years = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=60,
        error_messages={
            'min_value': 'Staż nie może być ujemny.',
            'max_value': 'Podaj realistyczny staż (0-60 lat).',
            'invalid': 'Staż musi być liczbą całkowitą.',
        },
    )

    class Meta:
        model = TherapistProfile
        fields = [
            'phone', 'location_address', 'bio', 'courses',
            'qualification_level', 'experience_years',
        ]

    def validate_phone(self, value):
        try:
            return normalize_and_validate_phone(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_location_address(self, value):
        try:
            return normalize_and_validate_address(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_bio(self, value):
        try:
            return normalize_and_validate_bio(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_courses(self, value):
        try:
            return normalize_and_validate_courses(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class TherapistPublicSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    qualification_label = serializers.SerializerMethodField()
    competences = serializers.SerializerMethodField()

    class Meta:
        model = TherapistProfile
        fields = [
            'id', 'first_name', 'last_name', 'bio', 'courses',
            'avatar_url', 'phone', 'location_address',
            'qualification_level', 'qualification_label', 'experience_years',
            'competences',
        ]

    def get_qualification_label(self, obj):
        return QualificationLevel.LABELS.get(obj.qualification_level, obj.qualification_level)

    def get_competences(self, obj):
        return obj.competence_snapshot().to_dict()
