"""Serializatory danych panelu administracyjnego PhysioCare.

Zawiera definicje serializatorów dla list i szczegółów użytkowników, harmonogramów,
statystyk terapeutów, analityki wizyt oraz moderacji recenzji.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import RoleChoices
from reviews.models import Review
from scheduling.models import TherapistAvailabilitySlot, Visit
from therapists.models import TherapistProfile

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer listy użytkowników dla panelu administracyjnego."""

    email_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'is_staff',
            'email_verified',
            'created_at',
            'last_login',
        ]
        read_only_fields = fields


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Szczegółowy serializer użytkownika dla administratora."""

    email_verified = serializers.BooleanField(read_only=True)
    google_linked = serializers.SerializerMethodField()
    has_mfa = serializers.SerializerMethodField()
    visits_count = serializers.SerializerMethodField()
    profile_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'is_staff',
            'is_superuser',
            'email_verified',
            'created_at',
            'updated_at',
            'last_login',
            'google_linked',
            'has_mfa',
            'visits_count',
            'profile_info',
        ]
        read_only_fields = fields

    def get_google_linked(self, obj: object) -> bool:
        return bool(getattr(obj, 'google_sub', None))

    def get_has_mfa(self, obj: object) -> bool:
        return bool(hasattr(obj, 'mfa') and obj.mfa and obj.mfa.is_enabled)

    def get_visits_count(self, obj: object) -> int:
        role = getattr(obj, 'role', '')
        if role == RoleChoices.PATIENT and hasattr(obj, 'patient_profile'):
            return obj.patient_profile.visits.count()
        if role == RoleChoices.THERAPIST and hasattr(obj, 'therapist_profile'):
            return obj.therapist_profile.visits.count()
        return 0

    def get_profile_info(self, obj: object) -> dict[str, object] | None:
        role = getattr(obj, 'role', '')
        if role == RoleChoices.THERAPIST and hasattr(obj, 'therapist_profile'):
            tp = obj.therapist_profile
            return {
                'pwzf_number': tp.pwzf_number,
                'phone': tp.phone,
                'qualification_level': tp.qualification_level,
                'experience_years': tp.experience_years,
                'rating_avg': float(tp.rating_avg),
                'rating_count': tp.rating_count,
            }
        if role == RoleChoices.PATIENT and hasattr(obj, 'patient_profile'):
            pp = obj.patient_profile
            return {
                'phone': pp.phone,
                'avatar_url': pp.avatar_url,
            }
        return None


class AdminUserStatusUpdateSerializer(serializers.Serializer):
    """Serializer zmiany statusu aktywności konta użytkownika."""

    is_active = serializers.BooleanField(required=True)


class AdminTherapistStatsSerializer(serializers.Serializer):
    """Serializer statystyk pracy i efektywności pojedynczego fizjoterapeuty."""

    therapist_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    pwzf_number = serializers.CharField()
    qualification_level = serializers.CharField()
    experience_years = serializers.IntegerField()
    rating_avg = serializers.FloatField()
    rating_count = serializers.IntegerField()
    total_visits = serializers.IntegerField()
    completed_visits = serializers.IntegerField()
    cancelled_visits = serializers.IntegerField()
    no_show_visits = serializers.IntegerField()
    pending_visits = serializers.IntegerField()


class AdminVisitSummarySerializer(serializers.ModelSerializer):
    """Podsumowanie wizyty w zbiorczym widoku harmonogramu."""

    patient_name = serializers.SerializerMethodField()
    therapist_name = serializers.SerializerMethodField()
    therapy_type_name = serializers.CharField(source='therapy_type.name', read_only=True)
    therapy_type_color = serializers.CharField(source='therapy_type.color_hex', read_only=True)

    class Meta:
        model = Visit
        fields = [
            'id',
            'start_at',
            'end_at',
            'status',
            'location_address',
            'patient_name',
            'therapist_name',
            'therapist_id',
            'therapy_type_name',
            'therapy_type_color',
        ]

    def get_patient_name(self, obj: Visit) -> str:
        return f'{obj.patient.user.first_name} {obj.patient.user.last_name}'

    def get_therapist_name(self, obj: Visit) -> str:
        return f'{obj.therapist.user.first_name} {obj.therapist.user.last_name}'


class AdminAvailabilitySlotSerializer(serializers.ModelSerializer):
    """Serializer slotu dostępności w harmonogramie zbiorczym."""

    class Meta:
        model = TherapistAvailabilitySlot
        fields = [
            'id',
            'therapist_id',
            'start_at',
            'end_at',
            'day_of_week',
            'start_time',
            'end_time',
            'is_recurring',
            'is_active',
        ]


class AdminReviewSerializer(serializers.ModelSerializer):
    """Serializer opinii pacjenta dla widoku moderacji."""

    patient_name = serializers.SerializerMethodField()
    therapist_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id',
            'patient_id',
            'patient_name',
            'therapist_id',
            'therapist_name',
            'visit_id',
            'rating',
            'comment',
            'is_anonymous',
            'is_visible',
            'therapist_reply',
            'therapist_replied_at',
            'created_at',
        ]

    def get_patient_name(self, obj: Review) -> str:
        if obj.is_anonymous:
            return f'{obj.patient.user.first_name} (Anonim)'
        return f'{obj.patient.user.first_name} {obj.patient.user.last_name}'

    def get_therapist_name(self, obj: Review) -> str:
        return f'{obj.therapist.user.first_name} {obj.therapist.user.last_name}'


class AdminReviewVisibilityUpdateSerializer(serializers.Serializer):
    """Serializer zmiany widoczności opinii."""

    is_visible = serializers.BooleanField(required=True)
