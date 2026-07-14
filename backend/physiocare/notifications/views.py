from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPatient

from .models import NotificationPreference
from .serializers import NotificationPreferenceSerializer


class MeNotificationPreferencesView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request):
        items = NotificationPreference.objects.filter(user=request.user)
        return Response(NotificationPreferenceSerializer(items, many=True).data)

    def patch(self, request):
        prefs = request.data if isinstance(request.data, dict) else {}
        if 'preferences' in prefs:
            prefs = prefs['preferences']
        for key, enabled in prefs.items():
            NotificationPreference.objects.update_or_create(
                user=request.user,
                pref_key=key,
                defaults={'enabled': bool(enabled)},
            )
        items = NotificationPreference.objects.filter(user=request.user)
        return Response(NotificationPreferenceSerializer(items, many=True).data)
