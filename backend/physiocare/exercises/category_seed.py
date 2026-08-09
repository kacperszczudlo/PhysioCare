"""Canonical exercise category taxonomy (kinds + slugs).

Used by migrations and tests. Keep slugs stable - API filters depend on them.
Kind values match CategoryKind on ExerciseCategory.
"""

KIND_TYPE = 'TYPE'
KIND_REGION = 'REGION'
KIND_MUSCLE = 'MUSCLE'
KIND_INJURY = 'INJURY'

LEGACY_CATEGORY_MAP = {
    'Rozciąganie': (KIND_TYPE, 'stretching'),
    'Mobilizacja': (KIND_TYPE, 'mobilization'),
    'Kończyna dolna': (KIND_REGION, 'lower_limb'),
    'Odcinek lędźwiowy': (KIND_REGION, 'lumbar'),
}

CATEGORY_SEED = [
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
]
