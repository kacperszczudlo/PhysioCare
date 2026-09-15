from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsTherapist
from exercises.models import ExerciseAssignment
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


class TherapistCompetencesView(APIView):
    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request):
        therapist = request.user.therapist_profile
        return Response(therapist.competence_snapshot().to_dict())



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
        patients_count = therapist.patient_links.filter(status='ACTIVE', patient__user__is_active=True).count()
        assignments_active = ExerciseAssignment.objects.filter(
            patient__therapist_links__therapist=therapist,
            patient__therapist_links__status='ACTIVE',
            patient__user__is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        ).count()
        return Response({
            'visits_today': upcoming,
            'patients_total': patients_count,
            'assignments_active': assignments_active,
        })


class TherapistPublicView(generics.RetrieveAPIView):
    serializer_class = TherapistPublicSerializer
    permission_classes = [IsAuthenticated]
    queryset = TherapistProfile.objects.select_related('user')


class TherapistPublicListView(generics.ListAPIView):
    serializer_class = TherapistPublicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TherapistProfile.objects.select_related('user').filter(user__is_active=True)
        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q, Value
            from django.db.models.functions import Concat
            qs = qs.annotate(
                full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            )
            query = (
                Q(full_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(location_address__icontains=search)
                | Q(pwzf_number__icontains=search)
            )
            for term in search.split():
                query |= Q(user__first_name__icontains=term)
                query |= Q(user__last_name__icontains=term)
            qs = qs.filter(query)
        return qs
