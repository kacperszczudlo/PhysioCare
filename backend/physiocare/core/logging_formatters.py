"""Structured log formatters for PhysioCare monitoring."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class StructuredJsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for aggregation-friendly logs."""

    _EXTRA_FIELDS = (
        'request_id',
        'method',
        'path',
        'status_code',
        'duration_ms',
        'user_id',
        'error_code',
        'view',
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            'timestamp': datetime.now(UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        for field in self._EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)
