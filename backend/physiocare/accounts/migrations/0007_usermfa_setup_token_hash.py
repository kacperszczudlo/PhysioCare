from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0006_customuser_uniq_users_email_lower'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermfa',
            name='setup_token_hash',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
