from django.db import migrations


def seed_exercise_categories(apps, schema_editor):
    ExerciseCategory = apps.get_model('exercises', 'ExerciseCategory')
    names = [
        'Rozciąganie',
        'Kończyna dolna',
        'Odcinek lędźwiowy',
        'Mobilizacja',
    ]
    for name in names:
        ExerciseCategory.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(seed_exercise_categories, migrations.RunPython.noop),
    ]
