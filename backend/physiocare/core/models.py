import uuid

from django.db import models


class UUIDModel(models.Model):
    """Abstrakcyjny model bazowy dostarczający klucz główny UUID."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    """Abstrakcyjny model bazowy rozszerzający UUIDModel o znacznik czasu utworzenia."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class TimestampedUpdatedModel(TimestampedModel):
    """Abstrakcyjny model bazowy rozszerzający TimestampedModel o znacznik czasu aktualizacji."""

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StoredMedia(TimestampedModel):
    """Trwały magazyn plików multimedialnych (awatary, PDF, wideo) w bazie danych."""

    path = models.CharField(max_length=500, unique=True, db_index=True)
    content_type = models.CharField(max_length=120, default='application/octet-stream')
    data = models.BinaryField()

    class Meta:
        db_table = 'stored_media'
