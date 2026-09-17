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

SAMPLE_TOKEN: str = 'ExponentPushToken[physiocare-test-device]'


@pytest.fixture
def locmem_email(settings: object) -> None:
    """Konfiguruje in-memory backend pocztowy dla celów testowych."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox.clear()


def _disable_pref(user: object, key: str) -> None:
    """Pomocniczo wyłącza określoną preferencję powiadomień dla użytkownika."""
    from notifications.defaults import ensure_default_preferences
    from notifications.models import NotificationPreference

    ensure_default_preferences(user)
    NotificationPreference.objects.filter(user=user, pref_key=key).update(enabled=False)


@pytest.mark.django_db
def test_therapist_visit_create_emails_patient(
    api_client: object, therapist: object, patient: object, therapy_type: object, locmem_email: None,
) -> None:
    """Sprawdza wysłanie wiadomości e-mail do pacjenta po utworzeniu nowej wizyty przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    start_at: object = timezone.now() + timedelta(days=2)
    end_at: object = start_at + timedelta(minutes=45)

    response: object = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert len(mail.outbox) == 1
    assert 'Nowa wizyta' in mail.outbox[0].subject
    delivery: NotificationDelivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.pref_key == NotificationPreferenceKey.VISIT_CHANGE
    assert delivery.channel == DeliveryChannel.EMAIL
    assert delivery.status == DeliveryStatus.SENT
    assert 'M54' not in delivery.body


@pytest.mark.django_db
def test_visit_change_skipped_when_pref_off(
    api_client: object, therapist: object, patient: object, therapy_type: object, locmem_email: None,
) -> None:
    """Sprawdza pominięcie wysyłki powiadomienia o wizycie, gdy pacjent wyłączył preferencję."""
    # Arrange
    _disable_pref(patient.user, NotificationPreferenceKey.VISIT_CHANGE)
    api_client.force_authenticate(user=therapist.user)
    start_at: object = timezone.now() + timedelta(days=2)
    end_at: object = start_at + timedelta(minutes=45)

    response: object = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    delivery: NotificationDelivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.status == DeliveryStatus.SKIPPED


@pytest.mark.django_db
def test_visit_create_uses_push_when_token_present(
    api_client: object, therapist: object, patient: object, therapy_type: object, locmem_email: None, monkeypatch: object,
) -> None:
    """Sprawdza wysyłanie powiadomień Push (Expo) gdy pacjent posiada zarejestrowany token urządzenia."""
    # Arrange
    DeviceToken.objects.create(
        user=patient.user,
        expo_push_token=SAMPLE_TOKEN,
        platform='android',
    )

    def fake_push(messages: list[dict[str, object]]) -> list[dict[str, str]]:
        assert messages[0]['to'] == SAMPLE_TOKEN
        return [{'status': 'ok', 'id': 'ticket'}]

    monkeypatch.setattr('notifications.delivery.send_expo_push', fake_push)

    api_client.force_authenticate(user=therapist.user)
    start_at: object = timezone.now() + timedelta(days=2)
    end_at: object = start_at + timedelta(minutes=45)
    response: object = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    delivery: NotificationDelivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.channel == DeliveryChannel.PUSH
    assert delivery.status == DeliveryStatus.SENT


@pytest.mark.django_db
def test_patient_request_does_not_notify_patient(
    api_client: object, patient: object, therapy_type: object, locmem_email: None,
) -> None:
    """Sprawdza, czy prośba o wizytę wysłana przez pacjenta nie generuje powiadomienia dla niego samego."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    start_at: object = timezone.now() + timedelta(days=2)
    end_at: object = start_at + timedelta(minutes=45)
    from scheduling.models import TherapistAvailabilitySlot
    TherapistAvailabilitySlot.objects.create(
        therapist=patient.therapist,
        is_recurring=False,
        start_at=start_at - timedelta(hours=1),
        end_at=end_at + timedelta(hours=1),
    )
    response: object = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    assert not NotificationDelivery.objects.filter(user=patient.user).exists()


@pytest.mark.django_db
def test_approve_and_therapist_cancel_notify(
    api_client: object, therapist: object, patient: object, therapy_type: object, locmem_email: None,
) -> None:
    """Sprawdza wysyłanie powiadomień przy zatwierdzaniu i odwoływaniu wizyty przez fizjoterapeutę."""
    # Arrange
    start_at: object = timezone.now() + timedelta(days=3)
    end_at: object = start_at + timedelta(minutes=45)
    visit: Visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
    )
    api_client.force_authenticate(user=therapist.user)
    approve: object = api_client.post(f'/api/v1/therapist/visits/{visit.id}/approve/', {}, format='json')
    # Assert
    assert approve.status_code == status.HTTP_200_OK
    assert any('zatwierdzona' in msg.body for msg in mail.outbox)

    cancel: object = api_client.post(
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
    api_client: object, therapist: object, patient: object, locmem_email: None,
) -> None:
    """Sprawdza wysłanie powiadomienia do pacjenta przy przypisaniu nowego ćwiczenia domowego."""
    # Arrange
    exercise: Exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    api_client.force_authenticate(user=therapist.user)
    today: object = timezone.localdate()
    response: object = api_client.post(
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
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert len(mail.outbox) == 1
    delivery: NotificationDelivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.pref_key == NotificationPreferenceKey.EXERCISE_REMINDER
    assert 'Mostek' not in delivery.body


@pytest.mark.django_db
def test_document_upload_notifies_patient(
    api_client: object, therapist: object, patient: object, locmem_email: None,
) -> None:
    """Sprawdza wysłanie powiadomienia po wgraniu nowego dokumentu medycznego przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    uploaded: SimpleUploadedFile = SimpleUploadedFile(
        'skierowanie.pdf',
        b'%PDF-1.4 test document',
        content_type='application/pdf',
    )
    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {'patient_id': str(patient.id), 'title': 'Skierowanie', 'file': uploaded},
        format='multipart',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert len(mail.outbox) == 1
    delivery: NotificationDelivery = NotificationDelivery.objects.get(user=patient.user)
    assert delivery.pref_key == NotificationPreferenceKey.NEW_DOCUMENT


@pytest.mark.django_db
def test_notify_upcoming_visits_command_dedupes(
    therapist: object, patient: object, therapy_type: object, locmem_email: None,
) -> None:
    """Sprawdza deduplikację przypomnień o nadchodzących wizytach uruchamianych komendą CLI."""
    # Arrange
    visit: Visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() + timedelta(hours=24),
        end_at=timezone.now() + timedelta(hours=24, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    call_command('notify_upcoming_visits')
    call_command('notify_upcoming_visits')
    # Assert
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.VISIT_REMINDER,
        dedupe_key=f'visit-reminder:{visit.id}:24h',
    ).count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_delivery_notify_today_exercises_command(
    therapist: object, patient: object, locmem_email: None,
) -> None:
    """Sprawdza deduplikację przypomnień o dzisiejszych ćwiczeniach uruchamianych komendą CLI."""
    # Arrange
    exercise: Exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    today: object = timezone.localdate()
    ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today,
        end_date=today + timedelta(days=3),
    )
    call_command('notify_today_exercises')
    call_command('notify_today_exercises')
    # Assert
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.EXERCISE_REMINDER,
    ).count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_run_notification_scheduler_once_sends_visit_and_exercise(
    therapist: object, patient: object, therapy_type: object, locmem_email: None,
) -> None:
    """Sprawdza pojedyncze wykonanie schedulera powiadomień (komenda run_notification_scheduler --once)."""
    # Arrange
    visit: Visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() + timedelta(hours=24),
        end_at=timezone.now() + timedelta(hours=24, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    exercise: Exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    today: object = timezone.localdate()
    ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today,
        end_date=today + timedelta(days=3),
    )
    call_command('run_notification_scheduler', '--once')
    call_command('run_notification_scheduler', '--once')
    # Assert
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


def test_run_notification_scheduler_rejects_non_positive_interval() -> None:
    """Sprawdza odrzucenie ujemnego lub zerowego interwału w komendzie schedulera powiadomień."""
    # Arrange
    from django.core.management.base import CommandError

    # Act
    with pytest.raises(CommandError):
        call_command('run_notification_scheduler', '--once', '--interval', '0')


@pytest.mark.django_db
def test_stale_expo_token_is_deactivated_and_falls_back_to_email(
    patient: object, locmem_email: None, monkeypatch: object,
) -> None:
    """Sprawdza dezaktywację wygasłego tokena Expo i przejście na kanał e-mail."""
    # Arrange
    DeviceToken.objects.create(
        user=patient.user,
        expo_push_token=SAMPLE_TOKEN,
        platform='android',
    )

    def fake_push(messages: list[dict[str, object]]) -> list[dict[str, object]]:
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

    token: DeviceToken = DeviceToken.objects.get(expo_push_token=SAMPLE_TOKEN)
    # Assert
    assert token.is_active is False
    assert len(mail.outbox) == 1
    assert NotificationDelivery.objects.filter(
        user=patient.user,
        channel=DeliveryChannel.PUSH,
        status=DeliveryStatus.FAILED,
    ).exists()


def test_notification_copy_has_no_clinical_detail() -> None:
    """Sprawdza, czy treści powiadomień nie zawierają wrażliwych danych klinicznych (kody ICD, diagnozy)."""
    # Arrange
    from notifications.events import _REMINDER_COPY, _VISIT_COPY

    blobs: str = ' '.join(
        title + ' ' + body
        for title, body in list(_VISIT_COPY.values()) + list(_REMINDER_COPY.values())
    )
    lowered: str = blobs.lower()
    # Assert
    assert 'icd' not in lowered
    assert 'rozpoznan' not in lowered
    assert 'm54' not in lowered



def test_delivery_type_errors():
    """Sprawdza rzucanie TypeError przy podaniu niepoprawnych typów argumentów w delivery.py."""
    # Arrange
    from notifications.delivery import _send_email, _send_push, already_delivered, is_pref_enabled, notify_user, schedule_notify

    # Act
    with pytest.raises(TypeError, match="Argument 'user' nie może być None."):
        is_pref_enabled(None, "visit_reminder")

    with pytest.raises(TypeError, match="Argument 'dedupe_key' musi być typu str."):
        already_delivered(object(), 123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Argument 'user' nie może być None."):
        schedule_notify(None, "key", "title", "body")

    with pytest.raises(TypeError, match="Argument 'user' nie może być None."):
        notify_user(None, "key", "title", "body")

    with pytest.raises(TypeError, match="Argument 'tokens' musi być listą"):
        _send_push(object(), "key", "title", "body", data={}, dedupe_key="", tokens="invalid_tokens")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Argument 'user' nie może być None."):
        _send_email(None, "key", "title", "body", data={}, dedupe_key="")


