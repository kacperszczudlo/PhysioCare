from django.db.models import QuerySet


class TherapistPatientQuerysetMixin:
    """Klasa pomocnicza filtrująca pacjentów przypisanych do zalogowanego terapeuty."""

    def get_therapist_profile(self) -> object:
        """Pobiera profil terapeuty powiązany z zalogowanym użytkownikiem.

        Returns:
            object: Profil terapeuty użytkownika.
        """
        request = self.request if hasattr(self, 'request') else None
        user = request.user if request is not None and hasattr(request, 'user') else None
        return user.therapist_profile if user is not None and hasattr(user, 'therapist_profile') else None

    def therapist_patients(self) -> QuerySet:
        """Pobiera queryset aktywnych pacjentów przypisanych do terapeuty.

        Returns:
            QuerySet: Queryset aktywnych profili pacjentów.
        """
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
    """Klasa pomocnicza umożliwiająca dostęp do własnego profilu pacjenta."""

    def get_patient_profile(self) -> object:
        """Pobiera profil pacjenta powiązany z zalogowanym użytkownikiem.

        Returns:
            object: Profil pacjenta użytkownika.
        """
        request = self.request if hasattr(self, 'request') else None
        user = request.user if request is not None and hasattr(request, 'user') else None
        return user.patient_profile if user is not None and hasattr(user, 'patient_profile') else None


def patient_belongs_to_therapist(patient: object, therapist_profile: object) -> bool:
    """Sprawdza, czy pacjent ma aktywne powiązanie z podanym terapeutą.

    Args:
        patient (object): Obiekt profilu pacjenta.
        therapist_profile (object): Obiekt profilu terapeuty.

    Returns:
        bool: True, jeśli istnieje aktywne powiązanie między pacjentem a terapeutą.

    Raises:
        TypeError: Gdy patient lub therapist_profile jest None.
    """
    if patient is None:
        raise TypeError("Argument 'patient' nie może być None.")
    if therapist_profile is None:
        raise TypeError("Argument 'therapist_profile' nie może być None.")

    from patients.models import PatientTherapistLink

    return PatientTherapistLink.objects.filter(
        patient=patient,
        therapist=therapist_profile,
        status='ACTIVE',
    ).exists()


def user_can_access_patient(user: object, patient: object) -> bool:
    """Sprawdza, czy użytkownik posiada dostęp do danych danego pacjenta.

    Args:
        user (object): Obiekt użytkownika składającego żądanie.
        patient (object): Obiekt profilu pacjenta.

    Returns:
        bool: True, jeśli użytkownik posiada prawo dostępu do pacjenta.

    Raises:
        TypeError: Gdy user lub patient jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if patient is None:
        raise TypeError("Argument 'patient' nie może być None.")

    user_role = user.role if hasattr(user, 'role') else ''
    patient_id = patient.id if hasattr(patient, 'id') else None

    if user_role == 'PATIENT':
        patient_profile = user.patient_profile if hasattr(user, 'patient_profile') else None
        user_patient_id = patient_profile.id if patient_profile is not None and hasattr(patient_profile, 'id') else None
        return user_patient_id == patient_id
    if user_role == 'THERAPIST':
        therapist_profile = user.therapist_profile if hasattr(user, 'therapist_profile') else None
        visits = patient.visits if hasattr(patient, 'visits') else None
        has_visit = visits.filter(therapist=therapist_profile).exists() if visits is not None and hasattr(visits, 'filter') else False
        return (
            therapist_profile is not None
            and (
                patient_belongs_to_therapist(patient, therapist_profile)
                or has_visit
            )
        )
    return bool(hasattr(user, 'is_staff') and user.is_staff)


def user_can_access_visit(user: object, visit: object) -> bool:
    """Sprawdza, czy użytkownik posiada dostęp do danej wizyty.

    Args:
        user (object): Obiekt użytkownika składającego żądanie.
        visit (object): Obiekt wizyty.

    Returns:
        bool: True, jeśli użytkownik jest pacjentem lub terapeutą powiązanym z wizytą albo administratorem.

    Raises:
        TypeError: Gdy user lub visit jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if visit is None:
        raise TypeError("Argument 'visit' nie może być None.")

    user_role = user.role if hasattr(user, 'role') else ''
    visit_patient_id = visit.patient_id if hasattr(visit, 'patient_id') else None
    visit_therapist_id = visit.therapist_id if hasattr(visit, 'therapist_id') else None

    if user_role == 'PATIENT':
        patient_profile = user.patient_profile if hasattr(user, 'patient_profile') else None
        user_patient_id = patient_profile.id if patient_profile is not None and hasattr(patient_profile, 'id') else None
        return user_patient_id == visit_patient_id
    if user_role == 'THERAPIST':
        therapist_profile = user.therapist_profile if hasattr(user, 'therapist_profile') else None
        user_therapist_id = therapist_profile.id if therapist_profile is not None and hasattr(therapist_profile, 'id') else None
        return user_therapist_id == visit_therapist_id
    return bool(hasattr(user, 'is_staff') and user.is_staff)


def user_can_access_episode(user: object, episode: object) -> bool:
    """Sprawdza, czy użytkownik posiada dostęp do epizodu leczenia.

    Args:
        user (object): Obiekt użytkownika składającego żądanie.
        episode (object): Obiekt epizodu leczenia.

    Returns:
        bool: True, jeśli użytkownik posiada dostęp do pacjenta powiązanego z epizodem.

    Raises:
        TypeError: Gdy user lub episode jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if episode is None:
        raise TypeError("Argument 'episode' nie może być None.")

    episode_patient = episode.patient if hasattr(episode, 'patient') else None
    return user_can_access_patient(user, episode_patient)

