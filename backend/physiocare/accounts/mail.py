from __future__ import annotations

import logging
from email.mime.image import MIMEImage
from pathlib import Path
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from core.logging_formatters import mask_email_for_logging

logger = logging.getLogger(__name__)


def _attach_brand_logo(message: EmailMultiAlternatives) -> None:
    """Załącza sygnet/logo PhysioCare jako osadzony załącznik inline CID.

    Args:
        message (EmailMultiAlternatives): Obiekt wiadomości e-mail.

    Raises:
        TypeError: Gdy message nie jest instancją EmailMultiAlternatives.
    """
    if not isinstance(message, EmailMultiAlternatives):
        raise TypeError("Argument 'message' musi być instancją EmailMultiAlternatives.")

    root_dir = settings.ROOT_DIR if hasattr(settings, 'ROOT_DIR') else None
    if not root_dir:
        root_dir = Path(settings.BASE_DIR).parent.parent

    candidates = [
        root_dir / 'brand' / 'sygnet.png',
        root_dir / 'brand' / 'logo.png',
        Path(settings.BASE_DIR) / 'accounts' / 'static' / 'accounts' / 'sygnet.png',
    ]

    logo_path: Path | None = None
    for cand in candidates:
        if cand.exists() and cand.is_file():
            logo_path = cand
            break

    if not logo_path:
        return

    try:
        with logo_path.open('rb') as f:
            logo_data = f.read()
        mime_img = MIMEImage(logo_data, _subtype='png')
        mime_img.add_header('Content-ID', '<physiocare_logo>')
        mime_img.add_header('Content-Disposition', 'inline', filename=logo_path.name)
        message.attach(mime_img)
    except Exception:
        logger.warning('Failed to attach inline brand logo for email', exc_info=True)


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

    text_body = render_to_string(f'{template_basename}.txt', context)
    html_body: str | None
    try:
        html_body = render_to_string(f'{template_basename}.html', context)
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
        _attach_brand_logo(message)

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



