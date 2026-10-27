KIND_TYPE: str = 'TYPE'
KIND_REGION: str = 'REGION'
KIND_MUSCLE: str = 'MUSCLE'
KIND_INJURY: str = 'INJURY'

LEGACY_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    'Rozciąganie': (KIND_TYPE, 'stretching'),
    'Mobilizacja': (KIND_TYPE, 'mobilization'),
    'Kończyna dolna': (KIND_REGION, 'lower_limb'),
    'Odcinek lędźwiowy': (KIND_REGION, 'lumbar'),
}

CATEGORY_SEED: list[tuple[str, str, str]] = [
    (KIND_TYPE, 'mobilization', 'Mobilizacja'),
    (KIND_TYPE, 'stretching', 'Rozciąganie'),
    (KIND_TYPE, 'strengthening', 'Wzmacnianie'),
    (KIND_TYPE, 'stabilization', 'Stabilizacja'),
    (KIND_TYPE, 'proprioception', 'Propriocepcja / równowaga'),
    (KIND_TYPE, 'neuromobilization', 'Neuromobilizacja'),
    (KIND_TYPE, 'breathing', 'Oddechowe'),
    (KIND_TYPE, 'education', 'Edukacja'),
    (KIND_REGION, 'cervical', 'Szyja / odcinek szyjny'),
    (KIND_REGION, 'shoulder', 'Bark / obręcz barkowa'),
    (KIND_REGION, 'thoracic', 'Odcinek piersiowy'),
    (KIND_REGION, 'lumbar', 'Odcinek lędźwiowy'),
    (KIND_REGION, 'hip', 'Biodro / miednica'),
    (KIND_REGION, 'knee', 'Kolano'),
    (KIND_REGION, 'ankle_foot', 'Kostka / stopa'),
    (KIND_REGION, 'upper_limb', 'Kończyna górna'),
    (KIND_REGION, 'lower_limb', 'Kończyna dolna'),
    (KIND_REGION, 'core', 'Tułów / core'),
    (KIND_MUSCLE, 'deep_neck_flexors', 'Głębokie zginacze szyi'),
    (KIND_MUSCLE, 'scm', 'Mostkowo-obojczykowo-sutkowy'),
    (KIND_MUSCLE, 'trapezius', 'Czworoboczny'),
    (KIND_MUSCLE, 'levator_scapulae', 'Dźwigacz łopatki'),
    (KIND_MUSCLE, 'deltoid', 'Mięsień naramienny'),
    (KIND_MUSCLE, 'latissimus_dorsi', 'Najszerszy grzbietu'),
    (KIND_MUSCLE, 'rhomboids', 'Równoległoboczne'),
    (KIND_MUSCLE, 'biceps', 'Dwugłowy ramienia / biceps'),
    (KIND_MUSCLE, 'triceps', 'Trójgłowy ramienia / triceps'),
    (KIND_MUSCLE, 'rotator_cuff', 'Rotatory barku'),
    (KIND_MUSCLE, 'pectoralis', 'Piersiowe'),
    (KIND_MUSCLE, 'erector_spinae', 'Prostownik grzbietu'),
    (KIND_MUSCLE, 'quadratus_lumborum', 'Czworoboczny lędźwi'),
    (KIND_MUSCLE, 'transversus_abdominis', 'Poprzeczny brzucha / core'),
    (KIND_MUSCLE, 'gluteals', 'Pośladkowe'),
    (KIND_MUSCLE, 'piriformis', 'Gruszkowaty'),
    (KIND_MUSCLE, 'quadriceps', 'Czworogłowy uda'),
    (KIND_MUSCLE, 'hamstrings', 'Tylna grupa uda'),
    (KIND_MUSCLE, 'adductors', 'Przywodziciele'),
    (KIND_MUSCLE, 'calf', 'Łydka (brzuchaty / płaszczkowaty)'),
    (KIND_MUSCLE, 'tibialis_anterior', 'Piszczelowy przedni'),
    (KIND_INJURY, 'lbp', 'Ból odcinka lędźwiowego'),
    (KIND_INJURY, 'neck_pain', 'Ból szyi'),
    (KIND_INJURY, 'shoulder_pain', 'Zespół bólowy barku'),
    (KIND_INJURY, 'impingement', 'Konflikt podbarkowy'),
    (KIND_INJURY, 'shoulder_instability', 'Niestabilność barku'),
    (KIND_INJURY, 'epicondylitis', 'Łokieć tenisisty / golfisty'),
    (KIND_INJURY, 'hip_pain', 'Ból biodra'),
    (KIND_INJURY, 'pfps', 'Zespół rzepkowo-udowy'),
    (KIND_INJURY, 'acl_rehab', 'Po rekonstrukcji ACL'),
    (KIND_INJURY, 'ankle_sprain', 'Skręcenie stawu skokowego'),
    (KIND_INJURY, 'achilles', 'Ścięgno Achillesa'),
    (KIND_INJURY, 'sciatica', 'Rwa kulszowa / objawy korzeniowe'),
    (KIND_INJURY, 'piriformis_syndrome', 'Zespół gruszkowatego'),
    (KIND_INJURY, 'tmj', 'Staw skroniowo-żuchwowy'),
    (KIND_INJURY, 'frozen_shoulder', 'Zamrożony bark / torebka stawowa'),
    (KIND_INJURY, 'carpal_tunnel', 'Zespół cieśni nadgarstka'),
    (KIND_INJURY, 'meniscus_tear', 'Uszkodzenie łąkotki'),
    (KIND_INJURY, 'plantar_fasciitis', 'Zapalenie rozcięgna podeszwowego'),
]


def get_category_seed() -> list[tuple[str, str, str]]:
    """Zwraca listę zdefiniowanych kategorii początkowych ćwiczeń.

    Returns:
        list[tuple[str, str, str]]: Kopia listy krotek określających typ, kod oraz nazwę kategorii.
    """
    return list(CATEGORY_SEED)


def resolve_legacy_category(name: str) -> tuple[str, str] | None:
    """Mapuje starą nazwę kategorii na nowy typ i kod kategorii.

    Args:
        name (str): Stara nazwa kategorii ćwiczenia.

    Returns:
        tuple[str, str] | None: Krotka (kind, code) lub None, jeśli nazwa nie występuje w mapowaniu.

    Raises:
        TypeError: Gdy argument name nie jest napisem.
    """
    if not isinstance(name, str):
        raise TypeError("Argument 'name' musi być typu str.")

    return LEGACY_CATEGORY_MAP.get(name)
