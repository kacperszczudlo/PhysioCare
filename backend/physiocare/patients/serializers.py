from rest_framework import serializers

from .models import PatientProfile


class PatientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'avatar_url']


class PatientDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pesel', 'phone', 'avatar_url',
        ]
