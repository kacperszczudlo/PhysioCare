from django.db import models
from django.db.models import Func, Q
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators, RangeBoundary, DateTimeRangeField


class TsTzRange(Func):
    """
    Funkcja pomocnicza ORM konwertująca pola start_at i end_at
    do przedziału czasowego zrozumiałego dla PostgreSQL (TSTZRANGE).
    """
    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


class Visit(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Zaplanowana'),
        ('CANCELLED', 'Anulowana'),
        ('COMPLETED', 'Zakończona')
    ]

    therapist = models.ForeignKey('therapists.TherapistProfile', on_delete=models.CASCADE)
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    location_address = models.CharField(max_length=255)
    prep_instructions = models.TextField(blank=True)

    class Meta:
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_visits',
                expressions=[
                    ('therapist', RangeOperators.EQUAL),
                    (TsTzRange('start_at', 'end_at', RangeBoundary()), RangeOperators.OVERLAPS),
                ],
                condition=~Q(status='CANCELLED'),
            )
        ]

    def __str__(self):
        return f"Wizyta: {self.patient} u {self.therapist} ({self.start_at})"
