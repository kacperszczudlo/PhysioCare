"""Therapist/patient queryset helpers and ownership checks."""


class TherapistPatientQuerysetMixin:
    """Filtruje queryset do pacjentów przypisanych do zalogowanego terapeuty."""

    def get_therapist_profile(self):
        return self.request.user.therapist_profile

    def therapist_patients(self):
        from patients.models import PatientProfile

        return (
            PatientProfile.objects.filter(
                therapist_links__therapist=self.get_therapist_profile(),
                therapist_links__status='ACTIVE',
            )
            .active()
            .select_related('user')
            .distinct()
        )


class PatientSelfMixin:
    """Dostęp do własnego profilu pacjenta."""

    def get_patient_profile(self):
        return self.request.user.patient_profile


def patient_belongs_to_therapist(patient, therapist_profile) -> bool:
    from patients.models import PatientTherapistLink

    return PatientTherapistLink.objects.filter(
        patient=patient,
        therapist=therapist_profile,
        status='ACTIVE',
    ).exists()


def user_can_access_patient(user, patient) -> bool:
    if user.role == 'PATIENT':
        return hasattr(user, 'patient_profile') and user.patient_profile.id == patient.id
    if user.role == 'THERAPIST':
        return (
            hasattr(user, 'therapist_profile')
            and (
                patient_belongs_to_therapist(patient, user.therapist_profile)
                or patient.visits.filter(therapist=user.therapist_profile).exists()
            )
        )
    return user.is_staff


def user_can_access_visit(user, visit) -> bool:
    if user.role == 'PATIENT':
        return (
            hasattr(user, 'patient_profile')
            and visit.patient_id == user.patient_profile.id
        )
    if user.role == 'THERAPIST':
        return (
            hasattr(user, 'therapist_profile')
            and visit.therapist_id == user.therapist_profile.id
        )
    return user.is_staff


def user_can_access_episode(user, episode) -> bool:
    return user_can_access_patient(user, episode.patient)
