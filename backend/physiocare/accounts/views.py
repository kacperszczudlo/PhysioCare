from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware import csrf


class LoginView(APIView):
    """
    Punkt kontaktowy (Endpoint) operacji weryfikacyjnej procesu tożsamości.
    Osadza token JWT jako zapieczętowany moduł HttpOnly zabezpieczający przed XSS.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role
                }
            }, status=status.HTTP_200_OK)

            response.set_cookie(
                key=settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token'),
                value=access_token,
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                secure=True,
                httponly=True,
                samesite='Lax'
            )

            response.set_cookie(
                key=settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
                value=refresh_token,
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                secure=True,
                httponly=True,
                samesite='Lax'
            )

            csrf.get_token(request)
            return response

        return Response(
            {"error": {"code": "AUTH_001", "message": "Błędny e-mail lub hasło."}},
            status=status.HTTP_401_UNAUTHORIZED
        )
