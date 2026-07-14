import logging

from rest_framework import permissions

logger = logging.getLogger('physiocare.auth')


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'PATIENT'
        )


class IsTherapist(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'THERAPIST'
        )


class IsOwnerPatientProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'PATIENT':
            return hasattr(request.user, 'patient_profile') and obj.user_id == request.user.id
        if request.user.role == 'THERAPIST':
            return (
                hasattr(request.user, 'therapist_profile')
                and obj.therapist_id == request.user.therapist_profile.id
            )
        return request.user.is_staff
