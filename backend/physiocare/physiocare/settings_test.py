import os

from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_TEST_DB', os.environ.get('POSTGRES_DB', 'physiocare_test')),
        'USER': os.environ.get('POSTGRES_USER', 'physiocare'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'change-me'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'TEST': {
            'NAME': 'test_physiocare',
        },
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
