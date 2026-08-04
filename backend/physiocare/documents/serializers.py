from rest_framework import serializers

from .models import MedicalDocument


class MedicalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalDocument
        fields = [
            'id', 'title', 'file_url', 'mime_type', 'visit', 'episode',
            'uploaded_by', 'created_at',
        ]
        read_only_fields = ['id', 'file_url', 'uploaded_by', 'created_at']
