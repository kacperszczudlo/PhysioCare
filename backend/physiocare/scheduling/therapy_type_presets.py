"""Proponowane typy wizyt - katalog startowy dla terapeuty.

Grupy:
- kind: główny typ wizyty (czas / charakter spotkania)
- profile: specjalizacja / profil wizyty
"""

from .models import TherapyType

THERAPY_TYPE_PRESETS = [
    (
        'kind',
        'Wizyta konsultacyjna',
        '#2F6FED',
        60,
        'Pierwsza wizyta / diagnostyczna. Wywiad, badanie funkcjonalne, plan leczenia (45-60 min).',
    ),
    (
        'kind',
        'Wizyta terapeutyczna',
        '#4A6B28',
        45,
        'Kolejna / robocza. Terapia manualna, kinezyterapia, praca z powięziami (30-45 min).',
    ),
    (
        'kind',
        'Pojedynczy zabieg fizykoterapeutyczny',
        '#0F766E',
        30,
        'Krótka wizyta na zabieg sprzętowy (fala, laser, pole magnetyczne, USG).',
    ),
    (
        'kind',
        'Wizyta kontrolna',
        '#B45309',
        45,
        'Ocena postępów, weryfikacja zmian i ewentualna modyfikacja ćwiczeń domowych.',
    ),
    (
        'kind',
        'Wizyta domowa',
        '#7C3AED',
        60,
        'W miejscu zamieszkania pacjenta - m.in. po urazach/operacjach bez dojazdu do gabinetu.',
    ),
    (
        'profile',
        'Ortopedyczna i sportowa',
        '#C2410C',
        45,
        'Kontuzje, bóle stawów, okres pooperacyjny (np. rekonstrukcja ACL).',
    ),
    (
        'profile',
        'Neurologiczna',
        '#1D4ED8',
        45,
        'Po udarach, SM, choroba Parkinsona - często PNF / NDT-Bobath.',
    ),
    (
        'profile',
        'Uroginekologiczna',
        '#BE185D',
        45,
        'Ciąża, połóg, nietrzymanie moczu, bóle miednicy mniejszej.',
    ),
    (
        'profile',
        'Pediatryczna',
        '#0891B2',
        45,
        'Rozwój niemowląt, korekcja wad postawy u dzieci.',
    ),
]


def preset_payloads():
    return [
        {
            'group': group,
            'name': name,
            'color_hex': color,
            'duration_min': duration,
            'description': description,
        }
        for group, name, color, duration, description in THERAPY_TYPE_PRESETS
    ]


def ensure_therapy_type_presets(therapist) -> list[TherapyType]:
    """Idempotentnie dopisz brakujące typy z katalogu proponowanego."""
    existing = set(
        TherapyType.objects.filter(therapist=therapist).values_list('name', flat=True),
    )
    created: list[TherapyType] = []
    for _group, name, color, duration, _description in THERAPY_TYPE_PRESETS:
        if name in existing:
            continue
        created.append(
            TherapyType(
                therapist=therapist,
                name=name,
                color_hex=color,
                duration_min=duration,
            ),
        )
        existing.add(name)
    if created:
        TherapyType.objects.bulk_create(created)
    return list(
        TherapyType.objects.filter(therapist=therapist).order_by('name'),
    )
