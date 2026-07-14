# accounts/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from patients.models import PatientProfile
# Załóżmy, że model Consent jest w odpowiedniej aplikacji (np. privacy/models.py)
# from privacy.models import Consent 

User = get_user_model()

class PatientRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializator dedykowany wielowarstwowemu procesowi rejestracji nowego pacjenta w systemie (UC-02).
    """
    # Te pola przyjmujemy od klienta (write_only), ale nie należą one bezpośrednio do modelu User
    first_name = serializers.CharField(max_length=150, write_only=True)
    last_name = serializers.CharField(max_length=150, write_only=True)
    
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Słownik ewaluujący wejścia z obszarów checkboxów polityk prywatności
    consents = serializers.DictField(child=serializers.BooleanField(), write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'consents')
        read_only_fields = ('id',)

    def validate_consents(self, value):
        """ Walidacja biznesowa: pacjent musi zaznaczyć oba checkboxy """
        if not value.get('terms', False):
            raise serializers.ValidationError("System odrzuca zgłoszenia pozbawione autoryzacji regulaminu.")
        if not value.get('medical_data', False):
            raise serializers.ValidationError("Przetwarzanie danych medycznych uwarunkowane jest zgodą formalną.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # UWAGA: Wyciąganie danych z użyciem .pop()
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        consents_data = validated_data.pop('consents')
        
        # Etap 1: Utworzenie centralnego profilu logowania dla rekordu CustomUser 
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data.pop('password'), # Hasło też musimy wyciągnąć osobno
            role='PATIENT'
        )
        
        # Etap 2: Stworzenie kartoteki sprzężonej w profilach relacji PatientProfile
        PatientProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name
        )
        
        # Etap 3: Rejestracja zgód RODO (Zakładając, że masz aplikację 'privacy' i model 'Consent')
        # Consent.objects.create(
        #     user=user,
        #     terms_accepted=consents_data['terms'],
        #     medical_accepted=consents_data['medical_data']
        # )
        
        return user