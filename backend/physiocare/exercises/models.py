from datetime import date

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import Func

from core.models import TimestampedModel, UUIDModel


class DateRange(Func):
    """Funkcja bazodanowa PostgreSQL tworząca zakres dat (DATERANGE)."""

    function: str = 'DATERANGE'
    output_field: DateRangeField = DateRangeField()


class MediaType(models.TextChoices):
    """Typy mediów obsługiwanych w ćwiczeniach (wideo, PDF)."""

    VIDEO: str = 'VIDEO', 'Wideo'
    PDF: str = 'PDF', 'PDF'


class CategoryKind(models.TextChoices):
    """Kategorie (rodzaje) przypisywane do ćwiczeń."""

    TYPE: str = 'TYPE', 'Typ ćwiczenia'
    REGION: str = 'REGION', 'Okolica ciała'
    MUSCLE: str = 'MUSCLE', 'Mięsień / grupa'
    INJURY: str = 'INJURY', 'Kontuzja / wskazanie'


class ExerciseCategory(UUIDModel):
    """Kategoria ćwiczenia w systemie PhysioCare."""

    name = models.CharField(max_length=80, unique=True)
    kind = models.CharField(
        max_length=10,
        choices=CategoryKind.choices,
        default=CategoryKind.TYPE,
        db_index=True,
    )
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        """Metadane modelu ExerciseCategory."""

        db_table: str = 'exercise_categories'
        ordering: list[str] = ['kind', 'name']
        indexes: list[models.Index] = [
            models.Index(fields=['kind', 'name'], name='idx_ex_cat_kind_name'),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową kategorii ćwiczenia.

        Returns:
            str: Nazwa kategorii oraz jej typ.
        """
        return f'{self.name} ({self.kind})'

    def matches_kind(self, target_kind: str) -> bool:
        """Sprawdza czy kategoria należy do określonego rodzaju.

        Args:
            target_kind (str): Oczekiwany kod rodzaju kategorii (np. TYPE, REGION).

        Returns:
            bool: True jeśli rodzaj kategorii zgadza się, False w przeciwnym razie.

        Raises:
            TypeError: Gdy argument target_kind nie jest napisem.
        """
        if not isinstance(target_kind, str):
            raise TypeError("Argument 'target_kind' musi być typu str.")

        return self.kind == target_kind


class Exercise(TimestampedModel):
    """Model reprezentujący ćwiczenie utworzone przez fizjoterapeutę."""

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
        """Metadane modelu Exercise."""

        db_table: str = 'exercises'

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową ćwiczenia.

        Returns:
            str: Tytuł ćwiczenia.
        """
        return self.title


class ExerciseCategoryMap(models.Model):
    """Tabela łącząca (wiele do wielu) ćwiczenie z kategoriami."""

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
        """Metadane modelu ExerciseCategoryMap."""

        db_table: str = 'exercise_category_map'
        constraints: list[object] = [
            models.UniqueConstraint(
                fields=['exercise', 'category'],
                name='uniq_exercise_category_map',
            ),
        ]


class ExerciseAssignment(UUIDModel):
    """Przypisanie ćwiczenia do pacjenta przez fizjoterapeutę."""

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
        """Metadane modelu ExerciseAssignment."""

        db_table: str = 'exercise_assignments'
        indexes: list[models.Index] = [
            models.Index(
                fields=['patient', 'start_date', 'end_date'],
                name='idx_ex_assign_patient_dates',
            ),
        ]
        constraints: list[object] = [
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

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową przypisania ćwiczenia.

        Returns:
            str: Tytuł ćwiczenia oraz pacjent.
        """
        return f'{self.exercise.title} - {self.patient}'

    def is_active_on(self, target_date: date) -> bool:
        """Sprawdza czy przypisanie ćwiczenia jest aktywne w podanym dniu.

        Args:
            target_date (date): Data do sprawdzenia aktywności.

        Returns:
            bool: True jeśli data mieści się w przedziale [start_date, end_date], False w przeciwnym razie.

        Raises:
            TypeError: Gdy argument target_date nie jest instancją datetime.date.
        """
        if not isinstance(target_date, date):
            raise TypeError("Argument 'target_date' musi być instancją datetime.date.")

        return self.start_date <= target_date <= self.end_date


class ExerciseCompletion(UUIDModel):
    """Wpis wykonania przypisanego ćwiczenia przez pacjenta w danym dniu."""

    assignment = models.ForeignKey(
        ExerciseAssignment,
        on_delete=models.CASCADE,
        related_name='completions',
    )
    completed_on = models.DateField()
    done = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadane modelu ExerciseCompletion."""

        db_table: str = 'exercise_completions'
        constraints: list[object] = [
            models.UniqueConstraint(
                fields=['assignment', 'completed_on'],
                name='uniq_exercise_completion_assignment_date',
            ),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową statusu wykonania ćwiczenia.

        Returns:
            str: Identyfikator przypisania oraz data wykonania.
        """
        return f'{self.assignment_id} @ {self.completed_on}'
