import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from notifications.delivery import notify_user
from notifications.jobs import run_scheduled_notification_jobs

logger: logging.Logger = logging.getLogger('physiocare.notifications')
User: type = get_user_model()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    name='notifications.tasks.send_notification_task',
)
def send_notification_task(
    self,
    user_id: int | str,
    pref_key: str,
    title: str,
    body: str,
    *,
    data: dict[str, object] | None = None,
    dedupe_key: str = '',
) -> None:
    """Asynchroniczne zadanie Celery wysyłające powiadomienie Push/Email do użytkownika w tle.

    Args:
        self: Instancja wykonawcza zadania Celery.
        user_id (int | str): Klucz główny identyfikatora użytkownika.
        pref_key (str): Klucz kategorii preferencji powiadomienia.
        title (str): Tytuł wiadomości powiadomienia.
        body (str): Treść wiadomości powiadomienia.
        data (dict[str, object] | None): Dodatkowe słownikowe metadane wiadomości.
        dedupe_key (str): Unikalny klucz zapobiegający powieleniom wysyłki.

    Raises:
        TypeError: Gdy user_id jest None lub parametry tekstowe nie są typu str.
    """
    if user_id is None:
        raise TypeError("Argument 'user_id' nie może być None.")
    if not isinstance(pref_key, str) or not isinstance(title, str) or not isinstance(body, str):
        raise TypeError('Parametry pref_key, title oraz body muszą być ciągami znaków.')

    user: object | None = User.objects.filter(pk=user_id).first()
    if user is None:
        logger.warning('send_notification_task cancelled: user_id=%s not found', user_id)
        return

    notify_user(
        user,
        pref_key,
        title,
        body,
        data=dict(data or {}),
        dedupe_key=dedupe_key,
    )


@shared_task(name='notifications.tasks.run_upcoming_visits_job_task')
def run_upcoming_visits_job_task() -> None:
    """Zadanie okresowe Celery uruchamiające cykl przypomnień o wizytach (24h/2h)."""
    run_scheduled_notification_jobs()


@shared_task(name='notifications.tasks.run_today_exercises_job_task')
def run_today_exercises_job_task() -> None:
    """Zadanie okresowe Celery wysyłające przypomnienia o planach ćwiczeń na bieżący dzień."""
    from django.core.management import call_command

    call_command('notify_today_exercises')
