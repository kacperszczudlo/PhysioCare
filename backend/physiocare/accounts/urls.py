from django.urls import path

from .views import (
    ChangePasswordView,
    CookieTokenRefreshView,
    EmailResendView,
    EmailVerifyView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PatientRegisterView,
    TherapistRegisterView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('google/', GoogleLoginView.as_view(), name='login-google'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/patient/', PatientRegisterView.as_view(), name='register-patient'),
    path('register/therapist/', TherapistRegisterView.as_view(), name='register-therapist'),
    path('email/verify/', EmailVerifyView.as_view(), name='email-verify'),
    path('email/resend/', EmailResendView.as_view(), name='email-resend'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password-change/', ChangePasswordView.as_view(), name='password-change'),
]
