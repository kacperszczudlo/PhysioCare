from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    DOCUMENT_TITLE_REQUIRED,
    DOCUMENT_TITLE_TOO_LONG,
    normalize_optional_text,
)

from .models import MedicalDocument


class MedicalDocumentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=200)

    class Meta:
        model = MedicalDocument
        fields = [
            'id', 'title', 'file_url', 'mime_type', 'visit', 'episode',
            'uploaded_by', 'created_at',
        ]
        read_only_fields = ['id', 'file_url', 'uploaded_by', 'created_at']

    def validate_title(self, value):
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
