from django.utils import timezone

from documents.models import MedicalDocument
from exercises.models import ExerciseAssignment
from notifications.privacy_export import notification_export_payload
from patients.serializers import ConsentSerializer, MeProfileSerializer
from privacy.models import Consent
from scheduling.models import Visit
from treatment.models import (
    DiagnosticRecommendation,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
)


def build_patient_export(user: object, profile: object) -> dict[str, object]:
    """Buduje kompletny słownik eksportu danych osobowych pacjenta (zgodnie z Art. 15 RODO).

    Args:
        user (object): Obiekt użytkownika Django.
        profile (object): Obiekt profilu pacjenta (PatientProfile).

    Returns:
        dict[str, object]: Słownik zawierający zagregowane dane pacjenta.

    Raises:
        TypeError: Gdy argument user lub profile jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if profile is None:
        raise TypeError("Argument 'profile' nie może być None.")

    consents: object = Consent.objects.filter(user=user)
    visits: object = Visit.objects.filter(patient=profile).select_related('therapy_type')
    episodes: object = TreatmentEpisode.objects.filter(patient=profile)
    documents: object = MedicalDocument.objects.filter(patient=profile)
    assignments: object = ExerciseAssignment.objects.filter(patient=profile).select_related('exercise')
    device_orders: object = MedicalDeviceOrder.objects.filter(patient=profile)
    referrals: object = ReceptaNaRuchReferral.objects.filter(patient=profile)
    recommendations: object = DiagnosticRecommendation.objects.filter(episode__patient=profile)
    refusals: object = PhysicianOrderRefusal.objects.filter(episode__patient=profile)

    payload: dict[str, object] = {
        'exported_at': timezone.now().isoformat(),
        'profile': MeProfileSerializer(profile).data,
        'consents': ConsentSerializer(consents, many=True).data,
        'visits': [
            {
                'id': str(visit.id),
                'start_at': visit.start_at.isoformat(),
                'end_at': visit.end_at.isoformat(),
                'status': visit.status,
                'therapy_type': visit.therapy_type.name if visit.therapy_type_id else None,
                'location_address': visit.location_address,
                'prep_instructions': visit.prep_instructions,
                'patient_summary': visit.patient_summary,
                'patient_note': visit.patient_note,
                'cancel_reason': visit.cancel_reason,
            }
            for visit in visits  # type: ignore[union-attr]
        ],
        'episodes': [
            {
                'id': str(episode.id),
                'icd10_code': episode.icd10_code,
                'functional_diagnosis': episode.functional_diagnosis,
                'status': episode.status,
                'summary_note': episode.summary_note,
                'started_at': episode.started_at.isoformat() if episode.started_at else None,
                'ended_at': episode.ended_at.isoformat() if episode.ended_at else None,
                'body_pain': [
                    {
                        'body_region': entry.body_region,
                        'view_side': entry.view_side,
                        'vas_score': entry.vas_score,
                        'pain_character': entry.pain_character,
                        'treatment_targets': entry.treatment_targets,
                    }
                    for entry in episode.body_pain_entries.all()
                ],
            }
            for episode in episodes.prefetch_related('body_pain_entries')  # type: ignore[union-attr]
        ],
        'documents': [
            {
                'id': str(document.id),
                'title': document.title,
                'mime_type': document.mime_type,
                'created_at': document.created_at.isoformat(),
                'file_url': document.file_url,
            }
            for document in documents  # type: ignore[union-attr]
        ],
        'exercise_assignments': [
            {
                'id': str(assignment.id),
                'exercise_title': assignment.exercise.title,
                'dosage': assignment.dosage,
                'start_date': assignment.start_date.isoformat(),
                'end_date': assignment.end_date.isoformat(),
                'completions': [
                    {
                        'completed_on': completion.completed_on.isoformat(),
                        'done': completion.done,
                    }
                    for completion in assignment.completions.all()
                ],
            }
            for assignment in assignments.prefetch_related('completions')  # type: ignore[union-attr]
        ],
        'device_orders': [
            {
                'id': str(order.id),
                'device_code': order.device_code,
                'device_name': order.device_name,
                'access_code': order.access_code,
                'status': order.status,
            }
            for order in device_orders  # type: ignore[union-attr]
        ],
        'diagnostic_recommendations': [
            {
                'id': str(item.id),
                'recommendation_type': item.recommendation_type,
                'justification': item.justification,
            }
            for item in recommendations  # type: ignore[union-attr]
        ],
        'physician_order_refusals': [
            {
                'id': str(item.id),
                'refusal_reason': item.refusal_reason,
            }
            for item in refusals  # type: ignore[union-attr]
        ],
        'recepta_na_ruch': [
            {
                'id': str(item.id),
                'status': item.status,
                'activity_notes': item.activity_notes,
            }
            for item in referrals  # type: ignore[union-attr]
        ],
    }
    payload.update(notification_export_payload(user))
    return payload
