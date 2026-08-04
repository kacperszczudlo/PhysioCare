from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsTherapist
from scheduling.models import Visit, VisitStatus

from .models import TherapistProfile
from .serializers import (
    TherapistProfileSerializer,
    TherapistProfileUpdateSerializer,
    TherapistPublicSerializer,
)


class TherapistProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_object(self):
        return self.request.user.therapist_profile

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TherapistProfileUpdateSerializer
        return TherapistProfileSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(TherapistProfileSerializer(instance).data)



class TherapistDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request):
        therapist = request.user.therapist_profile
        today = timezone.localdate()
        upcoming = Visit.objects.filter(
            therapist=therapist,
            start_at__date=today,
            status=VisitStatus.SCHEDULED,
        ).count()
        patients_count = therapist.patients.count()
        return Response({
            'visits_today': upcoming,
            'patients_total': patients_count,
        })


class TherapistPublicView(generics.RetrieveAPIView):
    serializer_class = TherapistPublicSerializer
    permission_classes = [IsAuthenticated]
    queryset = TherapistProfile.objects.select_related('user')
