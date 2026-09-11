import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import CustomUserManager


class RoleChoices(models.TextChoices):
    PATIENT = 'PATIENT', 'Pacjent'
    THERAPIST = 'THERAPIST', 'Fizjoterapeuta'


class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('adres e-mail', unique=True, max_length=254)
    role = models.CharField(
        'rola w systemie',
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.PATIENT,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    google_sub = models.CharField(
        'Google subject ID',
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    email_verified_at = models.DateTimeField(
        'e-mail zweryfikowany',
        null=True,
        blank=True,
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'

    def __str__(self):
        return f'{self.email} ({self.get_role_display()})'

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class EmailCodePurpose(models.TextChoices):
    VERIFY_EMAIL = 'VERIFY_EMAIL', 'Weryfikacja e-mail'
    PASSWORD_RESET = 'PASSWORD_RESET', 'Reset hasła'


class EmailCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_codes',
    )
    purpose = models.CharField(max_length=32, choices=EmailCodePurpose.choices)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_codes'
        indexes = [
            models.Index(fields=['user', 'purpose', 'used_at'], name='idx_email_code_user_purpose'),
        ]

    def __str__(self):
        return f'{self.purpose} for {self.user.email}'


class PasswordResetToken(models.Model):
    """Short-lived token issued after a valid password-reset OTP."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f'Reset token for {self.user.email}'


class UserMFA(models.Model):
    """TOTP 2FA configuration and backup recovery codes for a user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mfa',
    )
    secret_key = models.CharField(max_length=64)
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_mfa'
        verbose_name = 'Udwierzytelnianie 2FA'
        verbose_name_plural = 'Udwierzytelniania 2FA'

    def __str__(self):
        status_str = 'enabled' if self.is_enabled else 'disabled'
        return f'MFA ({status_str}) for {self.user.email}'

