"""Widoki API panelu administracyjnego PhysioCare.

Zawiera punkty końcowe do zarządzania kontami użytkowników, monitorowania harmonogramów,
analityki wizyt, profili fizjoterapeutów oraz moderacji opinii pacjentów.
"""

import logging
from datetime import datetime, time, timedelta
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.email_codes import send_password_reset_code
from accounts.models import RoleChoices
from accounts.token_ops import blacklist_user_refresh_tokens
from core.permissions import IsAdminRole
from core.throttling import AdminPasswordResetRateThrottle
from exercises.models import Exercise, ExerciseAssignment
from privacy.account_deletion import anonymize_user_for_deletion
from privacy.models import AccountDeletionRequest, Consent
from reviews.models import Review
from scheduling.models import TherapistAvailabilitySlot, Visit, VisitStatus
from therapists.models import TherapistProfile

from .serializers import (
    AdminAvailabilitySlotSerializer,
    AdminConsentSerializer,
    AdminPrivacyRequestSerializer,
    AdminProcessPrivacyRequestSerializer,
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

        # Statystyki użytkowników w 1 zapytaniu agregującym
        user_stats = User.objects.aggregate(
            total_users=Count('id'),
            patients_count=Count('id', filter=Q(role=RoleChoices.PATIENT)),
            therapists_count=Count('id', filter=Q(role=RoleChoices.THERAPIST)),
            admins_count=Count('id', filter=Q(role=RoleChoices.ADMIN)),
            active_count=Count('id', filter=Q(is_active=True)),
            inactive_count=Count('id', filter=Q(is_active=False)),
            new_last_30_days=Count('id', filter=Q(created_at__gte=thirty_days_ago)),
        )

        # Statystyki wizyt w 1 zapytaniu agregującym
        visit_stats = Visit.objects.aggregate(
            total_visits=Count('id'),
            scheduled_visits=Count('id', filter=Q(status=VisitStatus.SCHEDULED)),
            completed_visits=Count('id', filter=Q(status=VisitStatus.COMPLETED)),
            cancelled_visits=Count('id', filter=Q(status=VisitStatus.CANCELLED)),
            no_show_visits=Count('id', filter=Q(status=VisitStatus.NO_SHOW)),
            pending_visits=Count('id', filter=Q(status=VisitStatus.PENDING_APPROVAL)),
        )

        completed_visits = visit_stats['completed_visits']
        no_show_visits = visit_stats['no_show_visits']
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
                'total': user_stats['total_users'],
                'patients_count': user_stats['patients_count'],
                'therapists_count': user_stats['therapists_count'],
                'admins_count': user_stats['admins_count'],
                'active_count': user_stats['active_count'],
                'inactive_count': user_stats['inactive_count'],
                'new_last_30_days': user_stats['new_last_30_days'],
            },
            'visits': {
                'total': visit_stats['total_visits'],
                'scheduled': visit_stats['scheduled_visits'],
                'completed': visit_stats['completed_visits'],
                'cancelled': visit_stats['cancelled_visits'],
                'no_show': visit_stats['no_show_visits'],
                'pending_approval': visit_stats['pending_visits'],
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
        qs = User.objects.all().order_by('-created_at', 'pk')

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
        if user.is_superuser and not getattr(request.user, 'is_superuser', False):
            raise PermissionDenied('Tylko superadministrator może usunąć konto superusera.')

        # Zgodnie z wytycznymi medycznymi/RODO - pełna anonimizacja PII i deaktywacja sesji
        anonymize_user_for_deletion(
            user,
            reason='Usunięcie konta przez administratora (RODO)',
            source='admin',
        )
        blacklist_user_refresh_tokens(user)

        logger.info(
            'Administrator %s zanonimizował i zdezaktywował użytkownika %s (%s).',
            request.user.email,
            user.email,
            user.id,
        )
        return Response(
            {'message': 'Użytkownik został pomyślnie usunięty i zanonimizowany zgodnie z RODO.'},
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
        if user.is_superuser and not getattr(request.user, 'is_superuser', False):
            raise PermissionDenied('Tylko superadministrator może modyfikować status konta superusera.')

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
    throttle_classes = [AdminPasswordResetRateThrottle]

    def post(self, request, pk: UUID, *args, **kwargs) -> Response:
        user = get_object_or_404(User, id=pk)
        if user.is_superuser and not getattr(request.user, 'is_superuser', False):
            raise PermissionDenied('Tylko superadministrator może zresetować hasło konta superusera.')
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
        therapist_uuid = None
        if therapist_id:
            try:
                therapist_uuid = UUID(therapist_id)
            except (ValueError, AttributeError) as err:
                raise ValidationError({'therapist_id': ['Niepoprawny format identyfikatora UUID.']}) from err

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

        if end_dt < start_dt:
            raise ValidationError({'range': ['Data końcowa nie może być wcześniejsza niż data początkowa.']})
        if (end_dt - start_dt).days > 60:
            raise ValidationError({'range': ['Maksymalny dozwolony zakres czasu w harmonogramie to 60 dni.']})

        # Pobranie terapeutów
        therapists_qs = TherapistProfile.objects.select_related('user').all()
        if therapist_uuid:
            therapists_qs = therapists_qs.filter(id=therapist_uuid)

        # Pobranie wizyt
        visits_qs = (
            Visit.objects.filter(start_at__lt=end_dt, end_at__gt=start_dt)
            .select_related('patient__user', 'therapist__user', 'therapy_type')
            .order_by('start_at', 'pk')
        )
        if therapist_uuid:
            visits_qs = visits_qs.filter(therapist_id=therapist_uuid)

        # Pobranie aktywnych slotów dostępności
        slots_qs = TherapistAvailabilitySlot.objects.filter(is_active=True).order_by(
            'day_of_week', 'start_time', 'pk'
        )
        if therapist_uuid:
            slots_qs = slots_qs.filter(therapist_id=therapist_uuid)

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
        therapists = (
            TherapistProfile.objects.select_related('user')
            .annotate(
                total_visits_count=Count('visits'),
                completed_visits_count=Count('visits', filter=Q(visits__status=VisitStatus.COMPLETED)),
                cancelled_visits_count=Count('visits', filter=Q(visits__status=VisitStatus.CANCELLED)),
                no_show_visits_count=Count('visits', filter=Q(visits__status=VisitStatus.NO_SHOW)),
                pending_visits_count=Count('visits', filter=Q(visits__status=VisitStatus.PENDING_APPROVAL)),
            )
            .order_by('user__last_name', 'user__first_name', 'pk')[:200]
        )
        data = [
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
                'total_visits': t.total_visits_count,
                'completed_visits': t.completed_visits_count,
                'cancelled_visits': t.cancelled_visits_count,
                'no_show_visits': t.no_show_visits_count,
                'pending_visits': t.pending_visits_count,
            }
            for t in therapists
        ]

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
            .order_by('-created_at', 'pk')
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
            try:
                therapist_uuid = UUID(therapist_id)
            except (ValueError, AttributeError) as err:
                raise ValidationError({'therapist_id': ['Niepoprawny format identyfikatora UUID.']}) from err
            qs = qs.filter(therapist_id=therapist_uuid)

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


class AdminPrivacyRequestsListView(generics.ListAPIView):
    """Lista wniosków o usunięcie konta (RODO / Prawo do bycia zapomnianym)."""

    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AdminPrivacyRequestSerializer

    def get_queryset(self) -> QuerySet[AccountDeletionRequest]:
        """Zwraca przefiltrowany zbiór wniosków o usunięcie konta.

        Returns:
            QuerySet[AccountDeletionRequest]: Zestaw wniosków posortowany malejąco po dacie zgłoszenia.
        """
        qs = (
            AccountDeletionRequest.objects.select_related('user')
            .all()
            .order_by('-created_at', 'pk')
        )

        is_processed = self.request.query_params.get('is_processed')
        if is_processed is not None:
            if is_processed.lower() in ('true', '1'):
                qs = qs.filter(processed_at__isnull=False)
            elif is_processed.lower() in ('false', '0'):
                qs = qs.filter(processed_at__isnull=True)

        search = self.request.query_params.get('search')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(notes__icontains=search)
                | Q(reason__icontains=search)
            )
        return qs


class AdminProcessPrivacyRequestView(APIView):
    """Przetwarzanie i realizacja wniosku o usunięcie konta przez administratora."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request: Request, pk: UUID, *args: object, **kwargs: object) -> Response:
        """Przetwarza wniosek o usunięcie konta, wykonując trwałą anonimizację danych osobowych.

        Args:
            request (Request): Obiekt żądania HTTP z opcjonalnymi notatkami administratora.
            pk (UUID): Identyfikator wniosku o usunięcie konta.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty słownikowe.

        Returns:
            Response: Odpowiedź zawierająca zaktualizowany obiekt przetworzonego wniosku.

        Raises:
            PermissionDenied: Gdy zwykły administrator próbuje przetworzyć wniosek superusera.
        """
        req_obj = get_object_or_404(
            AccountDeletionRequest.objects.select_related('user'), pk=pk
        )

        # Ochrona superusera
        if req_obj.user.is_superuser and not request.user.is_superuser:
            raise PermissionDenied(
                'Tylko superadministrator może przetworzyć wniosek konta superusera.'
            )

        serializer = AdminProcessPrivacyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get('notes', '').strip()

        # Anonimizacja danych (jeśli jeszcze nie wykonana)
        anonymize_user_for_deletion(
            req_obj.user,
            reason=req_obj.reason or 'Zatwierdzono przez administratora',
            source='admin_process_request',
        )

        req_obj.processed_at = timezone.now()
        if notes:
            req_obj.notes = f'{req_obj.notes}\n[Admin note: {notes}]'.strip()
        req_obj.save()

        blacklist_user_refresh_tokens(req_obj.user)

        logger.info(
            'Administrator %s przetworzył wniosek usunięcia konta %s (użytkownik %s).',
            request.user.email,
            req_obj.id,
            req_obj.user.id,
        )

        detail_serializer = AdminPrivacyRequestSerializer(req_obj)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)


class AdminPrivacyConsentsListView(generics.ListAPIView):
    """Rejestr zgód użytkowników dla audytu RODO."""

    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AdminConsentSerializer

    def get_queryset(self) -> QuerySet[Consent]:
        """Zwraca przefiltrowany zbiór zarejestrowanych zgód użytkowników.

        Returns:
            QuerySet[Consent]: Zestaw zgód posortowany malejąco po dacie udzielenia.
        """
        qs = Consent.objects.select_related('user').all().order_by('-granted_at', 'pk')

        consent_type = self.request.query_params.get('consent_type')
        if consent_type:
            qs = qs.filter(consent_type=consent_type)

        granted = self.request.query_params.get('granted')
        if granted is not None:
            if granted.lower() in ('true', '1'):
                qs = qs.filter(granted=True)
            elif granted.lower() in ('false', '0'):
                qs = qs.filter(granted=False)

        search = self.request.query_params.get('search')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        return qs


