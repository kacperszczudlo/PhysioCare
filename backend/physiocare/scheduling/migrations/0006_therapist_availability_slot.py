import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0005_visit_patient_summary'),
        ('therapists', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TherapistAvailabilitySlot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_at', models.DateTimeField(blank=True, null=True)),
                ('end_at', models.DateTimeField(blank=True, null=True)),
                ('day_of_week', models.PositiveSmallIntegerField(blank=True, help_text='0=Poniedziałek, 6=Niedziela', null=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('is_recurring', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('therapist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availability_slots', to='therapists.therapistprofile')),
            ],
            options={
                'db_table': 'therapist_availability_slots',
                'indexes': [
                    models.Index(fields=['therapist', 'is_active', 'start_at'], name='idx_avail_therapist_start'),
                    models.Index(fields=['therapist', 'is_active', 'day_of_week'], name='idx_avail_therapist_dow'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='therapistavailabilityslot',
            constraint=models.CheckConstraint(
                condition=models.Q(is_recurring=False, start_at__isnull=False, end_at__isnull=False, end_at__gt=models.F('start_at')) |
                          models.Q(is_recurring=True, day_of_week__isnull=False, start_time__isnull=False, end_time__isnull=False, end_time__gt=models.F('start_time')),
                name='chk_avail_slot_valid_range',
            ),
        ),
    ]
