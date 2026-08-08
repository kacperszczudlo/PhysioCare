from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.field_policies import (
    NOTE_REQUIRED,
    NOTE_TOO_LONG,
    SUMMARY_TOO_LONG,
    normalize_and_validate_icd10,
    normalize_optional_text,
)
from therapists.competence import deny_message, snapshot_for_therapist
from therapists.medical_devices import get_device

from .models import (
    BodyAreaPain,
    BodySide,
    DeviceOrderStatus,
    DiagnosticRecommendation,
    FundingHint,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    RecommendationType,
    TreatmentEpisode,
    VisitNote,
)

FUNCTIONAL_DIAGNOSIS_TOO_LONG = 'Diagnoza funkcjonalna może mieć co najwyżej 5000 znaków.'
JUSTIFICATION_REQUIRED = 'Podaj uzasadnienie kliniczne.'
REFUSAL_REASON_REQUIRED = 'Podaj uzasadnienie odmowy w dokumentacji.'
ORDER_DESC_REQUIRED = 'Opisz zlecenie lekarskie, którego dotyczy odmowa.'


class TreatmentEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentEpisode
        fields = [
            'id', 'patient', 'icd10_code', 'functional_diagnosis', 'status',
            'summary_note', 'started_at', 'ended_at', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'created_at']

    def validate_icd10_code(self, value):
        try:
            return normalize_and_validate_icd10(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_functional_diagnosis(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=FUNCTIONAL_DIAGNOSIS_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_summary_note(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=SUMMARY_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if request is None or not hasattr(request.user, 'therapist_profile'):
            return attrs
        therapist = request.user.therapist_profile
        snapshot = snapshot_for_therapist(therapist)
        functional = attrs.get('functional_diagnosis')
        if functional is None and self.instance is not None:
            functional = self.instance.functional_diagnosis
        if functional and str(functional).strip() and not snapshot.allows('functional_diagnosis'):
            raise serializers.ValidationError({
                'functional_diagnosis': deny_message('functional_diagnosis', snapshot),
            })
        return attrs


class TreatmentEpisodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentEpisode
        fields = [
            'id', 'icd10_code', 'functional_diagnosis', 'status',
            'summary_note', 'started_at',
        ]
        read_only_fields = ['id']

    def validate_icd10_code(self, value):
        try:
            return normalize_and_validate_icd10(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_functional_diagnosis(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=FUNCTIONAL_DIAGNOSIS_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_summary_note(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=SUMMARY_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if request is None or not hasattr(request.user, 'therapist_profile'):
            return attrs
        snapshot = snapshot_for_therapist(request.user.therapist_profile)
        functional = attrs.get('functional_diagnosis') or ''
        if str(functional).strip() and not snapshot.allows('functional_diagnosis'):
            raise serializers.ValidationError({
                'functional_diagnosis': deny_message('functional_diagnosis', snapshot),
            })
        return attrs


class BodyAreaPainSerializer(serializers.ModelSerializer):
    vas_score = serializers.IntegerField(
        min_value=0,
        max_value=10,
        error_messages={
            'min_value': 'Skala VAS musi być liczbą od 0 do 10.',
            'max_value': 'Skala VAS musi być liczbą od 0 do 10.',
            'invalid': 'Skala VAS musi być liczbą od 0 do 10.',
            'required': 'Podaj natężenie bólu (VAS 0-10).',
        },
    )
    body_region = serializers.CharField(
        max_length=50,
        error_messages={
            'blank': 'Wskaż obszar ciała.',
            'required': 'Wskaż obszar ciała.',
            'max_length': 'Nazwa obszaru ciała może mieć co najwyżej 50 znaków.',
        },
    )

    class Meta:
        model = BodyAreaPain
        fields = [
            'id', 'episode', 'body_region', 'view_side',
            'vas_score', 'pain_character', 'treatment_targets', 'recorded_at',
        ]
        read_only_fields = ['id', 'episode', 'recorded_at']

    def validate_body_region(self, value):
        region = ' '.join(str(value).split())
        if not region:
            raise serializers.ValidationError('Wskaż obszar ciała.')
        return region

    def validate_pain_character(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Charakter bólu musi być listą.')
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise serializers.ValidationError(
                    'Każdy charakter bólu musi być niepustym tekstem.'
                )
            cleaned.append(item.strip())
        return cleaned

    def validate_treatment_targets(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Cele terapii muszą być listą.')
        cleaned = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise serializers.ValidationError(
                    'Każdy cel terapii musi być niepustym tekstem.'
                )
            cleaned.append(item.strip())
        return cleaned


class VisitNoteSerializer(serializers.ModelSerializer):
    content = serializers.CharField(
        error_messages={
            'blank': NOTE_REQUIRED,
            'required': NOTE_REQUIRED,
        },
    )

    class Meta:
        model = VisitNote
        fields = ['id', 'episode', 'visit', 'content', 'created_at']
        read_only_fields = ['id', 'episode', 'created_at']

    def validate_content(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
                allow_blank=False,
                required_message=NOTE_REQUIRED,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_visit(self, visit):
        if visit is None:
            return visit
        episode = self.context.get('episode')
        if episode is None:
            return visit
        if visit.patient_id != episode.patient_id:
            raise serializers.ValidationError(
                'Wizyta nie należy do pacjenta tego epizodu.'
            )
        if visit.episode_id is not None and visit.episode_id != episode.id:
            raise serializers.ValidationError(
                'Wizyta nie należy do tego epizodu.'
            )
        return visit


class DiagnosticRecommendationSerializer(serializers.ModelSerializer):
    recommendation_type = serializers.ChoiceField(choices=RecommendationType.choices)
    funding_hint = serializers.ChoiceField(
        choices=FundingHint.choices,
        required=False,
        default=FundingHint.NFZ_VIA_DOCTOR,
    )

    class Meta:
        model = DiagnosticRecommendation
        fields = [
            'id', 'episode', 'therapist', 'recommendation_type', 'target_specialty',
            'body_area', 'justification', 'red_flags_noted', 'funding_hint', 'created_at',
        ]
        read_only_fields = ['id', 'episode', 'therapist', 'created_at']

    def validate_justification(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
                allow_blank=False,
                required_message=JUSTIFICATION_REQUIRED,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        therapist = request.user.therapist_profile
        snapshot = snapshot_for_therapist(therapist)
        if not snapshot.allows('imaging_recommendation'):
            raise serializers.ValidationError(
                deny_message('imaging_recommendation', snapshot),
            )

        rec_type = attrs.get('recommendation_type')
        # Formalne skierowanie NFZ na obrazowanie — zawsze niedozwolone w aplikacji.
        if rec_type in (
            RecommendationType.IMAGING_MRI,
            RecommendationType.IMAGING_CT,
            RecommendationType.IMAGING_RTG,
        ):
            funding = attrs.get('funding_hint', FundingHint.NFZ_VIA_DOCTOR)
            if rec_type == RecommendationType.IMAGING_RTG:
                attrs['funding_hint'] = FundingHint.NFZ_VIA_DOCTOR
            elif funding == FundingHint.PRIVATE and rec_type == RecommendationType.IMAGING_MRI:
                attrs['funding_hint'] = FundingHint.PRIVATE
            else:
                attrs['funding_hint'] = FundingHint.NFZ_VIA_DOCTOR
        return attrs


class MedicalDeviceOrderSerializer(serializers.ModelSerializer):
    device_code = serializers.CharField(max_length=40)
    side = serializers.ChoiceField(choices=BodySide.choices, required=False, default=BodySide.NA)
    quantity = serializers.IntegerField(min_value=1, max_value=24, default=1)
    status = serializers.ChoiceField(
        choices=DeviceOrderStatus.choices,
        required=False,
        default=DeviceOrderStatus.ISSUED,
    )

    class Meta:
        model = MedicalDeviceOrder
        fields = [
            'id', 'episode', 'patient', 'therapist', 'device_code', 'device_group',
            'device_name', 'side', 'quantity', 'icd10_code', 'status', 'notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'episode', 'patient', 'therapist', 'device_group',
            'device_name', 'created_at',
        ]

    def validate_icd10_code(self, value):
        try:
            return normalize_and_validate_icd10(value, allow_blank=False)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_notes(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message='Notatka do zlecenia może mieć co najwyżej 2000 znaków.',
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        therapist = request.user.therapist_profile
        snapshot = snapshot_for_therapist(therapist)

        device = get_device(attrs.get('device_code', ''))
        if device is None:
            raise serializers.ValidationError({
                'device_code': 'Nieznany kod wyrobu. Wybierz pozycję z katalogu.',
            })

        from therapists.competence import QualificationLevel

        min_q = device['min_qualification']
        level = snapshot.qualification_level
        if min_q == QualificationLevel.FIZJO_SPEC and level != QualificationLevel.FIZJO_SPEC:
            raise serializers.ValidationError({
                'device_code': deny_message('order_specialist_devices', snapshot),
            })
        if min_q == QualificationLevel.MAGISTER and level not in (
            QualificationLevel.MAGISTER,
            QualificationLevel.FIZJO_SPEC,
        ):
            raise serializers.ValidationError({
                'device_code': deny_message('order_serial_devices', snapshot),
            })

        attrs['device_group'] = device['group']
        attrs['device_name'] = device['name']
        return attrs


class PhysicianOrderRefusalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicianOrderRefusal
        fields = [
            'id', 'episode', 'therapist', 'physician_order_description',
            'refusal_reason', 'physician_notified', 'created_at',
        ]
        read_only_fields = ['id', 'episode', 'therapist', 'created_at']

    def validate_physician_order_description(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message=NOTE_TOO_LONG,
                allow_blank=False,
                required_message=ORDER_DESC_REQUIRED,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_refusal_reason(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=NOTE_TOO_LONG,
                allow_blank=False,
                required_message=REFUSAL_REASON_REQUIRED,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc


class ReceptaNaRuchReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceptaNaRuchReferral
        fields = [
            'id', 'patient', 'therapist', 'episode', 'readiness_confirmed',
            'activity_notes', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'therapist', 'created_at']

    def validate_activity_notes(self, value):
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message='Notatka może mieć co najwyżej 2000 znaków.',
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('readiness_confirmed', False):
            raise serializers.ValidationError({
                'readiness_confirmed': (
                    'Potwierdź weryfikację gotowości do wysiłku '
                    '(kwestionariusz / ocena stanu zdrowia).'
                ),
            })
        return attrs
