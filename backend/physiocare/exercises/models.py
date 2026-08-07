from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import Func

from core.models import TimestampedModel, UUIDModel


class DateRange(Func):
    function = 'DATERANGE'
    output_field = DateRangeField()


class MediaType(models.TextChoices):
    VIDEO = 'VIDEO', 'Wideo'
    PDF = 'PDF', 'PDF'


class CategoryKind(models.TextChoices):
    TYPE = 'TYPE', 'Typ ćwiczenia'
    REGION = 'REGION', 'Okolica ciała'
    MUSCLE = 'MUSCLE', 'Mięsień / grupa'
    INJURY = 'INJURY', 'Kontuzja / wskazanie'


class ExerciseCategory(UUIDModel):
    name = models.CharField(max_length=80, unique=True)
    kind = models.CharField(
        max_length=10,
        choices=CategoryKind.choices,
        default=CategoryKind.TYPE,
        db_index=True,
    )
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        db_table = 'exercise_categories'
        ordering = ['kind', 'name']
        indexes = [
            models.Index(fields=['kind', 'name'], name='idx_ex_cat_kind_name'),
        ]

    def __str__(self):
        return f'{self.name} ({self.kind})'


class Exercise(TimestampedModel):
    therapist = models.ForeignKey(
        'therapists.TherapistProfile',
        on_delete=models.CASCADE,
        related_name='exercises',
    )
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    file_url = models.CharField(max_length=500)
    instruction = models.TextField(blank=True, default='')
    categories = models.ManyToManyField(
        ExerciseCategory,
        through='ExerciseCategoryMap',
        related_name='exercises',
    )

    class Meta:
        db_table = 'exercises'

    def __str__(self):
        return self.title


class ExerciseCategoryMap(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        db_column='exercise_id',
    )
    category = models.ForeignKey(
        ExerciseCategory,
        on_delete=models.CASCADE,
        db_column='category_id',
    )

    class Meta:
        db_table = 'exercise_category_map'
        constraints = [
            models.UniqueConstraint(
                fields=['exercise', 'category'],
                name='uniq_exercise_category_map',
            ),
        ]


class ExerciseAssignment(UUIDModel):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.CASCADE,
        related_name='exercise_assignments',
    )
    episode = models.ForeignKey(
        'treatment.TreatmentEpisode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercise_assignments',
    )
    dosage = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exercise_assignments'
        indexes = [
            models.Index(
                fields=['patient', 'start_date', 'end_date'],
                name='idx_ex_assign_patient_dates',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F('start_date')),
                name='chk_exercise_assignment_dates',
            ),
            ExclusionConstraint(
                name='exclude_overlapping_exercise_assignments',
                expressions=[
                    ('patient', RangeOperators.EQUAL),
                    ('exercise', RangeOperators.EQUAL),
                    (
                        DateRange(
                            'start_date',
                            'end_date',
                            RangeBoundary(inclusive_lower=True, inclusive_upper=True),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
            ),
        ]

    def __str__(self):
        return f'{self.exercise.title} - {self.patient}'


class ExerciseCompletion(UUIDModel):
    assignment = models.ForeignKey(
        ExerciseAssignment,
        on_delete=models.CASCADE,
        related_name='completions',
    )
    completed_on = models.DateField()
    done = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exercise_completions'
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'completed_on'],
                name='uniq_exercise_completion_assignment_date',
            ),
        ]

    def __str__(self):
        return f'{self.assignment_id} @ {self.completed_on}'
