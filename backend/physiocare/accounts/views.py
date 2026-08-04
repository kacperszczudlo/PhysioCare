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
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from core.throttling import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RegisterRateThrottle,
)

from .models import PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PatientRegistrationSerializer,
    TherapistRegistrationSerializer,
)

User = get_user_model()
logger = logging.getLogger('physiocare.auth')


def _set_auth_cookies(response, refresh):
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
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
    response.delete_cookie(
        key=settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token'),
        samesite='Lax',
        secure=secure,
    )
    response.delete_cookie(
        key=settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
        samesite='Lax',
        secure=secure,
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


class LoginView(APIView):
    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:
            refresh = RefreshToken.for_user(user)
            response = Response({'user': _user_payload(user)}, status=status.HTTP_200_OK)
            return _set_auth_cookies(response, refresh)

        logger.info('Failed login attempt for email=%s', email)
        return Response(
            {'error': {'code': 'AUTH_001', 'message': 'Błędny e-mail lub hasło.', 'details': {}}},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
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
        response = Response(
            {'user': _user_payload(user)},
            status=status.HTTP_201_CREATED,
        )
        return _set_auth_cookies(response, refresh)


class TherapistRegisterView(APIView):
    permission_classes = []
    throttle_classes = [RegisterRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = TherapistRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response(
            {'user': _user_payload(user)},
            status=status.HTTP_201_CREATED,
        )
        return _set_auth_cookies(response, refresh)


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
        serializer.is_valid(raise_exception=True)
        refresh = RefreshToken(refresh_value)
        response = Response({'detail': 'Token odświeżony.'}, status=status.HTTP_200_OK)
        return _set_auth_cookies(response, refresh)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


class PasswordResetRequestView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            raw_token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(
                user=user,
                token_hash=_hash_token(raw_token),
                expires_at=timezone.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT),
            )
            reset_url = f'{settings.FRONTEND_URL}/reset?token={raw_token}'
            from django.core.mail import send_mail
            send_mail(
                subject='PhysioCare — reset hasła',
                message=f'Użyj linku w ciągu 30 minut: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

        return Response(
            {'detail': 'Jeśli konto istnieje, wysłaliśmy instrukcje resetu hasła.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_hash = _hash_token(serializer.validated_data['token'])

        reset_token = PasswordResetToken.objects.filter(
            token_hash=token_hash,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).select_related('user').first()

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

        serializer = ChangePasswordSerializer(data=request.data)
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
        return Response({'detail': 'Hasło zostało zmienione.'}, status=status.HTTP_200_OK)

