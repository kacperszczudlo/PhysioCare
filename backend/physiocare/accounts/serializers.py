from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.email_policy import (
    EMAIL_FIELD_ERRORS,
    EMAIL_TAKEN,
    normalize_and_validate_email,
)
from accounts.password_policy import enforce_password_policy
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
from notifications.defaults import ensure_default_preferences
from patients.models import PatientProfile
from privacy.models import Consent, ConsentType
from therapists.models import TherapistProfile
from therapists.pwzf_policy import (
    PWZF_FIELD_ERRORS,
    PWZF_TAKEN,
    normalize_and_validate_pwzf,
)

User = get_user_model()

EMAIL_TAKEN_MESSAGE = EMAIL_TAKEN
PWZF_TAKEN_MESSAGE = PWZF_TAKEN

_PASSWORD_FIELD_ERRORS = {
    'blank': 'Podaj hasło.',
    'required': 'Podaj hasło.',
    'null': 'Podaj hasło.',
}

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

_PWZF_FIELD_ERRORS = PWZF_FIELD_ERRORS

_THERAPIST_ID_FIELD_ERRORS = {
    'required': 'Podaj kod terapeuty.',
    'null': 'Podaj kod terapeuty.',
    'invalid': 'Podaj prawidłowy kod terapeuty (UUID z panelu terapeuty).',
}


def _password_user_from_data(data) -> User:
    """Build an unsaved user for similarity checks during registration."""
    return User(
        email=(data.get('email') or '') if hasattr(data, 'get') else '',
        first_name=(data.get('first_name') or '') if hasattr(data, 'get') else '',
        last_name=(data.get('last_name') or '') if hasattr(data, 'get') else '',
    )


def _validate_password_value(password: str, user=None) -> str:
    try:
        return enforce_password_policy(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc


class PatientRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=100,
        write_only=True,
        error_messages=_FIRST_NAME_FIELD_ERRORS,
    )
    last_name = serializers.CharField(
        max_length=100,
        write_only=True,
        error_messages=_LAST_NAME_FIELD_ERRORS,
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )
    therapist_id = serializers.UUIDField(
        write_only=True,
        error_messages=_THERAPIST_ID_FIELD_ERRORS,
    )
    consents = serializers.DictField(child=serializers.BooleanField(), write_only=True)
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        write_only=True,
        error_messages=PHONE_FIELD_ERRORS,
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'first_name', 'last_name',
            'therapist_id', 'consents', 'phone',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'validators': [], 'error_messages': EMAIL_FIELD_ERRORS},
        }

    def validate_email(self, value):
        try:
            email = normalize_and_validate_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

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

    def validate_password(self, value):
        return _validate_password_value(
            value,
            user=_password_user_from_data(self.initial_data),
        )

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

    def validate_phone(self, value):
        try:
            return normalize_and_validate_phone(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        therapist_id = validated_data.pop('therapist_id')
        consents_data = validated_data.pop('consents')
        password = validated_data.pop('password')
        phone = validated_data.pop('phone', '')

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
            phone=phone,
        )

        ensure_default_preferences(user)

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
    first_name = serializers.CharField(
        max_length=100,
        write_only=True,
        error_messages=_FIRST_NAME_FIELD_ERRORS,
    )
    last_name = serializers.CharField(
        max_length=100,
        write_only=True,
        error_messages=_LAST_NAME_FIELD_ERRORS,
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )
    pwzf_number = serializers.CharField(
        max_length=20,
        write_only=True,
        error_messages=_PWZF_FIELD_ERRORS,
    )
    pwzf_declaration = serializers.BooleanField(write_only=True)
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        write_only=True,
        error_messages=PHONE_FIELD_ERRORS,
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'first_name', 'last_name',
            'pwzf_number', 'pwzf_declaration', 'phone',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'validators': [], 'error_messages': EMAIL_FIELD_ERRORS},
        }

    def validate_email(self, value):
        try:
            email = normalize_and_validate_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

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

    def validate_password(self, value):
        return _validate_password_value(
            value,
            user=_password_user_from_data(self.initial_data),
        )

    def validate_pwzf_declaration(self, value):
        if not value:
            raise serializers.ValidationError(
                'Zaznacz oświadczenie o posiadaniu ważnego numeru PWZFz.'
            )
        return value

    def validate_pwzf_number(self, value):
        try:
            normalized = normalize_and_validate_pwzf(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        if TherapistProfile.objects.filter(pwzf_number=normalized).exists():
            raise serializers.ValidationError(PWZF_TAKEN_MESSAGE)
        return normalized

    def validate_phone(self, value):
        try:
            return normalize_and_validate_phone(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        pwzf_number = validated_data.pop('pwzf_number')
        validated_data.pop('pwzf_declaration')
        password = validated_data.pop('password')
        phone = validated_data.pop('phone', '')

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
            phone=phone,
        )

        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages=EMAIL_FIELD_ERRORS)
    client = serializers.ChoiceField(
        choices=('web', 'mobile'),
        required=False,
        default='web',
    )

    def validate_email(self, value):
        try:
            return User.objects.normalize_email(normalize_and_validate_email(value))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )

    def validate_new_password(self, value):
        user = self.context.get('user')
        return _validate_password_value(value, user=user)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': 'Podaj obecne hasło.',
            'required': 'Podaj obecne hasło.',
            'null': 'Podaj obecne hasło.',
        },
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )

    def validate_new_password(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request is not None else None
        if user is not None and not getattr(user, 'is_authenticated', False):
            user = None
        return _validate_password_value(value, user=user)
