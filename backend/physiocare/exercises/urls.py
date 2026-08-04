from django.urls import path

from .views import (
    MeExerciseCompletionCreateView,
    MeExercisesTodayView,
    TherapistExerciseAssignmentCreateView,
    TherapistExerciseCategoryListView,
    TherapistExerciseListCreateView,
)

urlpatterns = [
    path(
        'therapist/exercises/',
        TherapistExerciseListCreateView.as_view(),
        name='therapist-exercises',
    ),
    path(
        'therapist/exercise-categories/',
        TherapistExerciseCategoryListView.as_view(),
        name='therapist-exercise-categories',
    ),
    path(
        'therapist/exercise-assignments/',
        TherapistExerciseAssignmentCreateView.as_view(),
        name='therapist-exercise-assignments',
    ),
]

me_urlpatterns = [
    path('exercises/today/', MeExercisesTodayView.as_view(), name='me-exercises-today'),
    path(
        'exercise-completions/',
        MeExerciseCompletionCreateView.as_view(),
        name='me-exercise-completions',
    ),
]
