<<<<<<< HEAD
from __future__ import annotations
from tlumacz_tekst import TlumaczBraille

class TlumaczBrailleOCR:
    def __init__(self):
        self.tlumacz_prosty = TlumaczBraille()
        self._ocr_dostepne = self._sprawdz_dostepnosc_ocr()

    def _sprawdz_dostepnosc_ocr(self) -> bool:
        try:
            import cv2
            import numpy as np
            from sklearn.cluster import KMeans
            import detekcja_i_translacja
            import tablica_unicode
            print("[OCR] ✓ Moduły detekcja_i_translacja.py i tablica_unicode.py dostępne")
            return True
        except ImportError as e:
            print(f"[OCR] ✗ Moduły OCR niedostępne: {e}")
            return False

    def czy_ocr_dostepne(self) -> bool:
        return self._ocr_dostepne

    def przetlumacz_z_tekstu_braille(self, tekst_braille: str) -> tuple[bool, str, str, str]:
        if not tekst_braille or not tekst_braille.strip():
            return False, "", "", "Pusty tekst Braille"

        if self._ocr_dostepne:
            try:
                from tablica_unicode import maska_na_tekst

                print("[TŁUMACZENIE] Próba użycia tablica_unicode.py...")

                stan = {
                    "liczbowe": False,
                    "kap_nastepna": False,
                    "kap_oczekiwanie": 0,
                    "kap_slowo": False,
                    "nawias_bal": 0
                }

                wynik = []
                for ch in tekst_braille:
                    code = ord(ch)
                    if 0x2800 <= code <= 0x28FF:
                        maska = code - 0x2800
                        wynik.append(maska_na_tekst(maska, stan))
                    else:
                        wynik.append(ch)

                tekst_polski = ''.join(wynik)

                if tekst_polski.strip():
                    print("[TŁUMACZENIE] ✓ Użyto tablica_unicode.py")
                    return True, tekst_braille, tekst_polski, "Użyto tłumaczenia z tablica_unicode.py"

            except Exception as e:
                print(f"[TŁUMACZENIE] ✗ Błąd tablica_unicode.py: {e}")

        print("[TŁUMACZENIE] Fallback do prostego mapowania (tlumacz_laczenie.py)")
        sukces, polski, kom = self.tlumacz_prosty.braille_na_polski(tekst_braille)

        if sukces:
            return True, tekst_braille, polski, "Użyto prostego mapowania (tlumacz_laczenie.py)"
        else:
            return False, "", "", kom

    def przetlumacz_z_obrazu(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str, str]:
        if not self._ocr_dostepne:
            return False, "", "", "Brak wymaganych bibliotek OCR (opencv-python, scikit-learn, PyMuPDF)"

        try:
            from detekcja_i_translacja import rozpoznaj_obraz
            import cv2

            print(f"[TŁUMACZENIE] Przetwarzanie obrazu: {sciezka}")
            print("[TŁUMACZENIE] Używam detekcja_i_translacja.py + tablica_unicode.py")

            img = cv2.imread(sciezka)
            if img is None:
                return False, "", "", f"Nie można wczytać obrazu: {sciezka}"

            tekst_polski, tekst_braille, _ = rozpoznaj_obraz(
                img,
                debug=debug,
                naprawa="light",
                mnoz_slowa=1.6,
                mnoz_a=1.35
            )

            if not tekst_polski.strip():
                return False, "", "", "Nie rozpoznano tekstu Braille na obrazie"

            print(f"[TŁUMACZENIE] ✓ Rozpoznano {len(tekst_braille)} znaków Braille → {len(tekst_polski)} znaków polskich")
            komunikat = f"OCR: detekcja_i_translacja.py + tablica_unicode.py ({len(tekst_braille)} → {len(tekst_polski)} znaków)"
            return True, tekst_braille, tekst_polski, komunikat

        except ImportError as e:
            return False, "", "", f"Błąd importu modułu OCR: {str(e)}"
        except Exception as e:
            return False, "", "", f"Błąd OCR: {str(e)}"

    def przetlumacz_z_pdf(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str, str]:
        if not self._ocr_dostepne:
            return False, "", "", "Brak wymaganych bibliotek OCR"

        try:
            print(f"[TŁUMACZENIE] Przetwarzanie PDF: {sciezka}")

            if self._pdf_zawiera_unicode_braille(sciezka):
                print("[TŁUMACZENIE] PDF zawiera Unicode Braille - używam tablica_unicode.py")
                return self._przetlumacz_pdf_unicode_ocr(sciezka)
            else:
                print("[TŁUMACZENIE] PDF bez Unicode - używam OCR (detekcja_i_translacja.py + tablica_unicode.py)")
                return self._przetlumacz_pdf_ocr(sciezka, debug)

        except Exception as e:
            return False, "", "", f"Błąd przetwarzania PDF: {str(e)}"

    def _pdf_zawiera_unicode_braille(self, sciezka: str) -> bool:
        try:
            import fitz
            doc = fitz.open(sciezka)
            for p in doc:
                txt = p.get_text()
                if any(0x2800 <= ord(ch) <= 0x28FF for ch in txt):
                    doc.close()
                    return True
            doc.close()
            return False
        except:
            return False

    def _przetlumacz_pdf_unicode_ocr(self, sciezka: str) -> tuple[bool, str, str, str]:
        try:
            import fitz
            from tablica_unicode import maska_na_tekst

            print("[TŁUMACZENIE] Wydobywanie Unicode z PDF używając tablica_unicode.py...")

            doc = fitz.open(sciezka)
            tekst_braille_all = []
            tekst_polski_all = []

            for nr_strony, strona in enumerate(doc, 1):
                txt = strona.get_text()

                stan = {
                    "liczbowe": False,
                    "kap_nastepna": False,
                    "kap_oczekiwanie": 0,
                    "kap_slowo": False,
                    "nawias_bal": 0
                }

                braille_buf = []
                polski_buf = []

                i = 0
                while i < len(txt):
                    ch = txt[i]
                    code = ord(ch)

                    if 0x2800 <= code <= 0x28FF:
                        maska = code - 0x2800

                        if maska == (8 | 32):  # ZNAK_KAPITAL
                            if i + 1 < len(txt) and ord(txt[i+1]) == code:
                                braille_buf.append(ch)
                                braille_buf.append(txt[i+1])
                                stan["kap_slowo"] = True
                                stan["kap_nastepna"] = False
                                i += 2
                                continue

                        wynik = maska_na_tekst(maska, stan)
                        polski_buf.append(wynik)
                        braille_buf.append(ch)
                        i += 1

                    else:
                        if ch in ' \t\r\n,.;:?!-()[]"\'':
                            stan["kap_slowo"] = False

                        if stan.get("kap_slowo") and ch.isalpha():
                            polski_buf.append(ch.upper())
                        else:
                            polski_buf.append(ch)

                        braille_buf.append(ch)
                        i += 1

                tekst_braille_all.append(''.join(braille_buf))
                tekst_polski_all.append(''.join(polski_buf))
                print(f"[TŁUMACZENIE] Strona {nr_strony}: {len(braille_buf)} znaków Braille")

            doc.close()

            braille_final = '\n\n'.join(tekst_braille_all)
            polski_final = '\n\n'.join(tekst_polski_all)

            print(f"[TŁUMACZENIE] ✓ Przetłumaczono PDF: {len(braille_final)} → {len(polski_final)} znaków")
            komunikat = f"PDF Unicode: tablica_unicode.py ({len(doc)} stron, {len(braille_final)} → {len(polski_final)} znaków)"
            return True, braille_final, polski_final, komunikat

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", "", f"Błąd wydobywania Unicode z PDF: {str(e)}"

    def _przetlumacz_pdf_ocr(self, sciezka: str, debug: bool) -> tuple[bool, str, str, str]:
        try:
            from detekcja_i_translacja import pdf_na_obrazy, rozpoznaj_obraz

            print("[TŁUMACZENIE] OCR na obrazach PDF (detekcja_i_translacja.py + tablica_unicode.py)...")

            obrazy = pdf_na_obrazy(sciezka, dpi=300)
            braille_all = []
            polski_all = []

            for i, img in enumerate(obrazy, 1):
                print(f"[TŁUMACZENIE] Strona {i}/{len(obrazy)}...")

                polski, braille, _ = rozpoznaj_obraz(
                    img,
                    debug=debug,
                    naprawa="light",
                    mnoz_slowa=1.6,
                    mnoz_a=1.35
                )

                if polski.strip():
                    polski_all.append(polski)
                    braille_all.append(braille)
                    print(f"[TŁUMACZENIE] Strona {i}: {len(braille)} → {len(polski)} znaków")
                else:
                    print(f"[TŁUMACZENIE] Strona {i}: brak tekstu")

            braille_final = '\n\n'.join(braille_all)
            polski_final = '\n\n'.join(polski_all)

            if not polski_final.strip():
                return False, "", "", "Nie rozpoznano tekstu Braille w PDF"

            print(f"[TŁUMACZENIE] ✓ OCR PDF zakończony: {len(braille_final)} → {len(polski_final)} znaków")
            komunikat = f"PDF OCR: detekcja_i_translacja.py + tablica_unicode.py ({len(obrazy)} stron, {len(braille_final)} → {len(polski_final)} znaków)"
            return True, braille_final, polski_final, komunikat

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", "", f"Błąd OCR na PDF: {str(e)}"


class ProcesorDokumentow:
    def __init__(self, menadzer_dokumentow):
        self.menadzer = menadzer_dokumentow
        self.tlumacz = TlumaczBraille()
        self.tlumacz_ocr = TlumaczBrailleOCR()
        self.przetlumaczony_tekst = ""
        self.tekst_braille_zrodlowy = ""
        self.kierunek_tlumaczenia = None
        self.metoda_uzyta = None

    def przetlumacz_dokument(self, kierunek: str) -> tuple[bool, str, str]:
        if not self.menadzer.czy_ma_dokument():
            return False, "", "Brak załadowanego dokumentu"

        tekst_zrodlowy = self.menadzer.pobierz_zawartosc()

        if not tekst_zrodlowy or not tekst_zrodlowy.strip():
            return False, "", "Dokument jest pusty"

        self.kierunek_tlumaczenia = kierunek

        if kierunek == 'pl_br':
            print("[TŁUMACZENIE] Polski → Braille: używam tlumacz_laczenie.py")
            sukces, self.przetlumaczony_tekst, komunikat = self.tlumacz.polski_na_braille(tekst_zrodlowy)
            self.metoda_uzyta = 'prosty'

        elif kierunek == 'br_pl':
            print("[TŁUMACZENIE] Braille → Polski: próba użycia tablica_unicode.py...")
            sukces, braille, polski, kom = self.tlumacz_ocr.przetlumacz_z_tekstu_braille(tekst_zrodlowy)

            if sukces:
                self.przetlumaczony_tekst = polski
                self.tekst_braille_zrodlowy = braille
                komunikat = kom
                self.metoda_uzyta = 'ocr' if 'braille_translate' in kom else 'prosty'
            else:
                komunikat = kom

        else:
            return False, "", f"Nieznany kierunek tłumaczenia: {kierunek}"

        return sukces, self.przetlumaczony_tekst, komunikat

    def przetlumacz_tekst(self, tekst: str, kierunek: str) -> tuple[bool, str, str]:
        if not tekst or not tekst.strip():
            return False, "", "Tekst jest pusty"

        self.kierunek_tlumaczenia = kierunek

        if kierunek == 'pl_br':
            print("[TŁUMACZENIE] Polski → Braille: używam tlumacz_laczenie.py")
            sukces, self.przetlumaczony_tekst, komunikat = self.tlumacz.polski_na_braille(tekst)
            self.metoda_uzyta = 'prosty'

        elif kierunek == 'br_pl':
            print("[TŁUMACZENIE] Braille → Polski: próba użycia tablica_unicode.py...")
            sukces, braille, polski, kom = self.tlumacz_ocr.przetlumacz_z_tekstu_braille(tekst)

            if sukces:
                self.przetlumaczony_tekst = polski
                self.tekst_braille_zrodlowy = braille
                komunikat = kom
                self.metoda_uzyta = 'ocr' if 'braille_translate' in kom else 'prosty'
            else:
                komunikat = kom

        else:
            return False, "", f"Nieznany kierunek tłumaczenia: {kierunek}"

        return sukces, self.przetlumaczony_tekst, komunikat

    def przetlumacz_z_pliku_obrazu(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str]:
        if not self.tlumacz_ocr.czy_ocr_dostepne():
            return False, "", "OCR niedostępne. Zainstaluj: pip install opencv-python scikit-learn PyMuPDF"

        sukces, braille, polski, komunikat = self.tlumacz_ocr.przetlumacz_z_obrazu(sciezka, debug)

        if sukces:
            self.tekst_braille_zrodlowy = braille
            self.przetlumaczony_tekst = polski
            self.kierunek_tlumaczenia = 'br_pl'
            self.metoda_uzyta = 'ocr'

        return sukces, polski, komunikat

    def przetlumacz_z_pliku_pdf(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str]:
        if not self.tlumacz_ocr.czy_ocr_dostepne():
            return False, "", "OCR niedostępne. Zainstaluj: pip install opencv-python scikit-learn PyMuPDF"

        sukces, braille, polski, komunikat = self.tlumacz_ocr.przetlumacz_z_pdf(sciezka, debug)

        if sukces:
            self.tekst_braille_zrodlowy = braille
            self.przetlumaczony_tekst = polski
            self.kierunek_tlumaczenia = 'br_pl'
            self.metoda_uzyta = 'ocr'

        return sukces, polski, komunikat

    def pobierz_przetlumaczony(self) -> str:
        return self.przetlumaczony_tekst

    def pobierz_braille_zrodlowy(self) -> str:
        return self.tekst_braille_zrodlowy

    def pobierz_statystyki(self, tekst_wejsciowy: str) -> dict:
        if not self.przetlumaczony_tekst:
            return None

        return self.tlumacz.pobierz_statystyki_tlumaczenia(
            tekst_wejsciowy,
            self.przetlumaczony_tekst
        )

    def wykryj_typ_tekstu(self, tekst: str) -> str:
        if not tekst or not tekst.strip():
            return 'nieznany'

        if self.tlumacz.czy_jest_braillem(tekst):
            return 'braille'

        polskie_znaki = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
        for znak in tekst:
            if znak in polskie_znaki:
                return 'polski'

        if any(c.isalpha() for c in tekst):
            return 'polski'

        return 'nieznany'
=======
from __future__ import annotations
from tlumacz_tekst import TlumaczBraille

class TlumaczBrailleOCR:
    def __init__(self):
        self.tlumacz_prosty = TlumaczBraille()
        self._ocr_dostepne = self._sprawdz_dostepnosc_ocr()

    def _sprawdz_dostepnosc_ocr(self) -> bool:
        try:
            import cv2
            import numpy as np
            from sklearn.cluster import KMeans
            import detekcja_i_translacja
            import tablica_unicode
            print("[OCR] ✓ Moduły detekcja_i_translacja.py i tablica_unicode.py dostępne")
            return True
        except ImportError as e:
            print(f"[OCR] ✗ Moduły OCR niedostępne: {e}")
            return False

    def czy_ocr_dostepne(self) -> bool:
        return self._ocr_dostepne

    def przetlumacz_z_tekstu_braille(self, tekst_braille: str) -> tuple[bool, str, str, str]:
        if not tekst_braille or not tekst_braille.strip():
            return False, "", "", "Pusty tekst Braille"

        if self._ocr_dostepne:
            try:
                from tablica_unicode import maska_na_tekst

                print("[TŁUMACZENIE] Próba użycia tablica_unicode.py...")

                stan = {
                    "liczbowe": False,
                    "kap_nastepna": False,
                    "kap_oczekiwanie": 0,
                    "kap_slowo": False,
                    "nawias_bal": 0
                }

                wynik = []
                for ch in tekst_braille:
                    code = ord(ch)
                    if 0x2800 <= code <= 0x28FF:
                        maska = code - 0x2800
                        wynik.append(maska_na_tekst(maska, stan))
                    else:
                        wynik.append(ch)

                tekst_polski = ''.join(wynik)

                if tekst_polski.strip():
                    print("[TŁUMACZENIE] ✓ Użyto tablica_unicode.py")
                    return True, tekst_braille, tekst_polski, "Użyto tłumaczenia z tablica_unicode.py"

            except Exception as e:
                print(f"[TŁUMACZENIE] ✗ Błąd tablica_unicode.py: {e}")

        print("[TŁUMACZENIE] Fallback do prostego mapowania (tlumacz_laczenie.py)")
        sukces, polski, kom = self.tlumacz_prosty.braille_na_polski(tekst_braille)

        if sukces:
            return True, tekst_braille, polski, "Użyto prostego mapowania (tlumacz_laczenie.py)"
        else:
            return False, "", "", kom

    def przetlumacz_z_obrazu(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str, str]:
        if not self._ocr_dostepne:
            return False, "", "", "Brak wymaganych bibliotek OCR (opencv-python, scikit-learn, PyMuPDF)"

        try:
            from detekcja_i_translacja import rozpoznaj_obraz
            import cv2

            print(f"[TŁUMACZENIE] Przetwarzanie obrazu: {sciezka}")
            print("[TŁUMACZENIE] Używam detekcja_i_translacja.py + tablica_unicode.py")

            img = cv2.imread(sciezka)
            if img is None:
                return False, "", "", f"Nie można wczytać obrazu: {sciezka}"

            tekst_polski, tekst_braille, _ = rozpoznaj_obraz(
                img,
                debug=debug,
                naprawa="light",
                mnoz_slowa=1.6,
                mnoz_a=1.35
            )

            if not tekst_polski.strip():
                return False, "", "", "Nie rozpoznano tekstu Braille na obrazie"

            print(f"[TŁUMACZENIE] ✓ Rozpoznano {len(tekst_braille)} znaków Braille → {len(tekst_polski)} znaków polskich")
            komunikat = f"OCR: detekcja_i_translacja.py + tablica_unicode.py ({len(tekst_braille)} → {len(tekst_polski)} znaków)"
            return True, tekst_braille, tekst_polski, komunikat

        except ImportError as e:
            return False, "", "", f"Błąd importu modułu OCR: {str(e)}"
        except Exception as e:
            return False, "", "", f"Błąd OCR: {str(e)}"

    def przetlumacz_z_pdf(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str, str]:
        if not self._ocr_dostepne:
            return False, "", "", "Brak wymaganych bibliotek OCR"

        try:
            print(f"[TŁUMACZENIE] Przetwarzanie PDF: {sciezka}")

            if self._pdf_zawiera_unicode_braille(sciezka):
                print("[TŁUMACZENIE] PDF zawiera Unicode Braille - używam tablica_unicode.py")
                return self._przetlumacz_pdf_unicode_ocr(sciezka)
            else:
                print("[TŁUMACZENIE] PDF bez Unicode - używam OCR (detekcja_i_translacja.py + tablica_unicode.py)")
                return self._przetlumacz_pdf_ocr(sciezka, debug)

        except Exception as e:
            return False, "", "", f"Błąd przetwarzania PDF: {str(e)}"

    def _pdf_zawiera_unicode_braille(self, sciezka: str) -> bool:
        try:
            import fitz
            doc = fitz.open(sciezka)
            for p in doc:
                txt = p.get_text()
                if any(0x2800 <= ord(ch) <= 0x28FF for ch in txt):
                    doc.close()
                    return True
            doc.close()
            return False
        except:
            return False

    def _przetlumacz_pdf_unicode_ocr(self, sciezka: str) -> tuple[bool, str, str, str]:
        try:
            import fitz
            from tablica_unicode import maska_na_tekst

            print("[TŁUMACZENIE] Wydobywanie Unicode z PDF używając tablica_unicode.py...")

            doc = fitz.open(sciezka)
            tekst_braille_all = []
            tekst_polski_all = []

            for nr_strony, strona in enumerate(doc, 1):
                txt = strona.get_text()

                stan = {
                    "liczbowe": False,
                    "kap_nastepna": False,
                    "kap_oczekiwanie": 0,
                    "kap_slowo": False,
                    "nawias_bal": 0
                }

                braille_buf = []
                polski_buf = []

                i = 0
                while i < len(txt):
                    ch = txt[i]
                    code = ord(ch)

                    if 0x2800 <= code <= 0x28FF:
                        maska = code - 0x2800

                        if maska == (8 | 32):  # ZNAK_KAPITAL
                            if i + 1 < len(txt) and ord(txt[i+1]) == code:
                                braille_buf.append(ch)
                                braille_buf.append(txt[i+1])
                                stan["kap_slowo"] = True
                                stan["kap_nastepna"] = False
                                i += 2
                                continue

                        wynik = maska_na_tekst(maska, stan)
                        polski_buf.append(wynik)
                        braille_buf.append(ch)
                        i += 1

                    else:
                        if ch in ' \t\r\n,.;:?!-()[]"\'':
                            stan["kap_slowo"] = False

                        if stan.get("kap_slowo") and ch.isalpha():
                            polski_buf.append(ch.upper())
                        else:
                            polski_buf.append(ch)

                        braille_buf.append(ch)
                        i += 1

                tekst_braille_all.append(''.join(braille_buf))
                tekst_polski_all.append(''.join(polski_buf))
                print(f"[TŁUMACZENIE] Strona {nr_strony}: {len(braille_buf)} znaków Braille")

            doc.close()

            braille_final = '\n\n'.join(tekst_braille_all)
            polski_final = '\n\n'.join(tekst_polski_all)

            print(f"[TŁUMACZENIE] ✓ Przetłumaczono PDF: {len(braille_final)} → {len(polski_final)} znaków")
            komunikat = f"PDF Unicode: tablica_unicode.py ({len(doc)} stron, {len(braille_final)} → {len(polski_final)} znaków)"
            return True, braille_final, polski_final, komunikat

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", "", f"Błąd wydobywania Unicode z PDF: {str(e)}"

    def _przetlumacz_pdf_ocr(self, sciezka: str, debug: bool) -> tuple[bool, str, str, str]:
        try:
            from detekcja_i_translacja import pdf_na_obrazy, rozpoznaj_obraz

            print("[TŁUMACZENIE] OCR na obrazach PDF (detekcja_i_translacja.py + tablica_unicode.py)...")

            obrazy = pdf_na_obrazy(sciezka, dpi=300)
            braille_all = []
            polski_all = []

            for i, img in enumerate(obrazy, 1):
                print(f"[TŁUMACZENIE] Strona {i}/{len(obrazy)}...")

                polski, braille, _ = rozpoznaj_obraz(
                    img,
                    debug=debug,
                    naprawa="light",
                    mnoz_slowa=1.6,
                    mnoz_a=1.35
                )

                if polski.strip():
                    polski_all.append(polski)
                    braille_all.append(braille)
                    print(f"[TŁUMACZENIE] Strona {i}: {len(braille)} → {len(polski)} znaków")
                else:
                    print(f"[TŁUMACZENIE] Strona {i}: brak tekstu")

            braille_final = '\n\n'.join(braille_all)
            polski_final = '\n\n'.join(polski_all)

            if not polski_final.strip():
                return False, "", "", "Nie rozpoznano tekstu Braille w PDF"

            print(f"[TŁUMACZENIE] ✓ OCR PDF zakończony: {len(braille_final)} → {len(polski_final)} znaków")
            komunikat = f"PDF OCR: detekcja_i_translacja.py + tablica_unicode.py ({len(obrazy)} stron, {len(braille_final)} → {len(polski_final)} znaków)"
            return True, braille_final, polski_final, komunikat

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", "", f"Błąd OCR na PDF: {str(e)}"


class ProcesorDokumentow:
    def __init__(self, menadzer_dokumentow):
        self.menadzer = menadzer_dokumentow
        self.tlumacz = TlumaczBraille()
        self.tlumacz_ocr = TlumaczBrailleOCR()
        self.przetlumaczony_tekst = ""
        self.tekst_braille_zrodlowy = ""
        self.kierunek_tlumaczenia = None
        self.metoda_uzyta = None

    def przetlumacz_dokument(self, kierunek: str) -> tuple[bool, str, str]:
        if not self.menadzer.czy_ma_dokument():
            return False, "", "Brak załadowanego dokumentu"

        tekst_zrodlowy = self.menadzer.pobierz_zawartosc()

        if not tekst_zrodlowy or not tekst_zrodlowy.strip():
            return False, "", "Dokument jest pusty"

        self.kierunek_tlumaczenia = kierunek

        if kierunek == 'pl_br':
            print("[TŁUMACZENIE] Polski → Braille: używam tlumacz_laczenie.py")
            sukces, self.przetlumaczony_tekst, komunikat = self.tlumacz.polski_na_braille(tekst_zrodlowy)
            self.metoda_uzyta = 'prosty'

        elif kierunek == 'br_pl':
            print("[TŁUMACZENIE] Braille → Polski: próba użycia tablica_unicode.py...")
            sukces, braille, polski, kom = self.tlumacz_ocr.przetlumacz_z_tekstu_braille(tekst_zrodlowy)

            if sukces:
                self.przetlumaczony_tekst = polski
                self.tekst_braille_zrodlowy = braille
                komunikat = kom
                self.metoda_uzyta = 'ocr' if 'braille_translate' in kom else 'prosty'
            else:
                komunikat = kom

        else:
            return False, "", f"Nieznany kierunek tłumaczenia: {kierunek}"

        return sukces, self.przetlumaczony_tekst, komunikat

    def przetlumacz_tekst(self, tekst: str, kierunek: str) -> tuple[bool, str, str]:
        if not tekst or not tekst.strip():
            return False, "", "Tekst jest pusty"

        self.kierunek_tlumaczenia = kierunek

        if kierunek == 'pl_br':
            print("[TŁUMACZENIE] Polski → Braille: używam tlumacz_laczenie.py")
            sukces, self.przetlumaczony_tekst, komunikat = self.tlumacz.polski_na_braille(tekst)
            self.metoda_uzyta = 'prosty'

        elif kierunek == 'br_pl':
            print("[TŁUMACZENIE] Braille → Polski: próba użycia tablica_unicode.py...")
            sukces, braille, polski, kom = self.tlumacz_ocr.przetlumacz_z_tekstu_braille(tekst)

            if sukces:
                self.przetlumaczony_tekst = polski
                self.tekst_braille_zrodlowy = braille
                komunikat = kom
                self.metoda_uzyta = 'ocr' if 'braille_translate' in kom else 'prosty'
            else:
                komunikat = kom

        else:
            return False, "", f"Nieznany kierunek tłumaczenia: {kierunek}"

        return sukces, self.przetlumaczony_tekst, komunikat

    def przetlumacz_z_pliku_obrazu(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str]:
        if not self.tlumacz_ocr.czy_ocr_dostepne():
            return False, "", "OCR niedostępne. Zainstaluj: pip install opencv-python scikit-learn PyMuPDF"

        sukces, braille, polski, komunikat = self.tlumacz_ocr.przetlumacz_z_obrazu(sciezka, debug)

        if sukces:
            self.tekst_braille_zrodlowy = braille
            self.przetlumaczony_tekst = polski
            self.kierunek_tlumaczenia = 'br_pl'
            self.metoda_uzyta = 'ocr'

        return sukces, polski, komunikat

    def przetlumacz_z_pliku_pdf(self, sciezka: str, debug: bool = False) -> tuple[bool, str, str]:
        if not self.tlumacz_ocr.czy_ocr_dostepne():
            return False, "", "OCR niedostępne. Zainstaluj: pip install opencv-python scikit-learn PyMuPDF"

        sukces, braille, polski, komunikat = self.tlumacz_ocr.przetlumacz_z_pdf(sciezka, debug)

        if sukces:
            self.tekst_braille_zrodlowy = braille
            self.przetlumaczony_tekst = polski
            self.kierunek_tlumaczenia = 'br_pl'
            self.metoda_uzyta = 'ocr'

        return sukces, polski, komunikat

    def pobierz_przetlumaczony(self) -> str:
        return self.przetlumaczony_tekst

    def pobierz_braille_zrodlowy(self) -> str:
        return self.tekst_braille_zrodlowy

    def pobierz_statystyki(self, tekst_wejsciowy: str) -> dict:
        if not self.przetlumaczony_tekst:
            return None

        return self.tlumacz.pobierz_statystyki_tlumaczenia(
            tekst_wejsciowy,
            self.przetlumaczony_tekst
        )

    def wykryj_typ_tekstu(self, tekst: str) -> str:
        if not tekst or not tekst.strip():
            return 'nieznany'

        if self.tlumacz.czy_jest_braillem(tekst):
            return 'braille'

        polskie_znaki = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
        for znak in tekst:
            if znak in polskie_znaki:
                return 'polski'

        if any(c.isalpha() for c in tekst):
            return 'polski'

        return 'nieznany'
>>>>>>> 6ecdc4fe137fd6bdbf48b60475110ab816c0aca2
