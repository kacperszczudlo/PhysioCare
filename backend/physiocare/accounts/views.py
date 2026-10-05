import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from core.logging_formatters import mask_email_for_logging
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
    send_mfa_setup_code,
    send_verify_email_code,
)
from .google_auth import GoogleAuthError, verify_google_id_token
from .mfa import (
    generate_backup_codes,
    generate_qr_code_svg,
    generate_totp_secret,
    get_totp_uri,
    hash_mfa_setup_token,
    issue_mfa_preauth_token,
    issue_mfa_setup_token,
    verify_and_consume_backup_code,
    verify_mfa_preauth_token,
    verify_mfa_setup_token,
    verify_totp_code,
)
from .models import EmailCodePurpose, RoleChoices, UserMFA
from .recaptcha import verify_recaptcha_token
from .serializers import (
    ChangePasswordSerializer,
    EmailResendSerializer,
    EmailVerifySerializer,
    MFADisableSerializer,
    MFAEnableSerializer,
    MFALoginSerializer,
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

User: type[object] = get_user_model()
logger: logging.Logger = logging.getLogger('physiocare.auth')


def _set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> Response:
    """Ustawia ciasteczka HTTP-only dla tokenów dostępowego i odświeżania.

    Args:
        response (Response): Obiekt odpowiedzi Django/DRF.
        access_token (str): Token dostępowy JWT.
        refresh_token (str): Token odświeżania JWT.

    Returns:
        Response: Obiekt odpowiedzi z ustawionymi ciasteczkami.

    Raises:
        TypeError: Gdy response jest None lub tokeny nie są typu str.
    """
    if response is None:
        raise TypeError("Argument 'response' nie może być None.")
    if not isinstance(access_token, str) or not isinstance(refresh_token, str):
        raise TypeError('Tokeny muszą być ciągami znaków.')

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


def _clear_auth_cookies(response: Response) -> Response:
    """Usuwa ciasteczka uwierzytelniające z odpowiedzi HTTP.

    Args:
        response (Response): Obiekt odpowiedzi Django/DRF.

    Returns:
        Response: Obiekt odpowiedzi z wyczyszczonymi ciasteczkami.

    Raises:
        TypeError: Gdy response jest None.
    """
    if response is None:
        raise TypeError("Argument 'response' nie może być None.")

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


def _user_payload(user: object) -> dict[str, object]:
    """Tworzy słownik z podstawowymi danymi użytkownika dla odpowiedzi API.

    Args:
        user (object): Instancja użytkownika.

    Returns:
        dict[str, object]: Słownik z danymi użytkownika.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    user_id = user.id if hasattr(user, 'id') else ''
    email = user.email if hasattr(user, 'email') else ''
    role = user.role if hasattr(user, 'role') else ''
    first_name = user.first_name if hasattr(user, 'first_name') else ''
    last_name = user.last_name if hasattr(user, 'last_name') else ''

    return {
        'id': str(user_id),
        'email': email,
        'role': role,
        'first_name': first_name,
        'last_name': last_name,
    }


def _token_pair(refresh: RefreshToken) -> dict[str, str]:
    """Generuje słownik z parami tokenów JWT.

    Args:
        refresh (RefreshToken): Instancja tokenu odświeżania.

    Returns:
        dict[str, str]: Słownik zawierający token dostępowy i odświeżania.

    Raises:
        TypeError: Gdy refresh nie jest typu RefreshToken.
    """
    if not isinstance(refresh, RefreshToken):
        raise TypeError("Argument 'refresh' musi być typu RefreshToken.")

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def _auth_response(request: object, user: object, refresh: RefreshToken, *, status_code: int = status.HTTP_200_OK) -> Response:
    """Buduje odpowiedź uwierzytelniania zawierającą dane użytkownika oraz ciasteczka JWT.

    Args:
        request (object): Obiekt żądania HTTP.
        user (object): Zalogowany użytkownik.
        refresh (RefreshToken): Instancja tokenu odświeżania.
        status_code (int): Kod statusu HTTP (domyślnie 200 OK).

    Returns:
        Response: Odpowiedź HTTP z danymi użytkownika i ustawionymi ciasteczkami.

    Raises:
        TypeError: Gdy argumenty mają niepoprawne typy.
    """
    if request is None:
        raise TypeError("Argument 'request' nie może być None.")
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(refresh, RefreshToken):
        raise TypeError("Argument 'refresh' musi być typu RefreshToken.")
    if not isinstance(status_code, int):
        raise TypeError("Argument 'status_code' musi być typu int.")

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


def _needs_verification_response(*, email: str, status_code: int = status.HTTP_201_CREATED) -> Response:
    """Tworzy odpowiedź informującą o konieczności weryfikacji adresu e-mail.

    Args:
        email (str): Adres e-mail wymagający weryfikacji.
        status_code (int): Kod statusu HTTP (domyślnie 201 Created).

    Returns:
        Response: Odpowiedź HTTP z informacją o weryfikacji e-mail.

    Raises:
        TypeError: Gdy email nie jest napisem lub status_code nie jest liczbą.
    """
    if not isinstance(email, str):
        raise TypeError('Adres e-mail musi być ciągiem znaków.')
    if not isinstance(status_code, int):
        raise TypeError('Argument status_code musi być typu int.')

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


def _mark_email_verified(user: object) -> None:
    """Oznacza e-mail użytkownika jako zweryfikowany i zapisuje czas weryfikacji.

    Args:
        user (object): Instancja użytkownika.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    email_verified_at = user.email_verified_at if hasattr(user, 'email_verified_at') else None
    if email_verified_at is None:
        user.email_verified_at = timezone.now()
        if hasattr(user, 'save'):
            user.save(update_fields=['email_verified_at', 'updated_at'])


def is_mfa_required_for_user(user: object | None) -> bool:
    """Sprawdza, czy rola użytkownika obliguje do aktywnego posiadania 2FA (terapeuci i admini)."""
    if not user:
        return False
    user_role = getattr(user, 'role', None)
    is_staff = getattr(user, 'is_staff', False)
    is_superuser = getattr(user, 'is_superuser', False)
    return user_role == RoleChoices.THERAPIST or is_staff or is_superuser


class LoginView(APIView):
    """Widok logowania przy użyciu adresu e-mail i hasła."""

    permission_classes: list[type[object]] = []
    throttle_classes: list[type[object]] = [LoginRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Obsługuje żądanie logowania użytkownika.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z danymi sesji, wymogiem 2FA/weryfikacji e-mail lub błędem logowania.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        email = data.get('email')
        password = data.get('password')
        recaptcha_token = data.get('recaptcha_token')
        recaptcha_client = data.get('recaptcha_client')
        verify_recaptcha_token(
            str(recaptcha_token) if recaptcha_token else None,
            request.META.get('REMOTE_ADDR') if hasattr(request, 'META') else None,
            str(recaptcha_client) if recaptcha_client in {'web', 'mobile'} else None,
        )

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

            if is_mfa_required_for_user(user) and not (hasattr(user, 'mfa') and user.mfa.is_enabled):
                setup_token = issue_mfa_setup_token(user)
                if not send_mfa_setup_code(user=user):
                    return Response(
                        {
                            'error': {
                                'code': 'AUTH_MFA_SETUP_EMAIL_FAILED',
                                'message': 'Nie udało się wysłać kodu konfiguracji MFA. Spróbuj ponownie.',
                                'details': {},
                            }
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_MFA_SETUP_REQUIRED',
                            'message': (
                                'Dla Twojej roli wymagane jest aktywne uwierzytelnianie dwuskładnikowe (MFA). '
                                'Skonfiguruj MFA, aby uzyskać dostęp do konta.'
                            ),
                            'details': {
                                'mfa_required': True,
                                'email': user.email,
                                'mfa_setup_token': setup_token,
                            },
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if hasattr(user, 'mfa') and user.mfa.is_enabled:
                mfa_token = issue_mfa_preauth_token(user)
                return Response(
                    {
                        'mfa_required': True,
                        'mfa_token': mfa_token,
                        'email': user.email,
                    },
                    status=status.HTTP_200_OK,
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

        logger.info('Failed login attempt for email=%s', mask_email_for_logging(str(email) if email else ''))

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


class MFALoginView(APIView):
    """Widok weryfikacji drugiego składnika autentykacji (2FA) podczas logowania."""

    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Obsługuje weryfikację kodu 2FA lub zapasowego na podstawie tokenu preautoryzacji.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z tokenami sesji lub błędem 2FA.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = MFALoginSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': {
                        'code': 'AUTH_001',
                        'message': 'Błędne dane weryfikacyjne 2FA.',
                        'details': serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mfa_token = serializer.validated_data['mfa_token']
        code = serializer.validated_data['code']

        user = verify_mfa_preauth_token(mfa_token)
        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_TOKEN_INVALID',
                        'message': 'Nieprawidłowy lub wygasły token 2FA. Zaloguj się ponownie.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not hasattr(user, 'mfa') or not user.mfa.is_enabled:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_NOT_ENABLED',
                        'message': 'Dwuskładnikowa autentykacja nie jest włączona na tym koncie.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_totp_valid = verify_totp_code(user.mfa.secret_key, code)
        is_backup_valid = False
        if not is_totp_valid:
            is_backup_valid = verify_and_consume_backup_code(user.mfa, code)

        if not is_totp_valid and not is_backup_valid:
            logger.info(
                'Failed 2FA attempt for user_id=%s email=%s',
                getattr(user, 'id', None),
                mask_email_for_logging(getattr(user, 'email', None)),
            )
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_INVALID_CODE',
                        'message': 'Nieprawidłowy kod 2FA lub kod zapasowy.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return _auth_response(request, user, refresh)


class MFASetupView(APIView):
    """Widok inicjalizacji konfiguracji 2FA (generowanie sekretu TOTP oraz kodu QR)."""

    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Generuje nowy sekret TOTP i kod QR w formacie SVG dla zalogowanego użytkownika.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z kluczem sekretnym, URI TOTP i kodem QR SVG.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        setup_token = data.get('mfa_setup_token')
        user = request.user if hasattr(request, 'user') else None
        if not getattr(user, 'is_authenticated', False):
            user = verify_mfa_setup_token(str(setup_token) if setup_token else '')
        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_SETUP_TOKEN_INVALID',
                        'message': 'Sesja konfiguracji MFA wygasła. Zaloguj się ponownie.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if setup_token:
            email_code = str(data.get('email_code') or '').strip()
            if not email_code:
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_MFA_EMAIL_CODE_REQUIRED',
                            'message': 'Podaj kod wysłany na adres e-mail.',
                            'details': {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                consume_email_code(
                    user=user,
                    purpose=EmailCodePurpose.MFA_SETUP,
                    raw_code=email_code,
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
        if hasattr(user, 'mfa') and user.mfa.is_enabled:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_ALREADY_ENABLED',
                        'message': 'Dwuskładnikowa autentykacja jest już włączona.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_mfa, created = UserMFA.objects.get_or_create(
            user=user,
            defaults={
                'secret_key': generate_totp_secret(),
                'is_enabled': False,
                'setup_token_hash': (
                    hash_mfa_setup_token(str(setup_token)) if setup_token else ''
                ),
            },
        )

        if user_mfa.is_enabled:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_ALREADY_ENABLED',
                        'message': 'Dwuskładnikowa autentykacja jest już aktywne na Twoim koncie.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if setup_token and user_mfa.setup_token_hash != hash_mfa_setup_token(str(setup_token)):
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_SETUP_TOKEN_INVALID',
                        'message': 'Sesja konfiguracji MFA wygasła. Zaloguj się ponownie.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user_mfa.secret_key:
            user_mfa.secret_key = generate_totp_secret()
            user_mfa.save(update_fields=['secret_key', 'updated_at'])

        otpauth_url = get_totp_uri(user, user_mfa.secret_key)
        qr_code_svg = generate_qr_code_svg(otpauth_url)

        return Response(
            {
                'secret_key': user_mfa.secret_key,
                'otpauth_url': otpauth_url,
                'qr_code_svg': qr_code_svg,
            },
            status=status.HTTP_200_OK,
        )


class MFAEnableView(APIView):
    """Widok aktywacji 2FA po zweryfikowaniu pierwszego kodu z aplikacji autoryzującej."""

    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Weryfikuje podany kod TOTP, włącza 2FA i zwraca kody zapasowe.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z potwierdzeniem aktywacji oraz listą kodów zapasowych.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        data = request.data if hasattr(request, 'data') else {}
        setup_token = data.get('mfa_setup_token')
        if not getattr(user, 'is_authenticated', False):
            user = verify_mfa_setup_token(str(setup_token) if setup_token else '')
        if user is None:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_SETUP_TOKEN_INVALID',
                        'message': 'Sesja konfiguracji MFA wygasła. Zaloguj się ponownie.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not hasattr(user, 'mfa') or not user.mfa.secret_key:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_SETUP_REQUIRED',
                        'message': 'Rozpocznij najpierw konfigurację 2FA wywołując setup.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_mfa = user.mfa
        if setup_token and user_mfa.setup_token_hash != hash_mfa_setup_token(str(setup_token)):
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_SETUP_TOKEN_INVALID',
                        'message': 'Sesja konfiguracji MFA wygasła. Zaloguj się ponownie.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user_mfa.is_enabled:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_ALREADY_ENABLED',
                        'message': 'Dwuskładnikowa autentykacja jest już włączona.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MFAEnableSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': {
                        'code': 'AUTH_001',
                        'message': 'Błędny kod weryfikacyjny.',
                        'details': serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = serializer.validated_data['code']
        if not verify_totp_code(user_mfa.secret_key, code):
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_INVALID_CODE',
                        'message': 'Nieprawidłowy kod z aplikacji weryfikującej. Sprawdź czas urządzenia.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_codes, hashed_codes = generate_backup_codes(8)
        with transaction.atomic():
            locked_mfa = UserMFA.objects.select_for_update().get(pk=user_mfa.pk)
            if locked_mfa.is_enabled or (
                setup_token
                and locked_mfa.setup_token_hash != hash_mfa_setup_token(str(setup_token))
            ):
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_MFA_SETUP_TOKEN_INVALID',
                            'message': 'Sesja konfiguracji MFA wygasła. Zaloguj się ponownie.',
                            'details': {},
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            locked_mfa.is_enabled = True
            locked_mfa.setup_token_hash = ''
            locked_mfa.backup_codes = hashed_codes
            locked_mfa.save(update_fields=['is_enabled', 'setup_token_hash', 'backup_codes', 'updated_at'])

        user_email = user.email if hasattr(user, 'email') else 'unknown'
        logger.info(
            '2FA enabled for user_id=%s email=%s',
            getattr(user, 'id', None),
            mask_email_for_logging(user_email),
        )

        return Response(
            {
                'message': 'Dwuskładnikowa autentykacja została pomyślnie aktywowana.',
                'backup_codes': raw_codes,
            },
            status=status.HTTP_200_OK,
        )


class MFADisableView(APIView):
    """Widok wyłączania 2FA dla zalogowanego użytkownika."""

    permission_classes = [IsAuthenticated]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Weryfikuje hasło oraz opcjonalny kod 2FA i wyłącza autentykację dwuskładnikową.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z potwierdzeniem wyłączenia 2FA.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        if not hasattr(user, 'mfa') or not user.mfa.is_enabled:
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_NOT_ENABLED',
                        'message': 'Dwuskładnikowa autentykacja nie jest włączona na Twoim koncie.',
                        'details': {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data if hasattr(request, 'data') else {}
        serializer = MFADisableSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': {
                        'code': 'AUTH_001',
                        'message': 'Błędne dane.',
                        'details': serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = serializer.validated_data['password']
        if not user.check_password(password):
            return Response(
                {
                    'error': {
                        'code': 'AUTH_001',
                        'message': 'Nieprawidłowe hasło.',
                        'details': {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        code = serializer.validated_data.get('code')
        if code:
            is_totp_valid = verify_totp_code(user.mfa.secret_key, code)
            is_backup_valid = False
            if not is_totp_valid:
                is_backup_valid = verify_and_consume_backup_code(user.mfa, code)

            if not is_totp_valid and not is_backup_valid:
                return Response(
                    {
                        'error': {
                            'code': 'AUTH_MFA_INVALID_CODE',
                            'message': 'Nieprawidłowy kod 2FA lub kod zapasowy.',
                            'details': {},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user_mfa = user.mfa
        user_mfa.is_enabled = False
        user_mfa.backup_codes = []
        user_mfa.save(update_fields=['is_enabled', 'backup_codes', 'updated_at'])

        user_email = user.email if hasattr(user, 'email') else 'unknown'
        logger.info(
            '2FA disabled for user_id=%s email=%s',
            getattr(user, 'id', None),
            mask_email_for_logging(user_email),
        )

        return Response(
            {
                'message': 'Dwuskładnikowa autentykacja została wyłączona.',
            },
            status=status.HTTP_200_OK,
        )



class MFAStatusView(APIView):
    """Widok sprawdzania statusu 2FA dla zalogowanego użytkownika."""

    permission_classes = [IsAuthenticated]

    def get(self, request: object, *args: object, **kwargs: object) -> Response:
        """Zwraca informację o stanie aktywacji 2FA oraz wymogu roli.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z polami is_enabled oraz mfa_required_for_role.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        is_enabled = hasattr(user, 'mfa') and user.mfa.is_enabled
        mfa_required_for_role = is_mfa_required_for_user(user)

        return Response(
            {
                'is_enabled': is_enabled,
                'mfa_required_for_role': mfa_required_for_role,
            },
            status=status.HTTP_200_OK,
        )


class GoogleLoginView(APIView):
    """Widok logowania i rejestracji za pomocą konta Google (ID Token)."""

    permission_classes: list[type[object]] = []
    throttle_classes: list[type[object]] = [LoginRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Wymienia token ID z Google na sesję PhysioCare JWT.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z tokenami sesji lub błędem autoryzacji Google.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        credential = data.get('credential') or data.get('id_token')
        try:
            identity = verify_google_id_token(str(credential) if credential else '')
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
        if is_mfa_required_for_user(user) and not (hasattr(user, 'mfa') and user.mfa.is_enabled):
            return Response(
                {
                    'error': {
                        'code': 'AUTH_MFA_SETUP_REQUIRED',
                        'message': (
                            'Dla Twojej roli wymagane jest aktywne uwierzytelnianie dwuskładnikowe (MFA). '
                            'Skonfiguruj MFA, aby uzyskać dostęp do konta.'
                        ),
                        'details': {
                            'mfa_required': True,
                            'email': user.email,
                        },
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if hasattr(user, 'mfa') and user.mfa.is_enabled:
            mfa_token = issue_mfa_preauth_token(user)
            return Response(
                {
                    'mfa_required': True,
                    'mfa_token': mfa_token,
                    'email': user.email,
                },
                status=status.HTTP_200_OK,
            )

        refresh = RefreshToken.for_user(user)
        return _auth_response(request, user, refresh)


class LogoutView(APIView):
    """Widok wylogowania użytkownika i unieważnienia tokenów JWT."""

    permission_classes = []

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Unieważnia token odświeżający i czyści ciasteczka uwierzytelniające.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z komunikatem o wylogowaniu.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        cookies = request.COOKIES if hasattr(request, 'COOKIES') else {}
        refresh_cookie = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        raw_refresh = data.get('refresh') or cookies.get(refresh_cookie)
        blacklist_refresh_value(str(raw_refresh) if raw_refresh else None)
        response = Response({'detail': 'Wylogowano.'}, status=status.HTTP_200_OK)
        return _clear_auth_cookies(response)


class PatientRegisterView(APIView):
    """Widok rejestracji nowego pacjenta."""

    permission_classes = []
    throttle_classes = [RegisterRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Rejestruje nowego pacjenta i wysyła kod weryfikacyjny e-mail.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z tokenami sesji (dla Google) lub informacją o konieczności weryfikacji e-mail.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = PatientRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email_verified_at is not None:
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh, status_code=status.HTTP_201_CREATED)
        send_verify_email_code(user=user)
        return _needs_verification_response(email=user.email)


class TherapistRegisterView(APIView):
    """Widok rejestracji nowego fizjoterapeuty."""

    permission_classes = []
    throttle_classes = [RegisterRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Rejestruje nowego fizjoterapeutę i wysyła kod weryfikacyjny e-mail.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z tokenami sesji (dla Google) lub informacją o konieczności weryfikacji e-mail.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = TherapistRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.email_verified_at is not None:
            refresh = RefreshToken.for_user(user)
            return _auth_response(request, user, refresh, status_code=status.HTTP_201_CREATED)
        send_verify_email_code(user=user)
        return _needs_verification_response(email=user.email)


class EmailVerifyView(APIView):
    """Widok weryfikacji adresu e-mail za pomocą kodu OTP."""

    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Weryfikuje kod jednorazowy i aktywuje weryfikację e-mail użytkownika.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z tokenami sesji po pomyślnej weryfikacji.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = EmailVerifySerializer(data=data)
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
    """Widok ponownej wysyłki kodu weryfikacji adresu e-mail."""

    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Wysyła ponowne żądanie z kodem weryfikacji e-mail, jeśli konto nie jest zweryfikowane.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z informacją o wysłaniu kodu.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = EmailResendSerializer(data=data)
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
    """Widok odświeżania tokenu dostępowego JWT z ciasteczka lub treści żądania."""

    permission_classes = []

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Odświeża token dostępowy na podstawie ważnego tokenu odświeżenia.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z nowym tokenem dostępowym i ciasteczkami.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        cookies = request.COOKIES if hasattr(request, 'COOKIES') else {}
        refresh_cookie = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        refresh_value = data.get('refresh') or cookies.get(refresh_cookie)
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
        if data.get('refresh'):
            payload['access'] = access
            payload['refresh'] = new_refresh
        response = Response(payload, status=status.HTTP_200_OK)
        return _set_auth_cookies(response, access_token=access, refresh_token=new_refresh)


class PasswordResetRequestView(APIView):
    """Widok żądania resetowania hasła i wysyłki kodu OTP na e-mail."""

    permission_classes: list[type[object]] = []
    throttle_classes: list[type[object]] = [PasswordResetRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Wysyła 6-cyfrowy kod resetu hasła na podany adres e-mail.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z potwierdzeniem wysłania kodu resetu.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = PasswordResetRequestSerializer(data=data)
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
    """Widok weryfikacji kodu OTP resetowania hasła."""

    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Weryfikuje kod OTP resetowania hasła i wydaje tymczasowy token resetu.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP zawierająca token sesji resetu hasła.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        serializer = PasswordResetVerifySerializer(data=data)
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
    """Widok zatwierdzania nowego hasła po weryfikacji tokenu resetu."""

    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Ustawia nowe hasło użytkownika po pomyślnej weryfikacji tokenu resetu.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z potwierdzeniem zmiany hasła.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        data = request.data if hasattr(request, 'data') else {}
        token_raw = data.get('reset_token')
        peek = lookup_password_reset_token(
            raw_token=str(token_raw) if token_raw else '',
        )
        user = peek.user if peek is not None else None

        serializer = PasswordResetConfirmSerializer(
            data=data,
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
    """Widok zmiany hasła przez zalogowanego użytkownika."""

    def post(self, request: object, *args: object, **kwargs: object) -> Response:
        """Zmienia obecne hasło zalogowanego użytkownika na nowe.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z potwierdzeniem zmiany hasła i wyczyszczonymi ciasteczkami.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        is_authenticated = user.is_authenticated if hasattr(user, 'is_authenticated') else False
        if not is_authenticated:
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

        data = request.data if hasattr(request, 'data') else {}
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

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
