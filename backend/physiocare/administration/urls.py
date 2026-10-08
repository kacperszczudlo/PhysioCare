"""Definicje tras URL dla panelu administracyjnego PhysioCare."""

from django.urls import path

from .views import (
    AdminDashboardAnalyticsView,
    AdminReviewListView,
    AdminReviewVisibilityToggleView,
    AdminSchedulingOverviewView,
    AdminTherapistStatsView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserResetPasswordView,
    AdminUserStatusToggleView,
)

app_name = 'administration'

urlpatterns = [
    # Analityka i KPI
    path('analytics/dashboard/', AdminDashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('dashboard/', AdminDashboardAnalyticsView.as_view(), name='dashboard-analytics-alias'),
    
    # Zarządzanie użytkownikami
    path('users/', AdminUserListView.as_view(), name='users-list'),
    path('users/<uuid:pk>/', AdminUserDetailView.as_view(), name='users-detail'),
    path('users/<uuid:pk>/status/', AdminUserStatusToggleView.as_view(), name='users-status-toggle'),
    path('users/<uuid:pk>/reset-password/', AdminUserResetPasswordView.as_view(), name='users-reset-password'),
    
    # Harmonogramy i Zespół
    path('scheduling/overview/', AdminSchedulingOverviewView.as_view(), name='scheduling-overview'),
    path('schedules/overview/', AdminSchedulingOverviewView.as_view(), name='schedules-overview-alias'),
    path('therapists/stats/', AdminTherapistStatsView.as_view(), name='therapists-stats'),
    
    # Moderacja Opinii
    path('reviews/', AdminReviewListView.as_view(), name='reviews-list'),
    path('reviews/<uuid:pk>/visibility/', AdminReviewVisibilityToggleView.as_view(), name='reviews-visibility-toggle'),
]
