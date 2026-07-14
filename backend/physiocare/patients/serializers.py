from rest_framework import serializers
from .models import PatientProfile

class PatientProfileSerializer(serializers.ModelSerializer):
    # Wyciągamy e-mail logowania bezpośrednio z połączonej tabeli CustomUser
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = PatientProfile
        # Definiujemy, które dokładnie kolumny chcemy upublicznić w naszym API
        fields = ['id', 'email', 'first_name', 'last_name', 'pesel', 'phone_number']