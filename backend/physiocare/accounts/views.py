import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from core.throttling import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RegisterRateThrottle,
)

from .mail import send_templated_mail
from .models import PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PatientRegistrationSerializer,
    TherapistRegistrationSerializer,
)
from .token_ops import (
    blacklist_refresh_value,
    blacklist_user_refresh_tokens,
    wants_tokens_in_body,
)

User = get_user_model()
logger = logging.getLogger('physiocare.auth')


def _set_auth_cookies(response, *, access_token: str, refresh_token: str):
    secure = settings.SECURE_COOKIES

    response.set_cookie(
        key=settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token'),
        value=access_token,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        secure=secure,
        httponly=True,
        samesite='Lax',
    )
    response.set_cookie(
        key=settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
        value=refresh_token,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        secure=secure,
        httponly=True,
        samesite='Lax',
    )
    return response


def _clear_auth_cookies(response):
    secure = settings.SECURE_COOKIES
    for key in (
        settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token'),
        settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
    ):
        response.set_cookie(
            key=key,
            value='',
            max_age=0,
            expires='Thu, 01 Jan 1970 00:00:00 GMT',
            secure=secure,
            httponly=True,
            samesite='Lax',
        )
    return response


def _user_payload(user):
    return {
        'id': str(user.id),
        'email': user.email,
        'role': user.role,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }


def _token_pair(refresh: RefreshToken) -> dict[str, str]:
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def _auth_response(request, user, refresh: RefreshToken, *, status_code=status.HTTP_200_OK):
    tokens = _token_pair(refresh)
    payload = {'user': _user_payload(user)}
    if wants_tokens_in_body(request):
        payload.update(tokens)
    response = Response(payload, status=status_code)
    return _set_auth_cookies(
        response,
        access_token=tokens['access'],
        refresh_token=tokens['refresh'],
    )


class LoginView(APIView):
    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh)

        logger.info('Failed login attempt for email=%s', email)

        # Same message for unknown email and wrong password (no account enumeration).
        return Response(
            {
                'error': {
                    'code': 'AUTH_001',
                    'message': 'Nieprawidłowy e-mail lub hasło.',
                    'details': {},
                }
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        refresh_cookie = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        raw_refresh = request.data.get('refresh') or request.COOKIES.get(refresh_cookie)
        blacklist_refresh_value(raw_refresh)
        response = Response({'detail': 'Wylogowano.'}, status=status.HTTP_200_OK)
        return _clear_auth_cookies(response)


class PatientRegisterView(APIView):
    permission_classes = []
    throttle_classes = [RegisterRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PatientRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return _auth_response(request, user, refresh, status_code=status.HTTP_201_CREATED)


class TherapistRegisterView(APIView):
    permission_classes = []
    throttle_classes = [RegisterRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = TherapistRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return _auth_response(request, user, refresh, status_code=status.HTTP_201_CREATED)


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        refresh_cookie = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        refresh_value = request.data.get('refresh') or request.COOKIES.get(refresh_cookie)
        if not refresh_value:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_003',
                        'message': 'Brak tokenu odświeżania.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={'refresh': refresh_value})
        try:
            serializer.is_valid(raise_exception=True)
        except (User.DoesNotExist, TokenError, InvalidToken):
            response = Response(
                {
                    'error': {
                        'code': 'AUTH_003',
                        'message': 'Token odświeżania jest nieprawidłowy lub wygasł.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return _clear_auth_cookies(response)

        access = serializer.validated_data['access']
        new_refresh = serializer.validated_data.get('refresh', refresh_value)
        payload = {'detail': 'Token odświeżony.'}
        if request.data.get('refresh'):
            payload['access'] = access
            payload['refresh'] = new_refresh
        response = Response(payload, status=status.HTTP_200_OK)
        return _set_auth_cookies(response, access_token=access, refresh_token=new_refresh)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _build_password_reset_url(*, client: str, raw_token: str) -> str:
    if client == 'mobile':
        base = settings.MOBILE_RESET_URL_BASE
        path = 'password-reset'
        if base.endswith('://') or base.endswith(':/'):
            return f'{base}{path}?token={raw_token}'
        return f'{base.rstrip("/")}/{path}?token={raw_token}'
    return f'{settings.FRONTEND_URL}/reset?token={raw_token}'


def _build_web_password_reset_url(raw_token: str) -> str:
    return f'{settings.FRONTEND_URL}/reset?token={raw_token}'


class PasswordResetRequestView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        client = serializer.validated_data.get('client', 'web')

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            raw_token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(
                user=user,
                token_hash=_hash_token(raw_token),
                expires_at=timezone.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT),
            )
            reset_url = _build_password_reset_url(client=client, raw_token=raw_token)
            web_reset_url = _build_web_password_reset_url(raw_token)
            validity_minutes = max(1, settings.PASSWORD_RESET_TIMEOUT // 60)
            send_templated_mail(
                subject='PhysioCare - reset hasła',
                to=[user.email],
                template_basename='accounts/email/password_reset',
                context={
                    'reset_url': reset_url,
                    'web_reset_url': web_reset_url,
                    'is_mobile_client': client == 'mobile',
                    'validity_minutes': validity_minutes,
                },
            )

        detail = 'Jeśli konto istnieje, wysłaliśmy instrukcje resetu hasła.'
        if settings.DEBUG and 'console' in settings.EMAIL_BACKEND.lower():
            detail = (
                f'{detail} '
                '(DEBUG: EMAIL_BACKEND=console - wiadomość jest w logu Django, '
                'nie na skrzynce. Ustaw SMTP/Mailtrap w .env.)'
            )

        return Response(
            {'detail': detail},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        raw_token = request.data.get('token')
        reset_token = None
        if isinstance(raw_token, str) and raw_token.strip():
            reset_token = PasswordResetToken.objects.filter(
                token_hash=_hash_token(raw_token.strip()),
                used_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).select_related('user').first()

        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={'user': reset_token.user if reset_token is not None else None},
        )
        serializer.is_valid(raise_exception=True)

        if reset_token is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_002',
                        'message': 'Token resetu jest nieprawidłowy lub wygasł.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_token.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        blacklist_user_refresh_tokens(user)

        reset_token.used_at = timezone.now()
        reset_token.save(update_fields=['used_at'])
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).exclude(
            id=reset_token.id
        ).update(used_at=timezone.now())

        return Response({'detail': 'Hasło zostało zmienione.'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_001',
                        'message': 'Wymagane logowanie.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {
                    'error': {
                        'code': 'AUTH_004',
                        'message': 'Obecne hasło jest nieprawidłowe.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        blacklist_user_refresh_tokens(user)
        response = Response({'detail': 'Hasło zostało zmienione. Zaloguj się ponownie.'})
        return _clear_auth_cookies(response)

