from django.urls import path

from .views import (
    ChangePasswordView,
    CookieTokenRefreshView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PatientRegisterView,
    TherapistRegisterView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/patient/', PatientRegisterView.as_view(), name='register-patient'),
    path('register/therapist/', TherapistRegisterView.as_view(), name='register-therapist'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password-change/', ChangePasswordView.as_view(), name='password-change'),
]
