from rest_framework import serializers

from .models import TherapistProfile


class TherapistProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = TherapistProfile
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'pwzf_number', 'phone', 'bio', 'courses', 'avatar_url', 'created_at',
        ]
        read_only_fields = ['id', 'pwzf_number', 'created_at']


class TherapistProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistProfile
        fields = ['phone', 'bio', 'courses']


class TherapistPublicSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = TherapistProfile
        fields = [
            'id', 'first_name', 'last_name', 'bio', 'courses',
            'avatar_url', 'phone',
        ]
