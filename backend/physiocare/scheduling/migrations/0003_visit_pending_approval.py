from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visit',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_APPROVAL', 'Oczekuje na zatwierdzenie'),
                    ('SCHEDULED', 'Zaplanowana'),
                    ('COMPLETED', 'Zakończona'),
                    ('CANCELLED', 'Anulowana'),
                    ('NO_SHOW', 'Nieobecność'),
                ],
                default='SCHEDULED',
                max_length=20,
            ),
        ),
    ]
