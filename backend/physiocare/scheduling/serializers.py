from datetime import datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from core.field_policies import (
    ADDRESS_TOO_LONG,
    CANCEL_REASON_TOO_LONG,
    NOTE_TOO_LONG,
    PREP_TOO_LONG,
    normalize_and_validate_address,
    normalize_and_validate_color_hex,
    normalize_and_validate_duration_min,
    normalize_and_validate_therapy_name,
    normalize_optional_text,
)
from patients.models import PatientProfile
from treatment.models import TreatmentEpisode

from .holidays import is_polish_holiday
from .models import TherapistAvailabilitySlot, TherapyType, Visit, VisitStatus


def is_visit_within_therapist_availability(therapist: object, start_at: datetime, end_at: datetime) -> bool:
    """Sprawdza, czy odcinek czasu mieści się w dostępności fizjoterapeuty.

    Uwzględnia polskie święta państwowe: domyślnie blokują dostępność cykliczną,
    chyba że fizjoterapeuta utworzy dedykowany jednorazowy slot pracy w dane święto.

    Args:
        therapist (object): Profil fizjoterapeuty.
        start_at (datetime): Data i godzina rozpoczęcia wizyty.
        end_at (datetime): Data i godzina zakończenia wizyty.

    Returns:
        bool: True, jeśli termin mieści się w dostępności terapeuty, w przeciwnym razie False.

    Raises:
        TypeError: Gdy parametr therapist jest None lub start_at/end_at nie są instancjami datetime.
    """
    if therapist is None:
        raise TypeError('Parametr therapist nie może być None.')
    if not isinstance(start_at, datetime) or not isinstance(end_at, datetime):
        raise TypeError('Parametry start_at oraz end_at muszą być instancjami datetime.')

    slots = TherapistAvailabilitySlot.objects.filter(therapist=therapist, is_active=True)
    if not slots.exists():
        return False

    is_holiday, _ = is_polish_holiday(start_at.date())

    date_match = slots.filter(
        is_recurring=False,
        start_at__lte=start_at,
        end_at__gte=end_at,
    ).exists()
    if date_match:
        return True

    if is_holiday:
        return False

    dow = start_at.weekday()
    v_start_time = start_at.time()
    v_end_time = end_at.time()

    recurring_match = slots.filter(
        is_recurring=True,
        day_of_week=dow,
        start_time__lte=v_start_time,
        end_time__gte=v_end_time,
    ).exists()
    return recurring_match


class TherapistAvailabilitySlotSerializer(serializers.ModelSerializer):
    """Serializator dla slotów dostępności fizjoterapeuty."""

    class Meta:
        """Metadane serializatora TherapistAvailabilitySlotSerializer."""

        model = TherapistAvailabilitySlot
        fields = [
            'id', 'therapist', 'start_at', 'end_at',
            'day_of_week', 'start_time', 'end_time',
            'is_recurring', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'therapist', 'created_at']

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje poprawność zakreślonego slotu dostępności.

        Args:
            attrs (dict[str, object]): Słownik z danymi slotu dostępności.

        Returns:
            dict[str, object]: Zwalidowany słownik atrybutów.

        Raises:
            serializers.ValidationError: Gdy podane parametry slotu są nieprawidłowe.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        is_recurring = attrs.get('is_recurring', False)
        if not is_recurring:
            start_at = attrs.get('start_at')
            end_at = attrs.get('end_at')
            if not start_at or not end_at:
                raise serializers.ValidationError(
                    {'detail': 'Jednorazowy slot dostępności wymaga podania start_at oraz end_at.'}
                )
            if end_at <= start_at:
                raise serializers.ValidationError(
                    {'end_at': 'Koniec slotu dostępności musi być po rozpoczęciu.'}
                )
        else:
            dow = attrs.get('day_of_week')
            start_time = attrs.get('start_time')
            end_time = attrs.get('end_time')
            if dow is None or start_time is None or end_time is None:
                raise serializers.ValidationError(
                    {'detail': 'Cykliczny slot wymaga podania day_of_week, start_time oraz end_time.'}
                )
            if dow < 0 or dow > 6:
                raise serializers.ValidationError(
                    {'day_of_week': 'Dzień tygodnia musi mieścić się w zakresie 0 (Pon) do 6 (Nie).'}
                )
            if end_time <= start_time:
                raise serializers.ValidationError(
                    {'end_time': 'Godzina zakończenia musi być po godzinie rozpoczęcia.'}
                )
        return attrs


class TherapyTypeSerializer(serializers.ModelSerializer):
    """Serializator dla typów terapii oferowanych przez fizjoterapeutę."""

    class Meta:
        """Metadane serializatora TherapyTypeSerializer."""

        model = TherapyType
        fields = ['id', 'name', 'color_hex', 'duration_min', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value: str) -> str:
        """Waliduje nazwę typu terapii.

        Args:
            value (str): Wprowadzona nazwa typu terapii.

        Returns:
            str: Znormalizowana nazwa terapii.

        Raises:
            serializers.ValidationError: Gdy nazwa jest nieprawidłowa.
        """
        try:
            return normalize_and_validate_therapy_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_color_hex(self, value: str) -> str:
        """Waliduje kod koloru w formacie HEX.

        Args:
            value (str): Kod koloru HEX.

        Returns:
            str: Znormalizowany kod koloru HEX.

        Raises:
            serializers.ValidationError: Gdy kod HEX jest nieprawidłowy.
        """
        try:
            return normalize_and_validate_color_hex(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_duration_min(self, value: int) -> int:
        """Waliduje czas trwania terapii w minutach.

        Args:
            value (int): Czas trwania terapii w minutach.

        Returns:
            int: Zwalidowany czas trwania w minutach.

        Raises:
            serializers.ValidationError: Gdy czas trwania jest nieprawidłowy.
        """
        try:
            return normalize_and_validate_duration_min(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class VisitSerializer(serializers.ModelSerializer):
    """Serializator dla obiektu wizyty fizjoterapeutycznej."""

    patient_first_name = serializers.CharField(
        source='patient.user.first_name',
        read_only=True,
    )
    patient_last_name = serializers.CharField(
        source='patient.user.last_name',
        read_only=True,
    )
    patient_avatar_url = serializers.CharField(
        source='patient.avatar_url',
        read_only=True,
    )
    therapist_first_name = serializers.CharField(
        source='therapist.user.first_name',
        read_only=True,
    )
    therapist_last_name = serializers.CharField(
        source='therapist.user.last_name',
        read_only=True,
    )
    therapy_type_id = serializers.PrimaryKeyRelatedField(
        source='therapy_type',
        queryset=TherapyType.objects.all(),
        write_only=True,
        required=False,
    )
    therapy_type_name = serializers.CharField(
        source='therapy_type.name',
        read_only=True,
    )
    therapy_type_color = serializers.CharField(
        source='therapy_type.color_hex',
        read_only=True,
    )
    therapy_type_duration_min = serializers.IntegerField(
        source='therapy_type.duration_min',
        read_only=True,
    )
    review = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora VisitSerializer."""

        model = Visit
        fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type', 'therapy_type_id',
            'patient_first_name', 'patient_last_name', 'patient_avatar_url',
            'therapist_first_name', 'therapist_last_name',
            'therapy_type_name', 'therapy_type_color', 'therapy_type_duration_min',
            'start_at', 'end_at', 'status', 'location_address',
            'prep_instructions', 'patient_summary', 'patient_note', 'cancel_reason',
            'review', 'created_at',
        ]
        read_only_fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type',
            'patient_first_name', 'patient_last_name', 'patient_avatar_url',
            'therapist_first_name', 'therapist_last_name',
            'therapy_type_name', 'therapy_type_color', 'therapy_type_duration_min',
            'patient_note', 'review', 'created_at',
        ]

    def get_review(self, obj: Visit) -> dict | None:
        """Zwraca skróconą recenzję powiązaną z wizytą."""
        if not hasattr(obj, 'review') or obj.review is None:
            return None
        rev = obj.review
        return {
            'id': str(rev.id),
            'rating': rev.rating,
            'comment': rev.comment,
            'is_anonymous': rev.is_anonymous,
            'created_at': rev.created_at.isoformat() if rev.created_at else None,
            'therapist_reply': rev.therapist_reply,
            'therapist_replied_at': rev.therapist_replied_at.isoformat() if rev.therapist_replied_at else None,
        }

    def validate_therapy_type_id(self, therapy_type: TherapyType) -> TherapyType:
        """Waliduje czy podany typ terapii należy do danego terapeuty.

        Args:
            therapy_type (TherapyType): Obiekt typu terapii.

        Returns:
            TherapyType: Zwalidowany obiekt typu terapii.

        Raises:
            serializers.ValidationError: Gdy typ terapii nie należy do danego terapeuty lub typ obiektu jest niepoprawny.
        """
        if not isinstance(therapy_type, TherapyType):
            raise serializers.ValidationError('Typ terapii musi być instancją TherapyType.')
        if self.instance is None:
            return therapy_type
        if therapy_type.therapist_id != self.instance.therapist_id:
            raise serializers.ValidationError('Typ terapii nie należy do tego terapeuty.')
        return therapy_type

    def validate_location_address(self, value: str) -> str:
        """Waliduje adres lokalizacji wizyty.

        Args:
            value (str): Adres wizyty.

        Returns:
            str: Znormalizowany adres.

        Raises:
            serializers.ValidationError: Gdy adres jest nieprawidłowy lub za długi.
        """
        try:
            return normalize_and_validate_address(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_prep_instructions(self, value: str) -> str:
        """Waliduje instrukcje przygotowawcze do wizyty.

        Args:
            value (str): Treść instrukcji.

        Returns:
            str: Znormalizowana treść instrukcji.

        Raises:
            serializers.ValidationError: Gdy tekst jest za długi.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=PREP_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_patient_summary(self, value: str) -> str:
        """Waliduje podsumowanie wizyty dla pacjenta.

        Args:
            value (str): Podsumowanie dla pacjenta.

        Returns:
            str: Znormalizowana treść podsumowania.

        Raises:
            serializers.ValidationError: Gdy podsumowanie jest za długie.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje poprawność czasową wizyty (koniec po rozpoczęciu).

        Args:
            attrs (dict[str, object]): Slownik walidowanych atrybutów.

        Returns:
            dict[str, object]: Zwalidowany słownik atrybutów.

        Raises:
            serializers.ValidationError: Gdy czas zakończenia wyprzedza lub jest równy czasowi rozpoczęcia.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        instance_start = self.instance.start_at if self.instance and hasattr(self.instance, 'start_at') else None
        instance_end = self.instance.end_at if self.instance and hasattr(self.instance, 'end_at') else None
        start_at = attrs.get('start_at', instance_start)
        end_at = attrs.get('end_at', instance_end)
        if start_at is not None and end_at is not None and end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )
        return attrs

    def to_representation(self, instance: Visit) -> dict[str, object]:
        """Przekształca instancję wizyty na reprezentację słownikową z domyślnym adresem.

        Args:
            instance (Visit): Instancja wizyty.

        Returns:
            dict[str, object]: Reprezentacja słownikowa wizyty.

        Raises:
            TypeError: Gdy parametr instance nie jest instancją Visit.
        """
        if not isinstance(instance, Visit):
            raise TypeError('Parametr instance musi być instancją Visit.')
        data = super().to_representation(instance)
        if not (data.get('location_address') or '').strip():
            data['location_address'] = instance.therapist.location_address or ''
        return data


class VisitCreateSerializer(serializers.ModelSerializer):
    """Serializator do tworzenia nowej wizyty przez fizjoterapeutę."""

    patient_id = serializers.UUIDField(write_only=True)
    episode_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    therapy_type_id = serializers.UUIDField(write_only=True)
    prep_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': PREP_TOO_LONG},
    )

    class Meta:
        """Metadane serializatora VisitCreateSerializer."""

        model = Visit
        fields = [
            'patient_id', 'episode_id', 'therapy_type_id',
            'start_at', 'end_at', 'prep_instructions',
        ]

    def validate_prep_instructions(self, value: str) -> str:
        """Waliduje instrukcje przygotowawcze do wizyty.

        Args:
            value (str): Instrukcje przygotowawcze.

        Returns:
            str: Znormalizowane instrukcje.

        Raises:
            serializers.ValidationError: Gdy tekst instrukcji przekracza dozwolony limit.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=PREP_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje relacje z pacjentem, typem terapii, epizodem i poprawność czasową.

        Args:
            attrs (dict[str, object]): Walidowane atrybuty.

        Returns:
            dict[str, object]: Zwalidowane atrybuty wizyty.

        Raises:
            serializers.ValidationError: Gdy wybrane obiekty są nieprawidłowe lub niedostępne.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        therapist = self.context['therapist']
        patient_id = attrs['patient_id']
        therapy_type_id = attrs['therapy_type_id']
        episode_id = attrs.get('episode_id')

        if not PatientProfile.objects.active().filter(
            pk=patient_id,
            therapist_links__therapist=therapist,
            therapist_links__status='ACTIVE',
        ).exists():
            raise serializers.ValidationError(
                {'patient_id': 'Pacjent nie należy do tego terapeuty.'}
            )

        if not TherapyType.objects.filter(pk=therapy_type_id, therapist=therapist).exists():
            raise serializers.ValidationError(
                {'therapy_type_id': 'Typ terapii nie należy do tego terapeuty.'}
            )

        if episode_id is not None:
            episode = TreatmentEpisode.objects.filter(pk=episode_id).first()
            if episode is None or episode.patient_id != patient_id:
                raise serializers.ValidationError(
                    {'episode_id': 'Epizod nie należy do wskazanego pacjenta.'}
                )
            if episode.therapist_id is not None and episode.therapist_id != therapist.id:
                raise serializers.ValidationError(
                    {'episode_id': 'Epizod należy do innego fizjoterapeuty.'}
                )

        start_at = attrs.get('start_at')
        end_at = attrs.get('end_at')
        if start_at is not None and end_at is not None and end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )

        return attrs

    def create(self, validated_data: dict[str, object]) -> Visit:
        """Tworzy nową wizytę oraz upewnia się o aktywnym połączeniu terapeuty z pacjentem.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane wizyty.

        Returns:
            Visit: Utworzony obiekt wizyty.

        Raises:
            TypeError: Gdy parametr validated_data nie jest słownikiem.
        """
        if not isinstance(validated_data, dict):
            raise TypeError('Parametr validated_data musi być słownikiem.')
        patient_id = validated_data.pop('patient_id')
        episode_id = validated_data.pop('episode_id', None)
        therapy_type_id = validated_data.pop('therapy_type_id')
        therapist = self.context['therapist']

        from patients.models import LinkStatus, PatientTherapistLink
        with transaction.atomic():
            PatientTherapistLink.objects.get_or_create(
                patient_id=patient_id,
                therapist=therapist,
                defaults={'status': LinkStatus.ACTIVE},
            )
            return Visit.objects.create(
                patient_id=patient_id,
                therapist=therapist,
                episode_id=episode_id,
                therapy_type_id=therapy_type_id,
                location_address=therapist.location_address or '',
                **validated_data,
            )


class PatientVisitRequestSerializer(serializers.ModelSerializer):
    """Serializator do tworzenia zgłoszenia rezerwacji wizyty przez pacjenta."""

    therapist_id = serializers.UUIDField(required=False, write_only=True)
    therapy_type_id = serializers.UUIDField(write_only=True)
    patient_note = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': NOTE_TOO_LONG},
    )

    class Meta:
        """Metadane serializatora PatientVisitRequestSerializer."""

        model = Visit
        fields = ['therapist_id', 'therapy_type_id', 'start_at', 'end_at', 'patient_note']

    def validate_patient_note(self, value: str) -> str:
        """Waliduje notatkę dodaną przez pacjenta do zgłoszenia.

        Args:
            value (str): Notatka od pacjenta.

        Returns:
            str: Znormalizowany tekst notatki.

        Raises:
            serializers.ValidationError: Gdy treść przekracza dozwolony limit.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje dostępność wybranego terminu wizyty, terapeutę i brak nakładania się wizyt.

        Args:
            attrs (dict[str, object]): Dane zgłoszenia wizyty.

        Returns:
            dict[str, object]: Zwalidowany słownik atrybutów.

        Raises:
            serializers.ValidationError: Gdy wybrany termin jest zeszły, nieaktywny lub nakłada się z inną wizytą.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        therapy_type_id = attrs['therapy_type_id']
        therapy_type = TherapyType.objects.filter(pk=therapy_type_id).first()
        if not therapy_type:
            raise serializers.ValidationError(
                {'therapy_type_id': 'Nie znaleziono wskazanego typu terapii.'}
            )

        therapist_id = attrs.pop('therapist_id', None)
        if therapist_id:
            from therapists.models import TherapistProfile
            therapist = (
                TherapistProfile.objects.select_related('user')
                .filter(pk=therapist_id, user__is_active=True)
                .first()
            )
            if not therapist:
                raise serializers.ValidationError(
                    {'therapist_id': 'Nie znaleziono wskazanego terapeuty lub jego konto jest nieaktywne.'}
                )
        else:
            therapist = therapy_type.therapist
            if hasattr(therapist, 'user') and not therapist.user.is_active:
                raise serializers.ValidationError(
                    {'therapist_id': 'Konto wybranego fizjoterapeuty jest obecnie nieaktywne.'}
                )

        if therapy_type.therapist_id != therapist.id:
            raise serializers.ValidationError(
                {'therapy_type_id': 'Wybrana usługa nie należy do wskazanego terapeuty.'}
            )

        start_at = attrs['start_at']
        end_at = attrs['end_at']
        if end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )
        if start_at < timezone.now():
            raise serializers.ValidationError(
                {'start_at': 'Termin zgłoszenia musi być w przyszłości.'}
            )

        if not is_visit_within_therapist_availability(therapist, start_at, end_at):
            is_holiday, holiday_name = is_polish_holiday(start_at.date())
            has_any_slots = TherapistAvailabilitySlot.objects.filter(
                therapist=therapist, is_active=True
            ).exists()
            if is_holiday:
                raise serializers.ValidationError(
                    {
                        'start_at': (
                            f'Wybrany dzień ({holiday_name}) jest dniem wolnym od pracy. '
                            'Fizjoterapeuta nie przyjmuje pacjentów w to święto.'
                        )
                    }
                )
            if not has_any_slots:
                raise serializers.ValidationError(
                    {
                        'start_at': (
                            'Ten fizjoterapeuta nie udostępnił jeszcze swojego grafiku przyjęć w aplikacji. '
                            'Skontaktuj się z nim bezpośrednio lub wybierz innego specjalistę.'
                        )
                    }
                )
            raise serializers.ValidationError(
                {'start_at': 'Wybrany termin nie mieści się w godzinach przyjęć tego fizjoterapeuty. Wybierz inną datę lub godzinę.'}
            )

        overlapping = Visit.objects.filter(
            therapist=therapist,
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).exclude(status=VisitStatus.CANCELLED)
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        if overlapping.exists():
            raise serializers.ValidationError(
                {'start_at': 'Wybrana godzina jest już zarezerwowana przez innego pacjenta. Wybierz inny termin.'}
            )

        attrs['therapist'] = therapist
        return attrs

    def create(self, validated_data: dict[str, object]) -> Visit:
        """Tworzy zgłoszenie wizyty ze statusem PENDING_APPROVAL.

        Args:
            validated_data (dict[str, object]): Zwalidowane dane zgłoszenia.

        Returns:
            Visit: Utworzona instancja wizyty.

        Raises:
            TypeError: Gdy parametr validated_data nie jest słownikiem.
        """
        if not isinstance(validated_data, dict):
            raise TypeError('Parametr validated_data musi być słownikiem.')
        patient = self.context['patient']
        therapist = validated_data.pop('therapist')
        therapy_type_id = validated_data.pop('therapy_type_id')

        from patients.models import LinkStatus, PatientTherapistLink
        with transaction.atomic():
            PatientTherapistLink.objects.get_or_create(
                patient=patient,
                therapist=therapist,
                defaults={'status': LinkStatus.ACTIVE},
            )
            return Visit.objects.create(
                patient=patient,
                therapist=therapist,
                therapy_type_id=therapy_type_id,
                status=VisitStatus.PENDING_APPROVAL,
                location_address=therapist.location_address or '',
                **validated_data,
            )


class VisitApproveSerializer(serializers.Serializer):
    """Serializator do zatwierdzania zgłoszenia wizyty przez fizjoterapeutę."""

    therapy_type_id = serializers.UUIDField(required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False)
    prep_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': PREP_TOO_LONG},
    )
    location_address = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': ADDRESS_TOO_LONG},
    )

    def validate_prep_instructions(self, value: str) -> str:
        """Waliduje instrukcje przygotowawcze.

        Args:
            value (str): Treść instrukcji.

        Returns:
            str: Znormalizowany tekst instrukcji.

        Raises:
            serializers.ValidationError: Gdy przekroczono dopuszczalny limit długości.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=PREP_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_location_address(self, value: str) -> str:
        """Waliduje adres lokalizacji wizyty.

        Args:
            value (str): Wprowadzony adres.

        Returns:
            str: Znormalizowany adres.

        Raises:
            serializers.ValidationError: Gdy adres jest za długi.
        """
        try:
            return normalize_and_validate_address(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje typ terapii i poprawność ram czasowych przy zatwierdzaniu wizyty.

        Args:
            attrs (dict[str, object]): Dane do aktualizacji przy zatwierdzeniu.

        Returns:
            dict[str, object]: Zwalidowane dane.

        Raises:
            serializers.ValidationError: Gdy typ terapii jest błędny lub czas zakończenia przed rozpoczęciem.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        visit = self.context['visit']
        therapy_type_id = attrs.get('therapy_type_id')
        if therapy_type_id is not None and not TherapyType.objects.filter(
            pk=therapy_type_id,
            therapist_id=visit.therapist_id,
        ).exists():
            raise serializers.ValidationError(
                {'therapy_type_id': 'Typ terapii nie należy do tego terapeuty.'}
            )

        start_at = attrs.get('start_at', visit.start_at)
        end_at = attrs.get('end_at', visit.end_at)
        if end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )
        return attrs


class VisitRescheduleSerializer(serializers.ModelSerializer):
    """Serializator do zmiany terminu wizyty przez pacjenta."""

    class Meta:
        """Metadane serializatora VisitRescheduleSerializer."""

        model = Visit
        fields = ['start_at', 'end_at']

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje status wizyty, dostępność terminu oraz brak nakładania się na inne wizyty.

        Args:
            attrs (dict[str, object]): Proponowane nowe godziny wizyty.

        Returns:
            dict[str, object]: Zwalidowane atrybuty.

        Raises:
            serializers.ValidationError: Gdy status wizyty zabrania zmiany terminu lub termin jest zajęty.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        visit = self.instance
        if visit.status not in (VisitStatus.SCHEDULED, VisitStatus.PENDING_APPROVAL):
            raise serializers.ValidationError(
                {'detail': 'Można zmieniać termin tylko wizyt zaplanowanych lub oczekujących.'}
            )
        start_at = attrs.get('start_at', visit.start_at)
        end_at = attrs.get('end_at', visit.end_at)
        if end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )
        if start_at < timezone.now():
            raise serializers.ValidationError(
                {'start_at': 'Termin wizyty musi być w przyszłości.'}
            )

        therapist = visit.therapist
        if not is_visit_within_therapist_availability(therapist, start_at, end_at):
            is_holiday, holiday_name = is_polish_holiday(start_at.date())
            if is_holiday:
                raise serializers.ValidationError(
                    {'start_at': f'Wybrany dzień ({holiday_name}) jest dniem wolnym od pracy.'}
                )
            raise serializers.ValidationError(
                {'start_at': 'Wybrany termin nie mieści się w godzinach przyjęć tego fizjoterapeuty.'}
            )

        overlapping = Visit.objects.filter(
            therapist=therapist,
            start_at__lt=end_at,
            end_at__gt=start_at,
        ).exclude(pk=visit.pk).exclude(status=VisitStatus.CANCELLED)
        if overlapping.exists():
            raise serializers.ValidationError(
                {'start_at': 'Wybrana godzina jest już zarezerwowana przez innego pacjenta. Wybierz inny termin.'}
            )

        return attrs


class VisitCancelSerializer(serializers.Serializer):
    """Serializator dla operacji odwoływania wizyty."""

    cancel_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': CANCEL_REASON_TOO_LONG},
    )

    def validate_cancel_reason(self, value: str) -> str:
        """Waliduje podany powód odwołania wizyty.

        Args:
            value (str): Powód anulowania.

        Returns:
            str: Znormalizowany powód anulowania.

        Raises:
            serializers.ValidationError: Gdy podana treść przekracza dopuszczalny limit długości.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=500,
                too_long_message=CANCEL_REASON_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
