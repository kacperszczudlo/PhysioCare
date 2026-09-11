from .settings import *  # noqa: F401,F403

DEBUG = True
SECURE_SSL_REDIRECT = False

DATABASES = {
    'default': postgres_database(),  # noqa: F405
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # noqa: F405
    'anon': '60/minute',
    'user': '300/minute',
    'login': '5/minute',
    'register': '3/hour',
    'password_reset': '3/hour',
}

SSE_BUS_ENGINE = 'inmemory'
