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


class PasswordResetToken(models.Model):
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
