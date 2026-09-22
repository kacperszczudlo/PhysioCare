import uuid

from django.db import models


class UUIDModel(models.Model):
    """Abstrakcyjny model bazowy dostarczający klucz główny UUID."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    """Abstrakcyjny model bazowy rozszerzający UUIDModel o znacznik czasu utworzenia."""

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class TimestampedUpdatedModel(TimestampedModel):
    """Abstrakcyjny model bazowy rozszerzający TimestampedModel o znacznik czasu aktualizacji."""

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
