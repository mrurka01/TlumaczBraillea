<<<<<<< HEAD
# -*- coding: utf-8 -*-
from typing import Dict

def maska_na_unicode(maska: int) -> str:
    return chr(0x2800 + (maska & 0x3F))

# kropki 1..6
KROP1, KROP2, KROP3, KROP4, KROP5, KROP6 = 1, 2, 4, 8, 16, 32

# znaczniki trybów
ZNAK_LICZBY  = (KROP3 | KROP4 | KROP5 | KROP6)   # ⠼
ZNAK_KAPITAL = (KROP4 | KROP6)                   # ⠨  (POPRAWKA: kapitalizacja = 4+6)

# mapowanie liter podstawowych (łacińskie a–z)
MAPA_LITER: Dict[int, str] = {
    KROP1: "a", KROP1|KROP2: "b", KROP1|KROP4: "c", KROP1|KROP4|KROP5: "d", KROP1|KROP5: "e",
    KROP1|KROP2|KROP4: "f", KROP1|KROP2|KROP4|KROP5: "g", KROP1|KROP2|KROP5: "h",
    KROP2|KROP4: "i", KROP2|KROP4|KROP5: "j", KROP1|KROP3: "k", KROP1|KROP2|KROP3: "l",
    KROP1|KROP3|KROP4: "m", KROP1|KROP3|KROP4|KROP5: "n", KROP1|KROP3|KROP5: "o",
    KROP1|KROP2|KROP3|KROP4: "p", KROP1|KROP2|KROP3|KROP4|KROP5: "q", KROP1|KROP2|KROP3|KROP5: "r",
    KROP2|KROP3|KROP4: "s", KROP2|KROP3|KROP4|KROP5: "t", KROP1|KROP3|KROP6: "u",
    KROP1|KROP2|KROP3|KROP6: "v", KROP2|KROP4|KROP5|KROP6: "w", KROP1|KROP3|KROP4|KROP6: "x",
    KROP1|KROP3|KROP4|KROP5|KROP6: "y", KROP1|KROP3|KROP5|KROP6: "z",
}

# polskie znaki (zestaw jak w Twoim pliku)
MAPA_LITER.update({
    KROP1|KROP6: "ą",                        # 1+6
    KROP1|KROP4|KROP6: "ć",                  # 1+4+6
    KROP1|KROP5|KROP6: "ę",                  # 1+5+6
    KROP1|KROP2|KROP6: "ł",                  # 1+2+6
    KROP1|KROP4|KROP5|KROP6: "ń",            # 1+4+5+6
    KROP2|KROP4|KROP6: "ś",                  # 2+4+6
    KROP3|KROP4|KROP6: "ó",                  # 3+4+6
    KROP1|KROP2|KROP3|KROP4|KROP6: "ż",      # 1+2+3+4+6
    KROP2|KROP3|KROP4|KROP6: "ź",            # 2+3+4+6
})

# cyfry po znaku liczby (⠼)
MAPA_CYFR = {
    KROP1: "1", KROP1|KROP2: "2", KROP1|KROP4: "3", KROP1|KROP4|KROP5: "4", KROP1|KROP5: "5",
    KROP1|KROP2|KROP4: "6", KROP1|KROP2|KROP4|KROP5: "7", KROP1|KROP2|KROP5: "8",
    KROP2|KROP4: "9", KROP2|KROP4|KROP5: "0",
}

# interpunkcja (UWAGA: ⠄ = KROP3 → "." zgodnie z Twoją prośbą)
INTERPUNKCJA = {
    KROP2: ",",
    KROP3: ".",                      # ⠄  (POPRAWKA: kropka zamiast apostrofu)
    KROP2|KROP3: ";",
    KROP2|KROP5: ":",
    KROP2|KROP6: "?",
    KROP2|KROP3|KROP5: "!",
    KROP3|KROP6: "-",
    KROP2|KROP5|KROP6: ".",          # tradycyjny wariant kropki
    KROP3|KROP4|KROP5: "@",
    KROP3|KROP5: "*",
    0: " ",
}

# dodatkowe znaki z Twojej logiki (cudzysłowy/nawiasy)
CUDZYSLOW_L = (KROP2|KROP3|KROP6)   # „
CUDZYSLOW_P = (KROP3|KROP5|KROP6)   # ”
NAWIAS_OBU  = (KROP5)               # proste przełączanie ( i )
NAWIAS_KW_L = (KROP4|KROP6)         # [
NAWIAS_KW_P = (KROP5|KROP6)         # ]

SEPARATORY = set(" \t\r\n\u00A0,.;:?!-()[]“”'\"/\\—–")

def maska_na_tekst(maska: int, stan: dict) -> str:
    """
    Translacja pojedynczej komórki (6-kropkowej) na tekst z uwzględnieniem stanu:
    - liczby po ⠼,
    - kapitalizacja po ⠨ (pojedyncza litera) lub ⠨⠨ (całe słowo),
    - reset kapitalizacji na separatorach.
    """
    m = maska & 0x3F

    # domyślny stan
    stan.setdefault("liczbowe", False)
    stan.setdefault("kap_nastepna", False)
    stan.setdefault("kap_oczekiwanie", 0)
    stan.setdefault("kap_slowo", False)
    stan.setdefault("nawias_bal", 0)

    # znacznik liczby
    if m == ZNAK_LICZBY:
        stan["liczbowe"] = True
        return ""

    # kapitalizacja
    if m == ZNAK_KAPITAL:
        stan["kap_oczekiwanie"] += 1
        if stan["kap_oczekiwanie"] >= 2:      # ⠨⠨ → całe następne słowo
            stan["kap_oczekiwanie"] = 0
            stan["kap_slowo"] = True
        return ""

    # jeżeli mieliśmy jedno ⠨, a teraz weszła inna komórka – kapitalizuj TĘ jedną literę
    if stan["kap_oczekiwanie"] == 1 and m != ZNAK_KAPITAL:
        stan["kap_oczekiwanie"] = 0
        stan["kap_nastepna"] = True

    # tryb liczbowy
    if stan["liczbowe"]:
        if m in MAPA_CYFR:
            return MAPA_CYFR[m]
        # wyjście z trybu liczb przy czymś, co nie jest cyfrą
        stan["liczbowe"] = False

    # interpunkcja i znaki specjalne
    if m in (CUDZYSLOW_L, CUDZYSLOW_P, NAWIAS_OBU, NAWIAS_KW_L, NAWIAS_KW_P) or m in INTERPUNKCJA:
        if m == CUDZYSLOW_L:
            ch = "“"
        elif m == CUDZYSLOW_P:
            ch = "”"
        elif m == NAWIAS_OBU:
            ch = "(" if (stan["nawias_bal"] % 2 == 0) else ")"
            stan["nawias_bal"] += 1
        elif m == NAWIAS_KW_L:
            ch = "["
        elif m == NAWIAS_KW_P:
            ch = "]"
        else:
            ch = INTERPUNKCJA[m]
        # separator kończy kapitalizację całego słowa
        if ch in SEPARATORY:
            stan["kap_slowo"] = False
        return ch

    # litery
    lit = MAPA_LITER.get(m)
    if lit is None:
        stan["kap_slowo"] = False
        return "?"

    if stan["kap_nastepna"]:
        stan["kap_nastepna"] = False
        return lit.upper()

    if stan["kap_slowo"]:
        return lit.upper()

    return lit

__all__ = ["maska_na_unicode", "maska_na_tekst", "MAPA_CYFR", "ZNAK_LICZBY", "ZNAK_KAPITAL"]
=======
# -*- coding: utf-8 -*-
from typing import Dict

def maska_na_unicode(maska: int) -> str:
    return chr(0x2800 + (maska & 0x3F))

# kropki 1..6
KROP1, KROP2, KROP3, KROP4, KROP5, KROP6 = 1, 2, 4, 8, 16, 32

# znaczniki trybów
ZNAK_LICZBY  = (KROP3 | KROP4 | KROP5 | KROP6)   # ⠼
ZNAK_KAPITAL = (KROP4 | KROP6)                   # ⠨  (POPRAWKA: kapitalizacja = 4+6)

# mapowanie liter podstawowych (łacińskie a–z)
MAPA_LITER: Dict[int, str] = {
    KROP1: "a", KROP1|KROP2: "b", KROP1|KROP4: "c", KROP1|KROP4|KROP5: "d", KROP1|KROP5: "e",
    KROP1|KROP2|KROP4: "f", KROP1|KROP2|KROP4|KROP5: "g", KROP1|KROP2|KROP5: "h",
    KROP2|KROP4: "i", KROP2|KROP4|KROP5: "j", KROP1|KROP3: "k", KROP1|KROP2|KROP3: "l",
    KROP1|KROP3|KROP4: "m", KROP1|KROP3|KROP4|KROP5: "n", KROP1|KROP3|KROP5: "o",
    KROP1|KROP2|KROP3|KROP4: "p", KROP1|KROP2|KROP3|KROP4|KROP5: "q", KROP1|KROP2|KROP3|KROP5: "r",
    KROP2|KROP3|KROP4: "s", KROP2|KROP3|KROP4|KROP5: "t", KROP1|KROP3|KROP6: "u",
    KROP1|KROP2|KROP3|KROP6: "v", KROP2|KROP4|KROP5|KROP6: "w", KROP1|KROP3|KROP4|KROP6: "x",
    KROP1|KROP3|KROP4|KROP5|KROP6: "y", KROP1|KROP3|KROP5|KROP6: "z",
}

# polskie znaki (zestaw jak w Twoim pliku)
MAPA_LITER.update({
    KROP1|KROP6: "ą",                        # 1+6
    KROP1|KROP4|KROP6: "ć",                  # 1+4+6
    KROP1|KROP5|KROP6: "ę",                  # 1+5+6
    KROP1|KROP2|KROP6: "ł",                  # 1+2+6
    KROP1|KROP4|KROP5|KROP6: "ń",            # 1+4+5+6
    KROP2|KROP4|KROP6: "ś",                  # 2+4+6
    KROP3|KROP4|KROP6: "ó",                  # 3+4+6
    KROP1|KROP2|KROP3|KROP4|KROP6: "ż",      # 1+2+3+4+6
    KROP2|KROP3|KROP4|KROP6: "ź",            # 2+3+4+6
})

# cyfry po znaku liczby (⠼)
MAPA_CYFR = {
    KROP1: "1", KROP1|KROP2: "2", KROP1|KROP4: "3", KROP1|KROP4|KROP5: "4", KROP1|KROP5: "5",
    KROP1|KROP2|KROP4: "6", KROP1|KROP2|KROP4|KROP5: "7", KROP1|KROP2|KROP5: "8",
    KROP2|KROP4: "9", KROP2|KROP4|KROP5: "0",
}

# interpunkcja (UWAGA: ⠄ = KROP3 → "." zgodnie z Twoją prośbą)
INTERPUNKCJA = {
    KROP2: ",",
    KROP3: ".",                      # ⠄  (POPRAWKA: kropka zamiast apostrofu)
    KROP2|KROP3: ";",
    KROP2|KROP5: ":",
    KROP2|KROP6: "?",
    KROP2|KROP3|KROP5: "!",
    KROP3|KROP6: "-",
    KROP2|KROP5|KROP6: ".",          # tradycyjny wariant kropki
    KROP3|KROP4|KROP5: "@",
    KROP3|KROP5: "*",
    0: " ",
}

# dodatkowe znaki z Twojej logiki (cudzysłowy/nawiasy)
CUDZYSLOW_L = (KROP2|KROP3|KROP6)   # „
CUDZYSLOW_P = (KROP3|KROP5|KROP6)   # ”
NAWIAS_OBU  = (KROP5)               # proste przełączanie ( i )
NAWIAS_KW_L = (KROP4|KROP6)         # [
NAWIAS_KW_P = (KROP5|KROP6)         # ]

SEPARATORY = set(" \t\r\n\u00A0,.;:?!-()[]“”'\"/\\—–")

def maska_na_tekst(maska: int, stan: dict) -> str:
    """
    Translacja pojedynczej komórki (6-kropkowej) na tekst z uwzględnieniem stanu:
    - liczby po ⠼,
    - kapitalizacja po ⠨ (pojedyncza litera) lub ⠨⠨ (całe słowo),
    - reset kapitalizacji na separatorach.
    """
    m = maska & 0x3F

    # domyślny stan
    stan.setdefault("liczbowe", False)
    stan.setdefault("kap_nastepna", False)
    stan.setdefault("kap_oczekiwanie", 0)
    stan.setdefault("kap_slowo", False)
    stan.setdefault("nawias_bal", 0)

    # znacznik liczby
    if m == ZNAK_LICZBY:
        stan["liczbowe"] = True
        return ""

    # kapitalizacja
    if m == ZNAK_KAPITAL:
        stan["kap_oczekiwanie"] += 1
        if stan["kap_oczekiwanie"] >= 2:      # ⠨⠨ → całe następne słowo
            stan["kap_oczekiwanie"] = 0
            stan["kap_slowo"] = True
        return ""

    # jeżeli mieliśmy jedno ⠨, a teraz weszła inna komórka – kapitalizuj TĘ jedną literę
    if stan["kap_oczekiwanie"] == 1 and m != ZNAK_KAPITAL:
        stan["kap_oczekiwanie"] = 0
        stan["kap_nastepna"] = True

    # tryb liczbowy
    if stan["liczbowe"]:
        if m in MAPA_CYFR:
            return MAPA_CYFR[m]
        # wyjście z trybu liczb przy czymś, co nie jest cyfrą
        stan["liczbowe"] = False

    # interpunkcja i znaki specjalne
    if m in (CUDZYSLOW_L, CUDZYSLOW_P, NAWIAS_OBU, NAWIAS_KW_L, NAWIAS_KW_P) or m in INTERPUNKCJA:
        if m == CUDZYSLOW_L:
            ch = "“"
        elif m == CUDZYSLOW_P:
            ch = "”"
        elif m == NAWIAS_OBU:
            ch = "(" if (stan["nawias_bal"] % 2 == 0) else ")"
            stan["nawias_bal"] += 1
        elif m == NAWIAS_KW_L:
            ch = "["
        elif m == NAWIAS_KW_P:
            ch = "]"
        else:
            ch = INTERPUNKCJA[m]
        # separator kończy kapitalizację całego słowa
        if ch in SEPARATORY:
            stan["kap_slowo"] = False
        return ch

    # litery
    lit = MAPA_LITER.get(m)
    if lit is None:
        stan["kap_slowo"] = False
        return "?"

    if stan["kap_nastepna"]:
        stan["kap_nastepna"] = False
        return lit.upper()

    if stan["kap_slowo"]:
        return lit.upper()

    return lit

__all__ = ["maska_na_unicode", "maska_na_tekst", "MAPA_CYFR", "ZNAK_LICZBY", "ZNAK_KAPITAL"]
>>>>>>> 6ecdc4fe137fd6bdbf48b60475110ab816c0aca2
