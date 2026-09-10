import logging

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

from .email_codes import (
    EmailCodeError,
    consume_email_code,
    consume_password_reset_token,
    issue_password_reset_token,
    lookup_password_reset_token,
    send_password_reset_code,
    send_verify_email_code,
)
from .google_auth import GoogleAuthError, verify_google_id_token
from .models import EmailCodePurpose
from .serializers import (
    ChangePasswordSerializer,
    EmailResendSerializer,
    EmailVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
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


def _needs_verification_response(*, email: str, status_code=status.HTTP_201_CREATED):
    detail = 'Konto utworzone. Sprawdź e-mail i wpisz kod weryfikacyjny.'
    if settings.DEBUG and 'console' in settings.EMAIL_BACKEND.lower():
        detail = (
            f'{detail} '
            '(DEBUG: EMAIL_BACKEND=console - kod jest w logu Django.)'
        )
    return Response(
        {
            'needs_email_verification': True,
            'email': email,
            'detail': detail,
        },
        status=status_code,
    )


def _mark_email_verified(user) -> None:
    if user.email_verified_at is None:
        user.email_verified_at = timezone.now()
        user.save(update_fields=['email_verified_at', 'updated_at'])


class LoginView(APIView):
    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:
            if user.email_verified_at is None:
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_027',
                            'message': (
                                'Potwierdź adres e-mail kodem z wiadomości, '
                                'zanim się zalogujesz.'
                            ),
                            'details': {
                                'needs_email_verification': True,
                                'email': user.email,
                            },
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh)

        if email:
            google_only = (
                User.objects.filter(email__iexact=str(email).strip())
                .filter(google_sub__isnull=False)
                .exclude(google_sub='')
                .first()
            )
            if (
                google_only is not None
                and google_only.is_active
                and not google_only.has_usable_password()
            ):
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_023',
                            'message': 'To konto korzysta z logowania Google. Użyj przycisku „Kontynuuj z Google”.',
                            'details': {},
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        logger.info('Failed login attempt for email=%s', email)

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


class GoogleLoginView(APIView):
    """Exchange a Google ID token for PhysioCare JWT session (cookie or body)."""

    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        credential = request.data.get('credential') or request.data.get('id_token')
        try:
            identity = verify_google_id_token(credential)
        except GoogleAuthError as exc:
            return Response(
                {
                    'error': {
                        'code': exc.code,
                        'message': exc.message,
                        'details': {},
                    }
                },
                status=exc.http_status,
            )

        user = User.objects.filter(google_sub=identity.sub).first()
        if user is not None and not user.is_active:
            # Soft-deleted accounts must not block Google re-registration.
            user = None
        if user is None:
            user = User.objects.filter(email__iexact=identity.email, is_active=True).first()
            if user is not None:
                if user.google_sub and user.google_sub != identity.sub:
                    return Response(
                        {
                            'error': {
                                'code': 'AUTH_024',
                                'message': 'Ten adres e-mail jest już powiązany z innym kontem Google.',
                                'details': {},
                            }
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
                user.google_sub = identity.sub
                update_fields = ['google_sub', 'updated_at']
                if user.email_verified_at is None:
                    user.email_verified_at = timezone.now()
                    update_fields.append('email_verified_at')
                user.save(update_fields=update_fields)

        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_025',
                        'message': (
                            'Brak konta PhysioCare powiązanego z tym adresem Google. '
                            'Dokończ rejestrację w aplikacji.'
                        ),
                        'details': {
                            'needs_registration': True,
                            'email': identity.email,
                            'first_name': identity.given_name,
                            'last_name': identity.family_name,
                        },
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_001',
                        'message': 'Konto jest nieaktywne.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        _mark_email_verified(user)
        refresh = RefreshToken.for_user(user)
        return _auth_response(request, user, refresh)


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
        if user.email_verified_at is not None:
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh, status_code=status.HTTP_201_CREATED)
        send_verify_email_code(user=user)
        return _needs_verification_response(email=user.email)


class TherapistRegisterView(APIView):
    permission_classes = []
    throttle_classes = [RegisterRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = TherapistRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email_verified_at is not None:
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh, status_code=status.HTTP_201_CREATED)
        send_verify_email_code(user=user)
        return _needs_verification_response(email=user.email)


class EmailVerifyView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_028',
                        'message': 'Kod jest nieprawidłowy lub wygasł.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.email_verified_at is not None:
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh)

        try:
            consume_email_code(
                user=user,
                purpose=EmailCodePurpose.VERIFY_EMAIL,
                raw_code=code,
            )
        except EmailCodeError as exc:
            return Response(
                {
                    'error': {
                        'code': exc.code,
                        'message': exc.message,
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        _mark_email_verified(user)
        refresh = RefreshToken.for_user(user)
        return _auth_response(request, user, refresh)


class EmailResendView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = EmailResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None and user.email_verified_at is None:
            send_verify_email_code(user=user)

        detail = 'Jeśli konto wymaga weryfikacji, wysłaliśmy nowy kod.'
        if settings.DEBUG and 'console' in settings.EMAIL_BACKEND.lower():
            detail = (
                f'{detail} '
                '(DEBUG: EMAIL_BACKEND=console - kod jest w logu Django.)'
            )
        return Response({'detail': detail}, status=status.HTTP_200_OK)


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


class PasswordResetRequestView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_029',
                        'message': (
                            'Nie mamy konta z tym adresem e-mail. '
                            'Załóż konto albo sprawdź pisownię adresu.'
                        ),
                        'details': {'email': ['Nie znaleziono konta z tym e-mailem.']},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.has_usable_password():
            return Response(
                {
                    'error': {
                        'code': 'AUTH_023',
                        'message': (
                            'To konto korzysta z logowania Google i nie ma lokalnego hasła. '
                            'Użyj przycisku „Kontynuuj z Google”.'
                        ),
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        sent = send_password_reset_code(user=user)
        detail = 'Wysłaliśmy 6-cyfrowy kod resetu hasła na podany e-mail.'
        if settings.DEBUG:
            if 'console' in settings.EMAIL_BACKEND.lower():
                detail = (
                    f'{detail} '
                    '(DEBUG: EMAIL_BACKEND=console - kod jest w logu Django.)'
                )
            elif not sent:
                detail = (
                    f'{detail} '
                    '(DEBUG: wysyłka SMTP nie powiodła się - sprawdź log Django / EMAIL_* w .env.)'
                )
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_030',
                            'message': (
                                'Nie udało się wysłać e-maila. '
                                'Spróbuj ponownie za chwilę lub sprawdź konfigurację poczty.'
                            ),
                            'details': {},
                        }
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        if not sent:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_030',
                        'message': (
                            'Nie udało się wysłać e-maila. '
                            'Spróbuj ponownie za chwilę.'
                        ),
                        'details': {},
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'detail': detail}, status=status.HTTP_200_OK)


class PasswordResetVerifyView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data['email'],
            is_active=True,
        ).first()
        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_028',
                        'message': 'Kod jest nieprawidłowy lub wygasł.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            consume_email_code(
                user=user,
                purpose=EmailCodePurpose.PASSWORD_RESET,
                raw_code=serializer.validated_data['code'],
            )
        except EmailCodeError as exc:
            return Response(
                {
                    'error': {
                        'code': exc.code,
                        'message': exc.message,
                        'details': {'code': [exc.message]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_token = issue_password_reset_token(user=user)
        return Response(
            {
                'detail': 'Kod jest poprawny. Ustaw nowe hasło.',
                'reset_token': reset_token,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        token_raw = request.data.get('reset_token')
        peek = lookup_password_reset_token(
            raw_token=token_raw if isinstance(token_raw, str) else '',
        )
        user = peek.user if peek is not None else None

        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={'user': user},
        )
        serializer.is_valid(raise_exception=True)

        try:
            user = consume_password_reset_token(
                raw_token=serializer.validated_data['reset_token'],
            )
        except EmailCodeError as exc:
            return Response(
                {
                    'error': {
                        'code': exc.code,
                        'message': exc.message,
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        update_fields = ['password']
        if user.email_verified_at is None:
            user.email_verified_at = timezone.now()
            update_fields.append('email_verified_at')
        user.save(update_fields=update_fields)
        blacklist_user_refresh_tokens(user)

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
        if not user.has_usable_password():
            return Response(
                {
                    'error': {
                        'code': 'AUTH_026',
                        'message': 'Konto korzysta z logowania Google i nie ma lokalnego hasła.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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
