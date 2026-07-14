from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import PatientProfile
from .serializers import PatientProfileSerializer

class PatientListView(generics.ListAPIView):
    # Wskazujemy skąd Django ma pobrać dane
    queryset = PatientProfile.objects.all()
    # Wskazujemy jakiego "tłumacza" użyć do formatu JSON
    serializer_class = PatientProfileSerializer