from django.core.management import call_command


def run_scheduled_notification_jobs() -> None:
    """Uruchamia cykliczne polecenia zarządzające wysyłką powiadomień."""
    call_command('notify_upcoming_visits')
    call_command('notify_today_exercises')
