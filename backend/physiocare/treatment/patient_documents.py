"""
Budowa skrzynki dokumentacji klinicznej dla pacjenta.

Wystawienie przez terapeutę = automatyczna widoczność dla pacjenta
(bez osobnego kroku „wyślij PDF”).
"""

from __future__ import annotations

import contextlib
from typing import Any

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

KIND_RECOMMENDATION = 'recommendation'
KIND_DEVICE_ORDER = 'device_order'
KIND_REFUSAL = 'refusal'
KIND_RECEPTA = 'recepta_na_ruch'
KIND_PDF = 'pdf'

KIND_LABELS = {
    KIND_RECOMMENDATION: 'Kierowanie',
    KIND_DEVICE_ORDER: 'Wyrób medyczny',
    KIND_REFUSAL: 'Odmowa zabiegu',
    KIND_RECEPTA: 'Recepta na Ruch',
    KIND_PDF: 'Dokument PDF',
}

REFUSAL_PATIENT_NOTICE = (
    'Twój fizjoterapeuta odmówił wykonania zlecenia lekarskiego. '
    'Skonsultuj się z lekarzem prowadzącym.'
)


def _therapist_name(therapist) -> str:
    user = therapist.user
    name = f'{user.first_name} {user.last_name}'.strip()
    return name or user.email


def _choice_label(choices, value: str) -> str:
    return dict(choices).get(value, value)


def _item(
    *,
    kind: str,
    obj_id,
    title: str,
    summary: str,
    created_at,
    therapist_name: str,
    episode_id=None,
    status: str | None = None,
    file_url: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
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


def serialize_recommendation(rec: DiagnosticRecommendation) -> dict[str, Any]:
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


def serialize_device_order(order: MedicalDeviceOrder) -> dict[str, Any]:
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


def serialize_refusal(refusal: PhysicianOrderRefusal) -> dict[str, Any]:
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


def serialize_recepta(ref: ReceptaNaRuchReferral) -> dict[str, Any]:
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


def serialize_pdf(doc: MedicalDocument) -> dict[str, Any]:
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
        # Auth-gated download endpoint (not raw /media/ storage path).
        file_url=f'/api/v1/{doc.id}/download/',
        details={
            'mime_type': doc.mime_type,
            'visit_id': str(doc.visit_id) if doc.visit_id else None,
        },
    )


def build_clinical_documents_for_patient(patient, *, kind: str | None = None) -> list[dict[str, Any]]:
    """Zwraca chronologiczną listę dokumentów widocznych dla pacjenta.

    Podsumowania wizyt (`patient_summary`) celowo nie trafiają tutaj —
    pacjent widzi je wyłącznie na karcie wizyty.
    """
    items: list[dict[str, Any]] = []

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
