from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from therapists.models import TherapistProfile


class QualificationLevel:
    """Poziomy kwalifikacji zawodowych fizjoterapeutów w Polsce."""

    TECHNIK: str = 'TECHNIK'
    LICENCJAT: str = 'LICENCJAT'
    MAGISTER: str = 'MAGISTER'
    FIZJO_SPEC: str = 'FIZJO_SPEC'

    CHOICES: tuple[tuple[str, str], ...] = (
        (TECHNIK, 'Technik fizjoterapii'),
        (LICENCJAT, 'Licencjat fizjoterapii'),
        (MAGISTER, 'Magister fizjoterapii'),
        (FIZJO_SPEC, 'Specjalista w dziedzinie fizjoterapii (FIZJO SPEC)'),
    )

    LABELS: dict[str, str] = dict(CHOICES)


MAGISTER_DEVICE_GROUPS: frozenset[str] = frozenset({'J', 'L', 'M', 'O', 'S'})

FIZJO_SPEC_EXTRA_GROUPS: frozenset[str] = frozenset({'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'Ł', 'N', 'P', 'W'})

ALL_ORDINABLE_GROUPS: frozenset[str] = MAGISTER_DEVICE_GROUPS | FIZJO_SPEC_EXTRA_GROUPS

YEARS_FOR_INDEPENDENT_PLANNING: int = 3
YEARS_FOR_SUPERVISION: int = 5



@dataclass(frozen=True)
class CompetenceCapability:
    """Reprezentacja pojedynczego uprawnienia zawodowego fizjoterapeuty."""

    code: str
    allowed: bool
    label: str
    detail: str


@dataclass(frozen=True)
class CompetenceSnapshot:
    """Migawka uprawnień zawodowych fizjoterapeuty."""

    qualification_level: str
    qualification_label: str
    experience_years: int
    is_magister_or_above: bool
    is_fizjo_spec: bool
    can_plan_therapy: bool
    can_supervise: bool
    device_groups: tuple[str, ...]
    capabilities: tuple[CompetenceCapability, ...]

    def to_dict(self) -> dict[str, object]:
        """Konwertuje migawkę kompetencji do słownika.

        Returns:
            dict[str, object]: Słownik reprezentujący dane migawki kompetencji.
        """
        data = asdict(self)
        return data

    def capability(self, code: str) -> CompetenceCapability | None:
        """Wyszukuje uprawnienie o podanym kodzie w migawce.

        Args:
            code (str): Kod uprawnienia.

        Returns:
            CompetenceCapability | None: Obiekt uprawnienia lub None, jeśli nie znaleziono.
        """
        if not isinstance(code, str):
            return None
        for item in self.capabilities:
            if item.code == code:
                return item
        return None

    def allows(self, code: str) -> bool:
        """Sprawdza, czy dane uprawnienie jest dozwolone.

        Args:
            code (str): Kod uprawnienia.

        Returns:
            bool: True, jeśli uprawnienie jest dozwolone, w przeciwnym razie False.
        """
        if not isinstance(code, str):
            return False
        item = self.capability(code)
        return bool(item and item.allowed)


def _is_magister_or_above(level: str) -> bool:
    """Sprawdza, czy poziom kwalifikacji odpowiada magistrowi lub specjaliscie.

    Args:
        level (str): Kod poziomu kwalifikacji.

    Returns:
        bool: True, jeśli poziom to MAGISTER lub FIZJO_SPEC.
    """
    if not isinstance(level, str):
        return False
    return level in (QualificationLevel.MAGISTER, QualificationLevel.FIZJO_SPEC)


def _is_fizjo_spec(level: str) -> bool:
    """Sprawdza, czy poziom kwalifikacji odpowiada specjaliście fizjoterapii.

    Args:
        level (str): Kod poziomu kwalifikacji.

    Returns:
        bool: True, jeśli poziom to FIZJO_SPEC.
    """
    if not isinstance(level, str):
        return False
    return level == QualificationLevel.FIZJO_SPEC


def allowed_device_groups(level: str) -> frozenset[str]:
    """Zwraca zbiór grup wyrobów medycznych dozwolonych do ordynacji dla danego poziomu.

    Args:
        level (str): Kod poziomu kwalifikacji.

    Returns:
        frozenset[str]: Zbiór symboli grup wyrobów medycznych.
    """
    if not isinstance(level, str):
        return frozenset()
    if _is_fizjo_spec(level):
        return ALL_ORDINABLE_GROUPS
    if level == QualificationLevel.MAGISTER:
        return MAGISTER_DEVICE_GROUPS
    return frozenset()


def can_order_device_group(level: str, group: str) -> bool:
    """Sprawdza, czy dany poziom kwalifikacji umożliwia ordynację grupy wyrobów medycznych.

    Args:
        level (str): Kod poziomu kwalifikacji.
        group (str): Symbol grupy wyrobów medycznych.

    Returns:
        bool: True, jeśli ordynacja danej grupy jest dozwolona.
    """
    if not isinstance(level, str) or not isinstance(group, str):
        return False
    return group.upper() in allowed_device_groups(level)


def build_competence_snapshot(
    qualification_level: str,
    experience_years: int = 0,
) -> CompetenceSnapshot:
    """Buduje pełną migawkę kompetencji na podstawie poziomu kwalifikacji i stażu pracy.

    Args:
        qualification_level (str): Kod poziomu wykształcenia/kwalifikacji.
        experience_years (int): Liczba lat doświadczenia zawodowego.

    Returns:
        CompetenceSnapshot: Wygenerowana migawka kompetencji.
    """
    level = qualification_level if isinstance(qualification_level, str) and qualification_level else QualificationLevel.MAGISTER
    years = max(0, int(experience_years or 0)) if isinstance(experience_years, (int, float, str)) else 0
    magister_plus = _is_magister_or_above(level)
    fizjo_spec = _is_fizjo_spec(level)
    can_plan = fizjo_spec or (level == QualificationLevel.MAGISTER and years >= YEARS_FOR_INDEPENDENT_PLANNING)
    can_supervise = fizjo_spec or (level == QualificationLevel.MAGISTER and years >= YEARS_FOR_SUPERVISION)
    groups = tuple(sorted(allowed_device_groups(level), key=lambda g: (g != 'Ł', g)))

    capabilities = (
        CompetenceCapability(
            code='functional_diagnosis',
            allowed=magister_plus,
            label='Diagnoza funkcjonalna',
            detail=(
                'Magister (i specjalista) samodzielnie przeprowadza badanie fizjoterapeutyczne '
                'i ustala diagnozę funkcjonalną. Diagnoza nozologiczna pozostaje domeną lekarza.'
            ),
        ),
        CompetenceCapability(
            code='plan_modify_therapy',
            allowed=can_plan,
            label='Planowanie i modyfikacja terapii (NFZ)',
            detail=(
                f'Wymagany magister z ≥{YEARS_FOR_INDEPENDENT_PLANNING} latami doświadczenia '
                'lub specjalista fizjoterapii. Licencjat/technik - tylko wykonanie planu.'
            ),
        ),
        CompetenceCapability(
            code='supervise_others',
            allowed=can_supervise,
            label='Nadzór nad innymi fizjoterapeutami',
            detail=f'Magister z ≥{YEARS_FOR_SUPERVISION} latami doświadczenia lub FIZJO SPEC.',
        ),
        CompetenceCapability(
            code='imaging_referral_nfz',
            allowed=False,
            label='Formalne skierowanie NFZ na RTG/MRI/TK',
            detail=(
                'Fizjoterapeuta nie wystawia e-skierowania NFZ na badania obrazowe. '
                'RTG/TK dodatkowo ogranicza Prawo atomowe - skierowanie wystawia lekarz.'
            ),
        ),
        CompetenceCapability(
            code='imaging_recommendation',
            allowed=magister_plus,
            label='Kierowanie pośrednie (opinia diagnostyczna)',
            detail=(
                'Można sporządzić uzasadnioną opinię / kartę oceny funkcjonalnej sugerującą '
                'konsultację lekarską lub obrazowanie (MRI prywatnie; RTG zawsze przez lekarza).'
            ),
        ),
        CompetenceCapability(
            code='recepta_na_ruch',
            allowed=True,
            label='Skierowanie do programu „Recepta na Ruch”',
            detail='Fizjoterapeuta z PWZFz może skierować pacjenta do programu w mojeIKP.',
        ),
        CompetenceCapability(
            code='order_serial_devices',
            allowed=level == QualificationLevel.MAGISTER or fizjo_spec,
            label='Ordynacja wyrobów seryjnych (e-ZWM)',
            detail='Magister: ortezy seryjne (J, L, M), kompresja (O), sprzęt pomocniczy (S).',
        ),
        CompetenceCapability(
            code='order_specialist_devices',
            allowed=fizjo_spec,
            label='Ordynacja wyrobów specjalistycznych / na miarę',
            detail=(
                'FIZJO SPEC: protezy, ortezy na miarę, wózki specjalne, pionizatory, '
                'wyroby po mastektomii i stomijne (grupa W).'
            ),
        ),
        CompetenceCapability(
            code='refuse_physician_order',
            allowed=True,
            label='Odmowa wykonania zlecenia lekarskiego (art. 6)',
            detail=(
                'Przy uzasadnionych wątpliwościach można żądać uzasadnienia i odmówić zabiegu '
                'zagrażającego pacjentowi - z wpisem w dokumentacji i powiadomieniem lekarza.'
            ),
        ),
        CompetenceCapability(
            code='prescribe_medications',
            allowed=False,
            label='Ordynacja leków / maści farmaceutycznych',
            detail=(
                'Fizjoterapeuta nie przepisuje leków ani maści jako produktów leczniczych. '
                'Uprawnienie dotyczy wyrobów medycznych (ortezy, protezy, sprzęt pomocniczy), nie recepty.'
            ),
        ),
    )

    return CompetenceSnapshot(
        qualification_level=level,
        qualification_label=QualificationLevel.LABELS.get(level, level),
        experience_years=years,
        is_magister_or_above=magister_plus,
        is_fizjo_spec=fizjo_spec,
        can_plan_therapy=can_plan,
        can_supervise=can_supervise,
        device_groups=groups,
        capabilities=capabilities,
    )


def snapshot_for_therapist(therapist: TherapistProfile) -> CompetenceSnapshot:
    """Generuje migawkę kompetencji dla wskazanego profilu fizjoterapeuty.

    Args:
        therapist (TherapistProfile): Instancja profilu fizjoterapeuty.

    Returns:
        CompetenceSnapshot: Migawka kompetencji dla danego fizjoterapeuty.

    Raises:
        TypeError: Gdy parametr therapist nie jest instancją TherapistProfile.
    """
    from therapists.models import TherapistProfile
    if not isinstance(therapist, TherapistProfile):
        raise TypeError('Argument therapist musi być instancją TherapistProfile.')

    qual = therapist.qualification_level if hasattr(therapist, 'qualification_level') else QualificationLevel.MAGISTER
    exp = therapist.experience_years if hasattr(therapist, 'experience_years') else 0
    return build_competence_snapshot(
        qualification_level=qual,
        experience_years=exp,
    )



def deny_message(capability_code: str, snapshot: CompetenceSnapshot) -> str:
    """Zwraca przyczyny odmowy dostępu do określonego uprawnienia.

    Args:
        capability_code (str): Kod uprawnienia.
        snapshot (CompetenceSnapshot): Migawka kompetencji fizjoterapeuty.

    Returns:
        str: Komunikat uzasadniający odmowę dostępu.
    """
    if not isinstance(capability_code, str) or not isinstance(snapshot, CompetenceSnapshot):
        return 'Brak uprawnienia do tej operacji.'
    item = snapshot.capability(capability_code)
    if item is None:
        return 'Brak uprawnienia do tej operacji.'
    if capability_code == 'plan_modify_therapy' and snapshot.qualification_level == QualificationLevel.MAGISTER:
        return (
            f'Planowanie/modyfikacja zabiegów wymaga ≥{YEARS_FOR_INDEPENDENT_PLANNING} lat '
            f'doświadczenia (obecnie: {snapshot.experience_years}).'
        )
    if capability_code == 'order_specialist_devices':
        return 'Ta grupa wyrobów wymaga tytułu specjalisty w dziedzinie fizjoterapii (FIZJO SPEC).'
    if capability_code == 'order_serial_devices':
        return 'Ordynacja wyrobów seryjnych wymaga tytułu magistra fizjoterapii lub specjalisty.'
    if capability_code == 'functional_diagnosis':
        return 'Samodzielna diagnoza funkcjonalna jest zastrzeżona dla magistra / specjalisty.'
    if capability_code == 'imaging_referral_nfz':
        return item.detail
    if capability_code == 'prescribe_medications':
        return item.detail
    return f'Brak uprawnienia: {item.label}.'
