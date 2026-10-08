import os
import urllib.parse
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent

load_dotenv(ROOT_DIR / '.env')


def require_env(name: str) -> str:
    """Wymaga obecności zmiennej środowiskowej i zwraca jej wartość.

    Args:
        name (str): Nazwa zmiennej środowiskowej.

    Returns:
        str: Wartość zmiennej środowiskowej.

    Raises:
        ImproperlyConfigured: Gdy zmienna środowiskowa nie jest ustawiona.
        TypeError: Gdy parametr name nie jest ciągiem znaków.
    """
    if not isinstance(name, str):
        raise TypeError('Parametr name musi być ciągiem znaków.')
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f'Set {name} in .env (see .env.example).'
        )
    return value


def env_bool(name: str, default: str = 'false') -> bool:
    """Odczytuje zmienną środowiskową jako wartość logiczną (bool).

    Args:
        name (str): Nazwa zmiennej środowiskowej.
        default (str): Domyślna wartość w przypadku braku zmiennej.

    Returns:
        bool: True jeśli wartość oznacza binarne włączenie (1, true, yes).

    Raises:
        TypeError: Gdy nazwa lub domyślna wartość nie są ciągiem znaków.
    """
    if not isinstance(name, str) or not isinstance(default, str):
        raise TypeError('Parametry name i default muszą być ciągami znaków.')
    return os.environ.get(name, default).lower() in ('1', 'true', 'yes')


def env_list(name: str, default: str = '') -> list[str]:
    """Odczytuje zmienną środowiskową rozdzieloną przecinkami jako listę napisów.

    Args:
        name (str): Nazwa zmiennej środowiskowej.
        default (str): Domyślna wartość ciągu tekstowego.

    Returns:
        list[str]: Lista wyodrębnionych elementów.

    Raises:
        TypeError: Gdy nazwa lub domyślna wartość nie są ciągiem znaków.
    """
    if not isinstance(name, str) or not isinstance(default, str):
        raise TypeError('Parametry name i default muszą być ciągami znaków.')
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]



SECRET_KEY = require_env('DJANGO_SECRET_KEY')

DEBUG = env_bool('DJANGO_DEBUG', 'false')

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
if DEBUG and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('*')

FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY', '').strip()
if not DEBUG and not FIELD_ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        'FIELD_ENCRYPTION_KEY jest wymagany przy DJANGO_DEBUG=false.'
    )
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        'Wildcard "*" w DJANGO_ALLOWED_HOSTS jest zabroniony przy DJANGO_DEBUG=false.'
    )


ADMIN_ENABLED = env_bool('DJANGO_ADMIN_ENABLED', 'true')
ADMIN_ALLOWED_IPS = env_list('DJANGO_ADMIN_ALLOWED_IPS', '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'core',
    'accounts',
    'patients',
    'therapists',
    'privacy',
    'notifications',
    'treatment',
    'scheduling',
    'exercises',
    'documents',
    'reviews',
    'administration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.AdminAccessMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestTimingMiddleware',
]

SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'


ROOT_URLCONF = 'physiocare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'physiocare.wsgi.application'
ASGI_APPLICATION = 'physiocare.asgi.application'


def postgres_database(*, db_name: str | None = None, test_db_name: str | None = None) -> dict[str, object]:
    """Buduje słownik konfiguracji połączenia z bazą danych PostgreSQL.

    Args:
        db_name (str | None): Opcjonalna nazwa bazy danych.
        test_db_name (str | None): Opcjonalna nazwa testowej bazy danych.

    Returns:
        dict[str, object]: Słownik konfiguracji bazy danych dla Django.

    Raises:
        TypeError: Gdy parametr db_name lub test_db_name ma niepoprawny typ.
    """
    if db_name is not None and not isinstance(db_name, str):
        raise TypeError('Parametr db_name musi być typu str lub None.')
    if test_db_name is not None and not isinstance(test_db_name, str):
        raise TypeError('Parametr test_db_name musi być typu str lub None.')

    db_url = os.environ.get('DATABASE_URL', '').strip()
    if db_url:
        parsed = urllib.parse.urlparse(db_url)
        db_name = db_name or (parsed.path[1:] if parsed.path.startswith('/') else parsed.path)
        db_user = urllib.parse.unquote(parsed.username or '')
        db_password = urllib.parse.unquote(parsed.password or '')
        db_host = parsed.hostname or 'localhost'
        db_port = str(parsed.port or 5432)
        query_params = urllib.parse.parse_qs(parsed.query)
        sslmode = query_params.get('sslmode', [''])[0] or os.environ.get('DB_SSLMODE', '').strip()
    else:
        db_name = db_name or require_env('POSTGRES_DB')
        db_user = require_env('POSTGRES_USER')
        db_password = require_env('POSTGRES_PASSWORD')
        db_host = os.environ.get('POSTGRES_HOST', 'localhost')
        db_port = os.environ.get('POSTGRES_PORT', '5432')
        sslmode = os.environ.get('DB_SSLMODE', '').strip()

    db_options: dict[str, str] = {}
    db_schema = os.environ.get('DB_SCHEMA', '').strip()
    if db_schema:
        db_options['options'] = f'-c search_path={db_schema},public'

    if not sslmode and ('.render.com' in db_host or not DEBUG):
        sslmode = 'require'
    if sslmode:
        db_options['sslmode'] = sslmode

    config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': db_options,
    }
    if test_db_name:
        config['TEST'] = {'NAME': test_db_name}
    return config


DATABASES = {
    'default': postgres_database(),
}

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'accounts.password_policy.SpecialCharacterValidator'},
]

LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
_static_path = os.environ.get('STATIC_ROOT', 'backend/staticfiles')
STATIC_ROOT = ROOT_DIR / _static_path if not os.path.isabs(_static_path) else Path(_static_path)

_media_path = os.environ.get('MEDIA_ROOT', 'backend/media')
MEDIA_ROOT = ROOT_DIR / _media_path if not os.path.isabs(_media_path) else Path(_media_path)
MEDIA_URL = '/media/'

MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', '50'))
MAX_AVATAR_MB = int(os.environ.get('MAX_AVATAR_MB', '5'))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_MB * 1024 * 1024

from corsheaders.defaults import default_headers  # noqa: E402

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://localhost:8081,http://127.0.0.1:5173,http://127.0.0.1:8081,https://physiocare-3yh.pages.dev',
)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https:\/\/.*\.pages\.dev$',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-physiocare-token-delivery',
    'x-request-id',
]
CORS_EXPOSE_HEADERS = [
    'x-request-id',
    'x-response-time-ms',
    'content-disposition',
]
CSRF_TRUSTED_ORIGINS = env_list(
    'CSRF_TRUSTED_ORIGINS',
    ','.join(CORS_ALLOWED_ORIGINS),
)

SECURE_COOKIES = env_bool('DJANGO_SECURE_COOKIES', 'true' if not DEBUG else 'false')

GOOGLE_CLIENT_IDS = env_list('GOOGLE_CLIENT_IDS') or env_list('GOOGLE_CLIENT_ID')

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.environ.get('JWT_ACCESS_LIFETIME_MIN', '15'))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.environ.get('JWT_REFRESH_LIFETIME_DAYS', '7'))
    ),
    'AUTH_COOKIE_ACCESS': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.CookieJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('THROTTLE_ANON', '60/minute'),
        'user': os.environ.get('THROTTLE_USER', '300/minute'),
        'login': os.environ.get('THROTTLE_LOGIN', '5/minute'),
        'register': os.environ.get('THROTTLE_REGISTER', '3/hour'),
        'password_reset': os.environ.get('THROTTLE_PASSWORD_RESET', '3/hour'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
        'rest_framework.renderers.BrowsableAPIRenderer'
    )

_LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json' if not DEBUG else 'text').lower()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s [%(name)s] %(message)s',
        },
        'json': {
            '()': 'core.logging_formatters.StructuredJsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if _LOG_FORMAT == 'json' else 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'physiocare.auth': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'physiocare.api': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', 'true')
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_COOKIES = True

USE_X_FORWARDED_HOST = env_bool('DJANGO_USE_X_FORWARDED_HOST', 'true')
if env_bool('DJANGO_SECURE_PROXY_SSL_HEADER', 'true' if not DEBUG else 'false'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')



_REDIS_URL = os.environ.get('REDIS_URL', '').strip()
if _REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _REDIS_URL,
            'KEY_PREFIX': 'physiocare',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'physiocare-default',
            'KEY_PREFIX': 'physiocare',
        }
    }

CELERY_BROKER_URL: str = os.environ.get('CELERY_BROKER_URL', _REDIS_URL or 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND: str = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT: list[str] = ['json']
CELERY_TASK_SERIALIZER: str = 'json'
CELERY_RESULT_SERIALIZER: str = 'json'
CELERY_TIMEZONE: str = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER: bool = env_bool('CELERY_TASK_ALWAYS_EAGER', 'true' if not _REDIS_URL else 'false')
CELERY_TASK_EAGER_PROPAGATES: bool = True

CELERY_BEAT_SCHEDULE: dict[str, dict[str, object]] = {
    'notify-upcoming-visits-every-15m': {
        'task': 'notifications.tasks.run_upcoming_visits_job_task',
        'schedule': 900.0,
    },
    'notify-today-exercises-daily': {
        'task': 'notifications.tasks.run_today_exercises_job_task',
        'schedule': 86400.0,
    },
}

DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_FROM', 'noreply@example.com')

GMAIL_CLIENT_ID = os.environ.get('GMAIL_CLIENT_ID', '').strip()
GMAIL_CLIENT_SECRET = os.environ.get('GMAIL_CLIENT_SECRET', '').strip()
GMAIL_REFRESH_TOKEN = os.environ.get('GMAIL_REFRESH_TOKEN', '').strip()
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))

_default_backend = (
    'django.core.mail.backends.console.EmailBackend'
    if DEBUG
    else 'core.gmail_backend.GmailEmailBackend'
)

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', _default_backend)
if not DEBUG and 'smtp' in EMAIL_BACKEND.lower() and not env_bool('ALLOW_SMTP_IN_PROD', 'false'):
    EMAIL_BACKEND = 'core.gmail_backend.GmailEmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', 'true')

if not DEBUG and EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend' and not env_bool('ALLOW_CONSOLE_EMAIL_IN_PROD', 'false'):
    raise ImproperlyConfigured(
        'Konfiguracja django.core.mail.backends.console.EmailBackend jest zabroniona przy DJANGO_DEBUG=false.'
    )

PASSWORD_RESET_TIMEOUT = int(os.environ.get('PASSWORD_RESET_TIMEOUT', '1800'))
EMAIL_CODE_MAX_ATTEMPTS = int(os.environ.get('EMAIL_CODE_MAX_ATTEMPTS', '5'))
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
EXPO_PUSH_URL = os.environ.get(
    'EXPO_PUSH_URL',
    'https://exp.host/--/api/v2/push/send',
)
EXPO_PUSH_TIMEOUT = int(os.environ.get('EXPO_PUSH_TIMEOUT', '10'))
NOTIFICATION_SCHEDULER_INTERVAL_SECONDS = int(
    os.environ.get('NOTIFICATION_SCHEDULER_INTERVAL_SECONDS', '900'),
)
SSE_HEARTBEAT_SECONDS = int(os.environ.get('SSE_HEARTBEAT_SECONDS', '20'))
SSE_MAX_FRAMES = int(os.environ.get('SSE_MAX_FRAMES', '0'))
SSE_BUS_ENGINE = os.environ.get('SSE_BUS_ENGINE', 'auto').lower()
SSE_REDIS_CHANNEL_PREFIX = os.environ.get('SSE_REDIS_CHANNEL_PREFIX', 'physiocare:sse:')

RECAPTCHA_ENABLED = env_bool('RECAPTCHA_ENABLED', 'true' if not DEBUG else 'false')
RECAPTCHA_V2_SECRET_KEY = os.environ.get('RECAPTCHA_V2_SECRET_KEY', '')
RECAPTCHA_V3_SECRET_KEY = os.environ.get('RECAPTCHA_V3_SECRET_KEY', '')
RECAPTCHA_SECRET_KEY = (
    os.environ.get('RECAPTCHA_SECRET_KEY', '').strip()
    or RECAPTCHA_V3_SECRET_KEY.strip()
    or RECAPTCHA_V2_SECRET_KEY.strip()
)
RECAPTCHA_SCORE_THRESHOLD = float(os.environ.get('RECAPTCHA_SCORE_THRESHOLD', '0.5'))

if not DEBUG:
    if not RECAPTCHA_ENABLED:
        raise ImproperlyConfigured(
            'RECAPTCHA_ENABLED musi być ustawione na true przy DJANGO_DEBUG=false.'
        )
    if not (
        RECAPTCHA_SECRET_KEY.strip()
        or (RECAPTCHA_V2_SECRET_KEY.strip() and RECAPTCHA_V3_SECRET_KEY.strip())
    ):
        raise ImproperlyConfigured(
            'RECAPTCHA_SECRET_KEY albo komplet RECAPTCHA_V2_SECRET_KEY i '
            'RECAPTCHA_V3_SECRET_KEY jest wymagany przy DJANGO_DEBUG=false.'
        )

_SENTRY_DSN = os.environ.get('SENTRY_DSN', '').strip()
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(level=None, event_level=None),
        ],
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'production' if not DEBUG else 'development'),
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        send_default_pii=False,
    )
