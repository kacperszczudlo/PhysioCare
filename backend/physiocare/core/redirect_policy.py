from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme


def get_allowed_redirect_hosts() -> set[str]:
    """Zbiera dozwolone domeny i hosty z konfiguracyjnych zmiennych FRONTEND_URL, CORS_ALLOWED_ORIGINS oraz ALLOWED_HOSTS.

    Returns:
        set[str]: Zbiór dozwolonych hostów dla przekierowań.
    """
    hosts: set[str] = set()

    frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else ''
    if frontend_url and isinstance(frontend_url, str):
        netloc = urlparse(frontend_url).netloc
        if netloc:
            hosts.add(netloc)

    cors_origins = settings.CORS_ALLOWED_ORIGINS if hasattr(settings, 'CORS_ALLOWED_ORIGINS') else []
    if isinstance(cors_origins, (list, tuple, set)):
        for origin in cors_origins:
            if isinstance(origin, str):
                netloc = urlparse(origin).netloc
                if netloc:
                    hosts.add(netloc)

    allowed_hosts = settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else []
    if isinstance(allowed_hosts, (list, tuple, set)):
        for host in allowed_hosts:
            if isinstance(host, str) and host and host != '*':
                hosts.add(host)

    return hosts


def is_safe_redirect_url(url: str | None) -> bool:
    """Sprawdza, czy podany URL przekierowania jest bezpieczny (względny lub wskazujący na dozwolone źródło).

    Zapobiega atakom typu Open Redirect (np. //evil.com, https://phishing.com).

    Args:
        url (str | None): Adres URL do przetestowania.

    Returns:
        bool: True jeśli adres jest bezpieczny, False w przeciwnym razie.
    """
    if not url or not isinstance(url, str):
        return False

    cleaned = url.strip()
    if not cleaned:
        return False

    allowed_hosts = get_allowed_redirect_hosts()
    debug_flag = settings.DEBUG if hasattr(settings, 'DEBUG') else True
    ssl_flag = settings.SECURE_SSL_REDIRECT if hasattr(settings, 'SECURE_SSL_REDIRECT') else False
    require_https = not debug_flag and ssl_flag

    return url_has_allowed_host_and_scheme(
        url=cleaned,
        allowed_hosts=allowed_hosts,
        require_https=require_https,
    )

