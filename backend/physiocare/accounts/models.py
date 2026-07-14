from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager

class RoleChoices(models.TextChoices):
    PATIENT = 'PATIENT', 'Pacjent'
    THERAPIST = 'THERAPIST', 'Fizjoterapeuta'
    ADMIN = 'ADMIN', 'Administrator'

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Wykorzystanie email jako głównego klucza logowania
    email = models.EmailField('adres e-mail', unique=True, max_length=355)
    role = models.CharField(
        'rola w systemie', 
        max_length=20, 
        choices=RoleChoices.choices,
        default=RoleChoices.PATIENT
    )
    
    # Flagi wymagane przez wewnętrzne mechanizmy administracyjne Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    # Rejestracja utworzonego wcześniej menedżera
    objects = CustomUserManager()

    # Informujemy Django, że pole email zastępuje domyślny username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    class Meta:
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"