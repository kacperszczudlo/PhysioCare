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


def mask_email_for_logging(email: str | None) -> str:
    """Zwraca zredagowany/zamaskowany adres e-mail do bezpiecznego logowania (np. j***n@domain.com).

    Args:
        email (str | None): Adres e-mail lub None.

    Returns:
        str: Zamaskowany adres lub 'anonymous'.
    """
    if not email or not isinstance(email, str) or '@' not in email:
        return 'anonymous'
    email = email.strip()
    try:
        local, domain = email.split('@', 1)
        if len(local) <= 1:
            masked_local = f'{local}***'
        elif len(local) == 2:
            masked_local = f'{local[0]}***'
        else:
            masked_local = f'{local[0]}***{local[-1]}'
        return f'{masked_local}@{domain}'
    except Exception:
        return 'anonymous'



