from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Menedżer modelu CustomUser obsługujący tworzenie zwykłych użytkowników oraz superużytkowników."""

    def create_user(self, email: str | None, password: str | None = None, **extra_fields: object) -> object:
        """Tworzy i zapisuje użytkownika o podanym adresie e-mail i haśle.

        Args:
            email (str | None): Adres e-mail użytkownika.
            password (str | None): Hasło użytkownika. Domyślnie None (tworzy konto bez używalnego hasła).
            **extra_fields (object): Dodatkowe pola modelu CustomUser.

        Returns:
            object: Utworzona instancja użytkownika.

        Raises:
            ValueError: Gdy adres e-mail nie zostanie podany.
            TypeError: Gdy typ podanego adresu e-mail lub hasła jest nieprawidłowy.
        """
        if email is not None and not isinstance(email, str):
            raise TypeError('Adres e-mail musi być ciągiem znaków.')
        if password is not None and not isinstance(password, str):
            raise TypeError('Hasło musi być ciągiem znaków lub None.')

        if not email:
            raise ValueError(_('Użytkownik musi posiadać adres e-mail.'))

        email = self.normalize_email(email).strip().lower()
        user = self.model(email=email, **extra_fields)
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str | None, password: str | None = None, **extra_fields: object) -> object:
        """Tworzy i zapisuje superużytkownika o podanym adresie e-mail i haśle.

        Args:
            email (str | None): Adres e-mail superużytkownika.
            password (str | None): Hasło superużytkownika.
            **extra_fields (object): Dodatkowe pola modelu CustomUser.

        Returns:
            object: Utworzona instancja superużytkownika.

        Raises:
            ValueError: Gdy flagi is_staff lub is_superuser nie mają wartości True.
            TypeError: Gdy typ podanego adresu e-mail lub hasła jest nieprawidłowy.
        """
        if email is not None and not isinstance(email, str):
            raise TypeError('Adres e-mail musi być ciągiem znaków.')
        if password is not None and not isinstance(password, str):
            raise TypeError('Hasło musi być ciągiem znaków lub None.')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'THERAPIST')
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'System')
        extra_fields.setdefault('email_verified_at', timezone.now())

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Konto typu Superuser musi posiadać flagę is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Konto typu Superuser musi posiadać flagę is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

