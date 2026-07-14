from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': postgres_database(),  # noqa: F405
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
