from __future__ import annotations

import contextlib

from django.core.exceptions import ObjectDoesNotExist

from documents.models import MedicalDocument
from treatment.models import (
    DEVICE_ORDER_DISCLAIMER,
    DEVICE_PICKUP_HINT,
    DeviceOrderStatus,
    DiagnosticRecommendation,
    FundingHint,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    RecommendationType,
)

KIND_RECOMMENDATION: str = 'recommendation'
KIND_DEVICE_ORDER: str = 'device_order'
KIND_REFUSAL: str = 'refusal'
KIND_RECEPTA: str = 'recepta_na_ruch'
KIND_PDF: str = 'pdf'

KIND_LABELS: dict[str, str] = {
    KIND_RECOMMENDATION: 'Kierowanie',
    KIND_DEVICE_ORDER: 'Wyrób medyczny',
    KIND_REFUSAL: 'Odmowa zabiegu',
    KIND_RECEPTA: 'Recepta na Ruch',
    KIND_PDF: 'Dokument PDF',
}

REFUSAL_PATIENT_NOTICE: str = (
    'Twój fizjoterapeuta odmówił wykonania zlecenia lekarskiego. '
    'Skonsultuj się z lekarzem prowadzącym.'
)



def _therapist_name(therapist: object) -> str:
    """Tworzy czytelne imię i nazwisko fizjoterapeuty lub zwraca jego e-mail.

    Args:
        therapist (object): Obiekt fizjoterapeuty.

    Returns:
        str: Imię i nazwisko lub e-mail.
    """
    if therapist is None:
        return ''
    user = therapist.user if hasattr(therapist, 'user') else None
    if user is None:
        return ''
    first_name = user.first_name if hasattr(user, 'first_name') else ''
    last_name = user.last_name if hasattr(user, 'last_name') else ''
    email = user.email if hasattr(user, 'email') else ''
    name = f'{first_name} {last_name}'.strip()
    return name or email


def _choice_label(choices: object, value: str) -> str:
    """Zwraca etykietę opcji z listy wyboru Django Choices.

    Args:
        choices (object): Lista lub krotka opcji wyboru (tuple/list choices).
        value (str): Wartość klucza.

    Returns:
        str: Etykieta opcji lub oryginalna wartość.

    Raises:
        TypeError: Gdy argumenty mają niepoprawne typy.
    """
    if not isinstance(choices, (list, tuple, dict)):
        raise TypeError('Parametr choices musi być listą, krotką lub słownikiem.')
    if not isinstance(value, str):
        raise TypeError('Parametr value musi być ciągiem znaków.')
    return dict(choices).get(value, value)


def _item(
    *,
    kind: str,
    obj_id: object,
    title: str,
    summary: str,
    created_at: object,
    therapist_name: str,
    episode_id: object = None,
    status: str | None = None,
    file_url: str | None = None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    """Buduje ustrukturyzowany słownik elementu dokumentacji pacjenta.

    Args:
        kind (str): Rodzaj dokumentu.
        obj_id (object): Identyfikator obiektu.
        title (str): Tytuł dokumentu.
        summary (str): Podsumowanie dokumentu.
        created_at (object): Data utworzenia.
        therapist_name (str): Imię i nazwisko wystawiającego fizjoterapeuty.
        episode_id (object): Opcjonalny identyfikator epizodu leczenia.
        status (str | None): Opcjonalny status dokumentu.
        file_url (str | None): Opcjonalna ścieżka pobierania pliku.
        details (dict[str, object] | None): Szczegółowe metadane dokumentu.

    Returns:
        dict[str, object]: Słownik pojedynczej pozycji w historii dokumentacji.

    Raises:
        TypeError: Gdy parametry mają niepoprawny typ.
    """
    if not isinstance(kind, str):
        raise TypeError('Parametr kind musi być ciągiem znaków.')
    if not isinstance(title, str):
        raise TypeError('Parametr title musi być ciągiem znaków.')
    if not isinstance(summary, str):
        raise TypeError('Parametr summary musi być ciągiem znaków.')
    if not isinstance(therapist_name, str):
        raise TypeError('Parametr therapist_name musi być ciągiem znaków.')
    if status is not None and not isinstance(status, str):
        raise TypeError('Parametr status musi być ciągiem znaków lub None.')
    if file_url is not None and not isinstance(file_url, str):
        raise TypeError('Parametr file_url musi być ciągiem znaków lub None.')
    if details is not None and not isinstance(details, dict):
        raise TypeError('Parametr details musi być słownikiem lub None.')
    return {
        'id': str(obj_id),
        'kind': kind,
        'kind_label': KIND_LABELS[kind],
        'title': title,
        'summary': summary,
        'created_at': created_at,
        'therapist_name': therapist_name,
        'episode_id': str(episode_id) if episode_id else None,
        'status': status,
        'file_url': file_url,
        'details': details or {},
    }


def serialize_recommendation(rec: DiagnosticRecommendation) -> dict[str, object]:
    """Serializuje rekomendację diagnostyczną do postaci podsumowania w historii pacjenta.

    Args:
        rec (DiagnosticRecommendation): Obiekt rekomendacji.

    Returns:
        dict[str, object]: Zserializowany słownik danych rekomendacji.

    Raises:
        TypeError: Gdy parametr rec ma nieprawidłowy typ.
    """
    if not isinstance(rec, DiagnosticRecommendation):
        raise TypeError('Parametr rec musi być instancją DiagnosticRecommendation.')
    type_label = _choice_label(RecommendationType.choices, rec.recommendation_type)
    parts = [type_label]
    if rec.target_specialty:
        parts.append(rec.target_specialty)
    if rec.body_area:
        parts.append(rec.body_area)
    summary = ' · '.join(parts)
    return _item(
        kind=KIND_RECOMMENDATION,
        obj_id=rec.id,
        title=type_label,
        summary=summary,
        created_at=rec.created_at,
        therapist_name=_therapist_name(rec.therapist),
        episode_id=rec.episode_id,
        details={
            'recommendation_type': rec.recommendation_type,
            'recommendation_type_label': type_label,
            'target_specialty': rec.target_specialty,
            'body_area': rec.body_area,
            'justification': rec.justification,
            'red_flags_noted': rec.red_flags_noted,
            'funding_hint': rec.funding_hint,
            'funding_hint_label': _choice_label(FundingHint.choices, rec.funding_hint),
            'disclaimer': (
                'To opinia fizjoterapeuty ułatwiająca diagnostykę. '
                'Nie jest formalnym e-skierowaniem NFZ na badania obrazowe.'
            ),
        },
    )


def serialize_device_order(order: MedicalDeviceOrder) -> dict[str, object]:
    """Serializuje zlecenie na wyrób medyczny do postaci podsumowania w historii pacjenta.

    Args:
        order (MedicalDeviceOrder): Obiekt zlecenia wyrobu.

    Returns:
        dict[str, object]: Zserializowany słownik zlecenia wyrobu medycznego.

    Raises:
        TypeError: Gdy parametr order ma nieprawidłowy typ.
    """
    if not isinstance(order, MedicalDeviceOrder):
        raise TypeError('Parametr order musi być instancją MedicalDeviceOrder.')
    side_label = _choice_label(
        (
            ('LEFT', 'lewa'),
            ('RIGHT', 'prawa'),
            ('BOTH', 'obustronnie'),
            ('NA', 'nie dotyczy'),
        ),
        order.side,
    )
    access_code = (order.access_code or '').strip()
    if access_code:
        summary = f'{order.device_name} · kod odbioru: {access_code}'
    else:
        summary = f'{order.device_name} · strona: {side_label}'
    return _item(
        kind=KIND_DEVICE_ORDER,
        obj_id=order.id,
        title=order.device_name,
        summary=summary,
        created_at=order.created_at,
        therapist_name=_therapist_name(order.therapist),
        episode_id=order.episode_id,
        status=order.status,
        details={
            'device_code': order.device_code,
            'device_group': order.device_group,
            'device_name': order.device_name,
            'side': order.side,
            'side_label': side_label,
            'quantity': order.quantity,
            'icd10_code': order.icd10_code,
            'access_code': access_code,
            'pickup_hint': DEVICE_PICKUP_HINT if access_code else (
                'Kod dostępu 4-cyfrowy znajdziesz w SMS/e-mailu z NFZ, '
                'na druku informacyjnym albo w IKP (Apteczka). '
                'Terapeuta może też wpisać go tutaj po wystawieniu e-ZWM.'
            ),
            'notes': order.notes,
            'disclaimer': DEVICE_ORDER_DISCLAIMER,
        },
    )


def serialize_refusal(refusal: PhysicianOrderRefusal) -> dict[str, object]:
    """Serializuje odmowę wykonania zlecenia lekarskiego.

    Args:
        refusal (PhysicianOrderRefusal): Obiekt odmowy zabiegu.

    Returns:
        dict[str, object]: Zserializowany słownik danych odmowy.

    Raises:
        TypeError: Gdy parametr refusal ma nieprawidłowy typ.
    """
    if not isinstance(refusal, PhysicianOrderRefusal):
        raise TypeError('Parametr refusal musi być instancją PhysicianOrderRefusal.')
    summary = refusal.physician_order_description[:160]
    if len(refusal.physician_order_description) > 160:
        summary = f'{summary}…'
    return _item(
        kind=KIND_REFUSAL,
        obj_id=refusal.id,
        title='Informacja o odmowie zabiegu',
        summary=summary,
        created_at=refusal.created_at,
        therapist_name=_therapist_name(refusal.therapist),
        episode_id=refusal.episode_id,
        details={
            'physician_order_description': refusal.physician_order_description,
            'refusal_reason': refusal.refusal_reason,
            'physician_notified': refusal.physician_notified,
            'patient_notice': REFUSAL_PATIENT_NOTICE,
        },
    )


def serialize_recepta(ref: ReceptaNaRuchReferral) -> dict[str, object]:
    """Serializuje skierowanie do programu Recepta na Ruch.

    Args:
        ref (ReceptaNaRuchReferral): Obiekt skierowania.

    Returns:
        dict[str, object]: Zserializowane dane skierowania.

    Raises:
        TypeError: Gdy parametr ref ma nieprawidłowy typ.
    """
    if not isinstance(ref, ReceptaNaRuchReferral):
        raise TypeError('Parametr ref musi być instancją ReceptaNaRuchReferral.')
    summary = ref.activity_notes.strip() or 'Skierowanie do programu Recepta na Ruch'
    return _item(
        kind=KIND_RECEPTA,
        obj_id=ref.id,
        title='Recepta na Ruch',
        summary=summary[:200],
        created_at=ref.created_at,
        therapist_name=_therapist_name(ref.therapist),
        episode_id=ref.episode_id,
        status=ref.status,
        details={
            'readiness_confirmed': ref.readiness_confirmed,
            'activity_notes': ref.activity_notes,
            'next_step': (
                'Dokończ zapis do programu w aplikacji mojeIKP '
                '(lub u lekarza / w placówce prowadzącej program).'
            ),
        },
    )


def serialize_pdf(doc: MedicalDocument) -> dict[str, object]:
    """Serializuje udostępniony plik PDF dokumentu medycznego.

    Args:
        doc (MedicalDocument): Obiekt dokumentu medycznego.

    Returns:
        dict[str, object]: Zserializowany słownik pliku PDF.

    Raises:
        TypeError: Gdy parametr doc ma nieprawidłowy typ.
    """
    if not isinstance(doc, MedicalDocument):
        raise TypeError('Parametr doc musi być instancją MedicalDocument.')
    uploader = doc.uploaded_by
    therapist_name = f'{uploader.first_name} {uploader.last_name}'.strip() or uploader.email
    with contextlib.suppress(ObjectDoesNotExist):
        therapist_name = _therapist_name(uploader.therapist_profile)
    return _item(
        kind=KIND_PDF,
        obj_id=doc.id,
        title=doc.title,
        summary='Plik PDF udostępniony przez terapeutę',
        created_at=doc.created_at,
        therapist_name=therapist_name,
        episode_id=doc.episode_id,
        file_url=f'/api/v1/{doc.id}/download/',
        details={
            'mime_type': doc.mime_type,
            'visit_id': str(doc.visit_id) if doc.visit_id else None,
        },
    )


def build_clinical_documents_for_patient(patient: object, *, kind: str | None = None) -> list[dict[str, object]]:
    """Zwraca chronologiczną listę dokumentów widocznych dla pacjenta.

    Args:
        patient (object): Profil pacjenta.
        kind (str | None): Opcjonalny typ filtrujący dokumenty.

    Returns:
        list[dict[str, object]]: Podsumowania wizyt pacjenta.

    Raises:
        TypeError: Gdy parametr patient lub kind ma nieprawidłowy typ.
    """
    if patient is None:
        raise TypeError('Parametr patient nie może być None.')
    if kind is not None and not isinstance(kind, str):
        raise TypeError('Parametr kind musi być ciągiem znaków lub None.')

    items: list[dict[str, object]] = []

    if kind in (None, KIND_RECOMMENDATION):
        recs = (
            DiagnosticRecommendation.objects.filter(episode__patient=patient)
            .select_related('therapist__user', 'episode')
            .order_by('-created_at')
        )
        items.extend(serialize_recommendation(r) for r in recs)

    if kind in (None, KIND_DEVICE_ORDER):
        orders = (
            MedicalDeviceOrder.objects.filter(
                patient=patient,
                status=DeviceOrderStatus.ISSUED,
            )
            .select_related('therapist__user')
            .order_by('-created_at')
        )
        items.extend(serialize_device_order(o) for o in orders)

    if kind in (None, KIND_REFUSAL):
        refusals = (
            PhysicianOrderRefusal.objects.filter(episode__patient=patient)
            .select_related('therapist__user')
            .order_by('-created_at')
        )
        items.extend(serialize_refusal(r) for r in refusals)

    if kind in (None, KIND_RECEPTA):
        refs = (
            ReceptaNaRuchReferral.objects.filter(
                patient=patient,
                status=DeviceOrderStatus.ISSUED,
            )
            .select_related('therapist__user')
            .order_by('-created_at')
        )
        items.extend(serialize_recepta(r) for r in refs)

    if kind in (None, KIND_PDF):
        docs = (
            MedicalDocument.objects.filter(patient=patient)
            .select_related('uploaded_by')
            .order_by('-created_at')
        )
        items.extend(serialize_pdf(d) for d in docs)

    items.sort(key=lambda row: row['created_at'], reverse=True)
    return items
