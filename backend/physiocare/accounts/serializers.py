from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.email_policy import (
    EMAIL_FIELD_ERRORS,
    EMAIL_TAKEN,
    EMAIL_TAKEN_GOOGLE,
    normalize_and_validate_email,
)
from accounts.google_auth import GoogleAuthError, verify_google_id_token
from accounts.password_policy import enforce_password_policy
from accounts.recaptcha import verify_recaptcha_token
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
from privacy.account_deletion import free_inactive_email_holder
from privacy.models import Consent, ConsentType
from therapists.competence import QualificationLevel
from therapists.models import TherapistProfile
from therapists.pwzf_policy import (
    PWZF_FIELD_ERRORS,
    PWZF_TAKEN,
    normalize_and_validate_pwzf,
)

User: type[object] = get_user_model()

EMAIL_TAKEN_MESSAGE: str = EMAIL_TAKEN
PWZF_TAKEN_MESSAGE: str = PWZF_TAKEN


def _ensure_email_available(email: str) -> None:
    """Odrzuca rejestrację, jeśli aktywne konto z danym adresem e-mail już istnieje.

    Args:
        email (str): Sprawdzany adres e-mail.

    Raises:
        serializers.ValidationError: Gdy adres e-mail jest zajęty przez aktywnego użytkownika.
        TypeError: Gdy podany adres e-mail nie jest ciągiem znaków.
    """
    if not isinstance(email, str):
        raise TypeError('Adres e-mail musi być ciągiem znaków.')
    existing = User.objects.filter(email__iexact=email).first()
    if existing is not None and existing.is_active:
        raise serializers.ValidationError(EMAIL_TAKEN_MESSAGE)


def _prepare_email_for_registration(email: str) -> None:
    """Zwalnia zanonimizowane/nieaktywne konta z tym adresem e-mail przed utworzeniem nowego konta.

    Args:
        email (str): Adres e-mail do przygotowania.

    Raises:
        TypeError: Gdy podany adres e-mail nie jest ciągiem znaków.
    """
    if not isinstance(email, str):
        raise TypeError('Adres e-mail musi być ciągiem znaków.')
    free_inactive_email_holder(email)


_PASSWORD_FIELD_ERRORS: dict[str, str] = {
    'blank': 'Podaj hasło.',
    'required': 'Podaj hasło.',
    'null': 'Podaj hasło.',
}

_FIRST_NAME_FIELD_ERRORS: dict[str, str] = {
    'blank': NAME_REQUIRED,
    'required': NAME_REQUIRED,
    'null': NAME_REQUIRED,
    'max_length': NAME_TOO_LONG,
    'min_length': NAME_TOO_SHORT,
    'invalid': NAME_INVALID,
}

_LAST_NAME_FIELD_ERRORS: dict[str, str] = {
    'blank': LAST_NAME_REQUIRED,
    'required': LAST_NAME_REQUIRED,
    'null': LAST_NAME_REQUIRED,
    'max_length': LAST_NAME_TOO_LONG,
    'min_length': LAST_NAME_TOO_SHORT,
    'invalid': LAST_NAME_INVALID,
}

_PWZF_FIELD_ERRORS: dict[str, str] = PWZF_FIELD_ERRORS

_THERAPIST_ID_FIELD_ERRORS: dict[str, str] = {
    'required': 'Podaj kod terapeuty.',
    'null': 'Podaj kod terapeuty.',
    'invalid': 'Podaj prawidłowy kod terapeuty (UUID z panelu terapeuty).',
}


def _password_user_from_data(data: object) -> object:
    """Tworzy niezapisaną instancję użytkownika na potrzeby sprawdzania podobieństwa hasła.

    Args:
        data (object): Słownik lub obiekt zawierający dane rejestracji.

    Returns:
        object: Tymczasowy obiekt użytkownika.

    Raises:
        TypeError: Gdy argument data jest None.
    """
    if data is None:
        raise TypeError("Argument 'data' nie może być None.")

    email_val = data.get('email') if hasattr(data, 'get') else ''
    first_name_val = data.get('first_name') if hasattr(data, 'get') else ''
    last_name_val = data.get('last_name') if hasattr(data, 'get') else ''

    return User(
        email=(email_val or ''),
        first_name=(first_name_val or ''),
        last_name=(last_name_val or ''),
    )


def _validate_password_value(password: str, user: object | None = None) -> str:
    """Waliduje podaną wartość hasła na podstawie reguł polityki haseł.

    Args:
        password (str): Hasło do zweryfikowania.
        user (object | None): Opcjonalna instancja użytkownika do sprawdzania podobieństwa.

    Returns:
        str: Zweryfikowane hasło.

    Raises:
        serializers.ValidationError: Gdy hasło nie spełnia wymogów polityki haseł.
        TypeError: Gdy password nie jest typu str.
    """
    if not isinstance(password, str):
        raise TypeError("Argument 'password' musi być typu str.")

    try:
        return enforce_password_policy(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc


def _apply_google_identity(attrs: dict[str, object], *, credential: str) -> dict[str, object]:
    """Weryfikuje poświadczenie Google i scala dane tożsamości z atrybutami rejestracji.

    Args:
        attrs (dict[str, object]): Atrybuty wejściowe rejestracji.
        credential (str): Token ID z Google.

    Returns:
        dict[str, object]: Zaktualizowane atrybuty rejestracji z danymi z Google.

    Raises:
        serializers.ValidationError: Gdy token Google jest nieprawidłowy lub konto e-mail jest już zajęte.
        TypeError: Gdy attrs nie jest słownikiem lub credential nie jest napisem.
    """
    if not isinstance(attrs, dict):
        raise TypeError("Argument 'attrs' musi być typu dict.")
    if not isinstance(credential, str):
        raise TypeError("Argument 'credential' musi być typu str.")

    try:
        identity = verify_google_id_token(credential)
    except GoogleAuthError as exc:
        raise serializers.ValidationError({'google_credential': [exc.message]}) from exc

    email = User.objects.normalize_email(identity.email)
    existing = User.objects.filter(email__iexact=email).first()
    if existing is not None and existing.is_active:
        role_label = 'pacjenta' if existing.role == 'PATIENT' else 'fizjoterapeuty'
        raise serializers.ValidationError(
            {
                'email': [
                    f'{EMAIL_TAKEN_GOOGLE} '
                    f'To konto ma rolę {role_label}.'
                ],
                'google_credential': [
                    'Konto z tym adresem Google już istnieje - użyj logowania zamiast rejestracji.'
                ],
            }
        )

    attrs['email'] = email
    first_name_attr = attrs.get('first_name')
    last_name_attr = attrs.get('last_name')
    first_name = (str(first_name_attr) if first_name_attr else '').strip() or (identity.given_name or '').strip()
    last_name = (str(last_name_attr) if last_name_attr else '').strip() or (identity.family_name or '').strip()
    attrs['first_name'] = first_name
    attrs['last_name'] = last_name

    name_errors: dict[str, list[str]] = {}
    try:
        fn_val = str(attrs['first_name']) if attrs['first_name'] else None
        attrs['first_name'] = normalize_and_validate_first_name(fn_val)
    except DjangoValidationError as exc:
        name_errors['first_name'] = list(exc.messages)
    try:
        ln_val = str(attrs['last_name']) if attrs['last_name'] else None
        attrs['last_name'] = normalize_and_validate_last_name(ln_val)
    except DjangoValidationError as exc:
        name_errors['last_name'] = list(exc.messages)
    if name_errors:
        raise serializers.ValidationError(name_errors)

    attrs.pop('password', None)
    attrs['_google_sub'] = identity.sub
    return attrs


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Serializator rejestracji nowego pacjenta."""

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
    recaptcha_token = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    recaptcha_client = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    therapist_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        write_only=True,
        error_messages=_THERAPIST_ID_FIELD_ERRORS,
    )
    therapist_code = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
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
            'id', 'email', 'password', 'google_credential', 'recaptcha_token', 'recaptcha_client', 'first_name', 'last_name',
            'therapist_id', 'therapist_code', 'consents', 'phone',
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

    def validate_email(self, value: object) -> str | None:
        """Waliduje i normalizuje adres e-mail pacjenta.

        Args:
            value (object): Podany adres e-mail.

        Returns:
            str | None: Znormalizowany adres e-mail lub None/pusty ciąg.

        Raises:
            serializers.ValidationError: Gdy adres e-mail jest nieprawidłowy lub zajęty.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Adres e-mail musi być tekstem.')
        try:
            email = normalize_and_validate_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        email = User.objects.normalize_email(email)
        _ensure_email_available(email)
        return email

    def validate_first_name(self, value: object) -> str | None:
        """Waliduje i normalizuje imię pacjenta.

        Args:
            value (object): Podane imię.

        Returns:
            str | None: Znormalizowane imię.

        Raises:
            serializers.ValidationError: Gdy imię nie spełnia wymogów walidacji.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Imię musi być tekstem.')
        try:
            return normalize_and_validate_first_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_last_name(self, value: object) -> str | None:
        """Waliduje i normalizuje nazwisko pacjenta.

        Args:
            value (object): Podane nazwisko.

        Returns:
            str | None: Znormalizowane nazwisko.

        Raises:
            serializers.ValidationError: Gdy nazwisko nie spełnia wymogów walidacji.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Nazwisko musi być tekstem.')
        try:
            return normalize_and_validate_last_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_password(self, value: object) -> str | None:
        """Waliduje hasło pacjenta zgodnie z polityką haseł.

        Args:
            value (object): Podane hasło.

        Returns:
            str | None: Zwalidowane hasło.

        Raises:
            serializers.ValidationError: Gdy hasło jest zbyt słabe lub nie jest tekstem.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Hasło musi być tekstem.')
        return _validate_password_value(
            value,
            user=_password_user_from_data(self.initial_data),
        )

    def validate_consents(self, value: object) -> dict[str, object]:
        """Waliduje wymagane zgody formalne i medyczne.

        Args:
            value (object): Słownik zawierający flagi zgód.

        Returns:
            dict[str, object]: Zwalidowany słownik zgód.

        Raises:
            serializers.ValidationError: Gdy brak wymaganych zgód lub typ nie jest słownikiem.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError('Zgody muszą być słownikiem.')

        if not value.get('terms', False):
            raise serializers.ValidationError(
                'System odrzuca zgłoszenia pozbawione autoryzacji regulaminu.'
            )
        if not value.get('medical_data', False):
            raise serializers.ValidationError(
                'Przetwarzanie danych medycznych uwarunkowane jest zgodą formalną.'
            )
        return value

    def validate_therapist_id(self, value: object) -> object | None:
        """Waliduje identyfikator powiązanego fizjoterapeuty.

        Args:
            value (object): UUID fizjoterapeuty lub None.

        Returns:
            object | None: Zwalidowany identyfikator fizjoterapeuty.

        Raises:
            serializers.ValidationError: Gdy fizjoterapeuta o danym ID nie istnieje.
        """
        if value is None:
            return None
        if not TherapistProfile.objects.filter(id=value).exists():
            raise serializers.ValidationError('Nie znaleziono wskazanego terapeuty.')
        return value

    def validate_phone(self, value: object) -> str | None:
        """Waliduje i normalizuje numer telefonu pacjenta.

        Args:
            value (object): Podany numer telefonu.

        Returns:
            str | None: Znormalizowany numer telefonu.

        Raises:
            serializers.ValidationError: Gdy numer telefonu jest niepoprawny.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Numer telefonu musi być tekstem.')
        try:
            return normalize_and_validate_phone(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Weryfikuje kompletność danych rejestracyjnych pacjenta i reCAPTCHA.

        Args:
            attrs (dict[str, object]): Atrybuty wejściowe.

        Returns:
            dict[str, object]: Zwalidowane atrybuty.

        Raises:
            serializers.ValidationError: Gdy brakuje wymaganych pól lub reCAPTCHA jest nieprawidłowa.
            TypeError: Gdy attrs nie jest słownikiem.
        """
        if not isinstance(attrs, dict):
            raise TypeError("Argument 'attrs' musi być słownikiem.")

        recaptcha_token = attrs.pop('recaptcha_token', None)
        recaptcha_client = attrs.pop('recaptcha_client', None)
        client_val = str(recaptcha_client).strip() if recaptcha_client in {'web', 'mobile'} else None

        credential = str(attrs.pop('google_credential', None) or '').strip()
        if credential:
            return _apply_google_identity(attrs, credential=credential)

        if client_val != 'mobile' or recaptcha_token:
            verify_recaptcha_token(
                str(recaptcha_token) if recaptcha_token else None,
                client=client_val,
            )

        errors = {}
        email_attr = attrs.get('email')
        fn_attr = attrs.get('first_name')
        ln_attr = attrs.get('last_name')
        pwd_attr = attrs.get('password')

        if not (str(email_attr) if email_attr else '').strip():
            errors['email'] = [EMAIL_FIELD_ERRORS.get('required', 'Podaj e-mail.')]
        if not (str(fn_attr) if fn_attr else '').strip():
            errors['first_name'] = [NAME_REQUIRED]
        if not (str(ln_attr) if ln_attr else '').strip():
            errors['last_name'] = [LAST_NAME_REQUIRED]
        if not (str(pwd_attr) if pwd_attr else '').strip():
            errors['password'] = ['Podaj hasło lub użyj Google.']
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, object]) -> object:
        """Tworzy konto pacjenta, jego profil oraz zapisuje zgody.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane formularza.

        Returns:
            object: Utworzona instancja użytkownika.

        Raises:
            TypeError: Gdy validated_data nie jest słownikiem.
        """
        if not isinstance(validated_data, dict):
            raise TypeError("Argument 'validated_data' musi być słownikiem.")

        first_name = str(validated_data.pop('first_name'))
        last_name = str(validated_data.pop('last_name'))
        therapist_id = validated_data.pop('therapist_id', None)
        therapist_code = validated_data.pop('therapist_code', None)
        consents_data = validated_data.pop('consents')
        password = validated_data.pop('password', None)
        google_sub = validated_data.pop('_google_sub', None)
        phone = str(validated_data.pop('phone', ''))

        email_val = str(validated_data['email'])
        _prepare_email_for_registration(email_val)

        user = User.objects.create_user(
            email=email_val,
            password=str(password) if password else None,
            role='PATIENT',
            first_name=first_name,
            last_name=last_name,
            google_sub=str(google_sub) if google_sub else None,
            email_verified_at=timezone.now() if google_sub else None,
        )

        patient_profile = PatientProfile.objects.create(
            user=user,
            phone=phone,
        )

        therapist_obj = None
        if therapist_id:
            therapist_obj = TherapistProfile.objects.filter(id=therapist_id).first()
        elif therapist_code and str(therapist_code).strip():
            code = str(therapist_code).strip()
            therapist_obj = TherapistProfile.objects.filter(
                models.Q(pwzf_number__iexact=code) | models.Q(id=code if len(code) == 36 else None)
            ).first()

        if therapist_obj:
            from patients.models import PatientTherapistLink
            PatientTherapistLink.objects.create(
                patient=patient_profile,
                therapist=therapist_obj,
                status='ACTIVE',
            )

        ensure_default_preferences(user)

        if isinstance(consents_data, dict):
            Consent.objects.create(
                user=user,
                consent_type=ConsentType.TERMS_REQUIRED,
                granted=bool(consents_data.get('terms')),
            )
            Consent.objects.create(
                user=user,
                consent_type=ConsentType.MEDICAL_DATA_REQUIRED,
                granted=bool(consents_data.get('medical_data')),
            )

        return user


class TherapistRegistrationSerializer(serializers.ModelSerializer):
    """Serializator rejestracji nowego fizjoterapeuty."""

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
    recaptcha_token = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )
    recaptcha_client = serializers.CharField(
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
    qualification_level = serializers.ChoiceField(
        choices=QualificationLevel.CHOICES,
        required=False,
        default=QualificationLevel.MAGISTER,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'google_credential', 'recaptcha_token', 'recaptcha_client', 'first_name', 'last_name',
            'pwzf_number', 'pwzf_declaration', 'phone', 'qualification_level',
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

    def validate_email(self, value: object) -> str | None:
        """Waliduje i normalizuje adres e-mail fizjoterapeuty.

        Args:
            value (object): Podany adres e-mail.

        Returns:
            str | None: Znormalizowany adres e-mail.

        Raises:
            serializers.ValidationError: Gdy e-mail jest nieprawidłowy lub zajęty.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Adres e-mail musi być tekstem.')
        try:
            email = normalize_and_validate_email(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        email = User.objects.normalize_email(email)
        _ensure_email_available(email)
        return email

    def validate_first_name(self, value: object) -> str | None:
        """Waliduje i normalizuje imię fizjoterapeuty.

        Args:
            value (object): Podane imię.

        Returns:
            str | None: Znormalizowane imię.

        Raises:
            serializers.ValidationError: Gdy imię nie spełnia wymogów.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Imię musi być tekstem.')
        try:
            return normalize_and_validate_first_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_last_name(self, value: object) -> str | None:
        """Waliduje i normalizuje nazwisko fizjoterapeuty.

        Args:
            value (object): Podane nazwisko.

        Returns:
            str | None: Znormalizowane nazwisko.

        Raises:
            serializers.ValidationError: Gdy nazwisko nie spełnia wymogów.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Nazwisko musi być tekstem.')
        try:
            return normalize_and_validate_last_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_password(self, value: object) -> str | None:
        """Waliduje hasło fizjoterapeuty zgodnie z polityką haseł.

        Args:
            value (object): Podane hasło.

        Returns:
            str | None: Zwalidowane hasło.

        Raises:
            serializers.ValidationError: Gdy hasło jest zbyt słabe.
        """
        if value is None or str(value).strip() == '':
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError('Hasło musi być tekstem.')
        return _validate_password_value(
            value,
            user=_password_user_from_data(self.initial_data),
        )

    def validate_pwzf_declaration(self, value: object) -> bool:
        """Sprawdza akceptację oświadczenia PWZFz.

        Args:
            value (object): Wartość oświadczenia.

        Returns:
            bool: True jeśli zaakceptowano.

        Raises:
            serializers.ValidationError: Gdy oświadczenie nie zostało zaznaczone.
        """
        if not isinstance(value, bool):
            raise serializers.ValidationError('Oświadczenie musi być wartością logiczną.')
        if not value:
            raise serializers.ValidationError(
                'Zaznacz oświadczenie o posiadaniu ważnego numeru PWZFz.'
            )
        return value

    def validate_pwzf_number(self, value: object) -> str:
        """Waliduje i sprawza unikalność numeru PWZFz.

        Args:
            value (object): Wprowadzony numer PWZFz.

        Returns:
            str: Znormalizowany numer PWZFz.

        Raises:
            serializers.ValidationError: Gdy numer PWZFz jest nieprawidłowy lub zajęty.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Numer PWZFz musi być tekstem.')
        try:
            normalized = normalize_and_validate_pwzf(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        if TherapistProfile.objects.filter(pwzf_number=normalized).exists():
            raise serializers.ValidationError(PWZF_TAKEN_MESSAGE)
        return normalized

    def validate_phone(self, value: object) -> str | None:
        """Waliduje i normalizuje numer telefonu fizjoterapeuty.

        Args:
            value (object): Podany numer telefonu.

        Returns:
            str | None: Znormalizowany numer telefonu.

        Raises:
            serializers.ValidationError: Gdy numer telefonu jest nieprawidłowy.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Numer telefonu musi być tekstem.')
        try:
            return normalize_and_validate_phone(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Weryfikuje dane rejestracyjne fizjoterapeuty i reCAPTCHA.

        Args:
            attrs (dict[str, object]): Atrybuty wejściowe.

        Returns:
            dict[str, object]: Zwalidowane atrybuty.

        Raises:
            serializers.ValidationError: Gdy brakuje wymaganych danych.
            TypeError: Gdy attrs nie jest słownikiem.
        """
        if not isinstance(attrs, dict):
            raise TypeError("Argument 'attrs' musi być słownikiem.")

        recaptcha_token = attrs.pop('recaptcha_token', None)
        recaptcha_client = attrs.pop('recaptcha_client', None)
        client_val = str(recaptcha_client).strip() if recaptcha_client in {'web', 'mobile'} else None

        credential = str(attrs.pop('google_credential', None) or '').strip()
        if credential:
            return _apply_google_identity(attrs, credential=credential)

        if client_val != 'mobile' or recaptcha_token:
            verify_recaptcha_token(
                str(recaptcha_token) if recaptcha_token else None,
                client=client_val,
            )

        errors = {}
        email_attr = attrs.get('email')
        fn_attr = attrs.get('first_name')
        ln_attr = attrs.get('last_name')
        pwd_attr = attrs.get('password')

        if not (str(email_attr) if email_attr else '').strip():
            errors['email'] = [EMAIL_FIELD_ERRORS.get('required', 'Podaj e-mail.')]
        if not (str(fn_attr) if fn_attr else '').strip():
            errors['first_name'] = [NAME_REQUIRED]
        if not (str(ln_attr) if ln_attr else '').strip():
            errors['last_name'] = [LAST_NAME_REQUIRED]
        if not (str(pwd_attr) if pwd_attr else '').strip():
            errors['password'] = ['Podaj hasło lub użyj Google.']
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, object]) -> object:
        """Tworzy konto fizjoterapeuty oraz profil fizjoterapeuty.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane formularza.

        Returns:
            object: Utworzona instancja użytkownika.

        Raises:
            TypeError: Gdy validated_data nie jest słownikiem.
        """
        if not isinstance(validated_data, dict):
            raise TypeError("Argument 'validated_data' musi być słownikiem.")

        first_name = str(validated_data.pop('first_name'))
        last_name = str(validated_data.pop('last_name'))
        pwzf_number = str(validated_data.pop('pwzf_number'))
        validated_data.pop('pwzf_declaration', None)
        password = validated_data.pop('password', None)
        google_sub = validated_data.pop('_google_sub', None)
        phone = str(validated_data.pop('phone', ''))
        qualification_level = str(validated_data.pop('qualification_level', QualificationLevel.MAGISTER))

        email_val = str(validated_data['email'])
        _prepare_email_for_registration(email_val)

        user = User.objects.create_user(
            email=email_val,
            password=str(password) if password else None,
            role='THERAPIST',
            first_name=first_name,
            last_name=last_name,
            google_sub=str(google_sub) if google_sub else None,
            email_verified_at=timezone.now() if google_sub else None,
        )

        TherapistProfile.objects.create(
            user=user,
            pwzf_number=pwzf_number,
            phone=phone,
            qualification_level=qualification_level,
        )

        return user




class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializator żądania wygenerowania kodu resetu hasła."""

    email = serializers.EmailField(error_messages=EMAIL_FIELD_ERRORS)
    client = serializers.ChoiceField(
        choices=('web', 'mobile'),
        required=False,
        default='web',
    )
    recaptcha_token = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Weryfikuje token reCAPTCHA w żądaniu resetu hasła.

        Args:
            attrs (dict[str, object]): Atrybuty wejściowe.

        Returns:
            dict[str, object]: Zwalidowane atrybuty.

        Raises:
            TypeError: Gdy attrs nie jest słownikiem.
        """
        if not isinstance(attrs, dict):
            raise TypeError("Argument 'attrs' musi być słownikiem.")

        recaptcha_token = attrs.pop('recaptcha_token', None)
        client_val = str(attrs.get('client')).strip() if attrs.get('client') in {'web', 'mobile'} else None
        verify_recaptcha_token(
            str(recaptcha_token) if recaptcha_token else None,
            client=client_val,
        )
        return attrs

    def validate_email(self, value: object) -> str:
        """Waliduje i normalizuje adres e-mail w żądaniu resetu hasła.

        Args:
            value (object): Podany adres e-mail.

        Returns:
            str: Znormalizowany adres e-mail.

        Raises:
            serializers.ValidationError: Gdy e-mail jest nieprawidłowy.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Adres e-mail musi być tekstem.')
        try:
            return User.objects.normalize_email(normalize_and_validate_email(value))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class PasswordResetVerifySerializer(serializers.Serializer):
    """Serializator weryfikacji kodu OTP resetu hasła."""

    email = serializers.EmailField(error_messages=EMAIL_FIELD_ERRORS)
    code = serializers.CharField()

    def validate_email(self, value: object) -> str:
        """Waliduje i normalizuje adres e-mail.

        Args:
            value (object): Podany adres e-mail.

        Returns:
            str: Znormalizowany adres e-mail.

        Raises:
            serializers.ValidationError: Gdy e-mail jest nieprawidłowy.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Adres e-mail musi być tekstem.')
        try:
            return User.objects.normalize_email(normalize_and_validate_email(value))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_code(self, value: object) -> str:
        """Waliduje format 6-cyfrowego kodu OTP resetu hasła.

        Args:
            value (object): Wprowadzony kod.

        Returns:
            str: Oczyszczony 6-cyfrowy kod.

        Raises:
            serializers.ValidationError: Gdy kod nie składa się z 6 cyfr.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Kod musi być tekstem.')
        cleaned = (str(value) if value else '').strip()
        if not cleaned.isdigit() or len(cleaned) != 6:
            raise serializers.ValidationError('Kod musi składać się z 6 cyfr.')
        return cleaned


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializator zatwierdzania nowego hasła po weryfikacji kodu OTP."""

    reset_token = serializers.CharField(
        error_messages={
            'blank': 'Sesja resetu wygasła. Poproś o nowy kod.',
            'required': 'Sesja resetu wygasła. Poproś o nowy kod.',
            'null': 'Sesja resetu wygasła. Poproś o nowy kod.',
        },
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages=_PASSWORD_FIELD_ERRORS,
    )
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': 'Powtórz nowe hasło.',
            'required': 'Powtórz nowe hasło.',
            'null': 'Powtórz nowe hasło.',
        },
    )

    def validate_reset_token(self, value: object) -> str:
        """Oczyszcza wartość tokenu resetu.

        Args:
            value (object): Token sesji resetu hasła.

        Returns:
            str: Oczyszczony token resetu.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Token musi być tekstem.')
        return (str(value) if value else '').strip()

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje zgodność haseł oraz ich poprawność z polityką haseł.

        Args:
            attrs (dict[str, object]): Dane formularza.

        Returns:
            dict[str, object]: Zwalidowane dane z nowym hasłem.

        Raises:
            serializers.ValidationError: Gdy hasła nie są takie same lub nie spełniają wymogów polityki haseł.
            TypeError: Gdy attrs nie jest słownikiem.
        """
        if not isinstance(attrs, dict):
            raise TypeError("Argument 'attrs' musi być słownikiem.")

        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError(
                {'new_password_confirm': ['Hasła muszą być takie same.']}
            )
        user = self.context.get('user') if hasattr(self, 'context') else None
        new_pwd = attrs.get('new_password')
        if not isinstance(new_pwd, str):
            raise serializers.ValidationError({'new_password': ['Hasło musi być tekstem.']})
        attrs['new_password'] = _validate_password_value(new_pwd, user=user)
        return attrs


class EmailVerifySerializer(serializers.Serializer):
    """Serializator weryfikacji adresu e-mail kodem jednorazowym."""

    email = serializers.EmailField(error_messages=EMAIL_FIELD_ERRORS)
    code = serializers.CharField()

    def validate_email(self, value: object) -> str:
        """Waliduje i normalizuje adres e-mail.

        Args:
            value (object): Podany adres e-mail.

        Returns:
            str: Znormalizowany adres e-mail.

        Raises:
            serializers.ValidationError: Gdy e-mail jest nieprawidłowy.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Adres e-mail musi być tekstem.')
        try:
            return User.objects.normalize_email(normalize_and_validate_email(value))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_code(self, value: object) -> str:
        """Waliduje format 6-cyfrowego kodu weryfikacyjnego.

        Args:
            value (object): Wprowadzony kod.

        Returns:
            str: Oczyszczony kod weryfikacyjny.

        Raises:
            serializers.ValidationError: Gdy kod nie składa się z 6 cyfr.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Kod musi być tekstem.')
        cleaned = (str(value) if value else '').strip()
        if not cleaned.isdigit() or len(cleaned) != 6:
            raise serializers.ValidationError('Kod musi składać się z 6 cyfr.')
        return cleaned


class EmailResendSerializer(serializers.Serializer):
    """Serializator ponownej wysyłki kodu weryfikacji e-mail."""

    email = serializers.EmailField(error_messages=EMAIL_FIELD_ERRORS)

    def validate_email(self, value: object) -> str:
        """Waliduje i normalizuje adres e-mail.

        Args:
            value (object): Podany adres e-mail.

        Returns:
            str: Znormalizowany adres e-mail.

        Raises:
            serializers.ValidationError: Gdy e-mail jest nieprawidłowy.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Adres e-mail musi być tekstem.')
        try:
            return User.objects.normalize_email(normalize_and_validate_email(value))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class ChangePasswordSerializer(serializers.Serializer):
    """Serializator zmiany hasła przez zalogowanego użytkownika."""

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

    def validate_new_password(self, value: str) -> str:
        """Waliduje nowe hasło zgodnie z polityką haseł.

        Args:
            value (str): Wartość nowego hasła.

        Returns:
            str: Zwalidowane hasło.

        Raises:
            serializers.ValidationError: Gdy nowe hasło nie jest tekstem lub nie spełnia zasad.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Nowe hasło musi być tekstem.')
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = request.user if request is not None and hasattr(request, 'user') else None
        if user is not None and not (hasattr(user, 'is_authenticated') and user.is_authenticated):
            user = None
        return _validate_password_value(value, user=user)


class MFALoginSerializer(serializers.Serializer):
    """Serializator logowania z użyciem tokenu preautoryzacji MFA oraz kodu 2FA."""

    mfa_token = serializers.CharField(
        error_messages={
            'blank': 'Brak tokenu 2FA.',
            'required': 'Brak tokenu 2FA.',
        }
    )
    code = serializers.CharField(
        error_messages={
            'blank': 'Podaj kod 2FA.',
            'required': 'Podaj kod 2FA.',
        }
    )
    token_delivery = serializers.ChoiceField(
        choices=('cookie', 'body'),
        required=False,
    )

    def validate_code(self, value: object) -> str:
        """Oczyszcza kod 2FA.

        Args:
            value (object): Podany kod 2FA.

        Returns:
            str: Oczyszczony kod.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Kod 2FA musi być tekstem.')
        return (str(value) if value else '').strip()

    def validate_mfa_token(self, value: object) -> str:
        """Oczyszcza token preautoryzacji 2FA.

        Args:
            value (object): Podany token.

        Returns:
            str: Oczyszczony token.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Token MFA musi być tekstem.')
        return (str(value) if value else '').strip()


class MFAEnableSerializer(serializers.Serializer):
    """Serializator aktywacji 2FA na koncie użytkownika."""

    code = serializers.CharField(
        error_messages={
            'blank': 'Podaj kod z aplikacji weryfikującej.',
            'required': 'Podaj kod z aplikacji weryfikującej.',
        }
    )

    def validate_code(self, value: object) -> str:
        """Waliduje format 6-cyfrowego kodu TOTP z aplikacji weryfikującej.

        Args:
            value (object): Podany kod.

        Returns:
            str: Oczyszczony 6-cyfrowy kod.

        Raises:
            serializers.ValidationError: Gdy kod nie składa się z 6 cyfr.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Kod musi być tekstem.')
        cleaned = (str(value) if value else '').strip()
        if not cleaned.isdigit() or len(cleaned) != 6:
            raise serializers.ValidationError('Kod musi składać się z 6 cyfr.')
        return cleaned


class MFADisableSerializer(serializers.Serializer):
    """Serializator wyłączania 2FA na koncie użytkownika."""

    password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': 'Podaj obecne hasło.',
            'required': 'Podaj obecne hasło.',
        },
    )
    code = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_password(self, value: object) -> str:
        """Oczyszcza obecne hasło.

        Args:
            value (object): Wprowadzone hasło.

        Returns:
            str: Oczyszczone hasło.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Hasło musi być tekstem.')
        return (str(value) if value else '').strip()

    def validate_code(self, value: object) -> str:
        """Waliduje opcjonalny kod 2FA lub zapasowy.

        Args:
            value (object): Wprowadzony kod 2FA.

        Returns:
            str: Oczyszczony kod.

        Raises:
            serializers.ValidationError: Gdy niepusty kod nie ma 6 cyfr.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Kod musi być tekstem.')
        cleaned = (str(value) if value else '').strip()
        if cleaned and (not cleaned.isdigit() or len(cleaned) != 6):
            raise serializers.ValidationError('Kod musi składać się z 6 cyfr.')
        return cleaned


class UpdateMeSerializer(serializers.Serializer):
    """Serializator aktualizacji danych osobowych zalogowanego użytkownika (imię, nazwisko)."""

    first_name = serializers.CharField(
        required=False,
        max_length=100,
        error_messages=_FIRST_NAME_FIELD_ERRORS,
    )
    last_name = serializers.CharField(
        required=False,
        max_length=100,
        error_messages=_LAST_NAME_FIELD_ERRORS,
    )

    def validate_first_name(self, value: object) -> str:
        """Waliduje i normalizuje imię użytkownika."""
        if value is None:
            return ''
        val_str = str(value).strip()
        if not val_str:
            raise serializers.ValidationError(NAME_REQUIRED)
        return normalize_and_validate_first_name(val_str)

    def validate_last_name(self, value: object) -> str:
        """Waliduje i normalizuje nazwisko użytkownika."""
        if value is None:
            return ''
        val_str = str(value).strip()
        if not val_str:
            raise serializers.ValidationError(LAST_NAME_REQUIRED)
        return normalize_and_validate_last_name(val_str)





