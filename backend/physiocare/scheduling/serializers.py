from django.core.exceptions import ValidationError as DjangoValidationError
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


def is_visit_within_therapist_availability(therapist, start_at, end_at):
    """
    Sprawdza, czy odcinek czasu [start_at, end_at] w całości mieści się w przynajmniej jednym
    aktywnym slocie dostępności fizjoterapeuty (zarówno jednorazowym, jak i cyklicznym).
    Uwzględnia polskie święta państwowe: domyślnie blokują dostępność cykliczną,
    chyba że fizjoterapeuta utworzy dedykowany jednorazowy slot pracy w dane święto.
    """
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
        # W święto państwowe cykliczne sloty nie obowiązują (wymagany jawny slot jednorazowy)
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
    class Meta:
        model = TherapistAvailabilitySlot
        fields = [
            'id', 'therapist', 'start_at', 'end_at',
            'day_of_week', 'start_time', 'end_time',
            'is_recurring', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'therapist', 'created_at']

    def validate(self, attrs):
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
    class Meta:
        model = TherapyType
        fields = ['id', 'name', 'color_hex', 'duration_min', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        try:
            return normalize_and_validate_therapy_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_color_hex(self, value):
        try:
            return normalize_and_validate_color_hex(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_duration_min(self, value):
        try:
            return normalize_and_validate_duration_min(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class VisitSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Visit
        fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type', 'therapy_type_id',
            'patient_first_name', 'patient_last_name', 'patient_avatar_url',
            'therapist_first_name', 'therapist_last_name',
            'therapy_type_name', 'therapy_type_color', 'therapy_type_duration_min',
            'start_at', 'end_at', 'status', 'location_address',
            'prep_instructions', 'patient_summary', 'patient_note', 'cancel_reason',
            'created_at',
        ]
        read_only_fields = [
            'id', 'patient', 'therapist', 'episode', 'therapy_type',
            'patient_first_name', 'patient_last_name', 'patient_avatar_url',
            'therapist_first_name', 'therapist_last_name',
            'therapy_type_name', 'therapy_type_color', 'therapy_type_duration_min',
            'patient_note', 'created_at',
        ]

    def validate_therapy_type_id(self, therapy_type):
        if self.instance is None:
            return therapy_type
        if therapy_type.therapist_id != self.instance.therapist_id:
            raise serializers.ValidationError('Typ terapii nie należy do tego terapeuty.')
        return therapy_type

    def validate_location_address(self, value):
        try:
            return normalize_and_validate_address(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_prep_instructions(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=PREP_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_patient_summary(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        start_at = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end_at = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        if start_at is not None and end_at is not None and end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not (data.get('location_address') or '').strip():
            data['location_address'] = instance.therapist.location_address or ''
        return data


class VisitCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.UUIDField(write_only=True)
    episode_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    therapy_type_id = serializers.UUIDField(write_only=True)
    prep_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': PREP_TOO_LONG},
    )

    class Meta:
        model = Visit
        fields = [
            'patient_id', 'episode_id', 'therapy_type_id',
            'start_at', 'end_at', 'prep_instructions',
        ]

    def validate_prep_instructions(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=PREP_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
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

        if episode_id is not None and not TreatmentEpisode.objects.filter(
            pk=episode_id,
            patient_id=patient_id,
        ).exists():
            raise serializers.ValidationError(
                {'episode_id': 'Epizod nie należy do wskazanego pacjenta.'}
            )

        start_at = attrs.get('start_at')
        end_at = attrs.get('end_at')
        if start_at is not None and end_at is not None and end_at <= start_at:
            raise serializers.ValidationError(
                {'end_at': 'Koniec wizyty musi być po rozpoczęciu.'}
            )

        return attrs

    def create(self, validated_data):
        patient_id = validated_data.pop('patient_id')
        episode_id = validated_data.pop('episode_id', None)
        therapy_type_id = validated_data.pop('therapy_type_id')
        therapist = self.context['therapist']

        from patients.models import LinkStatus, PatientTherapistLink
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
    therapist_id = serializers.UUIDField(required=False, write_only=True)
    therapy_type_id = serializers.UUIDField(write_only=True)
    patient_note = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': NOTE_TOO_LONG},
    )

    class Meta:
        model = Visit
        fields = ['therapist_id', 'therapy_type_id', 'start_at', 'end_at', 'patient_note']

    def validate_patient_note(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        therapy_type_id = attrs['therapy_type_id']
        therapy_type = TherapyType.objects.filter(pk=therapy_type_id).first()
        if not therapy_type:
            raise serializers.ValidationError(
                {'therapy_type_id': 'Nie znaleziono wskazanego typu terapii.'}
            )

        therapist_id = attrs.pop('therapist_id', None)
        if therapist_id:
            from therapists.models import TherapistProfile
            therapist = TherapistProfile.objects.filter(pk=therapist_id).first()
            if not therapist:
                raise serializers.ValidationError(
                    {'therapist_id': 'Nie znaleziono wskazanego terapeuty.'}
                )
        else:
            therapist = therapy_type.therapist

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

    def create(self, validated_data):
        patient = self.context['patient']
        therapist = validated_data.pop('therapist')
        therapy_type_id = validated_data.pop('therapy_type_id')

        from patients.models import LinkStatus, PatientTherapistLink
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

    def validate_prep_instructions(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=PREP_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_location_address(self, value):
        try:
            return normalize_and_validate_address(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
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
    class Meta:
        model = Visit
        fields = ['start_at', 'end_at']

    def validate(self, attrs):
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
    cancel_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={'max_length': CANCEL_REASON_TOO_LONG},
    )

    def validate_cancel_reason(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=500,
                too_long_message=CANCEL_REASON_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
