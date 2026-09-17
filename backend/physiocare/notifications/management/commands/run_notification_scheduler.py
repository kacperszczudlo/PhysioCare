import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from notifications.jobs import run_scheduled_notification_jobs

logger = logging.getLogger('physiocare.notifications')


class Command(BaseCommand):
    """Polecenie zarządcze Django obsługujące ciągłą pętlę harmonogramu powiadomień."""

    help = (
        'Pętla przypomnień: wizyty (24h/2h) i ćwiczenia na dziś. '
        'Uruchamiaj obok runserver / Gunicorn - nie w workerze HTTP.'
    )

    def add_arguments(self, parser) -> None:
        """Konfiguruje opcje wiersza poleceń dla schedulera.

        Args:
            parser: Parser argumentów polecenia.
        """
        parser.add_argument(
            '--once',
            action='store_true',
            help='Jedna tura i wyjście (testy / ręczny tick).',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=None,
            help='Sekundy między turami (domyślnie NOTIFICATION_SCHEDULER_INTERVAL_SECONDS).',
        )

    def handle(self, *args, **options) -> None:
        """Główna pętla wykonania zadań powiadomień.

        Args:
            *args: Argumenty pozycyjne.
            **options: Opcje wiersza poleceń.

        Raises:
            CommandError: Gdy interwał jest mniejszy niż 1 sekunda.
        """
        interval = options['interval']
        if interval is None:
            interval = settings.NOTIFICATION_SCHEDULER_INTERVAL_SECONDS if hasattr(settings, 'NOTIFICATION_SCHEDULER_INTERVAL_SECONDS') else 60
        if interval < 1:
            raise CommandError('Interval must be >= 1 second.')

        if options['once']:
            run_scheduled_notification_jobs()
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Scheduler powiadomień co {interval}s (Ctrl+C kończy).',
            ),
        )
        try:
            while True:
                run_scheduled_notification_jobs()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Scheduler powiadomień zatrzymany.'))
