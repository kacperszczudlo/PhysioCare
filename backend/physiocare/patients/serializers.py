from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    LAST_NAME_INVALID,
    LAST_NAME_REQUIRED,
    LAST_NAME_TOO_LONG,
    LAST_NAME_TOO_SHORT,
    NAME_INVALID,
    NAME_REQUIRED,
    NAME_TOO_LONG,
    NAME_TOO_SHORT,
    normalize_and_validate_first_name,
    normalize_and_validate_last_name,
)
from core.phone_policy import PHONE_FIELD_ERRORS, normalize_and_validate_phone
from patients.pesel_policy import PESEL_FIELD_ERRORS, normalize_and_validate_pesel
from privacy.models import Consent

from .models import PatientProfile

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


class PatientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'avatar_url']


class PatientDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pesel', 'phone', 'avatar_url', 'therapist', 'created_at',
        ]
        read_only_fields = ['id', 'therapist', 'created_at']


class MeProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pesel', 'phone', 'avatar_url', 'therapist',
        ]
        read_only_fields = ['id', 'therapist']


class MeProfileUpdateSerializer(serializers.ModelSerializer):
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
    pesel = serializers.CharField(
        max_length=11,
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages=PESEL_FIELD_ERRORS,
    )

    class Meta:
        model = PatientProfile
        fields = ['first_name', 'last_name', 'pesel', 'phone']

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

    def validate_pesel(self, value):
        try:
            return normalize_and_validate_pesel(value, allow_blank=True)
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


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = ['consent_type', 'granted', 'granted_at']
        read_only_fields = ['granted_at']


class OptionalConsentsUpdateSerializer(serializers.Serializer):
    marketing = serializers.BooleanField(required=False)
    research = serializers.BooleanField(required=False)
