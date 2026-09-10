from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('privacy', '0002_accountdeletionrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountdeletionrequest',
            name='reason',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Powód rezygnacji podany przez użytkownika.',
            ),
        ),
    ]
