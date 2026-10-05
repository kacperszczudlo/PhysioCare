import base64
import logging
from pathlib import Path
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from core.logging_formatters import mask_email_for_logging

logger = logging.getLogger(__name__)

_CACHED_BRAND_LOGO_DATA_URI: str | None = None


def get_brand_logo_data_uri() -> str:
    """Zwraca sygnet PhysioCare jako ciąg Data URI (base64) osadzany bezpośrednio w HTML.

    Dzięki temu w e-mailach nie ma żadnych załączników fizycznych (brak pliku do pobrania),
    a logo wyświetla się natychmiastowo we wszystkich klientach pocztowych.
    """
    global _CACHED_BRAND_LOGO_DATA_URI
    if _CACHED_BRAND_LOGO_DATA_URI is not None:
        return _CACHED_BRAND_LOGO_DATA_URI

    root_dir = settings.ROOT_DIR if hasattr(settings, 'ROOT_DIR') else None
    if not root_dir:
        root_dir = Path(settings.BASE_DIR).parent.parent

    candidates = [
        root_dir / 'brand' / 'sygnet.png',
        root_dir / 'brand' / 'logo.png',
        Path(settings.BASE_DIR) / 'accounts' / 'static' / 'accounts' / 'sygnet.png',
    ]

    for cand in candidates:
        if cand.exists() and cand.is_file():
            try:
                data = cand.read_bytes()
                encoded = base64.b64encode(data).decode('ascii')
                _CACHED_BRAND_LOGO_DATA_URI = f'data:image/png;base64,{encoded}'
                return _CACHED_BRAND_LOGO_DATA_URI
            except Exception:
                logger.warning('Failed to encode brand logo as data URI', exc_info=True)
                break

    _CACHED_BRAND_LOGO_DATA_URI = ''
    return _CACHED_BRAND_LOGO_DATA_URI


def send_templated_mail(
    *,
    subject: str,
    to: list[str],
    template_basename: str,
    context: dict[str, object],
) -> bool:
    """Renderuje szablony `{basename}.txt` oraz opcjonalnie `{basename}.html` i wysyła wiadomość e-mail.

    Args:
        subject (str): Temat wiadomości e-mail.
        to (list[str]): Lista adresatów e-mail.
        template_basename (str): Bazowa nazwa pliku szablonu.
        context (dict[str, object]): Kontekst z danymi do wyrenderowania szablonu.

    Returns:
        bool: True w przypadku powodzenia wysyłki, False w razie błędu protokołu SMTP lub systemu plików.

    Raises:
        TypeError: Gdy któryś z argumentów ma nieprawidłowy typ.
    """
    if not isinstance(subject, str):
        raise TypeError("Argument 'subject' musi być typu str.")
    if not isinstance(to, list):
        raise TypeError("Argument 'to' musi być typu list[str].")
    if not isinstance(template_basename, str):
        raise TypeError("Argument 'template_basename' musi być typu str.")
    if not isinstance(context, dict):
        raise TypeError("Argument 'context' musi być typu dict[str, object].")

    enriched_context = dict(context)
    if 'brand_logo_data_uri' not in enriched_context:
        enriched_context['brand_logo_data_uri'] = get_brand_logo_data_uri()

    text_body = render_to_string(f'{template_basename}.txt', enriched_context)
    html_body: str | None
    try:
        html_body = render_to_string(f'{template_basename}.html', enriched_context)
    except TemplateDoesNotExist:
        html_body = None

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    if html_body:
        message.attach_alternative(html_body, 'text/html')

    masked_to = (
        [mask_email_for_logging(t) for t in to]
        if isinstance(to, (list, tuple))
        else mask_email_for_logging(str(to))
    )
    try:
        message.send(fail_silently=False)
    except (OSError, SMTPException):
        logger.exception('Templated e-mail failed subject=%s to=%s', subject, masked_to)
        return False

    if hasattr(settings, 'DEBUG') and settings.DEBUG:
        logger.info('E-mail sent subject=%s to=%s', subject, masked_to)
    return True



