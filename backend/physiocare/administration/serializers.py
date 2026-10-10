"""Serializatory danych panelu administracyjnego PhysioCare.

Zawiera definicje serializatorów dla list i szczegółów użytkowników, harmonogramów,
statystyk terapeutów, analityki wizyt oraz moderacji recenzji.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import RoleChoices
from privacy.models import AccountDeletionRequest, Consent
from reviews.models import Review
from scheduling.models import TherapistAvailabilitySlot, Visit

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
        if obj.patient and getattr(obj.patient, 'user', None):
            name = f'{obj.patient.user.first_name} {obj.patient.user.last_name}'.strip()
            return name or obj.patient.user.email
        return 'Nieznany pacjent'

    def get_therapist_name(self, obj: Visit) -> str:
        if obj.therapist and getattr(obj.therapist, 'user', None):
            name = f'{obj.therapist.user.first_name} {obj.therapist.user.last_name}'.strip()
            return name or obj.therapist.user.email
        return 'Nieznany fizjoterapeuta'


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


class AdminPrivacyRequestSerializer(serializers.ModelSerializer):
    """Serializer wniosków o usunięcie konta (RODO Art. 17)."""

    user_email = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
    is_processed = serializers.SerializerMethodField()

    class Meta:
        model = AccountDeletionRequest
        fields = [
            'id',
            'user_id',
            'user_email',
            'user_full_name',
            'reason',
            'processed_at',
            'notes',
            'created_at',
            'is_processed',
        ]
        read_only_fields = fields

    def get_user_email(self, obj: AccountDeletionRequest) -> str:
        """Pobiera historyczny lub bieżący adres e-mail powiązany z wnioskiem.

        Args:
            obj (AccountDeletionRequest): Instancja wniosku o usunięcie konta.

        Returns:
            str: Pierwotny adres e-mail pacjenta lub zanonimizowany identyfikator.
        """
        if obj.notes:
            for line in obj.notes.splitlines():
                if line.startswith('email_at_request='):
                    return line.split('email_at_request=', 1)[1].strip()
        return obj.user.email

    def get_user_full_name(self, obj: AccountDeletionRequest) -> str:
        """Pobiera pełne imię i nazwisko wnioskującego użytkownika.

        Args:
            obj (AccountDeletionRequest): Instancja wniosku o usunięcie konta.

        Returns:
            str: Imię i nazwisko lub domyślny placeholder.
        """
        name = f'{obj.user.first_name} {obj.user.last_name}'.strip()
        return name or '(Użytkownik)'

    def get_is_processed(self, obj: AccountDeletionRequest) -> bool:
        """Sprawdza, czy dany wniosek został już przetworzony przez administratora.

        Args:
            obj (AccountDeletionRequest): Instancja wniosku o usunięcie konta.

        Returns:
            bool: True jeśli wniosek został zrealizowany, False w przeciwnym razie.
        """
        return obj.is_processed()


class AdminProcessPrivacyRequestSerializer(serializers.Serializer):
    """Serializer akcji przetworzenia/anonimizacji wniosku o usunięcie konta."""

    notes = serializers.CharField(required=False, allow_blank=True, default='')


class AdminConsentSerializer(serializers.ModelSerializer):
    """Serializer zgód użytkowników dla audytu RODO."""

    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    consent_type_display = serializers.CharField(source='get_consent_type_display', read_only=True)

    class Meta:
        model = Consent
        fields = [
            'id',
            'user_id',
            'user_email',
            'user_full_name',
            'consent_type',
            'consent_type_display',
            'granted',
            'granted_at',
        ]
        read_only_fields = fields

    def get_user_full_name(self, obj: Consent) -> str:
        """Pobiera pełne imię i nazwisko użytkownika powiązanego ze zgodą.

        Args:
            obj (Consent): Instancja zarejestrowanej zgody.

        Returns:
            str: Imię i nazwisko lub domyślny placeholder.
        """
        name = f'{obj.user.first_name} {obj.user.last_name}'.strip()
        return name or '(Użytkownik)'


