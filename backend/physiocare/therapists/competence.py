"""
Kompetencje fizjoterapeuty wg ustawy o zawodzie fizjoterapeuty
oraz rozporządzeń MZ w sprawie wyrobów medycznych (stan interpretacyjny 2024).

To nie jest poradnictwo prawne — reguły modelują granice produktu PhysioCare.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from therapists.models import TherapistProfile


class QualificationLevel:
    TECHNIK = 'TECHNIK'
    LICENCJAT = 'LICENCJAT'
    MAGISTER = 'MAGISTER'
    FIZJO_SPEC = 'FIZJO_SPEC'

    CHOICES = (
        (TECHNIK, 'Technik fizjoterapii'),
        (LICENCJAT, 'Licencjat fizjoterapii'),
        (MAGISTER, 'Magister fizjoterapii'),
        (FIZJO_SPEC, 'Specjalista w dziedzinie fizjoterapii (FIZJO SPEC)'),
    )

    LABELS = dict(CHOICES)


# Magistrowie: grupy seryjne (J, L, M/L, O, S) — stan na 2024 z raportu.
MAGISTER_DEVICE_GROUPS = frozenset({'J', 'L', 'M', 'O', 'S'})

# Specjalista: dodatkowo protezy, ortezy na miarę, zaawansowany sprzęt, grupa W.
FIZJO_SPEC_EXTRA_GROUPS = frozenset({'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'Ł', 'N', 'P', 'W'})

ALL_ORDINABLE_GROUPS = MAGISTER_DEVICE_GROUPS | FIZJO_SPEC_EXTRA_GROUPS

YEARS_FOR_INDEPENDENT_PLANNING = 3
YEARS_FOR_SUPERVISION = 5


@dataclass(frozen=True)
class CompetenceCapability:
    code: str
    allowed: bool
    label: str
    detail: str


@dataclass(frozen=True)
class CompetenceSnapshot:
    qualification_level: str
    qualification_label: str
    experience_years: int
    is_magister_or_above: bool
    is_fizjo_spec: bool
    can_plan_therapy: bool
    can_supervise: bool
    device_groups: tuple[str, ...]
    capabilities: tuple[CompetenceCapability, ...]

    def to_dict(self) -> dict:
        data = asdict(self)
        return data

    def capability(self, code: str) -> CompetenceCapability | None:
        for item in self.capabilities:
            if item.code == code:
                return item
        return None

    def allows(self, code: str) -> bool:
        item = self.capability(code)
        return bool(item and item.allowed)


def _is_magister_or_above(level: str) -> bool:
    return level in (QualificationLevel.MAGISTER, QualificationLevel.FIZJO_SPEC)


def _is_fizjo_spec(level: str) -> bool:
    return level == QualificationLevel.FIZJO_SPEC


def allowed_device_groups(level: str) -> frozenset[str]:
    if _is_fizjo_spec(level):
        return ALL_ORDINABLE_GROUPS
    if level == QualificationLevel.MAGISTER:
        return MAGISTER_DEVICE_GROUPS
    return frozenset()


def can_order_device_group(level: str, group: str) -> bool:
    return group.upper() in allowed_device_groups(level)


def build_competence_snapshot(
    qualification_level: str,
    experience_years: int = 0,
) -> CompetenceSnapshot:
    level = qualification_level or QualificationLevel.MAGISTER
    years = max(0, int(experience_years or 0))
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
                'lub specjalista fizjoterapii. Licencjat/technik — tylko wykonanie planu.'
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
                'RTG/TK dodatkowo ogranicza Prawo atomowe — skierowanie wystawia lekarz.'
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
                'zagrażającego pacjentowi — z wpisem w dokumentacji i powiadomieniem lekarza.'
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
    return build_competence_snapshot(
        qualification_level=therapist.qualification_level,
        experience_years=therapist.experience_years,
    )


def deny_message(capability_code: str, snapshot: CompetenceSnapshot) -> str:
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
