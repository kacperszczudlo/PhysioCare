from django.db import models

from core.crypto import decrypt_value, encrypt_value


class EncryptedCharField(models.CharField):
    """CharField that encrypts content into Fernet ciphertext before saving to DB."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if isinstance(value, str):
            return decrypt_value(value)
        return super().to_python(value)


class EncryptedTextField(models.TextField):
    """TextField that encrypts content into Fernet ciphertext before saving to DB."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if isinstance(value, str):
            return decrypt_value(value)
        return super().to_python(value)
