from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    DOCUMENT_TITLE_REQUIRED,
    DOCUMENT_TITLE_TOO_LONG,
    normalize_optional_text,
)

from .models import MedicalDocument


class MedicalDocumentSerializer(serializers.ModelSerializer):
    """Serializator dla dokumentu medycznego pacjenta."""

    title = serializers.CharField(max_length=200)

    class Meta:
        model = MedicalDocument
        fields = [
            'id', 'title', 'file_url', 'mime_type', 'visit', 'episode',
            'uploaded_by', 'created_at',
        ]
        read_only_fields = ['id', 'file_url', 'uploaded_by', 'created_at']

    def validate_title(self, value: str | None) -> str:
        """Waliduje i normalizuje tytuł dokumentu medycznego.

        Args:
            value (str | None): Wartość wejściowa tytułu dokumentu.

        Returns:
            str: Znormalizowana treść tytułu.

        Raises:
            serializers.ValidationError: Gdy tytuł jest pusty lub zbyt długi.
        """
        if value is not None and not isinstance(value, str):
            raise serializers.ValidationError('Tytuł musi być ciągiem znaków.')

        try:
            return normalize_optional_text(
                value,
                max_length=200,
                too_long_message=DOCUMENT_TITLE_TOO_LONG,
                allow_blank=False,
                required_message=DOCUMENT_TITLE_REQUIRED,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

