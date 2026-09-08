"""Shared e-mail helpers for accounts (password reset and related notices)."""

from __future__ import annotations

import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


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

    try:
        message.send(fail_silently=False)
    except (OSError, SMTPException):
        logger.exception('Templated e-mail failed subject=%s to=%s', subject, to)
        return False

    if settings.DEBUG:
        logger.info('E-mail sent subject=%s to=%s', subject, to)
    return True
