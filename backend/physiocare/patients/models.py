from django.db import models
from django.conf import settings

class PatientProfile(models.Model):
    # Relacja 1:1 do naszego CustomUser
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    pesel = models.CharField(max_length=11, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/patients/', blank=True, null=True)

    def __str__(self):
        return f"Karta Pacjenta: {self.first_name} {self.last_name}"