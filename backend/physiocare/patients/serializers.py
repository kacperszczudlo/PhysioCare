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



class PatientListSerializer(serializers.ModelSerializer):
    """Serializer dla listy pacjentów widocznej dla fizjoterapeuty."""

    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'avatar_url']


class PatientDetailSerializer(serializers.ModelSerializer):
    """Serializer dla szczegółowych danych profilu pacjenta."""

    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    therapists = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pesel', 'phone', 'avatar_url', 'therapists', 'created_at',
        ]
        read_only_fields = ['id', 'therapists', 'created_at']

    def get_therapists(self, obj: PatientProfile) -> list[dict[str, object]]:
        """Pobiera zserializowaną listę aktywnych fizjoterapeutów pacjenta.

        Args:
            obj (PatientProfile): Instancja profilu pacjenta.

        Returns:
            list[dict[str, object]]: Lista słowników reprezentujących fizjoterapeutów.
        """
        if not isinstance(obj, PatientProfile):
            return []
        from therapists.serializers import TherapistPublicSerializer
        active_therapists = obj.therapists.filter(patient_links__status='ACTIVE')
        return TherapistPublicSerializer(active_therapists, many=True).data


class MeProfileSerializer(serializers.ModelSerializer):
    """Serializer dla profilu własnego pacjenta (widok /me)."""

    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    therapists = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pesel', 'phone', 'avatar_url', 'therapists',
        ]
        read_only_fields = ['id', 'therapists']

    def get_therapists(self, obj: PatientProfile) -> list[dict[str, object]]:
        """Pobiera zserializowaną listę aktywnych fizjoterapeutów dla własnego profilu.

        Args:
            obj (PatientProfile): Instancja profilu pacjenta.

        Returns:
            list[dict[str, object]]: Lista słowników reprezentujących fizjoterapeutów.
        """
        if not isinstance(obj, PatientProfile):
            return []
        from therapists.serializers import TherapistPublicSerializer
        active_therapists = obj.therapists.filter(patient_links__status='ACTIVE')
        return TherapistPublicSerializer(active_therapists, many=True).data


class MeProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer służący do edycji profilu własnego pacjenta."""

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

    def validate_first_name(self, value: str) -> str:
        """Waliduje oraz normalizuje imię pacjenta.

        Args:
            value (str): Wprowadzone imię.

        Returns:
            str: Znormalizowane imię pacjenta.

        Raises:
            serializers.ValidationError: Gdy imię jest nieprawidłowe.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Imię musi być ciągiem znaków.')
        try:
            return normalize_and_validate_first_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_last_name(self, value: str) -> str:
        """Waliduje oraz normalizuje nazwisko pacjenta.

        Args:
            value (str): Wprowadzone nazwisko.

        Returns:
            str: Znormalizowane nazwisko pacjenta.

        Raises:
            serializers.ValidationError: Gdy nazwisko jest nieprawidłowe.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Nazwisko musi być ciągiem znaków.')
        try:
            return normalize_and_validate_last_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_phone(self, value: str) -> str:
        """Waliduje oraz normalizuje numer telefonu pacjenta.

        Args:
            value (str): Wprowadzony numer telefonu.

        Returns:
            str: Znormalizowany numer telefonu.

        Raises:
            serializers.ValidationError: Gdy numer telefonu jest nieprawidłowy.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Numer telefonu musi być ciągiem znaków.')
        try:
            return normalize_and_validate_phone(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_pesel(self, value: str | None) -> str | None:
        """Waliduje oraz normalizuje numer PESEL pacjenta.

        Args:
            value (str | None): Wprowadzony numer PESEL lub None.

        Returns:
            str | None: Znormalizowany numer PESEL lub None.

        Raises:
            serializers.ValidationError: Gdy numer PESEL jest nieprawidłowy.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('PESEL musi być ciągiem znaków.')
        try:
            return normalize_and_validate_pesel(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def update(self, instance: PatientProfile, validated_data: dict[str, object]) -> PatientProfile:
        """Aktualizuje dane w profilu pacjenta i obiekcie User.

        Args:
            instance (PatientProfile): Zmieniany profil pacjenta.
            validated_data (dict[str, object]): Zweryfikowane dane wejściowe.

        Returns:
            PatientProfile: Zaktualizowana instancja profilu pacjenta.
        """
        if not isinstance(instance, PatientProfile) or not isinstance(validated_data, dict):
            raise serializers.ValidationError('Nieprawidłowe dane wejściowe.')
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
    """Serializer dla zgód RODO pacjenta."""

    class Meta:
        model = Consent
        fields = ['consent_type', 'granted', 'granted_at']
        read_only_fields = ['granted_at']


class OptionalConsentsUpdateSerializer(serializers.Serializer):
    """Serializer do aktualizacji zgód opcjonalnych pacjenta."""

    marketing = serializers.BooleanField(required=False)
    research = serializers.BooleanField(required=False)

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje dane wejściowe zgód opcjonalnych.

        Args:
            attrs (dict[str, object]): Slownik przekazanych zgód.

        Returns:
            dict[str, object]: Zwalidowany słownik ze zgodami.

        Raises:
            TypeError: Gdy attrs nie jest słownikiem.
        """
        if not isinstance(attrs, dict):
            raise TypeError('Dane wejściowe muszą być słownikiem.')
        return attrs

