import pytest

from documents.models import MedicalDocument
from treatment.models import (
    DeviceOrderStatus,
    DiagnosticRecommendation,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
)


@pytest.mark.django_db
def test_patient_sees_clinical_documents_after_therapist_issues(
    api_client, therapist, patient,
):
    therapist.qualification_level = 'MAGISTER'
    therapist.experience_years = 5
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='M25.5')

    DiagnosticRecommendation.objects.create(
        episode=episode,
        therapist=therapist,
        recommendation_type='SPECIALIST_CONSULTATION',
        target_specialty='Ortopeda',
        body_area='Kolano L',
        justification='Ból i obrzęk po urazie.',
        red_flags_noted=False,
        funding_hint='NFZ_VIA_DOCTOR',
    )
    MedicalDeviceOrder.objects.create(
        episode=episode,
        patient=patient,
        therapist=therapist,
        device_code='J.ANKLE',
        device_group='J',
        device_name='Orteza stawu skokowego',
        side='LEFT',
        quantity=1,
        icd10_code='M25.5',
        status=DeviceOrderStatus.ISSUED,
        notes='Stabilizacja',
    )
    MedicalDeviceOrder.objects.create(
        episode=episode,
        patient=patient,
        therapist=therapist,
        device_code='J.ANKLE',
        device_group='J',
        device_name='Szkic — niewidoczny',
        side='LEFT',
        quantity=1,
        icd10_code='M25.5',
        status=DeviceOrderStatus.DRAFT,
    )
    PhysicianOrderRefusal.objects.create(
        episode=episode,
        therapist=therapist,
        physician_order_description='Masaż w ostrej fazie zapalenia',
        refusal_reason='Przeciwwskazanie miejscowe.',
        physician_notified=True,
    )
    ReceptaNaRuchReferral.objects.create(
        patient=patient,
        therapist=therapist,
        episode=episode,
        readiness_confirmed=True,
        activity_notes='Chód nordic walking 3×/tydz.',
        status=DeviceOrderStatus.ISSUED,
    )
    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Karta oceny funkcjonalnej',
        file_url='/media/documents/karta.pdf',
        mime_type='application/pdf',
        episode=episode,
    )

    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/clinical-documents/')
    assert response.status_code == 200
    assert response.data['count'] == 5
    kinds = {item['kind'] for item in response.data['results']}
    assert kinds == {
        'recommendation',
        'device_order',
        'refusal',
        'recepta_na_ruch',
        'pdf',
    }
    device = next(i for i in response.data['results'] if i['kind'] == 'device_order')
    assert device['title'] == 'Orteza stawu skokowego'
    assert 'Szkic' not in device['title']

    refusal = next(i for i in response.data['results'] if i['kind'] == 'refusal')
    assert 'patient_notice' in refusal['details']
    assert refusal['details']['physician_notified'] is True


@pytest.mark.django_db
def test_patient_clinical_documents_filter_by_kind(api_client, therapist, patient):
    episode = TreatmentEpisode.objects.create(patient=patient)
    ReceptaNaRuchReferral.objects.create(
        patient=patient,
        therapist=therapist,
        episode=episode,
        readiness_confirmed=True,
        activity_notes='Aktywność',
        status=DeviceOrderStatus.ISSUED,
    )

    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/clinical-documents/?kind=recepta_na_ruch')
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['kind'] == 'recepta_na_ruch'


@pytest.mark.django_db
def test_patient_cannot_see_other_patient_clinical_documents(
    api_client, therapist, patient, therapist_b,
):
    other_user = patient.user.__class__.objects.create_user(
        email='other@physiocare.test',
        password='test-pass',
        role='PATIENT',
        first_name='Inny',
        last_name='Pacjent',
    )
    from patients.models import PatientProfile

    other = PatientProfile.objects.create(user=other_user, therapist=therapist_b)
    episode = TreatmentEpisode.objects.create(patient=other)
    DiagnosticRecommendation.objects.create(
        episode=episode,
        therapist=therapist_b,
        recommendation_type='IMAGING_USG',
        justification='Kontrola po urazie.',
    )

    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/clinical-documents/')
    assert response.status_code == 200
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_therapist_cannot_access_patient_clinical_inbox(api_client, therapist):
    api_client.force_authenticate(user=therapist.user)
    response = api_client.get('/api/v1/me/clinical-documents/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_invalid_kind_returns_400(api_client, patient):
    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/clinical-documents/?kind=leki')
    assert response.status_code == 400


@pytest.mark.django_db
def test_therapist_can_delete_clinical_documents(api_client, therapist, patient):
    episode = TreatmentEpisode.objects.create(patient=patient)
    rec = DiagnosticRecommendation.objects.create(
        episode=episode,
        therapist=therapist,
        recommendation_type='SPECIALIST_CONSULTATION',
        justification='Do usunięcia.',
    )
    order = MedicalDeviceOrder.objects.create(
        episode=episode,
        patient=patient,
        therapist=therapist,
        device_code='J.ANKLE',
        device_group='J',
        device_name='Orteza',
        side='LEFT',
        quantity=1,
        icd10_code='M25.5',
        status=DeviceOrderStatus.ISSUED,
    )
    refusal = PhysicianOrderRefusal.objects.create(
        episode=episode,
        therapist=therapist,
        physician_order_description='Zabieg X',
        refusal_reason='Przeciwwskazanie',
    )
    recepta = ReceptaNaRuchReferral.objects.create(
        patient=patient,
        therapist=therapist,
        episode=episode,
        readiness_confirmed=True,
        status=DeviceOrderStatus.ISSUED,
    )

    api_client.force_authenticate(user=therapist.user)
    assert api_client.delete(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec.id}/',
    ).status_code == 204
    assert api_client.delete(
        f'/api/v1/episodes/{episode.id}/device-orders/{order.id}/',
    ).status_code == 204
    assert api_client.delete(
        f'/api/v1/episodes/{episode.id}/order-refusals/{refusal.id}/',
    ).status_code == 204
    assert api_client.delete(
        f'/api/v1/patients/{patient.id}/recepta-na-ruch/{recepta.id}/',
    ).status_code == 204

    api_client.force_authenticate(user=patient.user)
    inbox = api_client.get('/api/v1/me/clinical-documents/')
    assert inbox.status_code == 200
    assert inbox.data['count'] == 0


@pytest.mark.django_db
def test_other_therapist_cannot_delete_clinical_document(
    api_client, therapist, therapist_b, patient,
):
    episode = TreatmentEpisode.objects.create(patient=patient)
    rec = DiagnosticRecommendation.objects.create(
        episode=episode,
        therapist=therapist,
        recommendation_type='IMAGING_USG',
        justification='Cudze.',
    )
    api_client.force_authenticate(user=therapist_b.user)
    response = api_client.delete(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec.id}/',
    )
    assert response.status_code == 404
    assert DiagnosticRecommendation.objects.filter(pk=rec.id).exists()


@pytest.mark.django_db
def test_therapist_can_update_clinical_documents(api_client, therapist, patient):
    therapist.qualification_level = 'MAGISTER'
    therapist.experience_years = 5
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='M25.5')
    rec = DiagnosticRecommendation.objects.create(
        episode=episode,
        therapist=therapist,
        recommendation_type='SPECIALIST_CONSULTATION',
        target_specialty='Ortopeda',
        justification='Pierwotne uzasadnienie.',
        funding_hint='NFZ_VIA_DOCTOR',
    )
    order = MedicalDeviceOrder.objects.create(
        episode=episode,
        patient=patient,
        therapist=therapist,
        device_code='J.ANKLE',
        device_group='J',
        device_name='Orteza stawu skokowego',
        side='LEFT',
        quantity=1,
        icd10_code='M25.5',
        status=DeviceOrderStatus.ISSUED,
        notes='Stara notatka',
    )
    refusal = PhysicianOrderRefusal.objects.create(
        episode=episode,
        therapist=therapist,
        physician_order_description='Zabieg X',
        refusal_reason='Powód A',
        physician_notified=False,
    )
    recepta = ReceptaNaRuchReferral.objects.create(
        patient=patient,
        therapist=therapist,
        episode=episode,
        readiness_confirmed=True,
        activity_notes='Stara aktywność',
        status=DeviceOrderStatus.ISSUED,
    )

    api_client.force_authenticate(user=therapist.user)

    rec_resp = api_client.patch(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec.id}/',
        {
            'justification': 'Zaktualizowane uzasadnienie.',
            'target_specialty': 'Neurolog',
            'red_flags_noted': True,
        },
        format='json',
    )
    assert rec_resp.status_code == 200
    assert rec_resp.data['justification'] == 'Zaktualizowane uzasadnienie.'
    assert rec_resp.data['target_specialty'] == 'Neurolog'
    episode.refresh_from_db()
    assert episode.status == 'REFERRED'

    order_resp = api_client.patch(
        f'/api/v1/episodes/{episode.id}/device-orders/{order.id}/',
        {'notes': 'Nowa notatka', 'side': 'RIGHT'},
        format='json',
    )
    assert order_resp.status_code == 200
    assert order_resp.data['notes'] == 'Nowa notatka'
    assert order_resp.data['side'] == 'RIGHT'

    refusal_resp = api_client.patch(
        f'/api/v1/episodes/{episode.id}/order-refusals/{refusal.id}/',
        {
            'refusal_reason': 'Powód B',
            'physician_notified': True,
        },
        format='json',
    )
    assert refusal_resp.status_code == 200
    assert refusal_resp.data['refusal_reason'] == 'Powód B'
    assert refusal_resp.data['physician_notified'] is True

    recepta_resp = api_client.patch(
        f'/api/v1/patients/{patient.id}/recepta-na-ruch/{recepta.id}/',
        {'activity_notes': 'Nowa aktywność'},
        format='json',
    )
    assert recepta_resp.status_code == 200
    assert recepta_resp.data['activity_notes'] == 'Nowa aktywność'

    api_client.force_authenticate(user=patient.user)
    inbox = api_client.get('/api/v1/me/clinical-documents/')
    titles_and_summaries = ' '.join(
        f"{row['title']} {row['summary']}" for row in inbox.data['results']
    )
    assert 'Zaktualizowane uzasadnienie' in titles_and_summaries or 'Neurolog' in titles_and_summaries
    assert 'Nowa aktywność' in titles_and_summaries
