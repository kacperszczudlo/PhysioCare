from .settings import *  # noqa: F401,F403

DEBUG: bool = True
FIELD_ENCRYPTION_KEY: str = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
SECURE_SSL_REDIRECT: bool = False

DATABASES: dict[str, object] = {
    'default': postgres_database(),  # noqa: F405
}

CACHES: dict[str, object] = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

PASSWORD_HASHERS: list[str] = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # noqa: F405
    'anon': '60/minute',
    'user': '300/minute',
    'login': '5/minute',
    'register': '3/hour',
    'password_reset': '3/hour',
    'admin_password_reset': '10/minute',
    'export': '5/hour',
    'visit_booking': '20/hour',
    'document_upload': '30/hour',
}

SSE_BUS_ENGINE: str = 'inmemory'
RECAPTCHA_ENABLED: bool = False
RECAPTCHA_SECRET_KEY: str = ''
