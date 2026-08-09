from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.phone_policy import PHONE_FIELD_ERRORS, normalize_and_validate_phone
from patients.pesel_policy import PESEL_FIELD_ERRORS, normalize_and_validate_pesel
from privacy.models import Consent

from .models import PatientProfile


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
        fields = ['pesel', 'phone']

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


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = ['consent_type', 'granted', 'granted_at']
        read_only_fields = ['granted_at']


class OptionalConsentsUpdateSerializer(serializers.Serializer):
    marketing = serializers.BooleanField(required=False)
    research = serializers.BooleanField(required=False)
