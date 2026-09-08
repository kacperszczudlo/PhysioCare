from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from exercises.models import ExerciseAssignment
from notifications.events import notify_today_exercises

User = get_user_model()


class Command(BaseCommand):
    help = 'Wyślij dzienne przypomnienie o ćwiczeniach.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        rows = list(
            ExerciseAssignment.objects.filter(
                start_date__lte=today,
                end_date__gte=today,
            )
            .values('patient__user')
            .annotate(total=Count('id'))
        )
        users = User.objects.in_bulk([row['patient__user'] for row in rows])
        sent = 0
        for row in rows:
            user = users.get(row['patient__user'])
            if user is None:
                continue
            notify_today_exercises(user, row['total'])
            sent += 1
        self.stdout.write(self.style.SUCCESS(f'Przypomnienia o ćwiczeniach: {sent}'))
