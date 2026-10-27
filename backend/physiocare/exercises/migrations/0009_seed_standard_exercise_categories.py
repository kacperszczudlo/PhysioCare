import uuid

from django.db import migrations
from django.db.models import Q


def seed_standard_categories(apps, schema_editor):
    ExerciseCategory = apps.get_model('exercises', 'ExerciseCategory')
    from exercises.category_seed import CATEGORY_SEED

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
        else:
            ExerciseCategory.objects.create(
                id=uuid.uuid4(),
                name=name,
                kind=kind,
                slug=slug,
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0008_alter_exercise_created_at'),
    ]

    operations = [
        migrations.RunPython(seed_standard_categories, noop_reverse),
    ]
