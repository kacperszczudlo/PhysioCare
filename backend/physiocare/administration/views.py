"""Widoki API panelu administracyjnego PhysioCare.

Zawiera punkty końcowe do zarządzania kontami użytkowników, monitorowania harmonogramów,
analityki wizyt, profili fizjoterapeutów oraz moderacji opinii pacjentów.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal
import logging
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.email_codes import send_password_reset_code
from accounts.models import RoleChoices
from accounts.token_ops import blacklist_user_refresh_tokens
from core.permissions import IsAdminRole
from exercises.models import Exercise, ExerciseAssignment
from reviews.models import Review
from scheduling.models import TherapistAvailabilitySlot, Visit, VisitStatus
from therapists.models import TherapistProfile

from .serializers import (
    AdminAvailabilitySlotSerializer,
    AdminReviewSerializer,
    AdminReviewVisibilityUpdateSerializer,
    AdminTherapistStatsSerializer,
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AdminUserStatusUpdateSerializer,
    AdminVisitSummarySerializer,
)

User = get_user_model()
logger = logging.getLogger('physiocare.administration')


class AdminDashboardAnalyticsView(APIView):
    """Widok agregujący wskaźniki KPI i analitykę dla głównego pulpitu administratora."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs) -> Response:
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # Statystyki użytkowników
        total_users = User.objects.count()
        patients_count = User.objects.filter(role=RoleChoices.PATIENT).count()
        therapists_count = User.objects.filter(role=RoleChoices.THERAPIST).count()
        admins_count = User.objects.filter(role=RoleChoices.ADMIN).count()
        active_count = User.objects.filter(is_active=True).count()
        inactive_count = User.objects.filter(is_active=False).count()
        new_last_30_days = User.objects.filter(created_at__gte=thirty_days_ago).count()

        # Statystyki wizyt
        visits_qs = Visit.objects.all()
        total_visits = visits_qs.count()
        scheduled_visits = visits_qs.filter(status=VisitStatus.SCHEDULED).count()
        completed_visits = visits_qs.filter(status=VisitStatus.COMPLETED).count()
        cancelled_visits = visits_qs.filter(status=VisitStatus.CANCELLED).count()
        no_show_visits = visits_qs.filter(status=VisitStatus.NO_SHOW).count()
        pending_visits = visits_qs.filter(status=VisitStatus.PENDING_APPROVAL).count()

        attended_sum = completed_visits + no_show_visits
        show_up_rate = (
            round((completed_visits / attended_sum) * 100, 1) if attended_sum > 0 else 100.0
        )

        # Statystyki jakości i opinii
        reviews_agg = Review.objects.filter(is_visible=True).aggregate(
            avg_rating=Avg('rating'), count=Count('id')
        )
        rating_avg = round(float(reviews_agg['avg_rating'] or 0.0), 2)
        rating_count = reviews_agg['count'] or 0

        # Statystyki ćwiczeń
        total_exercises = Exercise.objects.count()
        total_assignments = ExerciseAssignment.objects.count()

        payload = {
            'users': {
                'total': total_users,
                'patients_count': patients_count,
                'therapists_count': therapists_count,
                'admins_count': admins_count,
                'active_count': active_count,
                'inactive_count': inactive_count,
                'new_last_30_days': new_last_30_days,
            },
            'visits': {
                'total': total_visits,
                'scheduled': scheduled_visits,
                'completed': completed_visits,
                'cancelled': cancelled_visits,
                'no_show': no_show_visits,
                'pending_approval': pending_visits,
                'show_up_rate_percent': show_up_rate,
            },
            'quality': {
                'rating_avg': rating_avg,
                'rating_count': rating_count,
            },
            'exercises': {
                'total_exercises': total_exercises,
                'total_assignments': total_assignments,
            },
        }
        return Response(payload, status=status.HTTP_200_OK)


class AdminUserListView(generics.ListAPIView):
    """Paginowana lista użytkowników z zaawansowanym filtrowaniem."""

    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')

        # Filtr roli
        role = self.request.query_params.get('role')
        if role in dict(RoleChoices.choices):
            qs = qs.filter(role=role)

        # Filtr statusu aktywności
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ('true', '1'):
                qs = qs.filter(is_active=True)
            elif is_active.lower() in ('false', '0'):
                qs = qs.filter(is_active=False)

        # Filtr weryfikacji e-mail
        email_verified = self.request.query_params.get('email_verified')
        if email_verified is not None:
            if email_verified.lower() in ('true', '1'):
                qs = qs.filter(email_verified_at__isnull=False)
            elif email_verified.lower() in ('false', '0'):
                qs = qs.filter(email_verified_at__isnull=True)

        # Wyszukiwanie tekstowe
        search = self.request.query_params.get('search')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        return qs


class AdminUserDetailView(APIView):
    """Pobieranie szczegółów oraz bezpieczna dezaktywacja (soft delete) użytkownika."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request, pk: UUID, *args, **kwargs) -> Response:
        user = get_object_or_404(User, id=pk)
        serializer = AdminUserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk: UUID, *args, **kwargs) -> Response:
        user = get_object_or_404(User, id=pk)
        if user.id == request.user.id:
            raise PermissionDenied('Nie możesz usunąć własnego konta administratora.')

        # Zgodnie z wytycznymi medycznymi/RODO - soft delete i deaktywacja sesji
        user.is_active = False
        user.save(update_fields=['is_active', 'updated_at'])
        blacklist_user_refresh_tokens(user)

        logger.info(
            'Administrator %s zdezaktywował użytkownika %s (%s).',
            request.user.email,
            user.email,
            user.id,
        )
        return Response(
            {'message': 'Użytkownik został pomyślnie zdezaktywowany.'},
            status=status.HTTP_200_OK,
        )


class AdminUserStatusToggleView(APIView):
    """Włączenie lub wyłączenie blokady konta użytkownika (is_active)."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, pk: UUID, *args, **kwargs) -> Response:
        user = get_object_or_404(User, id=pk)
        serializer = AdminUserStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['is_active']
        if user.id == request.user.id and not new_status:
            raise PermissionDenied('Nie możesz zablokować własnego konta administratora.')

        user.is_active = new_status
        user.save(update_fields=['is_active', 'updated_at'])

        if not new_status:
            blacklist_user_refresh_tokens(user)

        logger.info(
            'Administrator %s zmienił is_active użytkownika %s na %s.',
            request.user.email,
            user.email,
            new_status,
        )
        detail_serializer = AdminUserDetailSerializer(user)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)


class AdminUserResetPasswordView(APIView):
    """Inicjowanie wysyłki kodu resetu hasła na e-mail użytkownika przez administratora."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request, pk: UUID, *args, **kwargs) -> Response:
        user = get_object_or_404(User, id=pk)
        if not user.is_active:
            raise ValidationError('Nie można zresetować hasła zablokowanego konta.')

        sent = send_password_reset_code(user=user)
        if not sent:
            return Response(
                {'error': {'message': 'Wysyłka e-mail nie powiodła się. Sprawdź konfigurację SMTP.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(
            'Administrator %s zlecił wysłanie kodu resetu hasła dla %s.',
            request.user.email,
            user.email,
        )
        return Response(
            {'message': f'Kod resetu hasła został wysłany na adres {user.email}.'},
            status=status.HTTP_200_OK,
        )


class AdminSchedulingOverviewView(APIView):
    """Zbiorczy podgląd kalendarza i wizyt wszystkich fizjoterapeutów w wybranym przedziale czasu."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs) -> Response:
        now = timezone.now()
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        therapist_id = request.query_params.get('therapist_id')

        # Parsowanie dat (domyślnie bieżący tydzień - 3 dni wstecz do +7 dni w przód)
        start_dt = parse_datetime(date_from_str) if date_from_str else None
        if not start_dt and date_from_str:
            d = parse_date(date_from_str)
            if d:
                start_dt = timezone.make_aware(datetime.combine(d, time.min))
        if not start_dt:
            start_dt = now - timedelta(days=3)

        end_dt = parse_datetime(date_to_str) if date_to_str else None
        if not end_dt and date_to_str:
            d = parse_date(date_to_str)
            if d:
                end_dt = timezone.make_aware(datetime.combine(d, time.max))
        if not end_dt:
            end_dt = now + timedelta(days=7)

        # Pobranie terapeutów
        therapists_qs = TherapistProfile.objects.select_related('user').all()
        if therapist_id:
            therapists_qs = therapists_qs.filter(id=therapist_id)

        # Pobranie wizyt
        visits_qs = (
            Visit.objects.filter(start_at__lt=end_dt, end_at__gt=start_dt)
            .select_related('patient__user', 'therapist__user', 'therapy_type')
            .order_by('start_at')
        )
        if therapist_id:
            visits_qs = visits_qs.filter(therapist_id=therapist_id)

        # Pobranie aktywnych slotów dostępności
        slots_qs = TherapistAvailabilitySlot.objects.filter(is_active=True)
        if therapist_id:
            slots_qs = slots_qs.filter(therapist_id=therapist_id)

        therapists_list = [
            {
                'id': str(t.id),
                'user_id': str(t.user.id),
                'name': f'{t.user.first_name} {t.user.last_name}',
                'email': t.user.email,
                'qualification_level': t.qualification_level,
                'rating_avg': float(t.rating_avg),
                'rating_count': t.rating_count,
            }
            for t in therapists_qs
        ]

        return Response(
            {
                'range': {
                    'start_at': start_dt.isoformat(),
                    'end_at': end_dt.isoformat(),
                },
                'therapists': therapists_list,
                'visits': AdminVisitSummarySerializer(visits_qs, many=True).data,
                'availability_slots': AdminAvailabilitySlotSerializer(slots_qs, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminTherapistStatsView(APIView):
    """Zestawienie statystyk efektywności, wizyt i ocen wszystkich fizjoterapeutów."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request, *args, **kwargs) -> Response:
        therapists = TherapistProfile.objects.select_related('user').all()
        data = []

        for t in therapists:
            visits = t.visits.all()
            total = visits.count()
            completed = visits.filter(status=VisitStatus.COMPLETED).count()
            cancelled = visits.filter(status=VisitStatus.CANCELLED).count()
            no_show = visits.filter(status=VisitStatus.NO_SHOW).count()
            pending = visits.filter(status=VisitStatus.PENDING_APPROVAL).count()

            data.append(
                {
                    'therapist_id': str(t.id),
                    'user_id': str(t.user.id),
                    'first_name': t.user.first_name,
                    'last_name': t.user.last_name,
                    'email': t.user.email,
                    'pwzf_number': t.pwzf_number,
                    'qualification_level': t.qualification_level,
                    'experience_years': t.experience_years,
                    'rating_avg': float(t.rating_avg),
                    'rating_count': t.rating_count,
                    'total_visits': total,
                    'completed_visits': completed,
                    'cancelled_visits': cancelled,
                    'no_show_visits': no_show,
                    'pending_visits': pending,
                }
            )

        serializer = AdminTherapistStatsSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminReviewListView(generics.ListAPIView):
    """Paginowana lista recenzji z opcjami filtrowania do moderacji."""

    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AdminReviewSerializer

    def get_queryset(self):
        qs = (
            Review.objects.select_related('patient__user', 'therapist__user')
            .all()
            .order_by('-created_at')
        )

        rating = self.request.query_params.get('rating')
        if rating and rating.isdigit():
            qs = qs.filter(rating=int(rating))

        is_visible = self.request.query_params.get('is_visible')
        if is_visible is not None:
            if is_visible.lower() in ('true', '1'):
                qs = qs.filter(is_visible=True)
            elif is_visible.lower() in ('false', '0'):
                qs = qs.filter(is_visible=False)

        therapist_id = self.request.query_params.get('therapist_id')
        if therapist_id:
            qs = qs.filter(therapist_id=therapist_id)

        return qs


class AdminReviewVisibilityToggleView(APIView):
    """Przełączanie widoczności opinii pacjenta (ukrycie z powodu moderacji)."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, pk: UUID, *args, **kwargs) -> Response:
        review = get_object_or_404(Review, id=pk)
        serializer = AdminReviewVisibilityUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_visible = serializer.validated_data['is_visible']
        review.is_visible = new_visible
        review.save(update_fields=['is_visible'])

        logger.info(
            'Administrator %s zmienił widoczność recenzji %s na %s.',
            request.user.email,
            review.id,
            new_visible,
        )
        detail_serializer = AdminReviewSerializer(review)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)
