"""Komenda Django do zasilenia bazy danych słownikiem kategorii ćwiczeń."""
import uuid

from django.core.management.base import BaseCommand
from django.db.models import Q

from exercises.category_seed import CATEGORY_SEED
from exercises.models import ExerciseCategory


class Command(BaseCommand):
    """Zasila bazę danych pełnym słownikiem kategorii fizjoterapeutycznych."""

    help = 'Zasila bazę danych standardowym zestawem kategorii ćwiczeń (typ, okolica, mięsień, uraz).'

    def handle(self, *args: object, **options: object) -> None:
        created_count = 0
        updated_count = 0

        for kind, slug, name in CATEGORY_SEED:
            existing = ExerciseCategory.objects.filter(Q(slug=slug) | Q(name=name)).first()
            if existing:
                changed = False
                if existing.slug != slug:
                    existing.slug = slug
                    changed = True
                if existing.kind != kind:
                    existing.kind = kind
                    changed = True
                if existing.name != name:
                    existing.name = name
                    changed = True
                if changed:
                    existing.save(update_fields=['slug', 'kind', 'name'])
                    updated_count += 1
            else:
                ExerciseCategory.objects.create(
                    id=uuid.uuid4(),
                    name=name,
                    kind=kind,
                    slug=slug,
                )
                created_count += 1

        total = ExerciseCategory.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Pomyślnie zsynchronizowano kategorie: utworzono {created_count}, '
                f'zaktualizowano {updated_count}. Łącznie w bazie: {total}.'
            )
        )
