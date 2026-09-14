from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    ADDRESS_TOO_LONG,
    BIO_TOO_LONG,
    LAST_NAME_INVALID,
    LAST_NAME_REQUIRED,
    LAST_NAME_TOO_LONG,
    LAST_NAME_TOO_SHORT,
    NAME_INVALID,
    NAME_REQUIRED,
    NAME_TOO_LONG,
    NAME_TOO_SHORT,
    normalize_and_validate_address,
    normalize_and_validate_bio,
    normalize_and_validate_courses,
    normalize_and_validate_first_name,
    normalize_and_validate_last_name,
)
from core.phone_policy import PHONE_FIELD_ERRORS, normalize_and_validate_phone
from therapists.competence import QualificationLevel

from .models import TherapistProfile

_FIRST_NAME_FIELD_ERRORS = {
    'blank': NAME_REQUIRED,
    'required': NAME_REQUIRED,
    'null': NAME_REQUIRED,
    'max_length': NAME_TOO_LONG,
    'min_length': NAME_TOO_SHORT,
    'invalid': NAME_INVALID,
}

_LAST_NAME_FIELD_ERRORS = {
    'blank': LAST_NAME_REQUIRED,
    'required': LAST_NAME_REQUIRED,
    'null': LAST_NAME_REQUIRED,
    'max_length': LAST_NAME_TOO_LONG,
    'min_length': LAST_NAME_TOO_SHORT,
    'invalid': LAST_NAME_INVALID,
}


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
    first_name = serializers.CharField(
        max_length=100,
        required=False,
        error_messages=_FIRST_NAME_FIELD_ERRORS,
    )
    last_name = serializers.CharField(
        max_length=100,
        required=False,
        error_messages=_LAST_NAME_FIELD_ERRORS,
    )
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
            'first_name', 'last_name', 'phone', 'location_address', 'bio', 'courses',
            'qualification_level', 'experience_years',
        ]

    def validate_first_name(self, value):
        try:
            return normalize_and_validate_first_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_last_name(self, value):
        try:
            return normalize_and_validate_last_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

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

    def update(self, instance, validated_data):
        user = instance.user
        user_updated = False
        if 'first_name' in validated_data:
            user.first_name = validated_data.pop('first_name')
            user_updated = True
        if 'last_name' in validated_data:
            user.last_name = validated_data.pop('last_name')
            user_updated = True
        if user_updated:
            user.save(update_fields=['first_name', 'last_name', 'updated_at'])
        return super().update(instance, validated_data)


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
