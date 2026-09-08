from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPatient
from notifications.defaults import ensure_default_preferences
from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import DeviceToken, NotificationPreference
from notifications.serializers import (
    DeviceTokenDeleteSerializer,
    DeviceTokenSerializer,
    DeviceTokenWriteSerializer,
    NotificationPreferencePatchSerializer,
    NotificationPreferenceSerializer,
)


class MeNotificationPreferencesView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request):
        ensure_default_preferences(request.user)
        return Response(self._serialized_prefs(request.user))

    def patch(self, request):
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

    def _serialized_prefs(self, user):
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
    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request):
        tokens = DeviceToken.objects.filter(user=request.user, is_active=True).order_by(
            '-updated_at'
        )
        return Response(DeviceTokenSerializer(tokens, many=True).data)

    def post(self, request):
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

    def delete(self, request):
        serializer = DeviceTokenDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DeviceToken.objects.filter(
            user=request.user,
            expo_push_token=serializer.validated_data['expo_push_token'],
        ).update(is_active=False, updated_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)
