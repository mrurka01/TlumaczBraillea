class TlumaczBraille:
    POLSKI_NA_BRAILLE_PODSTAWOWE = {
        'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
        'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
        'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
        'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
        'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽',
        'z': '⠵',

        'ą': '⠡', 'ć': '⠩', 'ę': '⠱', 'ł': '⠣', 'ń': '⠹',
        'ó': '⠬', 'ś': '⠪', 'ź': '⠮', 'ż': '⠯',

        '0': '⠚', '1': '⠁', '2': '⠃', '3': '⠉', '4': '⠙',
        '5': '⠑', '6': '⠋', '7': '⠛', '8': '⠓', '9': '⠊',

        ' ': ' ',
        '.': '⠲',
        ',': '⠂',
        ';': '⠆',
        ':': '⠒',
        '!': '⠖',
        '?': '⠦',
        '-': '⠤',
        '(': '⠐⠣',
        ')': '⠐⠜',
        '"': '⠦',
        "'": '⠄',
        '/': '⠌',
        '\\': '⠳',
        '@': '⠈⠁',
        '#': '⠼⠹',
        '%': '⠼⠴',
        '&': '⠈⠯',
        '*': '⠐⠔',
        '+': '⠐⠖',
        '=': '⠐⠶',
        '<': '⠐⠣',
        '>': '⠐⠜',
        '\n': '\n',
        '\t': '\t',
    }

    PREFIKS_KAPITAL_POJEDYNCZY = '⠨'
    PREFIKS_KAPITAL_SLOWO = '⠨⠨'
    PREFIKS_LICZBA = '⠼'

    def __init__(self):
        self.POLSKI_NA_BRAILLE = self._utworz_pelne_mapowanie()
        self.BRAILLE_NA_POLSKI = {v: k for k, v in self.POLSKI_NA_BRAILLE.items()}

    def _utworz_pelne_mapowanie(self) -> dict:
        mapowanie = self.POLSKI_NA_BRAILLE_PODSTAWOWE.copy()

        for litera in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            braille_mala = self.POLSKI_NA_BRAILLE_PODSTAWOWE.get(litera.lower())
            if braille_mala:
                mapowanie[litera] = self.PREFIKS_KAPITAL_POJEDYNCZY + braille_mala

        polskie_male = {'ą': '⠡', 'ć': '⠩', 'ę': '⠱', 'ł': '⠣', 'ń': '⠹',
                'ó': '⠬', 'ś': '⠪', 'ź': '⠮', 'ż': '⠯'}
        for mala, braille in polskie_male.items():
            mapowanie[mala.upper()] = self.PREFIKS_KAPITAL_POJEDYNCZY + braille

        return mapowanie

    def _czy_cale_slowo_wielkie(self, slowo: str) -> bool:
        if not slowo:
            return False
        litery = [c for c in slowo if c.isalpha()]
        if not litery:
            return False
        return all(c.isupper() for c in litery) and len(litery) >= 2

    def _podziel_na_tokeny(self, tekst: str) -> list:
        tokeny = []
        i = 0

        while i < len(tekst):
            znak = tekst[i]

            if znak.isdigit():
                liczba = ''
                while i < len(tekst) and tekst[i].isdigit():
                    liczba += tekst[i]
                    i += 1
                tokeny.append(('liczba', liczba))
                continue

            elif znak.isalpha():
                slowo = ''
                while i < len(tekst) and tekst[i].isalnum():
                    slowo += tekst[i]
                    i += 1
                tokeny.append(('slowo', slowo))
                continue

            else:
                tokeny.append(('separator', znak))
                i += 1

        return tokeny

    def polski_na_braille(self, tekst: str) -> tuple[bool, str, str]:
        try:
            wynik = []
            nieobslugiwane = set()

            tokeny = self._podziel_na_tokeny(tekst)

            for typ, zawartosc in tokeny:
                if typ == 'liczba':
                    wynik.append(self.PREFIKS_LICZBA)
                    for cyfra in zawartosc:
                        if cyfra in self.POLSKI_NA_BRAILLE_PODSTAWOWE:
                            wynik.append(self.POLSKI_NA_BRAILLE_PODSTAWOWE[cyfra])
                        else:
                            wynik.append(cyfra)
                            nieobslugiwane.add(cyfra)

                elif typ == 'slowo':
                    if self._czy_cale_slowo_wielkie(zawartosc):
                        wynik.append(self.PREFIKS_KAPITAL_SLOWO)
                        for znak in zawartosc:
                            znak_maly = znak.lower()
                            if znak_maly in self.POLSKI_NA_BRAILLE_PODSTAWOWE:
                                wynik.append(self.POLSKI_NA_BRAILLE_PODSTAWOWE[znak_maly])
                            else:
                                wynik.append(znak)
                                nieobslugiwane.add(znak)
                    else:
                        for znak in zawartosc:
                            if znak.isupper():
                                znak_maly = znak.lower()
                                if znak_maly in self.POLSKI_NA_BRAILLE_PODSTAWOWE:
                                    wynik.append(self.PREFIKS_KAPITAL_POJEDYNCZY)
                                    wynik.append(self.POLSKI_NA_BRAILLE_PODSTAWOWE[znak_maly])
                                else:
                                    wynik.append(znak)
                                    nieobslugiwane.add(znak)
                            else:
                                if znak in self.POLSKI_NA_BRAILLE_PODSTAWOWE:
                                    wynik.append(self.POLSKI_NA_BRAILLE_PODSTAWOWE[znak])
                                else:
                                    wynik.append(znak)
                                    nieobslugiwane.add(znak)

                elif typ == 'separator':
                    if zawartosc in self.POLSKI_NA_BRAILLE_PODSTAWOWE:
                        wynik.append(self.POLSKI_NA_BRAILLE_PODSTAWOWE[zawartosc])
                    else:
                        wynik.append(zawartosc)
                        nieobslugiwane.add(zawartosc)

            komunikat = ""
            if nieobslugiwane:
                lista_znakow = ', '.join(f"'{z}'" for z in sorted(nieobslugiwane))
                komunikat = f"Ostrzeżenie: Nieobsługiwane znaki: {lista_znakow}"

            return True, ''.join(wynik), komunikat

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", f"Błąd tłumaczenia: {str(e)}"

    def braille_na_polski(self, tekst_braille: str) -> tuple[bool, str, str]:
        try:
            wynik = []
            nieobslugiwane = set()
            i = 0

            tryb_kapital_slowo = False
            tryb_liczba = False

            while i < len(tekst_braille):
                znak = tekst_braille[i]

                if i + 1 < len(tekst_braille):
                    dwuznakowy = tekst_braille[i:i + 2]

                    if dwuznakowy == self.PREFIKS_KAPITAL_SLOWO:
                        tryb_kapital_slowo = True
                        tryb_liczba = False
                        i += 2
                        continue

                if znak == self.PREFIKS_KAPITAL_POJEDYNCZY:
                    i += 1
                    if i < len(tekst_braille):
                        nastepny = tekst_braille[i]

                        braille_na_male = {v: k for k, v in self.POLSKI_NA_BRAILLE_PODSTAWOWE.items() if
                                           k.isalpha() and k.islower()}

                        if nastepny in braille_na_male:
                            wynik.append(braille_na_male[nastepny].upper())
                        else:
                            wynik.append(nastepny)
                            nieobslugiwane.add(nastepny)
                    i += 1
                    continue

                if znak == self.PREFIKS_LICZBA:
                    tryb_liczba = True
                    tryb_kapital_slowo = False
                    i += 1
                    continue

                if znak in ' \t\n\r.,;:!?-()[]{}"\'/\\':
                    tryb_kapital_slowo = False
                    tryb_liczba = False

                    if znak in self.POLSKI_NA_BRAILLE_PODSTAWOWE.values():
                        for k, v in self.POLSKI_NA_BRAILLE_PODSTAWOWE.items():
                            if v == znak:
                                wynik.append(k)
                                break
                    else:
                        wynik.append(znak)
                    i += 1
                    continue

                if tryb_liczba:
                    cyfry_braille = {
                        '⠚': '0', '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4',
                        '⠑': '5', '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9'
                    }

                    if znak in cyfry_braille:
                        wynik.append(cyfry_braille[znak])
                        i += 1
                        continue
                    else:
                        tryb_liczba = False

                if tryb_kapital_slowo:
                    braille_na_male = {v: k for k, v in self.POLSKI_NA_BRAILLE_PODSTAWOWE.items() if
                                       k.isalpha() and k.islower()}

                    if znak in braille_na_male:
                        wynik.append(braille_na_male[znak].upper())
                        i += 1
                        continue

                braille_na_znak = {
                    v: k
                    for k, v in self.POLSKI_NA_BRAILLE_PODSTAWOWE.items()
                    if not k.isdigit()
                    }

                if znak in braille_na_znak:
                    wynik.append(braille_na_znak[znak])
                else:
                    wynik.append(znak)
                    nieobslugiwane.add(znak)

                i += 1

            komunikat = ""
            if nieobslugiwane:
                komunikat = f"Ostrzeżenie: Nieobsługiwane znaki Braille'a: {len(nieobslugiwane)} znaków"

            return True, ''.join(wynik), komunikat

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", f"Błąd tłumaczenia: {str(e)}"

    def czy_jest_braillem(self, tekst: str) -> bool:
        for znak in tekst:
            if 0x2800 <= ord(znak) <= 0x28FF:
                return True
        return False

    def pobierz_statystyki_tlumaczenia(self, tekst_wejsciowy: str, tekst_wyjsciowy: str) -> dict:
        return {
            'znaki_wejsciowe': len(tekst_wejsciowy),
            'znaki_wyjsciowe': len(tekst_wyjsciowy),
            'slowa_wejsciowe': len(tekst_wejsciowy.split()),
            'slowa_wyjsciowe': len(tekst_wyjsciowy.split()),
            'linie': tekst_wejsciowy.count('\n') + 1,
        }
