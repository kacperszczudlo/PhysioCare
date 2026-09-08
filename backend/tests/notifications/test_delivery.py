from datetime import timedelta

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status

from exercises.models import Exercise, ExerciseAssignment, MediaType
from notifications.keys import NotificationPreferenceKey
from notifications.models import DeliveryChannel, DeliveryStatus, DeviceToken, NotificationDelivery
from scheduling.models import Visit, VisitStatus

SAMPLE_TOKEN = 'ExponentPushToken[physiocare-test-device]'


@pytest.fixture
def locmem_email(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox.clear()


def _disable_pref(user, key):
    from notifications.defaults import ensure_default_preferences

    ensure_default_preferences(user)
    from notifications.models import NotificationPreference

    NotificationPreference.objects.filter(user=user, pref_key=key).update(enabled=False)


@pytest.mark.django_db
def test_therapist_visit_create_emails_patient(
    api_client, therapist, patient, therapy_type, locmem_email,
):
    api_client.force_authenticate(user=therapist.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)

    response = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(mail.outbox) == 1
    assert 'Nowa wizyta' in mail.outbox[0].subject
    delivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.pref_key == NotificationPreferenceKey.VISIT_CHANGE
    assert delivery.channel == DeliveryChannel.EMAIL
    assert delivery.status == DeliveryStatus.SENT
    assert 'M54' not in delivery.body


@pytest.mark.django_db
def test_visit_change_skipped_when_pref_off(
    api_client, therapist, patient, therapy_type, locmem_email,
):
    _disable_pref(patient.user, NotificationPreferenceKey.VISIT_CHANGE)
    api_client.force_authenticate(user=therapist.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)

    response = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    delivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.status == DeliveryStatus.SKIPPED


@pytest.mark.django_db
def test_visit_create_uses_push_when_token_present(
    api_client, therapist, patient, therapy_type, locmem_email, monkeypatch,
):
    DeviceToken.objects.create(
        user=patient.user,
        expo_push_token=SAMPLE_TOKEN,
        platform='android',
    )

    def fake_push(messages):
        assert messages[0]['to'] == SAMPLE_TOKEN
        return [{'status': 'ok', 'id': 'ticket'}]

    monkeypatch.setattr('notifications.delivery.send_expo_push', fake_push)

    api_client.force_authenticate(user=therapist.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)
    response = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    delivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.channel == DeliveryChannel.PUSH
    assert delivery.status == DeliveryStatus.SENT


@pytest.mark.django_db
def test_patient_request_does_not_notify_patient(
    api_client, patient, therapy_type, locmem_email,
):
    api_client.force_authenticate(user=patient.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)
    response = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    assert not NotificationDelivery.objects.filter(user=patient.user).exists()


@pytest.mark.django_db
def test_approve_and_therapist_cancel_notify(
    api_client, therapist, patient, therapy_type, locmem_email,
):
    start_at = timezone.now() + timedelta(days=3)
    end_at = start_at + timedelta(minutes=45)
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
    )
    api_client.force_authenticate(user=therapist.user)
    approve = api_client.post(f'/api/v1/therapist/visits/{visit.id}/approve/', {}, format='json')
    assert approve.status_code == status.HTTP_200_OK
    assert any('zatwierdzona' in msg.body for msg in mail.outbox)

    cancel = api_client.post(
        f'/api/v1/visits/{visit.id}/cancel/',
        {'cancel_reason': 'Konflikt'},
        format='json',
    )
    assert cancel.status_code == status.HTTP_200_OK
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.VISIT_CHANGE,
        status=DeliveryStatus.SENT,
    ).count() == 2


@pytest.mark.django_db
def test_exercise_assignment_notifies_patient(
    api_client, therapist, patient, locmem_email,
):
    exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    api_client.force_authenticate(user=therapist.user)
    today = timezone.localdate()
    response = api_client.post(
        '/api/v1/therapist/exercise-assignments/',
        {
            'exercise_id': str(exercise.id),
            'patient_id': str(patient.id),
            'dosage': '3x10',
            'start_date': today.isoformat(),
            'end_date': (today + timedelta(days=7)).isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(mail.outbox) == 1
    delivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.pref_key == NotificationPreferenceKey.EXERCISE_REMINDER
    assert 'Mostek' not in delivery.body


@pytest.mark.django_db
def test_document_upload_notifies_patient(
    api_client, therapist, patient, locmem_email,
):
    api_client.force_authenticate(user=therapist.user)
    uploaded = SimpleUploadedFile(
        'skierowanie.pdf',
        b'%PDF-1.4 test document',
        content_type='application/pdf',
    )
    response = api_client.post(
        '/api/v1/therapist/documents/',
        {'patient_id': str(patient.id), 'title': 'Skierowanie', 'file': uploaded},
        format='multipart',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(mail.outbox) == 1
    delivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.pref_key == NotificationPreferenceKey.NEW_DOCUMENT


@pytest.mark.django_db
def test_notify_upcoming_visits_command_dedupes(
    therapist, patient, therapy_type, locmem_email,
):
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() + timedelta(hours=24),
        end_at=timezone.now() + timedelta(hours=24, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    call_command('notify_upcoming_visits')
    call_command('notify_upcoming_visits')
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.VISIT_REMINDER,
        dedupe_key=f'visit-reminder:{visit.id}:24h',
    ).count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_notify_today_exercises_command(therapist, patient, locmem_email):
    exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    today = timezone.localdate()
    ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today,
        end_date=today + timedelta(days=3),
    )
    call_command('notify_today_exercises')
    call_command('notify_today_exercises')
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.EXERCISE_REMINDER,
    ).count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_run_notification_scheduler_once_sends_visit_and_exercise(
    therapist, patient, therapy_type, locmem_email,
):
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() + timedelta(hours=24),
        end_at=timezone.now() + timedelta(hours=24, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    today = timezone.localdate()
    ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today,
        end_date=today + timedelta(days=3),
    )
    call_command('run_notification_scheduler', '--once')
    call_command('run_notification_scheduler', '--once')
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.VISIT_REMINDER,
        dedupe_key=f'visit-reminder:{visit.id}:24h',
    ).count() == 1
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.EXERCISE_REMINDER,
        dedupe_key=f'exercise-today:{patient.user.pk}:{today.isoformat()}',
    ).count() == 1


def test_run_notification_scheduler_rejects_non_positive_interval():
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command('run_notification_scheduler', '--once', '--interval', '0')


@pytest.mark.django_db
def test_stale_expo_token_is_deactivated_and_falls_back_to_email(
    patient, locmem_email, monkeypatch,
):
    DeviceToken.objects.create(
        user=patient.user,
        expo_push_token=SAMPLE_TOKEN,
        platform='android',
    )

    def fake_push(messages):
        return [
            {
                'status': 'error',
                'message': 'DeviceNotRegistered',
                'details': {'error': 'DeviceNotRegistered'},
            }
        ]

    monkeypatch.setattr('notifications.delivery.send_expo_push', fake_push)

    from notifications.delivery import notify_user

    notify_user(
        patient.user,
        NotificationPreferenceKey.VISIT_CHANGE,
        'Nowa wizyta',
        'Masz nową wizytę w kalendarzu.',
        data={'type': 'visit'},
    )

    token = DeviceToken.objects.get(expo_push_token=SAMPLE_TOKEN)
    assert token.is_active is False
    assert len(mail.outbox) == 1
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        channel=DeliveryChannel.PUSH,
        status=DeliveryStatus.FAILED,
    ).exists()


def test_notification_copy_has_no_clinical_detail():
    from notifications.events import _REMINDER_COPY, _VISIT_COPY

    blobs = ' '.join(
        title + ' ' + body
        for title, body in list(_VISIT_COPY.values()) + list(_REMINDER_COPY.values())
    )
    lowered = blobs.lower()
    assert 'icd' not in lowered
    assert 'rozpoznan' not in lowered
    assert 'm54' not in lowered

