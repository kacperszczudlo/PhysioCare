from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Niestandardowy menedżer, w którym adres e-mail jest unikalnym identyfikatorem.
    Klasa ta nadpisuje natywne metody Django, zapewniając spójność z wymaganiami projektu.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Użytkownik musi posiadać adres e-mail.'))
        
        # Normalizacja konwertuje domenę e-maila na małe litery w celu ujednolicenia
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        # Metoda set_password automatycznie poddaje hasło bezpiecznemu kryptograficznemu
        # procesowi hashowania (domyślnie PBKDF2 lub bcrypt) zapobiegając zapisowi czystym tekstem.
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """ Logika generowania kont z uprawnieniami pełnego dostępu do panelu administracyjnego. """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Konto typu Superuser musi posiadać flagę is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Konto typu Superuser musi posiadać flagę is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)