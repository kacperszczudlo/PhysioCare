from rest_framework import permissions


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
        from core.mixins import user_can_access_patient
        return user_can_access_patient(request.user, obj)


class IsVisitParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from core.mixins import user_can_access_visit
        return user_can_access_visit(request.user, obj)


class IsEpisodeParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from core.mixins import user_can_access_episode
        return user_can_access_episode(request.user, obj)
