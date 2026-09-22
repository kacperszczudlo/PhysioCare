from datetime import date, timedelta


def get_easter_date(year: int) -> date:
    """Oblicza datę Niedzieli Wielkanocnej w kalendarzu gregoriańskim za pomocą algorytmu Meeusa/Jonesa/Butchera.

    Args:
        year (int): Rok, dla którego ma zostać wyliczona data Wielkanocy.

    Returns:
        date: Wyliczona data Niedzieli Wielkanocnej.

    Raises:
        TypeError: Gdy parametr year nie jest liczbą całkowitą.
    """
    if not isinstance(year, int):
        raise TypeError('Parametr year musi być liczbą całkowitą.')

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    var_l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * var_l) // 451
    month = (h + var_l - 7 * m + 114) // 31
    day = ((h + var_l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_polish_holidays(year: int) -> dict[date, str]:
    """Zwraca słownik polskich świąt państwowych ustawowo wolnych od pracy dla podanego roku.

    Args:
        year (int): Rok, dla którego zwracane są święta.

    Returns:
        dict[date, str]: Słownik gdzie kluczem jest obiekt daty, a wartością nazwa święta.

    Raises:
        TypeError: Gdy parametr year nie jest liczbą całkowitą.
    """
    if not isinstance(year, int):
        raise TypeError('Parametr year musi być liczbą całkowitą.')

    easter = get_easter_date(year)
    easter_monday = easter + timedelta(days=1)
    zielone_swiatki = easter + timedelta(days=49)
    boze_cialo = easter + timedelta(days=60)

    holidays: dict[date, str] = {
        date(year, 1, 1): 'Nowy Rok',
        date(year, 1, 6): 'Święto Trzech Króli',
        easter: 'Wielkanoc (Pierwszy Dzień)',
        easter_monday: 'Poniedziałek Wielkanocny',
        date(year, 5, 1): 'Święto Pracy',
        date(year, 5, 3): 'Święto Konstytucji 3 Maja',
        zielone_swiatki: 'Zielone Świątki',
        boze_cialo: 'Boże Ciało',
        date(year, 8, 15): 'Wniebowzięcie Najświętszej Maryi Panny',
        date(year, 11, 1): 'Wszystkich Świętych',
        date(year, 11, 11): 'Święto Niepodległości',
        date(year, 12, 25): 'Boże Narodzenie (Pierwszy Dzień)',
        date(year, 12, 26): 'Boże Narodzenie (Drugi Dzień)',
    }
    return holidays


def is_polish_holiday(target_date: date) -> tuple[bool, str | None]:
    """Sprawdza, czy podana data jest polskim świętem państwowym wolnym od pracy.

    Args:
        target_date (date): Weryfikowana data.

    Returns:
        tuple[bool, str | None]: Krotka (True, nazwa_święta) lub (False, None).

    Raises:
        TypeError: Gdy parametr target_date nie jest instancją date.
    """
    if not isinstance(target_date, date):
        raise TypeError('Parametr target_date musi być instancją date.')

    holidays = get_polish_holidays(target_date.year)
    if target_date in holidays:
        return True, holidays[target_date]
    return False, None

