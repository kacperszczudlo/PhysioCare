from __future__ import annotations

from therapists.competence import (
    FIZJO_SPEC_EXTRA_GROUPS,
    MAGISTER_DEVICE_GROUPS,
    QualificationLevel,
)

DEVICE_CATALOG: tuple[dict[str, str], ...] = (
    {
        'code': 'J.ANKLE',
        'group': 'J',
        'name': 'Orteza stabilizująca staw skokowy (seryjna)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Limit zależny od kodu NFZ (np. raz na 3 lata u dorosłych).',
    },
    {
        'code': 'J.KNEE',
        'group': 'J',
        'name': 'Orteza stawu kolanowego z regulacją zgięcia',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Seryjna; strona ciała obowiązkowa.',
    },
    {
        'code': 'J.HIP',
        'group': 'J',
        'name': 'Orteza biodrowa / odwodząca (seryjna)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'W tym ortezy w dysplazji stawów biodrowych u niemowląt.',
    },
    {
        'code': 'L.WRIST',
        'group': 'L',
        'name': 'Orteza na rękę i przedramię (seryjna)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Bez aparatów Stacka/Capenera (poza zakresem seryjnym magistra).',
    },
    {
        'code': 'L.ELBOW',
        'group': 'L',
        'name': 'Orteza stawu łokciowego z regulacją kąta',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Zwykle raz na 3 lata.',
    },
    {
        'code': 'L.SHOULDER',
        'group': 'L',
        'name': 'Orteza na ramię i bark (typ Dessault)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Seryjna.',
    },
    {
        'code': 'M.LUMBAR',
        'group': 'M',
        'name': 'Pas / orteza lędźwiowo-krzyżowa (seryjna)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Odciążenie niepełne; limity wg kodu NFZ.',
    },
    {
        'code': 'M.CERVICAL',
        'group': 'M',
        'name': 'Kołnierz szyjny sztywny / półsztywny',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Seryjny.',
    },
    {
        'code': 'O.ARM',
        'group': 'O',
        'name': 'Rękaw uciskowy płaskodziany (≥20 mmHg)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Obrzęki limfatyczne.',
    },
    {
        'code': 'O.LEG',
        'group': 'O',
        'name': 'Nogawica uciskowa płaskodziana (≥30 mmHg)',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Obrzęki limfatyczne.',
    },
    {
        'code': 'S.07.01',
        'group': 'S',
        'name': 'Balkonik / chodzik / podpórka',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Np. balkonik raz na 5 lat; udział własny zwykle 30% u dorosłych.',
    },
    {
        'code': 'S.05.01',
        'group': 'S',
        'name': 'Kule łokciowe',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Sprzęt pomocniczy seryjny.',
    },
    {
        'code': 'S.06.01',
        'group': 'S',
        'name': 'Trójnóg / czwórnóg',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Sprzęt pomocniczy seryjny.',
    },
    {
        'code': 'S.MATTRESS',
        'group': 'S',
        'name': 'Materac / poduszka przeciwodleżynowa',
        'min_qualification': QualificationLevel.MAGISTER,
        'usage_hint': 'Z wyłączeniem niektórych wariantów piankowych wg limitu NFZ.',
    },
    {
        'code': 'A.PROST.TEMP',
        'group': 'A',
        'name': 'Proteza tymczasowa kończyny dolnej',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Wymaga FIZJO SPEC.',
    },
    {
        'code': 'C.PROST.MOD',
        'group': 'C',
        'name': 'Proteza ostateczna modularna podudzia / uda',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Wymaga FIZJO SPEC.',
    },
    {
        'code': 'H.AFO',
        'group': 'H',
        'name': 'Orteza AFO / DAFO / GRAFO na miarę',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Zaopatrzenie na zamówienie.',
    },
    {
        'code': 'K.CROW',
        'group': 'K',
        'name': 'Orteza CROW (stopa Charcota)',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Na miarę - FIZJO SPEC.',
    },
    {
        'code': 'N.SCOLIOSIS',
        'group': 'N',
        'name': 'Gorset korekcyjny w leczeniu skolioz',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Na miarę - FIZJO SPEC.',
    },
    {
        'code': 'S.18.01',
        'group': 'S',
        'name': 'Wózek inwalidzki specjalny (stabilizacja głowy/pleców)',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Limit przykładowy 4000 zł / 4 lata - FIZJO SPEC.',
    },
    {
        'code': 'P.STAND',
        'group': 'P',
        'name': 'Pionizator / urządzenie multifunkcyjne',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Zaawansowany sprzęt rehabilitacyjny - FIZJO SPEC.',
    },
    {
        'code': 'W.BRA.POSTOP',
        'group': 'W',
        'name': 'Biustonosz pooperacyjny / do protezy piersi',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Od 2024 - FIZJO SPEC; limit przykładowy 120 zł / rok.',
    },
    {
        'code': 'W.02.02',
        'group': 'W',
        'name': 'Zaopatrzenie stomijne (pierwszorazowe)',
        'min_qualification': QualificationLevel.FIZJO_SPEC,
        'usage_hint': 'Od 2024 - FIZJO SPEC może wystawić pierwszorazowe zlecenie.',
    },
)


def catalog_as_list(*, qualification_level: str | None = None) -> list[dict[str, object]]:
    """Zwraca katalog wyrobów medycznych w postaci listy słowników z informacją o dostępności.

    Args:
        qualification_level (str | None): Poziom kwalifikacji do filtrowania uprawnień.

    Returns:
        list[dict[str, object]]: Lista słowników reprezentujących wyroby medyczne z flagą dozwolenia.
    """
    if qualification_level is not None and not isinstance(qualification_level, str):
        qualification_level = None

    from therapists.competence import can_order_device_group

    items = []
    for entry in DEVICE_CATALOG:
        item = dict(entry)
        allowed = True
        if qualification_level:
            allowed = can_order_device_group(qualification_level, entry['group'])
            if entry['min_qualification'] == QualificationLevel.FIZJO_SPEC:
                allowed = qualification_level == QualificationLevel.FIZJO_SPEC
            elif entry['min_qualification'] == QualificationLevel.MAGISTER:
                allowed = qualification_level in (
                    QualificationLevel.MAGISTER,
                    QualificationLevel.FIZJO_SPEC,
                )
        item['allowed_for_therapist'] = allowed
        items.append(item)
    return items


def get_device(code: str) -> dict[str, object] | None:
    """Wyszukuje wyrób medyczny w katalogu po jego kodzie.

    Args:
        code (str): Kod wyrobu medycznego.

    Returns:
        dict[str, object] | None: Słownik zawierający dane wyrobu medycznego lub None.
    """
    if not isinstance(code, str):
        return None
    for entry in DEVICE_CATALOG:
        if entry['code'] == code:
            return dict(entry)
    return None


def groups_summary() -> dict[str, list[str]]:
    """Generuje podsumowanie dostępnych grup wyrobów medycznych według poziomów kwalifikacji.

    Returns:
        dict[str, list[str]]: Słownik z podziałem na grupy dla magistrów i specjalistów.
    """
    return {
        'magister_groups': sorted(MAGISTER_DEVICE_GROUPS),
        'fizjo_spec_extra_groups': sorted(FIZJO_SPEC_EXTRA_GROUPS, key=lambda g: (g != 'Ł', g)),
    }
