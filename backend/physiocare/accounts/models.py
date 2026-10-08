import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from core.fields import EncryptedCharField

from .managers import CustomUserManager


class RoleChoices(models.TextChoices):
    """Dostępne role użytkowników w systemie PhysioCare."""

    PATIENT = 'PATIENT', 'Pacjent'
    THERAPIST = 'THERAPIST', 'Fizjoterapeuta'
    ADMIN = 'ADMIN', 'Administrator'


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Niestandardowy model użytkownika w systemie PhysioCare.

    Używa adresu e-mail jako głównego identyfikatora logowania.
    """

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email: models.EmailField = models.EmailField('adres e-mail', unique=True, max_length=254)
    role: models.CharField = models.CharField(
        'rola w systemie',
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.PATIENT,
    )
    first_name: models.CharField = models.CharField(max_length=100)
    last_name: models.CharField = models.CharField(max_length=100)
    google_sub: models.CharField = models.CharField(
        'Google subject ID',
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    email_verified_at: models.DateTimeField = models.DateTimeField(
        'e-mail zweryfikowany',
        null=True,
        blank=True,
    )
    is_staff: models.BooleanField = models.BooleanField(default=False)
    is_active: models.BooleanField = models.BooleanField(default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    objects: CustomUserManager = CustomUserManager()

    USERNAME_FIELD: str = 'email'
    REQUIRED_FIELDS: list[str] = ['role', 'first_name', 'last_name']

    class Meta:
        db_table: str = 'users'
        verbose_name: str = 'Użytkownik'
        verbose_name_plural: str = 'Użytkownicy'
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='uniq_users_email_lower',
            ),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową użytkownika.

        Returns:
            str: Adres e-mail oraz rola użytkownika.
        """
        return f'{self.email} ({self.get_role_display()})'

    @property
    def email_verified(self) -> bool:
        """Sprawdza, czy adres e-mail użytkownika został zweryfikowany.

        Returns:
            bool: True jeśli adres e-mail jest zweryfikowany, False w przeciwnym razie.
        """
        return self.email_verified_at is not None


class EmailCodePurpose(models.TextChoices):
    """Cele generowania jednorazowych kodów weryfikacyjnych e-mail."""

    VERIFY_EMAIL = 'VERIFY_EMAIL', 'Weryfikacja e-mail'
    PASSWORD_RESET = 'PASSWORD_RESET', 'Reset hasła'
    MFA_SETUP = 'MFA_SETUP', 'Konfiguracja MFA'


class EmailCode(models.Model):
    """Model reprezentujący jednorazowy kod weryfikacyjny wysłany pocztą e-mail."""

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_codes',
    )
    purpose: models.CharField = models.CharField(max_length=32, choices=EmailCodePurpose.choices)
    code_hash: models.CharField = models.CharField(max_length=128)
    expires_at: models.DateTimeField = models.DateTimeField()
    used_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    attempts: models.PositiveSmallIntegerField = models.PositiveSmallIntegerField(default=0)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table: str = 'email_codes'
        indexes: list[models.Index] = [
            models.Index(fields=['user', 'purpose', 'used_at'], name='idx_email_code_user_purpose'),
        ]

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową kodu weryfikacyjnego.

        Returns:
            str: Opis celu i adresu e-mail użytkownika.
        """
        return f'{self.purpose} for {self.user.email}'


class PasswordResetToken(models.Model):
    """Krótkotrwały token wydawany po poprawnej weryfikacji kodu OTP resetu hasła."""

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user: models.ForeignKey = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token_hash: models.CharField = models.CharField(max_length=128, unique=True)
    expires_at: models.DateTimeField = models.DateTimeField()
    used_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table: str = 'password_reset_tokens'

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową tokenu resetu hasła.

        Returns:
            str: Opis tokenu dla danego użytkownika.
        """
        return f'Reset token for {self.user.email}'


class UserMFA(models.Model):
    """Konfiguracja dwuskładnikowej autentykacji TOTP 2FA oraz kody zapasowe użytkownika."""

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user: models.OneToOneField = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='mfa',
    )
    secret_key = EncryptedCharField(max_length=255)
    setup_token_hash: models.CharField = models.CharField(max_length=64, blank=True, default='')
    is_enabled: models.BooleanField = models.BooleanField(default=False)
    backup_codes: models.JSONField = models.JSONField(default=list, blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table: str = 'user_mfa'
        verbose_name: str = 'Udwierzytelnianie 2FA'
        verbose_name_plural: str = 'Udwierzytelniania 2FA'

    def __str__(self) -> str:
        """Zwraca reprezentację tekstową konfiguracji 2FA.

        Returns:
            str: Opis stanu aktywacji 2FA oraz adresu e-mail.
        """
        status_str = 'enabled' if self.is_enabled else 'disabled'
        return f'MFA ({status_str}) for {self.user.email}'
