from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class StructuredJsonFormatter(logging.Formatter):
    """Formatator logów generujący pojedynczy obiekt JSON dla każdej linii logów w celach agregacji i analizy."""

    _EXTRA_FIELDS: tuple[str, ...] = (
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
        """Formatuje wpis logu do postaci ciągu JSON.

        Args:
            record (logging.LogRecord): Obiekt rekordu logowania.

        Returns:
            str: Ciąg JSON reprezentujący sformatowany rekord.

        Raises:
            TypeError: Gdy record nie jest instancją logging.LogRecord.
        """
        if not isinstance(record, logging.LogRecord):
            raise TypeError("Argument 'record' musi być instancją logging.LogRecord.")

        payload: dict[str, object] = {
            'timestamp': datetime.now(UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        record_dict = record.__dict__
        for field in self._EXTRA_FIELDS:
            value = record_dict.get(field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


