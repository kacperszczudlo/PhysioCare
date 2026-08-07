from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0003_visit_pending_approval'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='patient_note',
            field=models.TextField(blank=True, default=''),
        ),
    ]
