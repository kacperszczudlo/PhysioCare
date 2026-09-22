from django.db import models

from core.crypto import decrypt_value, encrypt_value


class EncryptedCharField(models.CharField):
    """Pole CharField szyfrujące zawartość przed zapisem do bazy danych przy użyciu algorytmu Fernet."""

    def get_prep_value(self, value: object) -> str | None:
        """Przygotowuje wartość do zapisu w bazie danych poprzez jej zaszyfrowanie.

        Args:
            value (object): Wartość tekstowa przed zapisem.

        Returns:
            str | None: Zaszyfrowany ciąg znaków gotowy do zapisu w bazie danych lub None.

        Raises:
            TypeError: Gdy value nie jest typu str ani None.
        """
        if value is not None and not isinstance(value, str):
            raise TypeError("Wartość dla EncryptedCharField musi być typu str lub None.")
        prep = super().get_prep_value(value)
        return encrypt_value(prep)

    def from_db_value(self, value: object, expression: object, connection: object) -> str | None:
        """Odszyfrowuje wartość pobraną bezpośrednio z bazy danych.

        Args:
            value (object): Zaszyfrowana wartość z bazy danych.
            expression (object): Wyrażenie zapytania SQL.
            connection (object): Połączenie z bazą danych.

        Returns:
            str | None: Odszyfrowana wartość tekstowa lub None.

        Raises:
            TypeError: Gdy value nie jest typu str ani None.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("Wartość z bazy danych dla EncryptedCharField musi być typu str lub None.")
        return decrypt_value(value)

    def to_python(self, value: object) -> str | None:
        """Konwertuje wartość z bazy danych lub formularza na obiekt tekstowy.

        Args:
            value (object): Wartość wejściowa do przetworzenia.

        Returns:
            str | None: Odszyfrowana lub przekształcona wartość tekstowa.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return decrypt_value(value)
        converted = super().to_python(value)
        return decrypt_value(converted) if isinstance(converted, str) else converted


class EncryptedTextField(models.TextField):
    """Pole TextField szyfrujące zawartość przed zapisem do bazy danych przy użyciu algorytmu Fernet."""

    def get_prep_value(self, value: object) -> str | None:
        """Przygotowuje długi tekst do zapisu w bazie danych poprzez jego zaszyfrowanie.

        Args:
            value (object): Tekst przed zapisem.

        Returns:
            str | None: Zaszyfrowany ciąg znaków gotowy do zapisu w bazie danych lub None.

        Raises:
            TypeError: Gdy value nie jest typu str ani None.
        """
        if value is not None and not isinstance(value, str):
            raise TypeError("Wartość dla EncryptedTextField musi być typu str lub None.")
        prep = super().get_prep_value(value)
        return encrypt_value(prep)

    def from_db_value(self, value: object, expression: object, connection: object) -> str | None:
        """Odszyfrowuje długi tekst pobrany z bazy danych.

        Args:
            value (object): Zaszyfrowana wartość z bazy danych.
            expression (object): Wyrażenie zapytania SQL.
            connection (object): Połączenie z bazą danych.

        Returns:
            str | None: Odszyfrowany tekst lub None.

        Raises:
            TypeError: Gdy value nie jest typu str ani None.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("Wartość z bazy danych dla EncryptedTextField musi być typu str lub None.")
        return decrypt_value(value)

    def to_python(self, value: object) -> str | None:
        """Konwertuje wartość z bazy danych lub formularza na obiekt tekstowy.

        Args:
            value (object): Wartość wejściowa do przetworzenia.

        Returns:
            str | None: Odszyfrowana lub przekształcona wartość tekstowa.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return decrypt_value(value)
        converted = super().to_python(value)
        return decrypt_value(converted) if isinstance(converted, str) else converted
