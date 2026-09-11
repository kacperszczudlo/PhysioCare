"""Open Redirect prevention and safe redirect URL validation."""

from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme


def get_allowed_redirect_hosts() -> set[str]:
    """Gather allowed domains/hosts from FRONTEND_URL, CORS_ALLOWED_ORIGINS, and ALLOWED_HOSTS."""
    hosts = set()

    frontend_url = getattr(settings, 'FRONTEND_URL', '')
    if frontend_url:
        netloc = urlparse(frontend_url).netloc
        if netloc:
            hosts.add(netloc)

    cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    for origin in cors_origins:
        netloc = urlparse(origin).netloc
        if netloc:
            hosts.add(netloc)

    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
    for host in allowed_hosts:
        if host and host != '*':
            hosts.add(host)

    return hosts


def is_safe_redirect_url(url: str | None) -> bool:
    """
    Check if a redirect URL is safe (relative path or pointing strictly to allowed origins).
    Prevents Open Redirect vulnerabilities (e.g. //evil.com, https://phishing.com).
    """
    if not url or not isinstance(url, str):
        return False

    cleaned = url.strip()
    if not cleaned:
        return False

    allowed_hosts = get_allowed_redirect_hosts()
    require_https = not getattr(settings, 'DEBUG', True) and getattr(settings, 'SECURE_SSL_REDIRECT', False)

    return url_has_allowed_host_and_scheme(
        url=cleaned,
        allowed_hosts=allowed_hosts,
        require_https=require_https,
    )
