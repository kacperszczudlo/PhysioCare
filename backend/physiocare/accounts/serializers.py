from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from patients.models import PatientProfile
from privacy.models import Consent, ConsentType
from therapists.models import TherapistProfile

User = get_user_model()

EMAIL_TAKEN_MESSAGE = (
    'Ten adres e-mail jest już zarejestrowany. Zaloguj się lub użyj innego adresu.'
)
PWZF_TAKEN_MESSAGE = (
    'Konto z tym numerem PWZFz już istnieje. Zaloguj się lub użyj innego numeru.'
)


class PatientRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100, write_only=True)
    last_name = serializers.CharField(max_length=100, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    therapist_id = serializers.UUIDField(write_only=True)
    consents = serializers.DictField(child=serializers.BooleanField(), write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'first_name', 'last_name',
            'therapist_id', 'consents',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'validators': []},
        }

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

    def validate_consents(self, value):
        if not value.get('terms', False):
            raise serializers.ValidationError(
                'System odrzuca zgłoszenia pozbawione autoryzacji regulaminu.'
            )
        if not value.get('medical_data', False):
            raise serializers.ValidationError(
                'Przetwarzanie danych medycznych uwarunkowane jest zgodą formalną.'
            )
        return value

    def validate_therapist_id(self, value):
        if not TherapistProfile.objects.filter(id=value).exists():
            raise serializers.ValidationError('Nie znaleziono wskazanego terapeuty.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        therapist_id = validated_data.pop('therapist_id')
        consents_data = validated_data.pop('consents')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            role='PATIENT',
            first_name=first_name,
            last_name=last_name,
        )

        PatientProfile.objects.create(
            user=user,
            therapist_id=therapist_id,
        )

        Consent.objects.create(
            user=user,
            consent_type=ConsentType.TERMS_REQUIRED,
            granted=consents_data['terms'],
        )
        Consent.objects.create(
            user=user,
            consent_type=ConsentType.MEDICAL_DATA_REQUIRED,
            granted=consents_data['medical_data'],
        )

        return user


class TherapistRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100, write_only=True)
    last_name = serializers.CharField(max_length=100, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    pwzf_number = serializers.CharField(max_length=20, write_only=True)
    pwzf_declaration = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'first_name', 'last_name',
            'pwzf_number', 'pwzf_declaration',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'validators': []},
        }

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

    def validate_pwzf_declaration(self, value):
        if not value:
            raise serializers.ValidationError(
                'Zaznacz oświadczenie o posiadaniu ważnego numeru PWZFz.'
            )
        return value

    def validate_pwzf_number(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError('Podaj numer PWZFz.')
        if TherapistProfile.objects.filter(pwzf_number=normalized).exists():
            raise serializers.ValidationError(PWZF_TAKEN_MESSAGE)
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        pwzf_number = validated_data.pop('pwzf_number')
        validated_data.pop('pwzf_declaration')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            role='THERAPIST',
            first_name=first_name,
            last_name=last_name,
        )

        TherapistProfile.objects.create(
            user=user,
            pwzf_number=pwzf_number,
        )

        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
