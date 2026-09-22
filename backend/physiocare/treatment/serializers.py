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
    EpisodeStatus,
    FundingHint,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    RecommendationType,
    TreatmentEpisode,
    VisitNote,
)

FUNCTIONAL_DIAGNOSIS_TOO_LONG: str = 'Diagnoza funkcjonalna może mieć co najwyżej 5000 znaków.'
JUSTIFICATION_REQUIRED: str = 'Podaj uzasadnienie kliniczne.'
REFUSAL_REASON_REQUIRED: str = 'Podaj uzasadnienie odmowy w dokumentacji.'
ORDER_DESC_REQUIRED: str = 'Opisz zlecenie lekarskie, którego dotyczy odmowa.'



def _get_therapist_name(obj: object) -> str:
    """Zwraca pełne imię i nazwisko fizjoterapeuty lub jego adres e-mail.

    Args:
        obj (object): Obiekt reprezentujący model powiązany z fizjoterapeutą.

    Returns:
        str: Imię i nazwisko lub e-mail fizjoterapeuty.
    """
    if obj is None:
        return ''
    if hasattr(obj, 'therapist') and obj.therapist and hasattr(obj.therapist, 'user'):
        u = obj.therapist.user
        first_name = u.first_name if hasattr(u, 'first_name') else ''
        last_name = u.last_name if hasattr(u, 'last_name') else ''
        email = u.email if hasattr(u, 'email') else ''
        full_name = f"{first_name} {last_name}".strip()
        return full_name if full_name else email
    return ''


def _is_read_only(serializer: object, obj: object) -> bool:
    """Sprawdza, czy obiekt jest tylko do odczytu dla aktualnie uwierzytelnionego fizjoterapeuty.

    Args:
        serializer (object): Instancja serializatora DRF.
        obj (object): Weryfikowany obiekt z atrybutem therapist_id.

    Returns:
        bool: True jeśli obiekt utworzył inny fizjoterapeuta, False w przeciwnym razie.
    """
    if serializer is None or obj is None:
        return False
    request = serializer.context.get('request') if hasattr(serializer, 'context') else None
    if not request or not hasattr(request, 'user') or not hasattr(request.user, 'therapist_profile'):
        return False
    current_therapist = request.user.therapist_profile
    therapist_id = obj.therapist_id if hasattr(obj, 'therapist_id') else None
    return therapist_id is not None and therapist_id != current_therapist.id


class TreatmentEpisodeSerializer(serializers.ModelSerializer):
    """Serializator do szczegółów epizodu leczenia."""

    therapist_name = serializers.SerializerMethodField()
    is_read_only = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora epizodu leczenia."""

        model = TreatmentEpisode
        fields = [
            'id', 'patient', 'therapist', 'therapist_name', 'is_read_only',
            'icd10_code', 'functional_diagnosis', 'status',
            'summary_note', 'started_at', 'ended_at', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'therapist', 'created_at']

    def get_therapist_name(self, obj: object) -> str:
        """Pobiera imię i nazwisko fizjoterapeuty przypisanego do epizodu.

        Args:
            obj (object): Instancja epizodu leczenia.

        Returns:
            str: Imię i nazwisko fizjoterapeuty lub e-mail.
        """
        return _get_therapist_name(obj)

    def get_is_read_only(self, obj: object) -> bool:
        """Sprawdza, czy dany epizod jest w trybie tylko do odczytu dla fizjoterapeuty.

        Args:
            obj (object): Instancja epizodu leczenia.

        Returns:
            bool: True jeśli epizod jest tylko do odczytu, False w przeciwnym razie.
        """
        return _is_read_only(self, obj)

    def validate_icd10_code(self, value: object) -> str:
        """Waliduje kod ICD-10.

        Args:
            value (object): Kod ICD-10.

        Returns:
            str: Znormalizowany kod ICD-10.

        Raises:
            serializers.ValidationError: Gdy kod ICD-10 jest niepoprawny.
        """
        try:
            return normalize_and_validate_icd10(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_functional_diagnosis(self, value: object) -> str:
        """Waliduje opis diagnozy funkcjonalnej.

        Args:
            value (object): Wartość diagnozy funkcjonalnej.

        Returns:
            str: Znormalizowany tekst diagnozy funkcjonalnej.

        Raises:
            serializers.ValidationError: Gdy tekst przekracza dopuszczalny limit znaków.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=FUNCTIONAL_DIAGNOSIS_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_summary_note(self, value: object) -> str:
        """Waliduje podsumowanie epizodu leczenia.

        Args:
            value (object): Treść podsumowania.

        Returns:
            str: Znormalizowany tekst podsumowania.

        Raises:
            serializers.ValidationError: Gdy tekst przekracza dopuszczalny limit znaków.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=SUMMARY_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje kompetencje fizjoterapeuty do formułowania diagnozy funkcjonalnej.

        Args:
            attrs (dict[str, object]): Słownik z danymi zlecenia/epizodu.

        Returns:
            dict[str, object]: Zwalidowane dane epizodu.

        Raises:
            serializers.ValidationError: Gdy dane są niepoprawne lub fizjoterapeuta nie ma uprawnień.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
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
    """Serializator do tworzenia nowego epizodu leczenia."""

    class Meta:
        """Metadane serializatora tworzenia epizodu leczenia."""

        model = TreatmentEpisode
        fields = [
            'id', 'icd10_code', 'functional_diagnosis', 'status',
            'summary_note', 'started_at',
        ]
        read_only_fields = ['id']

    def validate_icd10_code(self, value: object) -> str:
        """Waliduje kod ICD-10 podczas tworzenia epizodu.

        Args:
            value (object): Kod ICD-10.

        Returns:
            str: Znormalizowany kod ICD-10.

        Raises:
            serializers.ValidationError: Gdy kod ICD-10 jest niepoprawny.
        """
        try:
            return normalize_and_validate_icd10(value, allow_blank=True)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_functional_diagnosis(self, value: object) -> str:
        """Waliduje diagnozę funkcjonalną podczas tworzenia epizodu.

        Args:
            value (object): Wartość diagnozy funkcjonalnej.

        Returns:
            str: Znormalizowany tekst diagnozy funkcjonalnej.

        Raises:
            serializers.ValidationError: Gdy treść jest zbyt długa.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=FUNCTIONAL_DIAGNOSIS_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_summary_note(self, value: object) -> str:
        """Waliduje notatkę podsumowującą przy tworzeniu epizodu.

        Args:
            value (object): Treść notatki podsumowującej.

        Returns:
            str: Znormalizowana notatka.

        Raises:
            serializers.ValidationError: Gdy treść przekracza dozwolony limit.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=5000,
                too_long_message=SUMMARY_TOO_LONG,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje kompetencje fizjoterapeuty przy tworzeniu epizodu leczenia.

        Args:
            attrs (dict[str, object]): Dane wejściowe do utworzenia epizodu.

        Returns:
            dict[str, object]: Zwalidowany słownik danych.

        Raises:
            serializers.ValidationError: Gdy dane są niepoprawne lub fizjoterapeuta nie ma wymaganych uprawnień.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
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


class PatientEpisodeSerializer(serializers.ModelSerializer):
    """Serializator epizodu leczenia tylko do odczytu dla aplikacji pacjenta."""

    status_label = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora epizodu dla pacjenta."""

        model = TreatmentEpisode
        fields = [
            'id', 'icd10_code', 'functional_diagnosis', 'status', 'status_label',
            'summary_note', 'started_at', 'ended_at', 'created_at',
        ]
        read_only_fields = fields

    def get_status_label(self, obj: object) -> str:
        """Zwraca słowną etykietę statusu epizodu leczenia.

        Args:
            obj (object): Obiekt epizodu leczenia.

        Returns:
            str: Przetłumaczona etykieta statusu.
        """
        status_val = obj.status if hasattr(obj, 'status') else ''
        return dict(EpisodeStatus.choices).get(status_val, status_val)


class BodyAreaPainSerializer(serializers.ModelSerializer):
    """Serializator natężenia bólu i celów terapeutycznych w obszarach ciała."""

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
        """Metadane serializatora bólu obszarów ciała."""

        model = BodyAreaPain
        fields = [
            'id', 'episode', 'body_region', 'view_side',
            'vas_score', 'pain_character', 'treatment_targets', 'recorded_at',
        ]
        read_only_fields = ['id', 'episode', 'recorded_at']

    def validate_body_region(self, value: object) -> str:
        """Waliduje i formatuje nazwę obszaru ciała.

        Args:
            value (object): Nazwa obszaru ciała.

        Returns:
            str: Oczyszczona nazwa obszaru ciała.

        Raises:
            serializers.ValidationError: Gdy obszar ciała jest pusty.
        """
        region = ' '.join(str(value).split())
        if not region:
            raise serializers.ValidationError('Wskaż obszar ciała.')
        return region

    def validate_pain_character(self, value: object) -> list[str]:
        """Waliduje listę z opisem charakteru bólu.

        Args:
            value (object): Wartość pola charakteru bólu.

        Returns:
            list[str]: Zwalidowana lista charakterów bólu.

        Raises:
            serializers.ValidationError: Gdy podana wartość nie jest listą niepustych ciągów tekstowych.
        """
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

    def validate_treatment_targets(self, value: object) -> list[str]:
        """Waliduje listę celów terapeutycznych.

        Args:
            value (object): Wartość pola celów terapii.

        Returns:
            list[str]: Zwalidowana lista celów terapii.

        Raises:
            serializers.ValidationError: Gdy wartość nie jest listą tekstów.
        """
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
    """Serializator wpisu notatki klinicznej z wizyty."""

    therapist_name = serializers.SerializerMethodField()
    content = serializers.CharField(
        error_messages={
            'blank': NOTE_REQUIRED,
            'required': NOTE_REQUIRED,
        },
    )

    class Meta:
        """Metadane serializatora notatki z wizyty."""

        model = VisitNote
        fields = ['id', 'episode', 'therapist', 'therapist_name', 'visit', 'content', 'created_at']
        read_only_fields = ['id', 'episode', 'therapist', 'created_at']

    def get_therapist_name(self, obj: object) -> str:
        """Zwraca imię i nazwisko autora notatki.

        Args:
            obj (object): Obiekt notatki z wizyty.

        Returns:
            str: Imię i nazwisko fizjoterapeuty.
        """
        return _get_therapist_name(obj)

    def validate_content(self, value: object) -> str:
        """Waliduje treść notatki medycznej z wizyty.

        Args:
            value (object): Treść notatki.

        Returns:
            str: Znormalizowana treść notatki.

        Raises:
            serializers.ValidationError: Gdy treść jest pusta lub za długa.
        """
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

    def validate_visit(self, visit: object) -> object:
        """Waliduje czy powiązana wizyta należy do tego samego pacjenta i epizodu.

        Args:
            visit (object): Obiekt wizyty.

        Returns:
            object: Zweryfikowany obiekt wizyty.

        Raises:
            serializers.ValidationError: Gdy wizyta nie pasuje do pacjenta lub epizodu.
        """
        if visit is None:
            return visit
        episode = self.context.get('episode')
        if episode is None:
            return visit
        patient_id = visit.patient_id if hasattr(visit, 'patient_id') else None
        if patient_id != episode.patient_id:
            raise serializers.ValidationError(
                'Wizyta nie należy do pacjenta tego epizodu.'
            )
        episode_id = visit.episode_id if hasattr(visit, 'episode_id') else None
        if episode_id is not None and episode_id != episode.id:
            raise serializers.ValidationError(
                'Wizyta nie należy do tego epizodu.'
            )
        return visit


class DiagnosticRecommendationSerializer(serializers.ModelSerializer):
    """Serializator opinii / rekomendacji diagnostycznej fizjoterapeuty."""

    recommendation_type = serializers.ChoiceField(choices=RecommendationType.choices)
    funding_hint = serializers.ChoiceField(
        choices=FundingHint.choices,
        required=False,
        default=FundingHint.NFZ_VIA_DOCTOR,
    )
    therapist_name = serializers.SerializerMethodField()
    is_read_only = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora rekomendacji diagnostycznej."""

        model = DiagnosticRecommendation
        fields = [
            'id', 'episode', 'therapist', 'therapist_name', 'is_read_only',
            'recommendation_type', 'target_specialty',
            'body_area', 'justification', 'red_flags_noted', 'funding_hint', 'created_at',
        ]
        read_only_fields = ['id', 'episode', 'therapist', 'created_at']

    def get_therapist_name(self, obj: object) -> str:
        """Zwraca dane osobowe autora rekomendacji.

        Args:
            obj (object): Obiekt rekomendacji.

        Returns:
            str: Imię i nazwisko fizjoterapeuty.
        """
        return _get_therapist_name(obj)

    def get_is_read_only(self, obj: object) -> bool:
        """Sprawdza, czy rekomendacja diagnostyczna jest tylko do odczytu.

        Args:
            obj (object): Obiekt rekomendacji.

        Returns:
            bool: True jeśli obiekt utworzył inny fizjoterapeuta.
        """
        return _is_read_only(self, obj)

    def validate_justification(self, value: object) -> str:
        """Waliduje uzasadnienie kliniczne rekomendacji.

        Args:
            value (object): Treść uzasadnienia.

        Returns:
            str: Znormalizowany tekst uzasadnienia.

        Raises:
            serializers.ValidationError: Gdy uzasadnienie jest puste lub za długie.
        """
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

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje uprawnienia fizjoterapeuty do wystawiania rekomendacji diagnostycznych.

        Args:
            attrs (dict[str, object]): Dane zlecenia rekomendacji.

        Returns:
            dict[str, object]: Zwalidowane dane.

        Raises:
            serializers.ValidationError: Gdy dane są niepoprawne lub fizjoterapeuta nie ma kompetencji.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        attrs = super().validate(attrs)
        request = self.context.get('request')
        therapist = request.user.therapist_profile
        snapshot = snapshot_for_therapist(therapist)
        if not snapshot.allows('imaging_recommendation'):
            raise serializers.ValidationError(
                deny_message('imaging_recommendation', snapshot),
            )

        rec_type = attrs.get('recommendation_type')
        if rec_type is None and self.instance is not None:
            rec_type = self.instance.recommendation_type

        funding = attrs.get('funding_hint')
        if funding is None and self.instance is not None:
            funding = self.instance.funding_hint
        if funding is None:
            funding = FundingHint.NFZ_VIA_DOCTOR

        if rec_type in (
            RecommendationType.IMAGING_MRI,
            RecommendationType.IMAGING_CT,
            RecommendationType.IMAGING_RTG,
        ):
            if rec_type == RecommendationType.IMAGING_RTG:
                attrs['funding_hint'] = FundingHint.NFZ_VIA_DOCTOR
            elif funding == FundingHint.PRIVATE and rec_type == RecommendationType.IMAGING_MRI:
                attrs['funding_hint'] = FundingHint.PRIVATE
            else:
                attrs['funding_hint'] = FundingHint.NFZ_VIA_DOCTOR
        return attrs


class MedicalDeviceOrderSerializer(serializers.ModelSerializer):
    """Serializator zlecenia na wyrób medyczny (e-ZWM)."""

    device_code = serializers.CharField(max_length=40)
    side = serializers.ChoiceField(choices=BodySide.choices, required=False, default=BodySide.NA)
    quantity = serializers.IntegerField(min_value=1, max_value=24, default=1)
    access_code = serializers.CharField(required=False, allow_blank=True, default='')
    status = serializers.ChoiceField(
        choices=DeviceOrderStatus.choices,
        required=False,
        default=DeviceOrderStatus.ISSUED,
    )
    therapist_name = serializers.SerializerMethodField()
    is_read_only = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora zlecenia na wyrób medyczny."""

        model = MedicalDeviceOrder
        fields = [
            'id', 'episode', 'patient', 'therapist', 'therapist_name', 'is_read_only',
            'device_code', 'device_group',
            'device_name', 'side', 'quantity', 'icd10_code', 'access_code',
            'status', 'notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'episode', 'patient', 'therapist', 'device_group',
            'device_name', 'created_at',
        ]

    def get_therapist_name(self, obj: object) -> str:
        """Zwraca dane osobowe fizjoterapeuty składającego zlecenie.

        Args:
            obj (object): Obiekt zlecenia.

        Returns:
            str: Imię i nazwisko fizjoterapeuty.
        """
        return _get_therapist_name(obj)

    def get_is_read_only(self, obj: object) -> bool:
        """Sprawdza, czy zlecenie na wyrób jest w trybie tylko do odczytu.

        Args:
            obj (object): Obiekt zlecenia.

        Returns:
            bool: True jeśli zalogowany użytkownik nie stworzył zlecenia.
        """
        return _is_read_only(self, obj)

    def validate_access_code(self, value: object) -> str:
        """Waliduje 4-cyfrowy kod dostępu z NFZ.

        Args:
            value (object): Kod dostępu.

        Returns:
            str: Znormalizowany 4-cyfrowy kod lub pusty napis.

        Raises:
            serializers.ValidationError: Gdy kod nie ma dokładnie 4 cyfr.
        """
        cleaned = (str(value) if value is not None else '').strip()
        if not cleaned:
            return ''
        if not cleaned.isdigit() or len(cleaned) != 4:
            raise serializers.ValidationError(
                'Kod dostępu e-ZWM musi składać się z dokładnie 4 cyfr '
                '(z SMS/e-mail/druku NFZ) albo pozostać pusty.',
            )
        return cleaned

    def validate_icd10_code(self, value: object) -> str:
        """Waliduje kod ICD-10 dla wyrobu medycznego.

        Args:
            value (object): Kod ICD-10.

        Returns:
            str: Znormalizowany kod ICD-10.

        Raises:
            serializers.ValidationError: Gdy kod jest niepoprawny lub pusty.
        """
        try:
            return normalize_and_validate_icd10(value, allow_blank=False)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_notes(self, value: object) -> str:
        """Waliduje notatkę do zlecenia wyrobu medycznego.

        Args:
            value (object): Treść notatki.

        Returns:
            str: Znormalizowany tekst notatki.

        Raises:
            serializers.ValidationError: Gdy tekst przekracza limit znaków.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message='Notatka do zlecenia może mieć co najwyżej 2000 znaków.',
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje poziom kwalifikacji fizjoterapeuty dla wskazanego wyrobu medycznego.

        Args:
            attrs (dict[str, object]): Dane zlecenia wyrobu.

        Returns:
            dict[str, object]: Zwalidowane dane z podpiętą grupą i nazwą wyrobu.

        Raises:
            serializers.ValidationError: Gdy wyrobu nie ma w katalogu lub kwalifikacje są niewystarczające.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        attrs = super().validate(attrs)
        request = self.context.get('request')
        therapist = request.user.therapist_profile
        snapshot = snapshot_for_therapist(therapist)

        device_code = attrs.get('device_code')
        if device_code is None and self.instance is not None:
            device_code = self.instance.device_code

        device = get_device(str(device_code) if device_code is not None else '')
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
    """Serializator odmowy wykonania zlecenia lekarskiego (art. 6 ust. 2 u.o.z.f.)."""

    therapist_name = serializers.SerializerMethodField()
    is_read_only = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora odmowy wykonania zlecenia lekarskiego."""

        model = PhysicianOrderRefusal
        fields = [
            'id', 'episode', 'therapist', 'therapist_name', 'is_read_only',
            'physician_order_description',
            'refusal_reason', 'physician_notified', 'created_at',
        ]
        read_only_fields = ['id', 'episode', 'therapist', 'created_at']

    def get_therapist_name(self, obj: object) -> str:
        """Zwraca dane osobowe fizjoterapeuty zgłaszającego odmowę.

        Args:
            obj (object): Obiekt odmowy wykonania zlecenia.

        Returns:
            str: Imię i nazwisko fizjoterapeuty.
        """
        return _get_therapist_name(obj)

    def get_is_read_only(self, obj: object) -> bool:
        """Sprawdza, czy odmowa wykonania zlecenia jest tylko do odczytu.

        Args:
            obj (object): Obiekt odmowy.

        Returns:
            bool: True jeśli wpis należy do innego fizjoterapeuty.
        """
        return _is_read_only(self, obj)

    def validate_physician_order_description(self, value: object) -> str:
        """Waliduje opis zlecenia lekarskiego.

        Args:
            value (object): Opis zlecenia lekarskiego.

        Returns:
            str: Znormalizowany opis zlecenia lekarskiego.

        Raises:
            serializers.ValidationError: Gdy opis jest pusty lub zbyt długi.
        """
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

    def validate_refusal_reason(self, value: object) -> str:
        """Waliduje powód odmowy wykonania zlecenia.

        Args:
            value (object): Powód odmowy.

        Returns:
            str: Znormalizowany powód odmowy.

        Raises:
            serializers.ValidationError: Gdy powód jest pusty lub zbyt długi.
        """
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
    """Serializator skierowania do programu Recepta na Ruch."""

    therapist_name = serializers.SerializerMethodField()
    is_read_only = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora skierowania Recepta na Ruch."""

        model = ReceptaNaRuchReferral
        fields = [
            'id', 'patient', 'therapist', 'therapist_name', 'is_read_only',
            'episode', 'readiness_confirmed',
            'activity_notes', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'therapist', 'created_at']

    def get_therapist_name(self, obj: object) -> str:
        """Zwraca dane osobowe fizjoterapeuty wystawiającego skierowanie.

        Args:
            obj (object): Obiekt skierowania.

        Returns:
            str: Imię i nazwisko fizjoterapeuty.
        """
        return _get_therapist_name(obj)

    def get_is_read_only(self, obj: object) -> bool:
        """Sprawdza, czy skierowanie jest w trybie tylko do odczytu.

        Args:
            obj (object): Obiekt skierowania.

        Returns:
            bool: True jeśli autorem jest inny fizjoterapeuta.
        """
        return _is_read_only(self, obj)

    def validate_activity_notes(self, value: object) -> str:
        """Waliduje uwagi dotyczące aktywności fizycznej.

        Args:
            value (object): Notatki dotyczące aktywności.

        Returns:
            str: Znormalizowany tekst notatek.

        Raises:
            serializers.ValidationError: Gdy treść przekracza dopuszczalną długość.
        """
        try:
            return normalize_optional_text(
                value,
                max_length=2000,
                too_long_message='Notatka może mieć co najwyżej 2000 znaków.',
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Waliduje potwierdzenie gotowości do wysiłku pacjenta.

        Args:
            attrs (dict[str, object]): Słownik z danymi skierowania.

        Returns:
            dict[str, object]: Zwalidowane dane.

        Raises:
            serializers.ValidationError: Gdy dane są niepoprawne lub nie potwierdzono gotowości do wysiłku.
        """
        if not isinstance(attrs, dict):
            raise serializers.ValidationError('Dane wejściowe muszą być słownikiem.')
        attrs = super().validate(attrs)
        confirmed = attrs.get('readiness_confirmed')
        if confirmed is None and self.instance is not None:
            confirmed = self.instance.readiness_confirmed
        if not confirmed:
            raise serializers.ValidationError({
                'readiness_confirmed': (
                    'Potwierdź weryfikację gotowości do wysiłku '
                    '(kwestionariusz / ocena stanu zdrowia).'
                ),
            })
        return attrs
