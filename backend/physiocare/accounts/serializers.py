from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.email_policy import (
    EMAIL_FIELD_ERRORS,
    EMAIL_TAKEN,
    EMAIL_TAKEN_GOOGLE,
    normalize_and_validate_email,
)
from accounts.google_auth import GoogleAuthError, verify_google_id_token
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


def _apply_google_identity(attrs: dict, *, credential: str) -> dict:
    """Verify Google credential and merge identity into registration attrs."""
    try:
        identity = verify_google_id_token(credential)
    except GoogleAuthError as exc:
        raise serializers.ValidationError({'google_credential': [exc.message]}) from exc

    email = User.objects.normalize_email(identity.email)
    existing = User.objects.filter(email__iexact=email).first()
    if existing is not None:
        role_label = 'pacjenta' if existing.role == 'PATIENT' else 'fizjoterapeuty'
        raise serializers.ValidationError(
            {
                'email': [
                    f'{EMAIL_TAKEN_GOOGLE} '
                    f'To konto ma rolę {role_label}.'
                ],
                'google_credential': [
                    'Konto z tym adresem Google już istnieje — użyj logowania zamiast rejestracji.'
                ],
            }
        )

    attrs['email'] = email
    # Names from form first, else Google claims (no placeholder names).
    first_name = (attrs.get('first_name') or '').strip() or (identity.given_name or '').strip()
    last_name = (attrs.get('last_name') or '').strip() or (identity.family_name or '').strip()
    attrs['first_name'] = first_name
    attrs['last_name'] = last_name

    name_errors: dict[str, list[str]] = {}
    try:
        attrs['first_name'] = normalize_and_validate_first_name(attrs['first_name'] or None)
    except DjangoValidationError as exc:
        name_errors['first_name'] = list(exc.messages)
    try:
        attrs['last_name'] = normalize_and_validate_last_name(attrs['last_name'] or None)
    except DjangoValidationError as exc:
        name_errors['last_name'] = list(exc.messages)
    if name_errors:
        raise serializers.ValidationError(name_errors)

    attrs.pop('password', None)
    attrs['_google_sub'] = identity.sub
    return attrs


class PatientRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        write_only=True,
        error_messages=_FIRST_NAME_FIELD_ERRORS,
    )
    last_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        write_only=True,
        error_messages=_LAST_NAME_FIELD_ERRORS,
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )
    google_credential = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
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
            'id', 'email', 'password', 'google_credential', 'first_name', 'last_name',
            'therapist_id', 'consents', 'phone',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {
                'required': False,
                'allow_blank': True,
                'validators': [],
                'error_messages': EMAIL_FIELD_ERRORS,
            },
        }

    def validate_email(self, value):
        if value is None or str(value).strip() == '':
            return value
        try:
            email = normalize_and_validate_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

    def validate_first_name(self, value):
        if value is None or str(value).strip() == '':
            return value
        try:
            return normalize_and_validate_first_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_last_name(self, value):
        if value is None or str(value).strip() == '':
            return value
        try:
            return normalize_and_validate_last_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_password(self, value):
        if value is None or str(value).strip() == '':
            return value
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

    def validate(self, attrs):
        credential = (attrs.pop('google_credential', None) or '').strip()
        if credential:
            return _apply_google_identity(attrs, credential=credential)

        errors = {}
        if not (attrs.get('email') or '').strip():
            errors['email'] = [EMAIL_FIELD_ERRORS.get('required', 'Podaj e-mail.')]
        if not (attrs.get('first_name') or '').strip():
            errors['first_name'] = [NAME_REQUIRED]
        if not (attrs.get('last_name') or '').strip():
            errors['last_name'] = [LAST_NAME_REQUIRED]
        if not (attrs.get('password') or '').strip():
            errors['password'] = ['Podaj hasło lub użyj Google.']
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        therapist_id = validated_data.pop('therapist_id')
        consents_data = validated_data.pop('consents')
        password = validated_data.pop('password', None)
        google_sub = validated_data.pop('_google_sub', None)
        phone = validated_data.pop('phone', '')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            role='PATIENT',
            first_name=first_name,
            last_name=last_name,
            google_sub=google_sub,
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
        required=False,
        allow_blank=True,
        write_only=True,
        error_messages=_FIRST_NAME_FIELD_ERRORS,
    )
    last_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        write_only=True,
        error_messages=_LAST_NAME_FIELD_ERRORS,
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )
    google_credential = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
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
            'id', 'email', 'password', 'google_credential', 'first_name', 'last_name',
            'pwzf_number', 'pwzf_declaration', 'phone',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {
                'required': False,
                'allow_blank': True,
                'validators': [],
                'error_messages': EMAIL_FIELD_ERRORS,
            },
        }

    def validate_email(self, value):
        if value is None or str(value).strip() == '':
            return value
        try:
            email = normalize_and_validate_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)
        return email

    def validate_first_name(self, value):
        if value is None or str(value).strip() == '':
            return value
        try:
            return normalize_and_validate_first_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_last_name(self, value):
        if value is None or str(value).strip() == '':
            return value
        try:
            return normalize_and_validate_last_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_password(self, value):
        if value is None or str(value).strip() == '':
            return value
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

    def validate(self, attrs):
        credential = (attrs.pop('google_credential', None) or '').strip()
        if credential:
            return _apply_google_identity(attrs, credential=credential)

        errors = {}
        if not (attrs.get('email') or '').strip():
            errors['email'] = [EMAIL_FIELD_ERRORS.get('required', 'Podaj e-mail.')]
        if not (attrs.get('first_name') or '').strip():
            errors['first_name'] = [NAME_REQUIRED]
        if not (attrs.get('last_name') or '').strip():
            errors['last_name'] = [LAST_NAME_REQUIRED]
        if not (attrs.get('password') or '').strip():
            errors['password'] = ['Podaj hasło lub użyj Google.']
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        pwzf_number = validated_data.pop('pwzf_number')
        validated_data.pop('pwzf_declaration')
        password = validated_data.pop('password', None)
        google_sub = validated_data.pop('_google_sub', None)
        phone = validated_data.pop('phone', '')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            role='THERAPIST',
            first_name=first_name,
            last_name=last_name,
            google_sub=google_sub,
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
