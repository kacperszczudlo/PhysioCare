from django.core.handlers.asgi import ASGIRequest
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPatient
from notifications.defaults import ensure_default_preferences
from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import DeviceToken, NotificationPreference
from notifications.renderers import ServerSentEventRenderer
from notifications.serializers import (
    DeviceTokenDeleteSerializer,
    DeviceTokenSerializer,
    DeviceTokenWriteSerializer,
    NotificationPreferencePatchSerializer,
    NotificationPreferenceSerializer,
)
from notifications.sse import aiter_sse_frames, get_sse_metrics, iter_sse_frames


class SseStatsView(APIView):
    """Widok zwracający w czasie rzeczywistym statystyki strumienia SSE oraz stan magistrali Redis."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Pobiera metryki połączeń SSE.

        Args:
            request (Request): Obiekt żądania HTTP.

        Returns:
            Response: Odpowiedź zawierająca statystyki SSE.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        metrics = get_sse_metrics()
        return Response(metrics, status=status.HTTP_200_OK)


class MeEventsView(APIView):
    """Strumień zdarzeń wysyłanych przez serwer (Server-Sent Events) dla unieważniania stanu interfejsu w czasie rzeczywistym."""

    permission_classes = [IsAuthenticated]
    renderer_classes = [ServerSentEventRenderer]

    def get(self, request: Request) -> StreamingHttpResponse:
        """Nawiązuje połączenie strumieniowe SSE dla zalogowanego użytkownika.

        Args:
            request (Request): Obiekt żądania HTTP.

        Returns:
            StreamingHttpResponse: Strumieniowa odpowiedź HTTP ze zdarzeniami SSE.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        user_id = str(request.user.pk)
        raw_req = request._request if hasattr(request, '_request') else request
        is_asgi = isinstance(raw_req, ASGIRequest) or hasattr(raw_req, 'scope')
        stream = aiter_sse_frames(user_id) if is_asgi else iter_sse_frames(user_id)

        response = StreamingHttpResponse(
            stream,
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache, no-transform'
        response['X-Accel-Buffering'] = 'no'
        return response


class MeNotificationPreferencesView(APIView):
    """Widok pobierania i aktualizacji preferencji powiadomień dla zalogowanego pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request: Request) -> Response:
        """Pobiera preferencje powiadomień pacjenta.

        Args:
            request (Request): Obiekt żądania HTTP.

        Returns:
            Response: Zserializowana lista preferencji powiadomień.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        ensure_default_preferences(request.user)
        return Response(self._serialized_prefs(request.user))

    def patch(self, request: Request) -> Response:
        """Aktualizuje ustawienia włączania/wyłączania konkretnych powiadomień.

        Args:
            request (Request): Obiekt żądania z danymi do aktualizacji.

        Returns:
            Response: Zaktualizowana lista preferencji.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        serializer = NotificationPreferencePatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ensure_default_preferences(request.user)
        for key, enabled in serializer.validated_data.items():
            NotificationPreference.objects.update_or_create(
                user=request.user,
                pref_key=key,
                defaults={'enabled': enabled},
            )
        return Response(self._serialized_prefs(request.user))

    def _serialized_prefs(self, user: object) -> list[dict[str, object]]:
        """Serializuje preferencje powiadomień dla danego użytkownika wg porządku kanonicznego.

        Args:
            user (object): Obiekt użytkownika.

        Returns:
            list[dict[str, object]]: Zserializowana lista słowników.

        Raises:
            TypeError: Gdy parametr user jest None.
        """
        if user is None:
            raise TypeError('Argument user nie może być None.')

        by_key = {
            item.pref_key: item
            for item in NotificationPreference.objects.filter(
                user=user,
                pref_key__in=CANONICAL_PREF_KEYS,
            )
        }
        ordered = [by_key[key] for key in CANONICAL_PREF_KEYS if key in by_key]
        return NotificationPreferenceSerializer(ordered, many=True).data



class MeDeviceTokenView(APIView):
    """Widok zarządzania tokenami urządzeń mobilnych (Expo Push) powiązanymi z kontem użytkownika."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request: Request) -> Response:
        """Pobiera listę aktywnych tokenów urządzeń użytkownika.

        Args:
            request (Request): Obiekt żądania HTTP.

        Returns:
            Response: Lista tokenów urządzeń.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        tokens = DeviceToken.objects.filter(user=request.user, is_active=True).order_by(
            '-updated_at'
        )
        return Response(DeviceTokenSerializer(tokens, many=True).data)

    def post(self, request: Request) -> Response:
        """Rejestruje lub uaktualnia token urządzenia push.

        Args:
            request (Request): Obiekt żądania zawierający token urządzenia.

        Returns:
            Response: Dane zarejestrowanego tokenu.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        serializer = DeviceTokenWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data['expo_push_token']
        platform = serializer.validated_data.get('platform')
        token, _created = DeviceToken.objects.update_or_create(
            expo_push_token=token_value,
            defaults={
                'user': request.user,
                'platform': platform,
                'is_active': True,
            },
        )
        return Response(DeviceTokenSerializer(token).data, status=status.HTTP_200_OK)

    def delete(self, request: Request) -> Response:
        """Dezaktywuje token urządzenia (wyrejestrowanie).

        Args:
            request (Request): Obiekt żądania z tokenem do dezaktywacji.

        Returns:
            Response: Odpowiedź HTTP 204 No Content.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        serializer = DeviceTokenDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DeviceToken.objects.filter(
            user=request.user,
            expo_push_token=serializer.validated_data['expo_push_token'],
        ).update(is_active=False, updated_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)


