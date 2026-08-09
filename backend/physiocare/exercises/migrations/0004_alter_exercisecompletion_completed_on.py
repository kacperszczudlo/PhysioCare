from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0003_seed_exercise_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercisecompletion',
            name='completed_on',
            field=models.DateField(),
        ),
    ]
