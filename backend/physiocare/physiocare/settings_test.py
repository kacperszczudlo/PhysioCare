from .settings import *  # noqa: F401,F403

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
