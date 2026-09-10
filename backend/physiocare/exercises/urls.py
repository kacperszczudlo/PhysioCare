from django.urls import path

from .views import (
    MeExerciseCompletionCreateView,
    MeExercisesListView,
    MeExercisesTodayView,
    TherapistExerciseAssignmentDetailView,
    TherapistExerciseAssignmentListCreateView,
    TherapistExerciseCategoryListView,
    TherapistExerciseDetailView,
    TherapistExerciseListCreateView,
)

urlpatterns = [
    path(
        'therapist/exercises/',
        TherapistExerciseListCreateView.as_view(),
        name='therapist-exercises',
    ),
    path(
        'therapist/exercises/<uuid:pk>/',
        TherapistExerciseDetailView.as_view(),
        name='therapist-exercise-detail',
    ),
    path(
        'therapist/exercise-categories/',
        TherapistExerciseCategoryListView.as_view(),
        name='therapist-exercise-categories',
    ),
    path(
        'therapist/exercise-assignments/',
        TherapistExerciseAssignmentListCreateView.as_view(),
        name='therapist-exercise-assignments',
    ),
    path(
        'therapist/exercise-assignments/<uuid:pk>/',
        TherapistExerciseAssignmentDetailView.as_view(),
        name='therapist-exercise-assignment-detail',
    ),
]

me_urlpatterns = [
    path('exercises/', MeExercisesListView.as_view(), name='me-exercises'),
    path('exercises/today/', MeExercisesTodayView.as_view(), name='me-exercises-today'),
    path(
        'exercise-completions/',
        MeExerciseCompletionCreateView.as_view(),
        name='me-exercise-completions',
    ),
]
