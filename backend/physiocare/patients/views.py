from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsTherapist

from .models import PatientProfile
from .serializers import PatientListSerializer


class PatientListView(generics.ListAPIView):
    serializer_class = PatientListSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_queryset(self):
        return PatientProfile.objects.filter(
            therapist=self.request.user.therapist_profile,
        ).select_related('user')
