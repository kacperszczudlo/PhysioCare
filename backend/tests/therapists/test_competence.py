import pytest

from therapists.competence import (
    QualificationLevel,
    build_competence_snapshot,
    can_order_device_group,
)


def test_magister_without_experience_cannot_plan_therapy():
    snap = build_competence_snapshot(QualificationLevel.MAGISTER, experience_years=1)
    assert snap.allows('functional_diagnosis')
    assert not snap.allows('plan_modify_therapy')
    assert snap.allows('order_serial_devices')
    assert not snap.allows('order_specialist_devices')
    assert not snap.allows('imaging_referral_nfz')
    assert not snap.allows('prescribe_medications')


def test_magister_with_3_years_can_plan():
    snap = build_competence_snapshot(QualificationLevel.MAGISTER, experience_years=3)
    assert snap.allows('plan_modify_therapy')
    assert not snap.allows('supervise_others')


def test_fizjo_spec_can_order_specialist_devices():
    snap = build_competence_snapshot(QualificationLevel.FIZJO_SPEC, experience_years=0)
    assert snap.allows('order_specialist_devices')
    assert snap.allows('plan_modify_therapy')
    assert can_order_device_group(QualificationLevel.FIZJO_SPEC, 'W')
    assert can_order_device_group(QualificationLevel.FIZJO_SPEC, 'A')
    assert not can_order_device_group(QualificationLevel.MAGISTER, 'W')


def test_licencjat_has_executive_scope_only():
    snap = build_competence_snapshot(QualificationLevel.LICENCJAT, experience_years=10)
    assert not snap.allows('functional_diagnosis')
    assert not snap.allows('order_serial_devices')
    assert snap.allows('refuse_physician_order')
    assert snap.allows('recepta_na_ruch')


@pytest.mark.django_db
def test_competences_endpoint(api_client, therapist):
    therapist.qualification_level = QualificationLevel.MAGISTER
    therapist.experience_years = 4
    therapist.save()
    api_client.force_authenticate(user=therapist.user)
    response = api_client.get('/api/v1/therapist/competences/')
    assert response.status_code == 200
    assert response.data['qualification_level'] == 'MAGISTER'
    assert response.data['can_plan_therapy'] is True
    assert response.data['can_supervise'] is False


@pytest.mark.django_db
def test_magister_can_issue_serial_device_order(api_client, therapist, patient):
    from treatment.models import MedicalDeviceOrder, TreatmentEpisode

    therapist.qualification_level = QualificationLevel.MAGISTER
    therapist.experience_years = 5
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='M25.5')

    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        f'/api/v1/episodes/{episode.id}/device-orders/',
        {
            'device_code': 'J.ANKLE',
            'side': 'LEFT',
            'quantity': 1,
            'icd10_code': 'M25.5',
            'access_code': '9012',
            'notes': 'Stabilizacja pourazowa',
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data['device_group'] == 'J'
    assert response.data['access_code'] == '9012'
    assert MedicalDeviceOrder.objects.filter(episode=episode).count() == 1


@pytest.mark.django_db
def test_magister_cannot_issue_fizjo_spec_device(api_client, therapist, patient):
    from treatment.models import TreatmentEpisode

    therapist.qualification_level = QualificationLevel.MAGISTER
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='C50.9')

    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        f'/api/v1/episodes/{episode.id}/device-orders/',
        {
            'device_code': 'W.BRA.POSTOP',
            'icd10_code': 'C50.9',
        },
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_diagnostic_recommendation_marks_referred_on_red_flags(
    api_client, therapist, patient,
):
    from treatment.models import EpisodeStatus, TreatmentEpisode

    therapist.qualification_level = QualificationLevel.MAGISTER
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient)

    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/',
        {
            'recommendation_type': 'SPECIALIST_CONSULTATION',
            'target_specialty': 'Neurolog',
            'body_area': 'Kręgosłup lędźwiowy',
            'justification': 'Objawy siodłowe - czerwone flagi.',
            'red_flags_noted': True,
            'funding_hint': 'NFZ_VIA_DOCTOR',
        },
        format='json',
    )
    assert response.status_code == 201
    episode.refresh_from_db()
    assert episode.status == EpisodeStatus.REFERRED


@pytest.mark.django_db
def test_recepta_na_ruch_requires_readiness(api_client, therapist, patient):
    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        f'/api/v1/patients/{patient.id}/recepta-na-ruch/',
        {
            'readiness_confirmed': False,
            'activity_notes': 'Brak aktywności',
        },
        format='json',
    )
    assert response.status_code == 400

    ok = api_client.post(
        f'/api/v1/patients/{patient.id}/recepta-na-ruch/',
        {
            'readiness_confirmed': True,
            'activity_notes': 'Gotowość potwierdzona kwestionariuszem',
        },
        format='json',
    )
    assert ok.status_code == 201


@pytest.mark.django_db
def test_licencjat_cannot_write_functional_diagnosis(api_client, therapist, patient):
    from treatment.models import TreatmentEpisode

    therapist.qualification_level = QualificationLevel.LICENCJAT
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient)

    api_client.force_authenticate(user=therapist.user)
    response = api_client.patch(
        f'/api/v1/episodes/{episode.id}/',
        {'functional_diagnosis': 'Deficyt zgięcia biodra L'},
        format='json',
    )
    assert response.status_code == 400
