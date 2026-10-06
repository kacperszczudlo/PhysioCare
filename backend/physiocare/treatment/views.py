from django.db.models import QuerySet
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import PatientSelfMixin, TherapistPatientQuerysetMixin
from core.permissions import IsEpisodeParticipant, IsPatient, IsTherapist
from notifications.events import publish_document_realtime
from patients.models import PatientProfile
from therapists.medical_devices import catalog_as_list, groups_summary

from .models import (
    DEVICE_ORDER_DISCLAIMER,
    BodyAreaPain,
    DeviceOrderStatus,
    DiagnosticRecommendation,
    EpisodeStatus,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
    VisitNote,
)
from .patient_documents import KIND_LABELS, build_clinical_documents_for_patient
from .serializers import (
    BodyAreaPainSerializer,
    DiagnosticRecommendationSerializer,
    MedicalDeviceOrderSerializer,
    PatientEpisodeSerializer,
    PhysicianOrderRefusalSerializer,
    ReceptaNaRuchReferralSerializer,
    TreatmentEpisodeCreateSerializer,
    TreatmentEpisodeSerializer,
    VisitNoteSerializer,
)


def _get_owned_episode(request: object, episode_id: object) -> TreatmentEpisode:
    """Pobiera epizod leczenia i weryfikuje uprawnienia dostępu użytkownika.

    Args:
        request (object): Obiekt żądania HTTP.
        episode_id (object): Identyfikator epizodu leczenia.

    Returns:
        TreatmentEpisode: Obiekt epizodu leczenia.

    Raises:
        NotFound: Gdy epizod nie istnieje lub użytkownik nie ma do niego dostępu.
        TypeError: Gdy parametr request nie jest obiektem.
    """
    from core.mixins import user_can_access_patient

    if request is None:
        raise TypeError('Parametr request nie może być None.')
    if not hasattr(request, 'user'):
        raise NotFound()

    episode = TreatmentEpisode.objects.select_related('patient', 'therapist').filter(pk=episode_id).first()
    if episode is None:
        raise NotFound()
    if not user_can_access_patient(request.user, episode.patient):
        raise NotFound()
    return episode


def _check_therapist_ownership(obj: object, request: object) -> None:
    """Sprawdza, czy fizjoterapeuta zgłaszający żądanie jest właścicielem wpisu.

    Args:
        obj (object): Obiekt z atrybutem therapist_id.
        request (object): Obiekt żądania HTTP z uwierzytelnionym użytkownikiem.

    Raises:
        PermissionDenied: Gdy użytkownik nie posiada profilu fizjoterapeuty lub nie jest właścicielem obiektu.
        TypeError: Gdy parametry są nieprawidłowe.
    """
    if obj is None or request is None:
        raise TypeError('Parametry obj oraz request nie mogą być None.')
    if not hasattr(request, 'user'):
        raise PermissionDenied('Możesz edytować i usuwać tylko własne wpisy.')
    therapist = request.user.therapist_profile if hasattr(request.user, 'therapist_profile') else None
    therapist_id = obj.therapist_id if hasattr(obj, 'therapist_id') else None
    if not therapist or (therapist_id is not None and therapist_id != therapist.id):
        raise PermissionDenied('Możesz edytować i usuwać tylko własne wpisy.')


class PatientEpisodeListCreateView(TherapistPatientQuerysetMixin, generics.ListCreateAPIView):
    """Widok listy i tworzenia epizodów leczenia dla konkretnego pacjenta."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get_patient(self) -> PatientProfile:
        """Pobiera profil pacjenta przypisanego do fizjoterapeuty na podstawie id z adresacji URL.

        Returns:
            PatientProfile: Profil pacjenta.

        Raises:
            NotFound: Gdy pacjent nie zostanie odnaleziony w relacji z fizjoterapeutą.
        """
        try:
            return self.therapist_patients().get(pk=self.kwargs['patient_id'])
        except PatientProfile.DoesNotExist as exc:
            raise NotFound() from exc

    def get_queryset(self) -> QuerySet:
        """Zwraca queryset epizodów leczenia wskazanego pacjenta.

        Returns:
            QuerySet: Zbiór epizodów leczenia pacjenta.
        """
        return TreatmentEpisode.objects.filter(
            patient=self.get_patient(),
        ).select_related('patient', 'patient__user', 'therapist', 'therapist__user').order_by('-created_at')

    def get_serializer_class(self) -> type[serializers.Serializer]:
        """Dobiera odpowiednią klasę serializatora w zależności od metody HTTP.

        Returns:
            type[serializers.Serializer]: Klasa serializatora DRF.
        """
        if self.request.method == 'POST':
            return TreatmentEpisodeCreateSerializer
        return TreatmentEpisodeSerializer

    def create(self, request: object, *args: object, **kwargs: object) -> Response:
        """Tworzy nowy epizod leczenia dla pacjenta.

        Args:
            request (object): Obiekt żądania HTTP.
            *args (object): Dodatkowe argumenty pozycyjne.
            **kwargs (object): Dodatkowe argumenty kluczowe.

        Returns:
            Response: Odpowiedź HTTP z utworzonym epizodem leczenia.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        serializer = self.get_serializer(data=request.data if hasattr(request, 'data') else None)
        serializer.is_valid(raise_exception=True)
        episode = serializer.save(
            patient=self.get_patient(),
            therapist=request.user.therapist_profile,
        )
        return Response(
            TreatmentEpisodeSerializer(episode, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class EpisodeDetailView(generics.RetrieveUpdateAPIView):
    """Widok pobierania szczegółów oraz aktualizacji epizodu leczenia."""

    serializer_class = TreatmentEpisodeSerializer
    permission_classes = [IsAuthenticated, IsTherapist, IsEpisodeParticipant]

    def get_queryset(self) -> QuerySet:
        """Zwraca epizody leczenia dostępne dla aktualnie zalogowanego fizjoterapeuty.

        Returns:
            QuerySet: Zbiór dostępnych epizodów leczenia.
        """
        return TreatmentEpisode.objects.filter(
            patient__therapist_links__therapist=self.request.user.therapist_profile,
            patient__therapist_links__status='ACTIVE',
        ).select_related('patient', 'patient__user', 'therapist', 'therapist__user').distinct()

    def perform_update(self, serializer: object) -> None:
        """Zapisuje aktualizację epizodu po weryfikacji prawa własności fizjoterapeuty.

        Args:
            serializer (object): Serializator z zebranymi danymi.

        Raises:
            PermissionDenied: Gdy fizjoterapeuta próbuje edytować epizod stworzony przez innego fizjoterapeutę.
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        episode = self.get_object()
        therapist = self.request.user.therapist_profile
        if episode.therapist_id is not None and episode.therapist_id != therapist.id:
            raise PermissionDenied('Epizod leczenia utworzony przez innego fizjoterapeutę jest tylko do odczytu.')
        serializer.save()


class EpisodeBodyPainListCreateView(generics.ListCreateAPIView):
    """Widok pobierania listy oraz rejestrowania lokalizacji i natężenia bólu pacjenta."""

    serializer_class = BodyAreaPainSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self) -> TreatmentEpisode:
        """Pobiera zweryfikowany epizod leczenia.

        Returns:
            TreatmentEpisode: Obiekt epizodu leczenia.
        """
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self) -> QuerySet:
        """Zwraca wpisy bólów obszarów ciała dla określonego epizodu.

        Returns:
            QuerySet: Zbiór wpisów bólu.
        """
        return BodyAreaPain.objects.filter(episode=self.get_episode())

    def perform_create(self, serializer: object) -> None:
        """Utwierdza nowy wpis bólu w epizodzie.

        Args:
            serializer (object): Serializator z danymi wpisu bólu.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        serializer.save(episode=self.get_episode())


class EpisodeBodyPainDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, edycji i usuwania wpisu o bólach obszaru ciała."""

    serializer_class = BodyAreaPainSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet:
        """Zwraca wpisy o bólach dostępne dla aktywnego fizjoterapeuty.

        Returns:
            QuerySet: Dostępne wpisy o bólach.
        """
        return BodyAreaPain.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist_links__therapist=self.request.user.therapist_profile,
            episode__patient__therapist_links__status='ACTIVE',
        ).distinct()

    def perform_update(self, serializer: object) -> None:
        """Aktualizuje wpis o bólu po weryfikacji uprawnień.

        Args:
            serializer (object): Serializator wpisu bólu.

        Raises:
            PermissionDenied: Gdy epizod należy do innego fizjoterapeuty.
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        episode = serializer.instance.episode
        if episode.therapist_id is not None and episode.therapist_id != self.request.user.therapist_profile.id:
            raise PermissionDenied('Epizod leczenia utworzony przez innego fizjoterapeutę jest tylko do odczytu.')
        serializer.save()

    def perform_destroy(self, instance: object) -> None:
        """Usuwa wpis o bólu po weryfikacji uprawnień.

        Args:
            instance (object): Wpis bólu do usunięcia.

        Raises:
            PermissionDenied: Gdy epizod należy do innego fizjoterapeuty.
            TypeError: Gdy instance jest None.
        """
        if instance is None:
            raise TypeError('Parametr instance nie może być None.')
        episode = instance.episode
        if episode.therapist_id is not None and episode.therapist_id != self.request.user.therapist_profile.id:
            raise PermissionDenied('Epizod leczenia utworzony przez innego fizjoterapeutę jest tylko do odczytu.')
        instance.delete()


class EpisodeNoteListCreateView(generics.ListCreateAPIView):
    """Widok listy oraz tworzenia notatek z wizyt w ramach epizodu leczenia."""

    serializer_class = VisitNoteSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self) -> TreatmentEpisode:
        """Pobiera epizod leczenia przypisany do żądania.

        Returns:
            TreatmentEpisode: Obiekt epizodu.
        """
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self) -> QuerySet:
        """Zwraca notatki z wizyt sporządzone przez aktualnego fizjoterapeutę.

        Returns:
            QuerySet: Zbiór notatek z wizyt.
        """
        return VisitNote.objects.filter(
            episode=self.get_episode(),
            therapist=self.request.user.therapist_profile,
        ).select_related('therapist', 'therapist__user').order_by('-created_at')

    def perform_create(self, serializer: object) -> None:
        """Zapisuje nową notatkę z wizyty.

        Args:
            serializer (object): Serializator notatki z wizyty.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        serializer.save(
            episode=self.get_episode(),
            therapist=self.request.user.therapist_profile,
        )

    def get_serializer_context(self) -> dict[str, object]:
        """Dodaje obiekt epizodu do kontekstu serializatora.

        Returns:
            dict[str, object]: Kontekst serializatora.
        """
        context = super().get_serializer_context()
        context['episode'] = self.get_episode()
        return context


class EpisodeDiagnosticRecommendationListCreateView(generics.ListCreateAPIView):
    """Widok listy oraz tworzenia rekomendacji diagnostycznych w epizodzie."""

    serializer_class = DiagnosticRecommendationSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self) -> TreatmentEpisode:
        """Pobiera epizod leczenia.

        Returns:
            TreatmentEpisode: Obiekt epizodu leczenia.
        """
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self) -> QuerySet:
        """Zwraca rekomendacje diagnostyczne powiązane z epizodem.

        Returns:
            QuerySet: Rekomendacje diagnostyczne.
        """
        return DiagnosticRecommendation.objects.filter(
            episode=self.get_episode(),
        ).select_related('therapist', 'therapist__user')

    def perform_create(self, serializer: object) -> None:
        """Tworzy rekomendację diagnostyczną i publikuje powiadomienie w czasie rzeczywistym.

        Args:
            serializer (object): Serializator rekomendacji.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        episode = self.get_episode()
        recommendation = serializer.save(
            episode=episode,
            therapist=self.request.user.therapist_profile,
        )
        if recommendation.red_flags_noted and episode.status == EpisodeStatus.IN_PROGRESS:
            episode.status = EpisodeStatus.REFERRED
            episode.save(update_fields=['status'])
        publish_document_realtime(episode.patient, recommendation.id)


class EpisodeDeviceOrderListCreateView(generics.ListCreateAPIView):
    """Widok listy oraz wystawiania zleceń na wyroby medyczne."""

    serializer_class = MedicalDeviceOrderSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self) -> TreatmentEpisode:
        """Pobiera epizod leczenia.

        Returns:
            TreatmentEpisode: Obiekt epizodu.
        """
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self) -> QuerySet:
        """Zwraca zlecenia na wyroby medyczne w ramach epizodu.

        Returns:
            QuerySet: Zlecenia na wyroby medyczne.
        """
        return MedicalDeviceOrder.objects.filter(
            episode=self.get_episode(),
        ).select_related('therapist', 'therapist__user')

    def perform_create(self, serializer: object) -> None:
        """Wystawia zlecenie na wyrób medyczny i publikuje powiadomienie po wystawieniu.

        Args:
            serializer (object): Serializator zlecenia wyrobu.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        episode = self.get_episode()
        order = serializer.save(
            episode=episode,
            patient=episode.patient,
            therapist=self.request.user.therapist_profile,
        )
        if order.status == DeviceOrderStatus.ISSUED:
            publish_document_realtime(episode.patient, order.id)


class EpisodeOrderRefusalListCreateView(generics.ListCreateAPIView):
    """Widok listy oraz rejestrowania odmów wykonania zlecenia lekarskiego."""

    serializer_class = PhysicianOrderRefusalSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_episode(self) -> TreatmentEpisode:
        """Pobiera epizod leczenia.

        Returns:
            TreatmentEpisode: Obiekt epizodu.
        """
        return _get_owned_episode(self.request, self.kwargs['episode_id'])

    def get_queryset(self) -> QuerySet:
        """Zwraca rejestr odmów zlecenia lekarskiego w epizodzie.

        Returns:
            QuerySet: Rekordy odmów wykonania zlecenia.
        """
        return PhysicianOrderRefusal.objects.filter(
            episode=self.get_episode(),
        ).select_related('therapist', 'therapist__user')

    def perform_create(self, serializer: object) -> None:
        """Tworzy wpis odmowy wykonania zlecenia lekarskiego.

        Args:
            serializer (object): Serializator odmowy zlecenia.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        episode = self.get_episode()
        refusal = serializer.save(
            episode=episode,
            therapist=self.request.user.therapist_profile,
        )
        publish_document_realtime(episode.patient, refusal.id)


class EpisodeDiagnosticRecommendationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, aktualizacji i usuwania rekomendacji diagnostycznej."""

    serializer_class = DiagnosticRecommendationSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet:
        """Zwraca rekomendacje diagnostyczne dostępne dla fizjoterapeuty.

        Returns:
            QuerySet: Zbiór rekomendacji.
        """
        return DiagnosticRecommendation.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist_links__therapist=self.request.user.therapist_profile,
            episode__patient__therapist_links__status='ACTIVE',
        ).select_related('episode', 'therapist', 'therapist__user').distinct()

    def perform_update(self, serializer: object) -> None:
        """Aktualizuje rekomendację po sprawdzeniu prawa własności wpisu.

        Args:
            serializer (object): Serializator rekomendacji.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        _check_therapist_ownership(serializer.instance, self.request)
        recommendation = serializer.save()
        episode = recommendation.episode
        if recommendation.red_flags_noted and episode.status == EpisodeStatus.IN_PROGRESS:
            episode.status = EpisodeStatus.REFERRED
            episode.save(update_fields=['status'])

    def perform_destroy(self, instance: object) -> None:
        """Usuwa rekomendację diagnostyczną po weryfikacji właściciela.

        Args:
            instance (object): Obiekt rekomendacji do usunięcia.

        Raises:
            TypeError: Gdy instance jest None.
        """
        if instance is None:
            raise TypeError('Parametr instance nie może być None.')
        _check_therapist_ownership(instance, self.request)
        instance.delete()


class EpisodeDeviceOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, aktualizacji i usuwania zlecenia na wyrób medyczny."""

    serializer_class = MedicalDeviceOrderSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet:
        """Zwraca zlecenia na wyroby medyczne dostępne dla aktywnego fizjoterapeuty.

        Returns:
            QuerySet: Zlecenia na wyroby medyczne.
        """
        return MedicalDeviceOrder.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist_links__therapist=self.request.user.therapist_profile,
            episode__patient__therapist_links__status='ACTIVE',
        ).select_related('therapist', 'therapist__user').distinct()

    def perform_update(self, serializer: object) -> None:
        """Aktualizuje zlecenie wyrobu medycznego po weryfikacji prawa własności.

        Args:
            serializer (object): Serializator zlecenia wyrobu.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        _check_therapist_ownership(serializer.instance, self.request)
        serializer.save()

    def perform_destroy(self, instance: object) -> None:
        """Usuwa zlecenie na wyrób medyczny po weryfikacji prawa własności.

        Args:
            instance (object): Obiekt zlecenia wyrobu.

        Raises:
            TypeError: Gdy instance jest None.
        """
        if instance is None:
            raise TypeError('Parametr instance nie może być None.')
        _check_therapist_ownership(instance, self.request)
        instance.delete()


class EpisodeOrderRefusalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, edycji i usuwania odmowy wykonania zlecenia lekarskiego."""

    serializer_class = PhysicianOrderRefusalSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet:
        """Zwraca odmowy zlecenia lekarskiego dostępne dla fizjoterapeuty.

        Returns:
            QuerySet: Zbiór odmów zleceń lekarskich.
        """
        return PhysicianOrderRefusal.objects.filter(
            episode_id=self.kwargs['episode_id'],
            episode__patient__therapist_links__therapist=self.request.user.therapist_profile,
            episode__patient__therapist_links__status='ACTIVE',
        ).select_related('therapist', 'therapist__user').distinct()

    def perform_update(self, serializer: object) -> None:
        """Aktualizuje odmowę zlecenia po weryfikacji autorstwa.

        Args:
            serializer (object): Serializator odmowy zlecenia.

        Raises:
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        _check_therapist_ownership(serializer.instance, self.request)
        serializer.save()

    def perform_destroy(self, instance: object) -> None:
        """Usuwa odmowę zlecenia lekarskiego po weryfikacji autorstwa.

        Args:
            instance (object): Wpis odmowy zlecenia do usunięcia.

        Raises:
            TypeError: Gdy instance jest None.
        """
        if instance is None:
            raise TypeError('Parametr instance nie może być None.')
        _check_therapist_ownership(instance, self.request)
        instance.delete()


class PatientReceptaNaRuchListCreateView(TherapistPatientQuerysetMixin, generics.ListCreateAPIView):
    """Widok listy oraz wystawiania skierowań do programu Recepta na Ruch."""

    serializer_class = ReceptaNaRuchReferralSerializer
    permission_classes = [IsAuthenticated, IsTherapist]

    def get_patient(self) -> PatientProfile:
        """Pobiera pacjenta na podstawie identyfikatora w URL.

        Returns:
            PatientProfile: Obiekt profilu pacjenta.

        Raises:
            NotFound: Gdy pacjent nie istnieje w relacji z fizjoterapeutą.
        """
        try:
            return self.therapist_patients().get(pk=self.kwargs['patient_id'])
        except PatientProfile.DoesNotExist as exc:
            raise NotFound() from exc

    def get_queryset(self) -> QuerySet:
        """Zwraca skierowania do Recepty na Ruch dla pacjenta.

        Returns:
            QuerySet: Zbiór skierowań Recepta na Ruch.
        """
        return ReceptaNaRuchReferral.objects.filter(
            patient=self.get_patient(),
        ).select_related('therapist', 'therapist__user', 'episode')

    def perform_create(self, serializer: object) -> None:
        """Tworzy nowe skierowanie Recepta na Ruch i publikuje zdarzenie powiadomienia.

        Args:
            serializer (object): Serializator skierowania.

        Raises:
            ValidationError: Gdy wybrany epizod nie należy do danego pacjenta.
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        patient = self.get_patient()
        episode = serializer.validated_data.get('episode') if hasattr(serializer, 'validated_data') else None
        if episode is not None and episode.patient_id != patient.id:
            raise ValidationError({'episode': 'Epizod nie należy do tego pacjenta.'})
        referral = serializer.save(
            patient=patient,
            therapist=self.request.user.therapist_profile,
        )
        if referral.status == DeviceOrderStatus.ISSUED:
            publish_document_realtime(patient, referral.id)


class PatientReceptaNaRuchDetailView(TherapistPatientQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    """Widok szczegółów, edycji oraz usuwania skierowania Recepta na Ruch."""

    serializer_class = ReceptaNaRuchReferralSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self) -> QuerySet:
        """Zwraca skierowania Recepta na Ruch dla wskazanego pacjenta i aktywnej relacji.

        Returns:
            QuerySet: Skierowania Recepta na Ruch.
        """
        return ReceptaNaRuchReferral.objects.filter(
            patient_id=self.kwargs['patient_id'],
            patient__therapist_links__therapist=self.get_therapist_profile(),
            patient__therapist_links__status='ACTIVE',
            patient__user__is_active=True,
        ).select_related('therapist', 'therapist__user').distinct()

    def perform_update(self, serializer: object) -> None:
        """Aktualizuje skierowanie Recepta na Ruch.

        Args:
            serializer (object): Serializator skierowania.

        Raises:
            NotFound: Gdy pacjent nie zostanie odnaleziony.
            ValidationError: Gdy powiązany epizod nie należy do pacjenta.
            TypeError: Gdy serializer nie jest instancją Serializer.
        """
        if serializer is None or not isinstance(serializer, serializers.Serializer):
            raise TypeError('Parametr serializer musi być instancją Serializer.')
        _check_therapist_ownership(serializer.instance, self.request)
        patient = self.therapist_patients().filter(pk=self.kwargs['patient_id']).first()
        if patient is None:
            raise NotFound()
        episode = serializer.validated_data.get('episode') if hasattr(serializer, 'validated_data') else None
        if episode is not None and episode.patient_id != patient.id:
            raise ValidationError({'episode': 'Epizod nie należy do tego pacjenta.'})
        serializer.save()

    def perform_destroy(self, instance: object) -> None:
        """Usuwa skierowanie Recepta na Ruch po weryfikacji własności.

        Args:
            instance (object): Obiekt skierowania do usunięcia.

        Raises:
            TypeError: Gdy instance jest None.
        """
        if instance is None:
            raise TypeError('Parametr instance nie może być None.')
        _check_therapist_ownership(instance, self.request)
        instance.delete()


class MedicalDeviceCatalogView(APIView):
    """Widok katalogu wyrobów medycznych dopasowanego do poziomu kwalifikacji fizjoterapeuty."""

    permission_classes = [IsAuthenticated, IsTherapist]

    def get(self, request: object) -> Response:
        """Zwraca katalog wyrobów medycznych, podsumowanie grup oraz migawkę kompetencji.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Odpowiedź zawierająca pozycje katalogowe i metadane uprawnień.

        Raises:
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        therapist = request.user.therapist_profile
        return Response({
            'groups': groups_summary(),
            'items': catalog_as_list(qualification_level=therapist.qualification_level),
            'competences': therapist.competence_snapshot().to_dict(),
            'disclaimer': DEVICE_ORDER_DISCLAIMER,
        })


class MeClinicalDocumentsListView(PatientSelfMixin, APIView):
    """Skrzynka dokumentacji pacjenta: kierowanie, wyroby, odmowy, Recepta na Ruch."""

    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request: object) -> Response:
        """Zwraca listę dokumentów klinicznych dostępnych dla zalogowanego pacjenta.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Lista przefiltrowanych dokumentów medycznych.

        Raises:
            ValidationError: Gdy parametr filtracji kind jest nieprawidłowy.
            TypeError: Gdy parametr request jest None.
        """
        if request is None:
            raise TypeError('Parametr request nie może być None.')
        kind = request.query_params.get('kind') or None if hasattr(request, 'query_params') else None
        if kind is not None and kind not in KIND_LABELS:
            raise ValidationError({
                'kind': (
                    f'Nieznany rodzaj. Dozwolone: {", ".join(sorted(KIND_LABELS))}.'
                ),
            })
        results = build_clinical_documents_for_patient(
            self.get_patient_profile(),
            kind=kind,
        )
        return Response({'count': len(results), 'results': results})


class MeEpisodeListView(PatientSelfMixin, generics.ListAPIView):
    """Lista własnych epizodów leczenia pacjenta (bez notatek klinicznych)."""

    serializer_class = PatientEpisodeSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet:
        """Zwraca epizody leczenia przypisane do zalogowanego pacjenta.

        Returns:
            QuerySet: Zbiór epizodów leczenia pacjenta.
        """
        return TreatmentEpisode.objects.filter(
            patient=self.get_patient_profile(),
        ).select_related('patient', 'therapist', 'therapist__user').order_by('-created_at')


class MeEpisodeDetailView(PatientSelfMixin, generics.RetrieveAPIView):
    """Szczegóły pojedynczego epizodu leczenia widoczne dla pacjenta."""

    serializer_class = PatientEpisodeSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet:
        """Zwraca epizod leczenia powiązany z zalogowanym pacjentem.

        Returns:
            QuerySet: Epizody leczenia pacjenta.
        """
        return TreatmentEpisode.objects.filter(
            patient=self.get_patient_profile(),
        ).select_related('patient', 'therapist', 'therapist__user')
