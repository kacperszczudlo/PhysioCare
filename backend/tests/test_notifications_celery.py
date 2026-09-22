import pytest
from django.contrib.auth import get_user_model

from notifications.delivery import schedule_notify
from notifications.keys import NotificationPreferenceKey
from notifications.models import NotificationDelivery
from notifications.tasks import send_notification_task

User = get_user_model()


@pytest.mark.django_db
def test_send_notification_task_eager_executes_successfully() -> None:
    """Weryfikuje, że zadanie send_notification_task wykonuje się poprawnie i tworzy wpis NotificationDelivery."""
    user = User.objects.create_user(email='test_celery@example.com', password='Password123!')
    send_notification_task(
        user.id,
        NotificationPreferenceKey.VISIT_CHANGE,
        'Tytuł testowy',
        'Treść testowa',
        data={'test': True},
        dedupe_key='test-key-1',
    )
    delivery = NotificationDelivery.objects.filter(user=user, dedupe_key='test-key-1').first()
    assert delivery is not None
    assert delivery.title == 'Tytuł testowy'


@pytest.mark.django_db
def test_schedule_notify_dispatches_celery_task() -> None:
    """Weryfikuje, że funkcja schedule_notify poprawnie przekazuje powiadomienie do wykonania."""
    user = User.objects.create_user(email='test_schedule@example.com', password='Password123!')
    schedule_notify(
        user,
        NotificationPreferenceKey.VISIT_CHANGE,
        'Nowa wizyta',
        'Została zaplanowana wizyta',
        dedupe_key='test-schedule-1',
    )
    delivery = NotificationDelivery.objects.filter(user=user, dedupe_key='test-schedule-1').first()
    assert delivery is not None
    assert delivery.title == 'Nowa wizyta'


@pytest.mark.django_db
def test_send_notification_task_handles_missing_user() -> None:
    """Weryfikuje bezpieczne anulowanie zadania Celery w przypadku braku użytkownika o podanym ID."""
    send_notification_task(
        999999,
        NotificationPreferenceKey.VISIT_CHANGE,
        'Tytuł',
        'Treść',
    )
    assert NotificationDelivery.objects.filter(title='Tytuł').count() == 0


@pytest.mark.django_db
def test_send_notification_task_raises_type_error_on_invalid_args() -> None:
    """Weryfikuje zgłoszenie TypeError w przypadku przekazania niepoprawnych typów argumentów."""
    with pytest.raises(TypeError):
        send_notification_task(
            None,  # type: ignore[arg-type]
            NotificationPreferenceKey.VISIT_CHANGE,
            'Tytuł',
            'Treść',
        )
