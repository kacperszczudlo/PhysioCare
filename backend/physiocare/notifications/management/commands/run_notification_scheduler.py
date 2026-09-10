import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from notifications.jobs import run_scheduled_notification_jobs

logger = logging.getLogger('physiocare.notifications')


class Command(BaseCommand):
    help = (
        'Pętla przypomnień: wizyty (24h/2h) i ćwiczenia na dziś. '
        'Uruchamiaj obok runserver / Gunicorn - nie w workerze HTTP.'
    )

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        interval = options['interval']
        if interval is None:
            interval = settings.NOTIFICATION_SCHEDULER_INTERVAL_SECONDS
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
        while True:
            try:
                run_scheduled_notification_jobs()
            except Exception:
                logger.exception('Notification scheduler tick failed')
            time.sleep(interval)
