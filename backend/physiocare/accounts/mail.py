"""Shared e-mail helpers for accounts (password reset and related notices)."""

from __future__ import annotations

import logging
from email.mime.image import MIMEImage
from pathlib import Path
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _attach_brand_logo(message: EmailMultiAlternatives) -> None:
    """Attach PhysioCare logo as inline CID attachment if file exists."""
    root_dir = getattr(settings, 'ROOT_DIR', None)
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
    context: dict,
) -> bool:
    """
    Render ``{basename}.txt`` + optional ``{basename}.html`` and send.

    Returns True on success, False on SMTP/OS failure (errors are logged).
    """
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

    try:
        message.send(fail_silently=False)
    except (OSError, SMTPException):
        logger.exception('Templated e-mail failed subject=%s to=%s', subject, to)
        return False

    if settings.DEBUG:
        logger.info('E-mail sent subject=%s to=%s', subject, to)
    return True

