"""Assemble a patient data-export payload (Art. 15 metadata, not file bytes)."""

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


def build_patient_export(user, profile) -> dict:
    consents = Consent.objects.filter(user=user)
    visits = Visit.objects.filter(patient=profile).select_related('therapy_type')
    episodes = TreatmentEpisode.objects.filter(patient=profile)
    documents = MedicalDocument.objects.filter(patient=profile)
    assignments = ExerciseAssignment.objects.filter(patient=profile).select_related('exercise')
    device_orders = MedicalDeviceOrder.objects.filter(patient=profile)
    referrals = ReceptaNaRuchReferral.objects.filter(patient=profile)
    recommendations = DiagnosticRecommendation.objects.filter(episode__patient=profile)
    refusals = PhysicianOrderRefusal.objects.filter(episode__patient=profile)

    payload = {
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
                'patient_note': visit.patient_note,
                'cancel_reason': visit.cancel_reason,
            }
            for visit in visits
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
            for episode in episodes.prefetch_related('body_pain_entries')
        ],
        'documents': [
            {
                'id': str(document.id),
                'title': document.title,
                'mime_type': document.mime_type,
                'created_at': document.created_at.isoformat(),
                'file_url': document.file_url,
            }
            for document in documents
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
            for assignment in assignments.prefetch_related('completions')
        ],
        'device_orders': [
            {
                'id': str(order.id),
                'device_code': order.device_code,
                'device_name': order.device_name,
                'status': order.status,
            }
            for order in device_orders
        ],
        'diagnostic_recommendations': [
            {
                'id': str(item.id),
                'recommendation_type': item.recommendation_type,
                'justification': item.justification,
            }
            for item in recommendations
        ],
        'physician_order_refusals': [
            {
                'id': str(item.id),
                'refusal_reason': item.refusal_reason,
            }
            for item in refusals
        ],
        'recepta_na_ruch': [
            {
                'id': str(item.id),
                'status': item.status,
                'activity_notes': item.activity_notes,
            }
            for item in referrals
        ],
    }
    payload.update(notification_export_payload(user))
    return payload
