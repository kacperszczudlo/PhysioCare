from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0004_visit_patient_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='patient_summary',
            field=models.TextField(blank=True, default=''),
        ),
    ]
