from django.utils import timezone
from rest_framework import serializers

from scheduling.models import Visit, VisitStatus

from .models import Review


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer tworzenia opinii przez pacjenta.

    Waliduje, że wizyta jest zakończona i nie ma jeszcze opinii.
    Kontekst musi zawierać 'visit' i 'request'.
    """

    class Meta:
        """Metadane serializatora ReviewCreateSerializer."""

        model = Review
        fields = ['rating', 'comment', 'is_anonymous']

    def validate_rating(self, value: int) -> int:
        """Waliduje ocenę w skali 1–5.

        Args:
            value (int): Wartość oceny.

        Returns:
            int: Zwalidowana ocena.

        Raises:
            serializers.ValidationError: Gdy ocena jest poza zakresem 1–5.
        """
        if not isinstance(value, int) or value < 1 or value > 5:
            raise serializers.ValidationError('Ocena musi być liczbą całkowitą w zakresie 1–5.')
        return value

    def validate(self, data: dict) -> dict:
        """Waliduje spójność danych: wizyta musi być zakończona i bez opinii.

        Args:
            data (dict): Dane wejściowe do walidacji.

        Returns:
            dict: Zwalidowane dane.

        Raises:
            serializers.ValidationError: Gdy wizyta nie jest zakończona lub ma już opinię.
        """
        visit = self.context.get('visit')
        if visit is None:
            raise serializers.ValidationError('Brak kontekstu wizyty.')

        if visit.status != VisitStatus.COMPLETED:
            raise serializers.ValidationError(
                {'non_field_errors': 'Opinia może dotyczyć wyłącznie zakończonej wizyty.'}
            )

        if hasattr(visit, 'review') and visit.review is not None:
            raise serializers.ValidationError(
                {'non_field_errors': 'Ta wizyta ma już wystawioną opinię.'}
            )

        request = self.context.get('request')
        if request is None:
            raise serializers.ValidationError('Brak kontekstu żądania.')

        patient_profile = getattr(request.user, 'patient_profile', None)
        if patient_profile is None or visit.patient_id != patient_profile.id:
            raise serializers.ValidationError(
                {'non_field_errors': 'Możesz wystawiać opinie tylko do własnych wizyt.'}
            )

        return data

    def create(self, validated_data: dict) -> Review:
        """Tworzy nową opinię powiązaną z wizytą i terapeutą poprzez warstwę usług.

        Args:
            validated_data (dict): Zwalidowane dane do zapisu.

        Returns:
            Review: Nowo utworzona opinia.
        """
        from .services import review_create_service

        visit = self.context['visit']
        request = self.context['request']
        patient = request.user.patient_profile
        return review_create_service(
            visit=visit,
            patient=patient,
            therapist=visit.therapist,
            **validated_data,
        )


class TherapistDirectReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer tworzenia opinii bezpośrednio z profilu fizjoterapeuty.

    Sprawdza, czy pacjent nie dodał już recenzji dla tego fizjoterapeuty.
    Jeśli pacjent posiada zakończoną wizytę bez recenzji u tego terapeuty,
    automatycznie wiąże opinię z tą wizytą (Verified Review).
    """

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'is_anonymous']

    def validate_rating(self, value: int) -> int:
        if not isinstance(value, int) or value < 1 or value > 5:
            raise serializers.ValidationError('Ocena musi być liczbą całkowitą w zakresie 1–5.')
        return value

    def validate(self, data: dict) -> dict:
        request = self.context.get('request')
        therapist = self.context.get('therapist')
        if not request or not therapist:
            raise serializers.ValidationError('Brak wymaganego kontekstu.')

        patient = getattr(request.user, 'patient_profile', None)
        if not patient:
            raise serializers.ValidationError('Tylko zalogowany pacjent może dodać opinię.')

        existing = Review.objects.filter(patient=patient, therapist=therapist).first()
        if existing:
            raise serializers.ValidationError(
                {
                    'non_field_errors': 'Dodałeś już opinię dla tego fizjoterapeuty. Możesz ją edytować.'
                }
            )

        return data

    def create(self, validated_data: dict) -> Review:
        from .services import review_create_service

        request = self.context['request']
        therapist = self.context['therapist']
        patient = request.user.patient_profile

        # Sprawdzamy czy jest nieoceniona zakończona wizyta
        unreviewed_visit = (
            Visit.objects.filter(
                patient=patient,
                therapist=therapist,
                status=VisitStatus.COMPLETED,
                review__isnull=True,
            )
            .order_by('-end_at')
            .first()
        )

        return review_create_service(
            therapist=therapist,
            patient=patient,
            visit=unreviewed_visit,
            **validated_data,
        )


class ReviewEditSerializer(serializers.ModelSerializer):
    """Serializer edycji własnej opinii przez pacjenta (okno 14 dni).

    Pozwala zmienić ocenę, komentarz i tryb anonimowości.
    """

    class Meta:
        """Metadane serializatora ReviewEditSerializer."""

        model = Review
        fields = ['rating', 'comment', 'is_anonymous']

    def validate_rating(self, value: int) -> int:
        """Waliduje ocenę w skali 1–5.

        Args:
            value (int): Wartość oceny.

        Returns:
            int: Zwalidowana ocena.

        Raises:
            serializers.ValidationError: Gdy ocena jest poza zakresem 1–5.
        """
        if not isinstance(value, int) or value < 1 or value > 5:
            raise serializers.ValidationError('Ocena musi być liczbą całkowitą w zakresie 1–5.')
        return value

    def validate(self, data: dict) -> dict:
        """Sprawdza, czy minęło mniej niż 14 dni od wystawienia opinii.

        Args:
            data (dict): Dane wejściowe.

        Returns:
            dict: Zwalidowane dane.

        Raises:
            serializers.ValidationError: Gdy upłynęło więcej niż 14 dni.
        """
        instance = self.instance
        if instance is not None:
            delta = timezone.now() - instance.created_at
            if delta.days > 14:
                raise serializers.ValidationError(
                    {
                        'non_field_errors': 'Edycja opinii jest możliwa tylko w ciągu 14 dni od jej wystawienia.'
                    }
                )
        return data

    def update(self, instance: Review, validated_data: dict) -> Review:
        """Aktualizuje opinię poprzez warstwę usług review_edit_service."""
        from .services import review_edit_service

        return review_edit_service(
            review=instance,
            rating=validated_data.get('rating'),
            comment=validated_data.get('comment'),
            is_anonymous=validated_data.get('is_anonymous'),
        )


class ReviewReadSerializer(serializers.ModelSerializer):
    """Publiczny serializer opinii — anonimizuje nazwisko pacjenta.

    Pola author_name i is_verified są obliczane dynamicznie.
    """

    author_name = serializers.SerializerMethodField()
    author_avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()

    class Meta:
        """Metadane serializatora ReviewReadSerializer."""

        model = Review
        fields = [
            'id',
            'rating',
            'comment',
            'author_name',
            'author_avatar_url',
            'is_anonymous',
            'is_verified',
            'is_own',
            'created_at',
            'therapist_reply',
            'therapist_replied_at',
        ]

    def get_is_own(self, obj: Review) -> bool:
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        patient_profile = getattr(request.user, 'patient_profile', None)
        return bool(patient_profile and obj.patient_id == patient_profile.id)

    def get_author_avatar_url(self, obj: Review) -> str | None:
        """Zwraca URL awatara pacjenta, jeśli opinia nie jest anonimowa."""
        if not isinstance(obj, Review) or obj.is_anonymous:
            return None
        try:
            return obj.patient.avatar_url or None
        except Exception:
            return None

    def get_author_name(self, obj: Review) -> str:
        """Zwraca imię i pierwszą literę nazwiska lub 'Pacjent PhysioCare' dla anonimowych.

        Args:
            obj (Review): Instancja opinii.

        Returns:
            str: Wyświetlana nazwa autora opinii.
        """
        if not isinstance(obj, Review):
            return ''
        if obj.is_anonymous:
            return 'Pacjent PhysioCare'
        try:
            user = obj.patient.user
            first = user.first_name or ''
            last = user.last_name or ''
            return f'{first} {last[0]}.' if last else first
        except Exception:
            return 'Pacjent PhysioCare'

    def get_is_verified(self, obj: Review) -> bool:
        """Sprawdza, czy opinia pochodzi ze zrealizowanej wizyty (Verified Review).

        Args:
            obj (Review): Instancja opinii.

        Returns:
            bool: True jeśli opinia ma powiązaną wizytę.
        """
        if not isinstance(obj, Review):
            return False
        return obj.visit_id is not None


class ReviewReplySerializer(serializers.ModelSerializer):
    """Serializer odpowiedzi fizjoterapeuty na opinię.

    Ustawia therapist_reply i therapist_replied_at.
    """

    class Meta:
        """Metadane serializatora ReviewReplySerializer."""

        model = Review
        fields = ['therapist_reply']

    def validate_therapist_reply(self, value: str) -> str:
        """Waliduje, że odpowiedź nie jest pusta.

        Args:
            value (str): Treść odpowiedzi.

        Returns:
            str: Znormalizowana odpowiedź.

        Raises:
            serializers.ValidationError: Gdy odpowiedź jest pusta lub zawiera tylko spacje.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError('Odpowiedź musi być ciągiem znaków.')
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError('Odpowiedź fizjoterapeuty nie może być pusta.')
        return stripped

    def update(self, instance: Review, validated_data: dict) -> Review:
        """Zapisuje odpowiedź poprzez warstwę usług review_reply_service.

        Args:
            instance (Review): Instancja opinii do aktualizacji.
            validated_data (dict): Zwalidowane dane z odpowiedzią.

        Returns:
            Review: Zaktualizowana opinia.
        """
        from .services import review_reply_service

        return review_reply_service(
            review=instance,
            therapist_reply=validated_data['therapist_reply'],
        )


class RatingSummarySerializer(serializers.Serializer):
    """Serializer podsumowania ocen fizjoterapeuty."""

    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_reviews = serializers.IntegerField()
    rating_breakdown = serializers.DictField(child=serializers.IntegerField())
