from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treatment', '0003_competence_and_clinical_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicaldeviceorder',
            name='access_code',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Opcjonalny 4-cyfrowy kod dostępu e-ZWM z NFZ '
                    '(nie generowany lokalnie).'
                ),
                max_length=4,
            ),
        ),
    ]
