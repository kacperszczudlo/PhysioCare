from rest_framework import serializers

from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import DevicePlatform, DeviceToken, NotificationPreference

_ALLOWED_KEYS = ', '.join(CANONICAL_PREF_KEYS)
EXPO_TOKEN_PREFIXES = ('ExponentPushToken[', 'ExpoPushToken[')


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializator pojedynczej preferencji powiadomień."""

    class Meta:
        model = NotificationPreference
        fields = ['pref_key', 'enabled']


class NotificationPreferencePatchSerializer(serializers.Serializer):
    """Serializator do masowej aktualizacji preferencji powiadomień użytkownika."""

    def to_internal_value(self, data: object) -> dict[str, bool]:
        """Przekształca i waliduje wejściową mapę preferencji.

        Args:
            data (object): Słownik danych wejściowych z preferencjami.

        Returns:
            dict[str, bool]: Słownik zmapowanych preferencji w postaci {pref_key: bool}.

        Raises:
            serializers.ValidationError: Gdy dane są niepoprawnego typu lub zawierają nieznane klucze.
        """
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                'Oczekiwano obiektu JSON z kluczami preferencji.'
            )

        prefs = data.get('preferences', data)
        if not isinstance(prefs, dict):
            raise serializers.ValidationError(
                'Oczekiwano mapy preferencji (klucz → wartość logiczna).'
            )

        unknown = [key for key in prefs if key not in CANONICAL_PREF_KEYS]
        if unknown:
            raise serializers.ValidationError(
                {
                    'pref_key': (
                        f'Nieznane klucze: {", ".join(unknown)}. '
                        f'Dozwolone: {_ALLOWED_KEYS}.'
                    )
                }
            )

        bool_field = serializers.BooleanField()
        parsed = {}
        errors = {}
        for key, value in prefs.items():
            try:
                parsed[key] = bool_field.to_internal_value(value)
            except serializers.ValidationError as exc:
                errors[key] = exc.detail
        if errors:
            raise serializers.ValidationError(errors)
        return parsed


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializator tokenu urządzenia powiadomień push."""

    class Meta:
        model = DeviceToken
        fields = ['id', 'expo_push_token', 'platform', 'is_active', 'updated_at']
        read_only_fields = ['id', 'is_active', 'updated_at']


class DeviceTokenWriteSerializer(serializers.Serializer):
    """Serializator zapisu/rejestracji nowego tokenu urządzenia Expo."""

    expo_push_token = serializers.CharField(max_length=200)
    platform = serializers.ChoiceField(
        choices=DevicePlatform.choices,
        required=False,
        default=DevicePlatform.UNKNOWN,
    )

    def validate_expo_push_token(self, value: str) -> str:
        """Waliduje poprawność formatu tokenu Expo Push.

        Args:
            value (str): Ciąg znaków reprezentujący token.

        Returns:
            str: Oczyszczony i zwalidowany token Expo Push.

        Raises:
            serializers.ValidationError: Gdy format tokenu jest nieprawidłowy.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Token musi być ciągiem znaków.')
        token = value.strip()
        if not (
            token.endswith(']')
            and any(token.startswith(prefix) for prefix in EXPO_TOKEN_PREFIXES)
        ):
            raise serializers.ValidationError(
                'Nieprawidłowy token powiadomień Expo.'
            )
        return token



class DeviceTokenDeleteSerializer(serializers.Serializer):
    """Serializator do usuwania tokenu urządzenia po podaniu expo_push_token."""

    expo_push_token = serializers.CharField(max_length=200)

    def validate_expo_push_token(self, value: str) -> str:
        """Waliduje token Expo Push podany do usunięcia.

        Args:
            value (str): Ciąg znaków reprezentujący token.

        Returns:
            str: Oczyszczony token.

        Raises:
            serializers.ValidationError: Gdy token nie jest ciągiem znaków.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Token musi być ciągiem znaków.')
        return value.strip()

