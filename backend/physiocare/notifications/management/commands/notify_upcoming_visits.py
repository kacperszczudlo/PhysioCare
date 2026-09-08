from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.events import notify_visit_reminder
from scheduling.models import Visit, VisitStatus

WINDOWS = {
    '24h': timedelta(hours=24),
    '2h': timedelta(hours=2),
}
SLACK = timedelta(minutes=30)


class Command(BaseCommand):
    help = 'Wyślij przypomnienia o wizytach (okna 24h i 2h).'

    def handle(self, *args, **options):
        now = timezone.now()
        sent = 0
        visits = Visit.objects.filter(
            status=VisitStatus.SCHEDULED,
            start_at__gte=now,
            start_at__lte=now + timedelta(hours=25),
        ).select_related('patient', 'patient__user')

        for visit in visits:
            for window, offset in WINDOWS.items():
                if (now + offset - SLACK) <= visit.start_at <= (now + offset + SLACK):
                    notify_visit_reminder(visit, window)
                    sent += 1

        self.stdout.write(self.style.SUCCESS(f'Przypomnienia zakolejkowane: {sent}'))
