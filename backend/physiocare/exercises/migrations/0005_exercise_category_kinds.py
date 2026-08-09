import uuid

from django.db import migrations, models
from django.db.models import Q


def seed_categorized_taxonomy(apps, schema_editor):
    ExerciseCategory = apps.get_model('exercises', 'ExerciseCategory')
    from exercises.category_seed import CATEGORY_SEED, LEGACY_CATEGORY_MAP

    for name, (kind, slug) in LEGACY_CATEGORY_MAP.items():
        ExerciseCategory.objects.filter(name=name).update(kind=kind, slug=slug)

    for row in ExerciseCategory.objects.filter(Q(slug__isnull=True) | Q(slug='')):
        row.slug = f'legacy-{row.pk.hex[:12]}'
        row.save(update_fields=['slug'])

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
        ('exercises', '0004_alter_exercisecompletion_completed_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercisecategory',
            name='kind',
            field=models.CharField(
                choices=[
                    ('TYPE', 'Typ ćwiczenia'),
                    ('REGION', 'Okolica ciała'),
                    ('MUSCLE', 'Mięsień / grupa'),
                    ('INJURY', 'Kontuzja / wskazanie'),
                ],
                db_index=True,
                default='TYPE',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='exercisecategory',
            name='slug',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.RunPython(seed_categorized_taxonomy, noop_reverse),
        migrations.AlterField(
            model_name='exercisecategory',
            name='slug',
            field=models.SlugField(max_length=60, unique=True),
        ),
        migrations.AlterModelOptions(
            name='exercisecategory',
            options={'ordering': ['kind', 'name']},
        ),
        migrations.AddIndex(
            model_name='exercisecategory',
            index=models.Index(fields=['kind', 'name'], name='idx_ex_cat_kind_name'),
        ),
    ]
