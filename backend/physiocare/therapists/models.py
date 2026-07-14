from django.db import models
from django.conf import settings

class TherapistProfile(models.Model):
    # Relacja 1:1 do naszego CustomUser
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='therapist_profile'
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    pwzf_number = models.CharField(max_length=11, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/therapists/', blank=True, null=True)

    def __str__(self):
        return f"Karta Terapeuty: {self.first_name} {self.last_name}"