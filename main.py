<<<<<<< HEAD
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog,
    QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout, QTextEdit, QWidget
)
from PyQt6.QtGui import QFont

from Inz_Okno_Glowne import Ui_MainWindow_glowne
from o_programie import Ui_MainWindow as Ui_OProgramie
from dok import MenadzerDokumentow, ImportExportPolskiBraille, ImportExportBraillePolski
from tlumacz_laczenie import ProcesorDokumentow, TlumaczBraille
from baza import BazaDanych
from ustawienia_czcionki import OknoCzcionka, MenadzerCzcionek

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

font_path = resource_path("fonts/DejaVuSans.ttf")

def load_styles():
    styles = []
    for file_name in ["style/base.qss", "style/jasny.qss", "style/ciemny.qss"]:
        path = resource_path(file_name)
        with open(path, "r", encoding="utf-8") as f:
            styles.append(f.read())
    return "\n".join(styles)

class OknoPodgladu(QDialog):
    def __init__(self, tekst: str, kierunek: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Podgląd tłumaczenia')
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        tytul_kierunek = "Polski → Braille" if kierunek == 'pl_br' else "Braille → Polski"
        label = QLabel(f"<b>Przetłumaczony tekst ({tytul_kierunek}):</b>")
        layout.addWidget(label)

        self.pole_tekstu = QTextEdit()
        self.pole_tekstu.setReadOnly(True)
        self.pole_tekstu.setPlainText(tekst)

        if kierunek == 'pl_br':
            czcionka = QFont("Arial", 36)
        else:
            czcionka = QFont("Arial", 14)

        self.pole_tekstu.setFont(czcionka)
        layout.addWidget(self.pole_tekstu)

        btn_layout = QHBoxLayout()

        btn_kopiuj = QPushButton("Kopiuj do schowka")
        btn_kopiuj.clicked.connect(self.kopiuj_do_schowka)
        btn_layout.addWidget(btn_kopiuj)

        btn_zamknij = QPushButton("Zamknij")
        btn_zamknij.clicked.connect(self.accept)
        btn_layout.addWidget(btn_zamknij)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def kopiuj_do_schowka(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.pole_tekstu.toPlainText())
        QMessageBox.information(self, "Skopiowano", "Tekst został skopiowany do schowka!")


class OknoPomocnicze(QMainWindow):
    def __init__(self, typ: str, parent=None):
        super().__init__(parent)

        if typ == "instrukcja":
            self.ui.setupUi(self)
            self.setWindowTitle("Instrukcja obsługi")
        elif typ == "o_programie":
            self.ui = Ui_OProgramie()
            self.ui.setupUi(self)
            self.setWindowTitle("O programie")


class OknoHistorii(QDialog):
    def __init__(self, baza: BazaDanych, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Historia tłumaczeń')
        self.setMinimumSize(700, 500)
        self.wybrany_wpis = None
        self.baza = baza

        layout = QVBoxLayout()

        label = QLabel("<b>Historia ostatnich tłumaczeń:</b>")
        layout.addWidget(label)

        self.lista_historii = QListWidget()

        try:
            historia = self.baza.pobierz_tlumaczenia()
            self.historia_danych = []

            for wpis in historia:
                try:
                    id_zrodla, sciezka, kierunek, typ_zrodla, zawartosc, wynik, data = wpis
                    kierunek_text = "Polski → Braille" if kierunek == 'pl_br' else "Braille → Polski"
                    typ_text = "Plik" if typ_zrodla == "plik" else "Tekst ręczny"
                    nazwa_pliku = os.path.basename(sciezka) if sciezka and typ_zrodla == "plik" else typ_text

                    tekst = f"{data} | {kierunek_text} | {nazwa_pliku}"
                    self.lista_historii.addItem(tekst)

                    self.historia_danych.append({
                        'sciezka': sciezka if sciezka else '',
                        'kierunek': kierunek if kierunek else 'pl_br',
                        'typ_zrodla': typ_zrodla if typ_zrodla else 'tekst',
                        'zawartosc': zawartosc if zawartosc else '',
                        'wynik': wynik if wynik else '',
                        'data': data if data else ''
                    })
                except Exception as e:
                    print(f"Błąd przetwarzania wpisu historii: {e}")
                    continue

        except Exception as e:
            print(f"Błąd pobierania historii: {e}")
            self.historia_danych = []

        self.lista_historii.itemDoubleClicked.connect(self.wybierz_wpis)
        layout.addWidget(self.lista_historii)

        btn_layout = QHBoxLayout()

        btn_otworz = QPushButton("Otwórz plik")
        btn_otworz.clicked.connect(self.otworz_plik)
        btn_layout.addWidget(btn_otworz)

        btn_wyczysc = QPushButton("Wyczyść historię")
        btn_wyczysc.clicked.connect(self.wyczysc_historie)
        btn_layout.addWidget(btn_wyczysc)

        btn_zamknij = QPushButton("Zamknij")
        btn_zamknij.clicked.connect(self.accept)
        btn_layout.addWidget(btn_zamknij)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def wybierz_wpis(self, item):
        indeks = self.lista_historii.row(item)
        if 0 <= indeks < len(self.historia_danych):
            self.wybrany_wpis = self.historia_danych[indeks]
            self.accept()

    def otworz_plik(self):
        indeks = self.lista_historii.currentRow()
        if 0 <= indeks < len(self.historia_danych):
            self.wybrany_wpis = self.historia_danych[indeks]
            self.accept()

    def wyczysc_historie(self):
        odpowiedz = QMessageBox.question(
            self,
            'Potwierdzenie',
            'Czy na pewno chcesz wyczyścić całą historię?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if odpowiedz == QMessageBox.StandardButton.Yes:
            self.baza.wyczysc_historie()
            self.historia_danych.clear()
            self.lista_historii.clear()
            QMessageBox.information(self, 'Wyczyszczono', 'Historia została wyczyszczona.')


class OknoGlowne(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow_glowne()
        self.ui.setupUi(self)

        self.aktualny_motyw = "jasny"
        self.wczytaj_motyw(self.aktualny_motyw)

        self.menadzer_czcionek = MenadzerCzcionek()

        self.ui.actionMotyw.triggered.connect(self.zmien_motyw)
        self.ui.actionCzcionka.triggered.connect(self.otworz_okno_czcionki)

        self.menadzer = MenadzerDokumentow()
        self.procesor = ProcesorDokumentow(self.menadzer)
        self.tlumacz = TlumaczBraille()
        self.baza = BazaDanych()
        self.import_export_pl_br = ImportExportPolskiBraille(self.menadzer)
        self.import_export_br_pl = ImportExportBraillePolski(self.menadzer)
        self.kierunek = None
        self.blokada_auto_tlumaczenia = False
        self.tekst_przed_tlumaczeniem_br = ""

        self.historia_edycji = []
        self.indeks_historii_edycji = -1
        self.aktualne_id_zrodla = None

        self.ui.pushButton_pl_br_okno.clicked.connect(lambda: self.ustaw_kierunek("pl_br"))
        self.ui.pushButton_br_pl_okno.clicked.connect(lambda: self.ustaw_kierunek("br_pl"))

        self.ui.pushButton_wybor_teskt.clicked.connect(lambda: self.zmien_tryb("tekst"))
        self.ui.pushButton_wybor_plik.clicked.connect(lambda: self.zmien_tryb("plik"))
        self.ui.pushButton_wybor_teskt_br.clicked.connect(lambda: self.zmien_tryb("tekst"))
        self.ui.pushButton_wybor_plik_br.clicked.connect(lambda: self.zmien_tryb("plik"))

        self.ui.pushButton_import_pl_br.clicked.connect(self.importuj_plik)
        self.ui.pushButton_import_br_pl.clicked.connect(self.importuj_plik)

        self.ui.pushButton_przetlumacz.clicked.connect(self.przetlumacz)
        self.ui.pushButton_podglad.clicked.connect(self.pokaz_podglad)
        self.ui.pushButton_zapisz.clicked.connect(self.zapisz_wynik)

        self.ui.textEdit_br_tekst.textChanged.connect(self.auto_tlumacz_na_braille)
        self.ui.textEdit_pl_tekst.textChanged.connect(self.zapisz_stan_edycji)

        self.ui.pushButton_wyczysc_tekst.clicked.connect(self.wyczysc_tekst)
        self.ui.pushButton_wyczysc_tekst_3.clicked.connect(self.wyczysc_pole_br)

        self.ui.actionNowe_T_umaczenie.triggered.connect(self.nowe_tlumaczenie)
        self.ui.actionOtw_rz_ostatni_plik.triggered.connect(self.otworz_ostatni)
        self.ui.actionCofjnij.triggered.connect(self.cofnij_edycje)
        self.ui.actionWyczy_tekst.triggered.connect(self.wyczysc_tekst)
        self.ui.actionPodgl_d_obecnego_pliku.triggered.connect(self.podglad_zrodlowego_pliku)

        self.ustaw_widok_startowy()

    def ustaw_widok_startowy(self):
        self.kierunek = None
        self.ui.stackedWidget_glowny.hide()
        self.ui.stackedWidget_wewnetrzny.hide()
        self.ui.stackedWidget_wewnetrzny_br.hide()

        self.ui.pushButton_pl_br_okno.show()
        self.ui.pushButton_br_pl_okno.show()
        self.ui.pushButton_przetlumacz.show()
        self.ui.pushButton_zapisz.show()
        self.ui.pushButton_podglad.show()

    def ustaw_kierunek(self, kierunek):
        self.kierunek = kierunek
        self.ui.stackedWidget_glowny.show()

        if kierunek == "pl_br":
            self.ui.stackedWidget_glowny.setCurrentIndex(0)
            self.ui.stackedWidget_wewnetrzny.show()
            self.ui.stackedWidget_wewnetrzny.setCurrentIndex(0)
        else:
            self.ui.stackedWidget_glowny.setCurrentIndex(1)
            self.ui.stackedWidget_wewnetrzny_br.show()
            self.ui.stackedWidget_wewnetrzny_br.setCurrentIndex(0)

    def zmien_tryb(self, typ):
        if self.kierunek == "pl_br":
            self.ui.stackedWidget_wewnetrzny.show()
            self.ui.stackedWidget_wewnetrzny.setCurrentIndex(0 if typ == "tekst" else 1)
        elif self.kierunek == "br_pl":
            self.ui.stackedWidget_wewnetrzny_br.show()
            self.ui.stackedWidget_wewnetrzny_br.setCurrentIndex(0 if typ == "tekst" else 1)

    def auto_tlumacz_na_braille(self):
        if self.blokada_auto_tlumaczenia:
            return

        self.blokada_auto_tlumaczenia = True
        try:
            pole = self.ui.textEdit_br_tekst
            tekst = pole.toPlainText()
            if tekst is None:
                tekst = ""

            T = self.tlumacz
            mapa = T.POLSKI_NA_BRAILLE_PODSTAWOWE

            import re
            ostatni = tekst[-1] if len(tekst) > 0 else ''

            znaki_konczace = set([' ', '\n', '\t', '.', ',', '!', '?', ';', ':'])

            nowy = tekst

            if len(tekst) > 0 and (ostatni.isascii() and (ostatni.isalnum())):
                ch = ostatni
                przed = tekst[:-1]

                if ch.isdigit():
                    bra = mapa.get(ch, ch)
                    if not re.search(r'⠼[⠁-⠚]*$', przed):
                        nowy = przed + '⠼' + bra
                    else:
                        nowy = przed + bra

                elif ch.isalpha():
                    if ch.isupper():
                        bra = mapa.get(ch.lower(), ch.lower())
                        nowy = przed + '⠨' + bra
                    else:
                        bra = mapa.get(ch, ch)
                        nowy = przed + bra

                else:
                    nowy = przed + ch

            else:
                if ostatni in znaki_konczace:
                    m = re.search(r'([⠨⠼⠁-⠾]+)(?=[\s\.,!?:;\n\t]|$)', tekst[:-1])
                    if m:
                        start, end = m.span(1)
                        token = m.group(1)
                        przed = tekst[:start]
                        po = tekst[end:-1]

                        token = re.sub(r'⠼+', '⠼', token)
                        if re.fullmatch(r'(?:⠨[⠁-⠵])+', token):
                            token_letters_only = re.sub(r'⠨', '', token)
                            token = '⠨⠨' + token_letters_only

                        nowy = przed + token + po + ostatni
                    else:
                        nowy = tekst
                else:
                    nowy = re.sub(r'⠼{2,}', '⠼', tekst)

            if nowy != tekst:
                pole.blockSignals(True)
                pole.setPlainText(nowy)
                k = pole.textCursor()
                k.setPosition(len(nowy))
                pole.setTextCursor(k)
                pole.blockSignals(False)

            self.tekst_przed_tlumaczeniem_br = nowy
            self.procesor.przetlumaczony_tekst = nowy

        finally:
            self.blokada_auto_tlumaczenia = False


    def wczytaj_motyw(self, motyw: str):
        try:
            sciezka_bazowy = resource_path(os.path.join("style", "bazowy.qss"))
            sciezka_motyw = resource_path(os.path.join("style", f"{motyw}.qss"))

            with open(sciezka_bazowy, "r", encoding="utf-8") as f:
                styl_bazowy = f.read()

            with open(sciezka_motyw, "r", encoding="utf-8") as f:
                styl_motyw = f.read()

            font_override = ""
            if hasattr(self, 'menadzer_czcionek'):
                czcionka = self.menadzer_czcionek.pobierz_czcionke()
                font_override = f"""
                        QWidget {{
                            font-family: "{czcionka.family()}";
                            font-size: {czcionka.pointSize()}pt;
                        }}
                        """

            pelny_styl = styl_bazowy + "\n\n" + styl_motyw
            self.setStyleSheet(pelny_styl)
            self.aktualny_motyw = motyw
            print(f"[INFO] Załadowano motyw: {motyw}")
        except Exception as e:
            print(f"[BŁĄD] Nie udało się załadować motywu '{motyw}': {e}")

    def zmien_motyw(self):
        nowy = "ciemny" if self.aktualny_motyw == "jasny" else "jasny"
        self.wczytaj_motyw(nowy)
        self.aktualny_motyw = nowy

    def ustaw_odstepy_kontrolek(self):
        try:
            from PyQt6.QtWidgets import QLayout

            for layout in self.findChildren(QLayout):
                if layout:
                    layout.setSpacing(5)
                    layout.setContentsMargins(5, 5, 5, 5)

            print("[INFO] Ustawiono odstępy (spacing=5, margins=5)")

        except Exception as e:
            print(f"[BŁĄD] Nie udało się ustawić odstępów: {e}")


    def otworz_okno_czcionki(self):
        print("[DEBUG] Otwieranie okna czcionki...")
        okno = OknoCzcionka(self.menadzer_czcionek, self)
        if okno.exec() == QDialog.DialogCode.Accepted:
            print("[DEBUG] Zmiany zaakceptowane, aplikowanie czcionki...")

            app = QApplication.instance()
            nowa_czcionka = self.menadzer_czcionek.pobierz_czcionke()
            app.setFont(nowa_czcionka)
            print(f"[INFO] Ustawiono czcionkę: {nowa_czcionka.family()} {nowa_czcionka.pointSize()}pt")

            self.menadzer_czcionek.zastosuj_do_widgetu(self)
            self.wczytaj_motyw(self.aktualny_motyw)

            self.menadzer_czcionek.zastosuj_do_widgetu(self)
            self.ustaw_odstepy_kontrolek()

            self.update()
            self.repaint()

            for widget in self.findChildren(QWidget):
                widget.update()
                widget.repaint()

            QMessageBox.information(
                self,
                "Czcionka zmieniona",
                f"Ustawiono czcionkę: {nowa_czcionka.family()} {nowa_czcionka.pointSize()}pt\n\n"
                f"Zalecany zakres: 11-14pt"
            )

    def wyczysc_pole_br(self):
        self.blokada_auto_tlumaczenia = True
        self.ui.textEdit_br_tekst.clear()
        self.tekst_przed_tlumaczeniem_br = ""
        self.blokada_auto_tlumaczenia = False

    def dodaj_do_historii(self, sciezka: str, kierunek: str, zawartosc_zrodlowa: str, wynik: str, typ_zrodla: str):
        try:
            self.baza.dodaj_tlumaczenie(sciezka, kierunek, zawartosc_zrodlowa, wynik, typ_zrodla)
            print(f"[HISTORIA] Dodano do bazy: {typ_zrodla}, {len(zawartosc_zrodlowa)} → {len(wynik)} znaków")
        except Exception as e:
            print(f"[BŁĄD] Nie udało się dodać do historii: {e}")
            import traceback
            traceback.print_exc()

    def otworz_ostatni(self):
        try:
            okno_historii = OknoHistorii(self.baza, self)
            if okno_historii.exec() == QDialog.DialogCode.Accepted:
                wpis = okno_historii.wybrany_wpis
                if not wpis:
                    return

                sciezka = wpis.get('sciezka', '')
                kierunek = wpis.get('kierunek', 'pl_br')
                typ_zrodla = wpis.get('typ_zrodla', 'tekst')
                zawartosc = wpis.get('zawartosc', '')

                print(f"[HISTORIA] Wczytywanie: {typ_zrodla}, kierunek: {kierunek}, znaków: {len(zawartosc)}")

                self.ustaw_kierunek(kierunek)

                if kierunek == 'pl_br':
                    self.ui.stackedWidget_wewnetrzny.setCurrentIndex(0)
                    self.ui.textEdit_pl_tekst.clear()
                    self.ui.textEdit_pl_tekst.setPlainText(zawartosc)

                    if typ_zrodla == 'plik' and sciezka and sciezka != "Tekst ręczny":
                        if os.path.exists(sciezka):
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n(zawartość z bazy danych)'
                        else:
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n Plik nie istnieje, ale zawartość zachowana w bazie'
                    else:
                        info = 'Wczytano tekst z historii'

                else:
                    self.ui.stackedWidget_wewnetrzny_br.setCurrentIndex(0)
                    self.blokada_auto_tlumaczenia = True
                    self.ui.textEdit_br_tekst.clear()
                    self.ui.textEdit_br_tekst.setPlainText(zawartosc)
                    self.tekst_przed_tlumaczeniem_br = zawartosc
                    self.blokada_auto_tlumaczenia = False

                    if typ_zrodla == 'plik' and sciezka and sciezka != "Tekst ręczny":
                        if os.path.exists(sciezka):
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n(zawartość z bazy danych)'
                        else:
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n Plik nie istnieje, ale zawartość zachowana w bazie'
                    else:
                        info = 'Wczytano tekst Braille z historii'

                QMessageBox.information(
                    self,
                    'Wczytano z historii',
                    info
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Błąd krytyczny',
                f'Wystąpił błąd podczas wczytywania z historii:\n{str(e)}'
            )
            import traceback
            traceback.print_exc()

    def nowe_tlumaczenie(self):
        odpowiedz = QMessageBox.question(
            self,
            'Nowe tłumaczenie',
            'Czy na pewno chcesz rozpocząć nowe tłumaczenie?\n'
            'Niezapisane zmiany zostaną utracone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if odpowiedz == QMessageBox.StandardButton.Yes:
            self.ui.textEdit_pl_tekst.clear()
            self.ui.textEdit_br_tekst.clear()
            self.menadzer.aktualny_dokument = None
            self.procesor.przetlumaczony_tekst = ""
            self.historia_edycji.clear()
            self.indeks_historii_edycji = -1
            self.tekst_przed_tlumaczeniem_br = ""
            self.aktualne_id_zrodla = None
            QMessageBox.information(self, 'Gotowe', 'Rozpoczęto nowe tłumaczenie.')

    def zapisz_stan_edycji(self):
        tekst = self.ui.textEdit_pl_tekst.toPlainText()

        if not self.historia_edycji or self.historia_edycji[-1] != tekst:
            if self.indeks_historii_edycji < len(self.historia_edycji) - 1:
                self.historia_edycji = self.historia_edycji[:self.indeks_historii_edycji + 1]

            self.historia_edycji.append(tekst)
            self.indeks_historii_edycji = len(self.historia_edycji) - 1

            if len(self.historia_edycji) > 50:
                self.historia_edycji.pop(0)
                self.indeks_historii_edycji -= 1

    def cofnij_edycje(self):
        if self.indeks_historii_edycji > 0:
            self.indeks_historii_edycji -= 1
            tekst_cofniety = self.historia_edycji[self.indeks_historii_edycji]

            self.ui.textEdit_pl_tekst.textChanged.disconnect(self.zapisz_stan_edycji)
            self.ui.textEdit_pl_tekst.setPlainText(tekst_cofniety)
            self.ui.textEdit_pl_tekst.textChanged.connect(self.zapisz_stan_edycji)

            self.statusBar().showMessage('Cofnięto zmianę', 2000)
        else:
            self.statusBar().showMessage('Brak zmian do cofnięcia', 2000)

    def wyczysc_tekst(self):
        odpowiedz = QMessageBox.question(
            self,
            'Potwierdzenie',
            'Czy na pewno chcesz wyczyścić tekst?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if odpowiedz == QMessageBox.StandardButton.Yes:
            if self.kierunek == 'pl_br':
                self.ui.textEdit_pl_tekst.clear()
            else:
                self.wyczysc_pole_br()

    def ustaw_pl_br(self):
        self.kierunek = 'pl_br'
        self.ui.stackedWidget_glowny.setCurrentIndex(0)

    def ustaw_br_pl(self):
        self.kierunek = 'br_pl'
        self.ui.stackedWidget_glowny.setCurrentIndex(1)

    def importuj_plik(self):
        try:
            if self.kierunek == 'pl_br':
                filtry = (
                    'Pliki tekstowe (*.txt);;'
                    'Dokument PDF (*.pdf);;'
                    'Dokument Word (*.docx);;'
                    'OpenDocument (*.odt);;'
                    'Rich Text Format (*.rtf);;'
                    'Wszystkie pliki (*.*)'
                )
            else:
                filtry = (
                    'Plik Braille (*.brf);;'
                    'Plik Braille BES (*.bes);;'
                    'Plik Braille BSE (*.bse);;'
                    'Plik tekstowy (*.txt);;'
                    'Dokument PDF (*.pdf);;'
                    'Dokument Word (*.docx);;'
                    'OpenDocument (*.odt);;'
                    'Rich Text Format (*.rtf);;'
                    'Obraz (*.jpg *.jpeg *.png);;'
                    'Wszystkie pliki (*.*)'
                )

            sciezka_pliku, _ = QFileDialog.getOpenFileName(
                self,
                'Wybierz plik do importu',
                os.getcwd(),
                filtry
            )

            if not sciezka_pliku:
                return

            rozszerzenie = os.path.splitext(sciezka_pliku)[1].lower()

            if self.kierunek == 'br_pl' and rozszerzenie in ['.png', '.jpg', '.jpeg']:
                sukces, zawartosc, blad = self._importuj_obraz_braille(sciezka_pliku)
                if sukces:
                    stats = {
                        'znaki': len(zawartosc),
                        'slowa': len(zawartosc.split()),
                        'linie': zawartosc.count('\n') + 1
                    }
                    komunikat = (
                        f'Plik zaimportowany (OCR Braille)!\n\n'
                        f'Rozpoznanych znaków: {stats["znaki"]}\n'
                        f'Słów: {stats["slowa"]}\n'
                        f'Linii: {stats["linie"]}'
                    )
                    QMessageBox.information(self, 'Import zakończony', komunikat)
                else:
                    QMessageBox.critical(self, 'Błąd OCR', blad or "Nie udało się rozpoznać Braille'a")
                return

            if self.kierunek == 'pl_br':
                sukces, blad = self.import_export_pl_br.importuj_plik(sciezka_pliku)
            else:
                sukces, blad = self.import_export_br_pl.importuj_plik(sciezka_pliku)

            if not sukces:
                QMessageBox.critical(self, 'Błąd importu', blad or "Nie udało się wczytać pliku")
                return

            zawartosc = self.menadzer.pobierz_zawartosc() or ""
            stats = self.menadzer.pobierz_statystyki()

            if self.kierunek == 'pl_br':
                self.ui.textEdit_pl_tekst.clear()
                self.ui.textEdit_pl_tekst.setPlainText(zawartosc)
            else:
                self.ui.textEdit_br_tekst.clear()
                self.ui.textEdit_br_tekst.setPlainText(zawartosc)
                self.tekst_przed_tlumaczeniem_br = zawartosc

            komunikat = (
                f'Plik zaimportowany!\n\n'
                f'Znaków: {stats["znaki"]}\n'
                f'Słów: {stats["slowa"]}\n'
                f'Linii: {stats["linie"]}'
            )
            QMessageBox.information(self, 'Import zakończony', komunikat)

        except Exception as e:
            QMessageBox.critical(self, 'Krytyczny błąd', f'Wystąpił błąd: {str(e)}')
            import traceback
            traceback.print_exc()

    def _importuj_obraz_braille(self, sciezka: str) -> tuple[bool, str, str]:
        try:
            from detekcja_i_translacja import rozpoznaj_obraz, pdf_na_obrazy, pdf_ma_unicode_braille
            import cv2

            rozszerzenie = os.path.splitext(sciezka)[1].lower()

            if rozszerzenie == '.pdf':
                if pdf_ma_unicode_braille(sciezka):
                    import fitz
                    doc = fitz.open(sciezka)
                    tekst_braille = ""
                    for strona in doc:
                        tekst_braille += strona.get_text() + "\n"
                    doc.close()

                    if tekst_braille.strip():
                        self.menadzer.utworz_nowy_dokument(tekst_braille)
                        return True, tekst_braille, None
                    else:
                        return False, "", "PDF nie zawiera tekstu Braille"
                else:
                    obrazy = pdf_na_obrazy(sciezka, dpi=300)
                    ascii_all = []

                    for i, img in enumerate(obrazy):
                        ascii_txt = rozpoznaj_obraz(img)
                        if ascii_txt.strip():
                            ascii_all.append(ascii_txt)

                    tekst_wynikowy = "\n\n".join(ascii_all)

                    if tekst_wynikowy.strip():
                        self.menadzer.utworz_nowy_dokument(tekst_wynikowy)
                        return True, tekst_wynikowy, None
                    else:
                        return False, "", "Nie rozpoznano tekstu Braille w PDF"

            else:
                img = cv2.imread(sciezka)
                if img is None:
                    return False, "", f"Nie można wczytać obrazu: {sciezka}"

                ascii_txt = rozpoznaj_obraz(img)

                if ascii_txt.strip():
                    self.menadzer.utworz_nowy_dokument(ascii_txt)
                    return True, ascii_txt, None
                else:
                    return False, "", "Nie rozpoznano tekstu Braille na obrazie"

        except ImportError as e:
            return False, "", f"Brak wymaganych bibliotek OCR: {e}\n\nZainstaluj: pip install opencv-python scikit-learn PyMuPDF"
        except Exception as e:
            return False, "", f"Błąd rozpoznawania Braille: {str(e)}"

    def przetlumacz(self):
        try:
            sciezka_zrodla = None
            typ_zrodla = "tekst"

            if self.kierunek == 'pl_br':
                if self.ui.stackedWidget_wewnetrzny.currentIndex() == 0:
                    tekst = self.ui.textEdit_pl_tekst.toPlainText()
                    if not tekst.strip():
                        QMessageBox.warning(self, 'Uwaga', 'Pole tekstowe jest puste!')
                        return
                    sukces, przetlumaczony, komunikat = self.procesor.przetlumacz_tekst(tekst, self.kierunek)
                    typ_zrodla = "tekst"
                else:
                    if not self.menadzer.czy_ma_dokument():
                        QMessageBox.warning(self, 'Uwaga', 'Nie zaimportowano żadnego pliku!')
                        return
                    sukces, przetlumaczony, komunikat = self.procesor.przetlumacz_dokument(self.kierunek)
                    meta = self.menadzer.pobierz_metadane()
                    if meta:
                        sciezka_zrodla = meta.get('sciezka', '')
                    typ_zrodla = "plik"

            else:
                if self.ui.stackedWidget_wewnetrzny_br.currentIndex() == 0:
                    tekst = self.tekst_przed_tlumaczeniem_br

                    if not tekst.strip():
                        QMessageBox.warning(self, 'Uwaga', 'Pole tekstowe jest puste!')
                        return

                    sukces_br, tekst_braille, _ = self.tlumacz.polski_na_braille(tekst)
                    if not sukces_br:
                        QMessageBox.critical(self, 'Błąd', 'Nie udało się przetłumaczyć na Braille')
                        return

                    sukces, przetlumaczony, komunikat = self.tlumacz.braille_na_polski(tekst_braille)
                    if sukces:
                        self.procesor.przetlumaczony_tekst = przetlumaczony
                        self.procesor.kierunek_tlumaczenia = self.kierunek
                    typ_zrodla = "tekst"
                else:
                    if not self.menadzer.czy_ma_dokument():
                        QMessageBox.warning(self, 'Uwaga', 'Nie zaimportowano żadnego pliku!')
                        return
                    sukces, przetlumaczony, komunikat = self.procesor.przetlumacz_dokument(self.kierunek)
                    meta = self.menadzer.pobierz_metadane()
                    if meta:
                        sciezka_zrodla = meta.get('sciezka', '')
                    typ_zrodla = "plik"

            if sukces:
                info = 'Tłumaczenie zakończone!\n\nKliknij "Podgląd" aby zobaczyć wynik.'
                if komunikat:
                    info += f'\n\n{komunikat}'

                if self.kierunek == 'pl_br':
                    tekst_zrodlowy = (self.ui.textEdit_pl_tekst.toPlainText()
                                      if self.ui.stackedWidget_wewnetrzny.currentIndex() == 0
                                      else self.menadzer.pobierz_zawartosc())
                else:
                    tekst_zrodlowy = (self.tekst_przed_tlumaczeniem_br
                                      if self.ui.stackedWidget_wewnetrzny_br.currentIndex() == 0
                                      else self.menadzer.pobierz_zawartosc())

                if tekst_zrodlowy:
                    info += f'\n\nZnaków wejściowych: {len(tekst_zrodlowy)}'
                    info += f'\nZnaków wyjściowych: {len(przetlumaczony)}'

                    self.dodaj_do_historii(
                        sciezka_zrodla or "Tekst ręczny",
                        self.kierunek,
                        tekst_zrodlowy,
                        przetlumaczony,
                        typ_zrodla
                    )

                QMessageBox.information(self, 'Sukces', info)
            else:
                QMessageBox.critical(self, 'Błąd tłumaczenia', komunikat)

        except Exception as e:
            QMessageBox.critical(self, 'Błąd', f'Wystąpił błąd: {str(e)}')
            import traceback
            traceback.print_exc()

    def pokaz_podglad(self):
        przetlumaczony = self.procesor.pobierz_przetlumaczony()

        if not przetlumaczony:
            QMessageBox.warning(
                self,
                'Brak tłumaczenia',
                'Najpierw przetłumacz tekst za pomocą przycisku "Przetłumacz"'
            )
            return

        okno_podgladu = OknoPodgladu(przetlumaczony, self.kierunek, self)
        okno_podgladu.exec()

    def podglad_zrodlowego_pliku(self):
        if not self.menadzer.czy_ma_dokument():
            QMessageBox.warning(
                self,
                'Brak pliku',
                'Nie załadowano żadnego pliku do podglądu.'
            )
            return

        zawartosc = self.menadzer.pobierz_zawartosc()
        if not zawartosc:
            QMessageBox.warning(
                self,
                'Pusty plik',
                'Załadowany plik jest pusty.'
            )
            return

        meta = self.menadzer.pobierz_metadane()
        nazwa_pliku = meta.get('nazwa_pliku', 'Plik') if meta else 'Plik'

        okno = QDialog(self)
        okno.setWindowTitle(f'Podgląd: {nazwa_pliku}')
        okno.setMinimumSize(700, 500)

        layout = QVBoxLayout()

        pole_tekstu = QTextEdit()
        pole_tekstu.setReadOnly(True)
        pole_tekstu.setPlainText(zawartosc)
        pole_tekstu.setFont(QFont("Arial", 12))
        layout.addWidget(pole_tekstu)

        btn_zamknij = QPushButton("Zamknij")
        btn_zamknij.clicked.connect(okno.accept)
        layout.addWidget(btn_zamknij)

        okno.setLayout(layout)
        okno.exec()

    def zapisz_wynik(self):
        przetlumaczony = self.procesor.pobierz_przetlumaczony()

        if not przetlumaczony:
            QMessageBox.warning(
                self,
                'Brak tłumaczenia',
                'Najpierw przetłumacz tekst za pomocą przycisku "Przetłumacz".'
            )
            return

        if self.kierunek == 'pl_br':
            filtry = (
                'Plik Braille (*.brf);;'
                'Plik Braille BES (*.bes);;'
                'Plik Braille BSE (*.bse);;'
                'Plik tekstowy (*.txt);;'
                'Dokument PDF (*.pdf);;'
                'Wszystkie pliki (*.*)'
            )
        else:
            filtry = (
                'Plik tekstowy (*.txt);;'
                'Dokument PDF (*.pdf);;'
                'Dokument Word (*.docx);;'
                'OpenDocument (*.odt);;'
                'Rich Text Format (*.rtf);;'
                'Wszystkie pliki (*.*)'
            )

        sciezka_zapisu, _ = QFileDialog.getSaveFileName(
            self,
            'Zapisz przetłumaczony tekst',
            '',
            filtry
        )

        if not sciezka_zapisu:
            return

        try:
            if self.menadzer.czy_ma_dokument():
                self.menadzer.ustaw_zawartosc(przetlumaczony)
            else:
                self.menadzer.utworz_nowy_dokument(przetlumaczony)

            if self.kierunek == 'pl_br':
                sukces, blad = self.import_export_pl_br.eksportuj_plik(sciezka_zapisu)
            else:
                sukces, blad = self.import_export_br_pl.eksportuj_plik(sciezka_zapisu)

            if sukces:
                QMessageBox.information(
                    self,
                    'Zapisano',
                    f'Plik zapisany:\n{sciezka_zapisu}'
                )
            else:
                QMessageBox.critical(
                    self,
                    'Błąd zapisu',
                    blad or "Nie udało się zapisać pliku"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Błąd zapisu',
                f'Wystąpił błąd: {str(e)}'
            )
            import traceback
            traceback.print_exc()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    domyslna_czcionka = QFont("Arial", 11)
    app.setFont(domyslna_czcionka)
    okno = OknoGlowne()
    okno.show()
    sys.exit(app.exec())
=======
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog,
    QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout, QTextEdit, QWidget
)
from PyQt6.QtGui import QFont

from Inz_Okno_Glowne import Ui_MainWindow_glowne
from o_programie import Ui_MainWindow as Ui_OProgramie
from dok import MenadzerDokumentow, ImportExportPolskiBraille, ImportExportBraillePolski
from tlumacz_laczenie import ProcesorDokumentow, TlumaczBraille
from baza import BazaDanych
from ustawienia_czcionki import OknoCzcionka, MenadzerCzcionek

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

font_path = resource_path("fonts/DejaVuSans.ttf")

def load_styles():
    styles = []
    for file_name in ["style/base.qss", "style/jasny.qss", "style/ciemny.qss"]:
        path = resource_path(file_name)
        with open(path, "r", encoding="utf-8") as f:
            styles.append(f.read())
    return "\n".join(styles)

class OknoPodgladu(QDialog):
    def __init__(self, tekst: str, kierunek: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Podgląd tłumaczenia')
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        tytul_kierunek = "Polski → Braille" if kierunek == 'pl_br' else "Braille → Polski"
        label = QLabel(f"<b>Przetłumaczony tekst ({tytul_kierunek}):</b>")
        layout.addWidget(label)

        self.pole_tekstu = QTextEdit()
        self.pole_tekstu.setReadOnly(True)
        self.pole_tekstu.setPlainText(tekst)

        if kierunek == 'pl_br':
            czcionka = QFont("Arial", 36)
        else:
            czcionka = QFont("Arial", 14)

        self.pole_tekstu.setFont(czcionka)
        layout.addWidget(self.pole_tekstu)

        btn_layout = QHBoxLayout()

        btn_kopiuj = QPushButton("Kopiuj do schowka")
        btn_kopiuj.clicked.connect(self.kopiuj_do_schowka)
        btn_layout.addWidget(btn_kopiuj)

        btn_zamknij = QPushButton("Zamknij")
        btn_zamknij.clicked.connect(self.accept)
        btn_layout.addWidget(btn_zamknij)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def kopiuj_do_schowka(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.pole_tekstu.toPlainText())
        QMessageBox.information(self, "Skopiowano", "Tekst został skopiowany do schowka!")


class OknoPomocnicze(QMainWindow):
    def __init__(self, typ: str, parent=None):
        super().__init__(parent)

        if typ == "instrukcja":
            self.ui.setupUi(self)
            self.setWindowTitle("Instrukcja obsługi")
        elif typ == "o_programie":
            self.ui = Ui_OProgramie()
            self.ui.setupUi(self)
            self.setWindowTitle("O programie")


class OknoHistorii(QDialog):
    def __init__(self, baza: BazaDanych, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Historia tłumaczeń')
        self.setMinimumSize(700, 500)
        self.wybrany_wpis = None
        self.baza = baza

        layout = QVBoxLayout()

        label = QLabel("<b>Historia ostatnich tłumaczeń:</b>")
        layout.addWidget(label)

        self.lista_historii = QListWidget()

        try:
            historia = self.baza.pobierz_tlumaczenia()
            self.historia_danych = []

            for wpis in historia:
                try:
                    id_zrodla, sciezka, kierunek, typ_zrodla, zawartosc, wynik, data = wpis
                    kierunek_text = "Polski → Braille" if kierunek == 'pl_br' else "Braille → Polski"
                    typ_text = "Plik" if typ_zrodla == "plik" else "Tekst ręczny"
                    nazwa_pliku = os.path.basename(sciezka) if sciezka and typ_zrodla == "plik" else typ_text

                    tekst = f"{data} | {kierunek_text} | {nazwa_pliku}"
                    self.lista_historii.addItem(tekst)

                    self.historia_danych.append({
                        'sciezka': sciezka if sciezka else '',
                        'kierunek': kierunek if kierunek else 'pl_br',
                        'typ_zrodla': typ_zrodla if typ_zrodla else 'tekst',
                        'zawartosc': zawartosc if zawartosc else '',
                        'wynik': wynik if wynik else '',
                        'data': data if data else ''
                    })
                except Exception as e:
                    print(f"Błąd przetwarzania wpisu historii: {e}")
                    continue

        except Exception as e:
            print(f"Błąd pobierania historii: {e}")
            self.historia_danych = []

        self.lista_historii.itemDoubleClicked.connect(self.wybierz_wpis)
        layout.addWidget(self.lista_historii)

        btn_layout = QHBoxLayout()

        btn_otworz = QPushButton("Otwórz plik")
        btn_otworz.clicked.connect(self.otworz_plik)
        btn_layout.addWidget(btn_otworz)

        btn_wyczysc = QPushButton("Wyczyść historię")
        btn_wyczysc.clicked.connect(self.wyczysc_historie)
        btn_layout.addWidget(btn_wyczysc)

        btn_zamknij = QPushButton("Zamknij")
        btn_zamknij.clicked.connect(self.accept)
        btn_layout.addWidget(btn_zamknij)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def wybierz_wpis(self, item):
        indeks = self.lista_historii.row(item)
        if 0 <= indeks < len(self.historia_danych):
            self.wybrany_wpis = self.historia_danych[indeks]
            self.accept()

    def otworz_plik(self):
        indeks = self.lista_historii.currentRow()
        if 0 <= indeks < len(self.historia_danych):
            self.wybrany_wpis = self.historia_danych[indeks]
            self.accept()

    def wyczysc_historie(self):
        odpowiedz = QMessageBox.question(
            self,
            'Potwierdzenie',
            'Czy na pewno chcesz wyczyścić całą historię?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if odpowiedz == QMessageBox.StandardButton.Yes:
            self.baza.wyczysc_historie()
            self.historia_danych.clear()
            self.lista_historii.clear()
            QMessageBox.information(self, 'Wyczyszczono', 'Historia została wyczyszczona.')


class OknoGlowne(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow_glowne()
        self.ui.setupUi(self)

        self.aktualny_motyw = "jasny"
        self.wczytaj_motyw(self.aktualny_motyw)

        self.menadzer_czcionek = MenadzerCzcionek()

        self.ui.actionMotyw.triggered.connect(self.zmien_motyw)
        self.ui.actionCzcionka.triggered.connect(self.otworz_okno_czcionki)

        self.menadzer = MenadzerDokumentow()
        self.procesor = ProcesorDokumentow(self.menadzer)
        self.tlumacz = TlumaczBraille()
        self.baza = BazaDanych()
        self.import_export_pl_br = ImportExportPolskiBraille(self.menadzer)
        self.import_export_br_pl = ImportExportBraillePolski(self.menadzer)
        self.kierunek = None
        self.blokada_auto_tlumaczenia = False
        self.tekst_przed_tlumaczeniem_br = ""

        self.historia_edycji = []
        self.indeks_historii_edycji = -1
        self.aktualne_id_zrodla = None

        self.ui.pushButton_pl_br_okno.clicked.connect(lambda: self.ustaw_kierunek("pl_br"))
        self.ui.pushButton_br_pl_okno.clicked.connect(lambda: self.ustaw_kierunek("br_pl"))

        self.ui.pushButton_wybor_teskt.clicked.connect(lambda: self.zmien_tryb("tekst"))
        self.ui.pushButton_wybor_plik.clicked.connect(lambda: self.zmien_tryb("plik"))
        self.ui.pushButton_wybor_teskt_br.clicked.connect(lambda: self.zmien_tryb("tekst"))
        self.ui.pushButton_wybor_plik_br.clicked.connect(lambda: self.zmien_tryb("plik"))

        self.ui.pushButton_import_pl_br.clicked.connect(self.importuj_plik)
        self.ui.pushButton_import_br_pl.clicked.connect(self.importuj_plik)

        self.ui.pushButton_przetlumacz.clicked.connect(self.przetlumacz)
        self.ui.pushButton_podglad.clicked.connect(self.pokaz_podglad)
        self.ui.pushButton_zapisz.clicked.connect(self.zapisz_wynik)

        self.ui.textEdit_br_tekst.textChanged.connect(self.auto_tlumacz_na_braille)
        self.ui.textEdit_pl_tekst.textChanged.connect(self.zapisz_stan_edycji)

        self.ui.pushButton_wyczysc_tekst.clicked.connect(self.wyczysc_tekst)
        self.ui.pushButton_wyczysc_tekst_3.clicked.connect(self.wyczysc_pole_br)

        self.ui.actionNowe_T_umaczenie.triggered.connect(self.nowe_tlumaczenie)
        self.ui.actionOtw_rz_ostatni_plik.triggered.connect(self.otworz_ostatni)
        self.ui.actionCofjnij.triggered.connect(self.cofnij_edycje)
        self.ui.actionWyczy_tekst.triggered.connect(self.wyczysc_tekst)
        self.ui.actionPodgl_d_obecnego_pliku.triggered.connect(self.podglad_zrodlowego_pliku)

        self.ustaw_widok_startowy()

    def ustaw_widok_startowy(self):
        self.kierunek = None
        self.ui.stackedWidget_glowny.hide()
        self.ui.stackedWidget_wewnetrzny.hide()
        self.ui.stackedWidget_wewnetrzny_br.hide()

        self.ui.pushButton_pl_br_okno.show()
        self.ui.pushButton_br_pl_okno.show()
        self.ui.pushButton_przetlumacz.show()
        self.ui.pushButton_zapisz.show()
        self.ui.pushButton_podglad.show()

    def ustaw_kierunek(self, kierunek):
        self.kierunek = kierunek
        self.ui.stackedWidget_glowny.show()

        if kierunek == "pl_br":
            self.ui.stackedWidget_glowny.setCurrentIndex(0)
            self.ui.stackedWidget_wewnetrzny.show()
            self.ui.stackedWidget_wewnetrzny.setCurrentIndex(0)
        else:
            self.ui.stackedWidget_glowny.setCurrentIndex(1)
            self.ui.stackedWidget_wewnetrzny_br.show()
            self.ui.stackedWidget_wewnetrzny_br.setCurrentIndex(0)

    def zmien_tryb(self, typ):
        if self.kierunek == "pl_br":
            self.ui.stackedWidget_wewnetrzny.show()
            self.ui.stackedWidget_wewnetrzny.setCurrentIndex(0 if typ == "tekst" else 1)
        elif self.kierunek == "br_pl":
            self.ui.stackedWidget_wewnetrzny_br.show()
            self.ui.stackedWidget_wewnetrzny_br.setCurrentIndex(0 if typ == "tekst" else 1)

    def auto_tlumacz_na_braille(self):
        if self.blokada_auto_tlumaczenia:
            return

        self.blokada_auto_tlumaczenia = True
        try:
            pole = self.ui.textEdit_br_tekst
            tekst = pole.toPlainText()
            if tekst is None:
                tekst = ""

            T = self.tlumacz
            mapa = T.POLSKI_NA_BRAILLE_PODSTAWOWE

            import re
            ostatni = tekst[-1] if len(tekst) > 0 else ''

            znaki_konczace = set([' ', '\n', '\t', '.', ',', '!', '?', ';', ':'])

            nowy = tekst

            if len(tekst) > 0 and (ostatni.isascii() and (ostatni.isalnum())):
                ch = ostatni
                przed = tekst[:-1]

                if ch.isdigit():
                    bra = mapa.get(ch, ch)
                    if not re.search(r'⠼[⠁-⠚]*$', przed):
                        nowy = przed + '⠼' + bra
                    else:
                        nowy = przed + bra

                elif ch.isalpha():
                    if ch.isupper():
                        bra = mapa.get(ch.lower(), ch.lower())
                        nowy = przed + '⠨' + bra
                    else:
                        bra = mapa.get(ch, ch)
                        nowy = przed + bra

                else:
                    nowy = przed + ch

            else:
                if ostatni in znaki_konczace:
                    m = re.search(r'([⠨⠼⠁-⠾]+)(?=[\s\.,!?:;\n\t]|$)', tekst[:-1])
                    if m:
                        start, end = m.span(1)
                        token = m.group(1)
                        przed = tekst[:start]
                        po = tekst[end:-1]

                        token = re.sub(r'⠼+', '⠼', token)
                        if re.fullmatch(r'(?:⠨[⠁-⠵])+', token):
                            token_letters_only = re.sub(r'⠨', '', token)
                            token = '⠨⠨' + token_letters_only

                        nowy = przed + token + po + ostatni
                    else:
                        nowy = tekst
                else:
                    nowy = re.sub(r'⠼{2,}', '⠼', tekst)

            if nowy != tekst:
                pole.blockSignals(True)
                pole.setPlainText(nowy)
                k = pole.textCursor()
                k.setPosition(len(nowy))
                pole.setTextCursor(k)
                pole.blockSignals(False)

            self.tekst_przed_tlumaczeniem_br = nowy
            self.procesor.przetlumaczony_tekst = nowy

        finally:
            self.blokada_auto_tlumaczenia = False


    def wczytaj_motyw(self, motyw: str):
        try:
            sciezka_bazowy = resource_path(os.path.join("style", "bazowy.qss"))
            sciezka_motyw = resource_path(os.path.join("style", f"{motyw}.qss"))

            with open(sciezka_bazowy, "r", encoding="utf-8") as f:
                styl_bazowy = f.read()

            with open(sciezka_motyw, "r", encoding="utf-8") as f:
                styl_motyw = f.read()

            font_override = ""
            if hasattr(self, 'menadzer_czcionek'):
                czcionka = self.menadzer_czcionek.pobierz_czcionke()
                font_override = f"""
                        QWidget {{
                            font-family: "{czcionka.family()}";
                            font-size: {czcionka.pointSize()}pt;
                        }}
                        """

            pelny_styl = styl_bazowy + "\n\n" + styl_motyw
            self.setStyleSheet(pelny_styl)
            self.aktualny_motyw = motyw
            print(f"[INFO] Załadowano motyw: {motyw}")
        except Exception as e:
            print(f"[BŁĄD] Nie udało się załadować motywu '{motyw}': {e}")

    def zmien_motyw(self):
        nowy = "ciemny" if self.aktualny_motyw == "jasny" else "jasny"
        self.wczytaj_motyw(nowy)
        self.aktualny_motyw = nowy

    def ustaw_odstepy_kontrolek(self):
        try:
            from PyQt6.QtWidgets import QLayout

            for layout in self.findChildren(QLayout):
                if layout:
                    layout.setSpacing(5)
                    layout.setContentsMargins(5, 5, 5, 5)

            print("[INFO] Ustawiono odstępy (spacing=5, margins=5)")

        except Exception as e:
            print(f"[BŁĄD] Nie udało się ustawić odstępów: {e}")


    def otworz_okno_czcionki(self):
        print("[DEBUG] Otwieranie okna czcionki...")
        okno = OknoCzcionka(self.menadzer_czcionek, self)
        if okno.exec() == QDialog.DialogCode.Accepted:
            print("[DEBUG] Zmiany zaakceptowane, aplikowanie czcionki...")

            app = QApplication.instance()
            nowa_czcionka = self.menadzer_czcionek.pobierz_czcionke()
            app.setFont(nowa_czcionka)
            print(f"[INFO] Ustawiono czcionkę: {nowa_czcionka.family()} {nowa_czcionka.pointSize()}pt")

            self.menadzer_czcionek.zastosuj_do_widgetu(self)
            self.wczytaj_motyw(self.aktualny_motyw)

            self.menadzer_czcionek.zastosuj_do_widgetu(self)
            self.ustaw_odstepy_kontrolek()

            self.update()
            self.repaint()

            for widget in self.findChildren(QWidget):
                widget.update()
                widget.repaint()

            QMessageBox.information(
                self,
                "Czcionka zmieniona",
                f"Ustawiono czcionkę: {nowa_czcionka.family()} {nowa_czcionka.pointSize()}pt\n\n"
                f"Zalecany zakres: 11-14pt"
            )

    def wyczysc_pole_br(self):
        self.blokada_auto_tlumaczenia = True
        self.ui.textEdit_br_tekst.clear()
        self.tekst_przed_tlumaczeniem_br = ""
        self.blokada_auto_tlumaczenia = False

    def dodaj_do_historii(self, sciezka: str, kierunek: str, zawartosc_zrodlowa: str, wynik: str, typ_zrodla: str):
        try:
            self.baza.dodaj_tlumaczenie(sciezka, kierunek, zawartosc_zrodlowa, wynik, typ_zrodla)
            print(f"[HISTORIA] Dodano do bazy: {typ_zrodla}, {len(zawartosc_zrodlowa)} → {len(wynik)} znaków")
        except Exception as e:
            print(f"[BŁĄD] Nie udało się dodać do historii: {e}")
            import traceback
            traceback.print_exc()

    def otworz_ostatni(self):
        try:
            okno_historii = OknoHistorii(self.baza, self)
            if okno_historii.exec() == QDialog.DialogCode.Accepted:
                wpis = okno_historii.wybrany_wpis
                if not wpis:
                    return

                sciezka = wpis.get('sciezka', '')
                kierunek = wpis.get('kierunek', 'pl_br')
                typ_zrodla = wpis.get('typ_zrodla', 'tekst')
                zawartosc = wpis.get('zawartosc', '')

                print(f"[HISTORIA] Wczytywanie: {typ_zrodla}, kierunek: {kierunek}, znaków: {len(zawartosc)}")

                self.ustaw_kierunek(kierunek)

                if kierunek == 'pl_br':
                    self.ui.stackedWidget_wewnetrzny.setCurrentIndex(0)
                    self.ui.textEdit_pl_tekst.clear()
                    self.ui.textEdit_pl_tekst.setPlainText(zawartosc)

                    if typ_zrodla == 'plik' and sciezka and sciezka != "Tekst ręczny":
                        if os.path.exists(sciezka):
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n(zawartość z bazy danych)'
                        else:
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n Plik nie istnieje, ale zawartość zachowana w bazie'
                    else:
                        info = 'Wczytano tekst z historii'

                else:
                    self.ui.stackedWidget_wewnetrzny_br.setCurrentIndex(0)
                    self.blokada_auto_tlumaczenia = True
                    self.ui.textEdit_br_tekst.clear()
                    self.ui.textEdit_br_tekst.setPlainText(zawartosc)
                    self.tekst_przed_tlumaczeniem_br = zawartosc
                    self.blokada_auto_tlumaczenia = False

                    if typ_zrodla == 'plik' and sciezka and sciezka != "Tekst ręczny":
                        if os.path.exists(sciezka):
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n(zawartość z bazy danych)'
                        else:
                            info = f'Wczytano z historii:\n{os.path.basename(sciezka)}\n\n Plik nie istnieje, ale zawartość zachowana w bazie'
                    else:
                        info = 'Wczytano tekst Braille z historii'

                QMessageBox.information(
                    self,
                    'Wczytano z historii',
                    info
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Błąd krytyczny',
                f'Wystąpił błąd podczas wczytywania z historii:\n{str(e)}'
            )
            import traceback
            traceback.print_exc()

    def nowe_tlumaczenie(self):
        odpowiedz = QMessageBox.question(
            self,
            'Nowe tłumaczenie',
            'Czy na pewno chcesz rozpocząć nowe tłumaczenie?\n'
            'Niezapisane zmiany zostaną utracone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if odpowiedz == QMessageBox.StandardButton.Yes:
            self.ui.textEdit_pl_tekst.clear()
            self.ui.textEdit_br_tekst.clear()
            self.menadzer.aktualny_dokument = None
            self.procesor.przetlumaczony_tekst = ""
            self.historia_edycji.clear()
            self.indeks_historii_edycji = -1
            self.tekst_przed_tlumaczeniem_br = ""
            self.aktualne_id_zrodla = None
            QMessageBox.information(self, 'Gotowe', 'Rozpoczęto nowe tłumaczenie.')

    def zapisz_stan_edycji(self):
        tekst = self.ui.textEdit_pl_tekst.toPlainText()

        if not self.historia_edycji or self.historia_edycji[-1] != tekst:
            if self.indeks_historii_edycji < len(self.historia_edycji) - 1:
                self.historia_edycji = self.historia_edycji[:self.indeks_historii_edycji + 1]

            self.historia_edycji.append(tekst)
            self.indeks_historii_edycji = len(self.historia_edycji) - 1

            if len(self.historia_edycji) > 50:
                self.historia_edycji.pop(0)
                self.indeks_historii_edycji -= 1

    def cofnij_edycje(self):
        if self.indeks_historii_edycji > 0:
            self.indeks_historii_edycji -= 1
            tekst_cofniety = self.historia_edycji[self.indeks_historii_edycji]

            self.ui.textEdit_pl_tekst.textChanged.disconnect(self.zapisz_stan_edycji)
            self.ui.textEdit_pl_tekst.setPlainText(tekst_cofniety)
            self.ui.textEdit_pl_tekst.textChanged.connect(self.zapisz_stan_edycji)

            self.statusBar().showMessage('Cofnięto zmianę', 2000)
        else:
            self.statusBar().showMessage('Brak zmian do cofnięcia', 2000)

    def wyczysc_tekst(self):
        odpowiedz = QMessageBox.question(
            self,
            'Potwierdzenie',
            'Czy na pewno chcesz wyczyścić tekst?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if odpowiedz == QMessageBox.StandardButton.Yes:
            if self.kierunek == 'pl_br':
                self.ui.textEdit_pl_tekst.clear()
            else:
                self.wyczysc_pole_br()

    def ustaw_pl_br(self):
        self.kierunek = 'pl_br'
        self.ui.stackedWidget_glowny.setCurrentIndex(0)

    def ustaw_br_pl(self):
        self.kierunek = 'br_pl'
        self.ui.stackedWidget_glowny.setCurrentIndex(1)

    def importuj_plik(self):
        try:
            if self.kierunek == 'pl_br':
                filtry = (
                    'Pliki tekstowe (*.txt);;'
                    'Dokument PDF (*.pdf);;'
                    'Dokument Word (*.docx);;'
                    'OpenDocument (*.odt);;'
                    'Rich Text Format (*.rtf);;'
                    'Wszystkie pliki (*.*)'
                )
            else:
                filtry = (
                    'Plik Braille (*.brf);;'
                    'Plik Braille BES (*.bes);;'
                    'Plik Braille BSE (*.bse);;'
                    'Plik tekstowy (*.txt);;'
                    'Dokument PDF (*.pdf);;'
                    'Dokument Word (*.docx);;'
                    'OpenDocument (*.odt);;'
                    'Rich Text Format (*.rtf);;'
                    'Obraz (*.jpg *.jpeg *.png);;'
                    'Wszystkie pliki (*.*)'
                )

            sciezka_pliku, _ = QFileDialog.getOpenFileName(
                self,
                'Wybierz plik do importu',
                os.getcwd(),
                filtry
            )

            if not sciezka_pliku:
                return

            rozszerzenie = os.path.splitext(sciezka_pliku)[1].lower()

            if self.kierunek == 'br_pl' and rozszerzenie in ['.png', '.jpg', '.jpeg']:
                sukces, zawartosc, blad = self._importuj_obraz_braille(sciezka_pliku)
                if sukces:
                    stats = {
                        'znaki': len(zawartosc),
                        'slowa': len(zawartosc.split()),
                        'linie': zawartosc.count('\n') + 1
                    }
                    komunikat = (
                        f'Plik zaimportowany (OCR Braille)!\n\n'
                        f'Rozpoznanych znaków: {stats["znaki"]}\n'
                        f'Słów: {stats["slowa"]}\n'
                        f'Linii: {stats["linie"]}'
                    )
                    QMessageBox.information(self, 'Import zakończony', komunikat)
                else:
                    QMessageBox.critical(self, 'Błąd OCR', blad or "Nie udało się rozpoznać Braille'a")
                return

            if self.kierunek == 'pl_br':
                sukces, blad = self.import_export_pl_br.importuj_plik(sciezka_pliku)
            else:
                sukces, blad = self.import_export_br_pl.importuj_plik(sciezka_pliku)

            if not sukces:
                QMessageBox.critical(self, 'Błąd importu', blad or "Nie udało się wczytać pliku")
                return

            zawartosc = self.menadzer.pobierz_zawartosc() or ""
            stats = self.menadzer.pobierz_statystyki()

            if self.kierunek == 'pl_br':
                self.ui.textEdit_pl_tekst.clear()
                self.ui.textEdit_pl_tekst.setPlainText(zawartosc)
            else:
                self.ui.textEdit_br_tekst.clear()
                self.ui.textEdit_br_tekst.setPlainText(zawartosc)
                self.tekst_przed_tlumaczeniem_br = zawartosc

            komunikat = (
                f'Plik zaimportowany!\n\n'
                f'Znaków: {stats["znaki"]}\n'
                f'Słów: {stats["slowa"]}\n'
                f'Linii: {stats["linie"]}'
            )
            QMessageBox.information(self, 'Import zakończony', komunikat)

        except Exception as e:
            QMessageBox.critical(self, 'Krytyczny błąd', f'Wystąpił błąd: {str(e)}')
            import traceback
            traceback.print_exc()

    def _importuj_obraz_braille(self, sciezka: str) -> tuple[bool, str, str]:
        try:
            from detekcja_i_translacja import rozpoznaj_obraz, pdf_na_obrazy, pdf_ma_unicode_braille
            import cv2

            rozszerzenie = os.path.splitext(sciezka)[1].lower()

            if rozszerzenie == '.pdf':
                if pdf_ma_unicode_braille(sciezka):
                    import fitz
                    doc = fitz.open(sciezka)
                    tekst_braille = ""
                    for strona in doc:
                        tekst_braille += strona.get_text() + "\n"
                    doc.close()

                    if tekst_braille.strip():
                        self.menadzer.utworz_nowy_dokument(tekst_braille)
                        return True, tekst_braille, None
                    else:
                        return False, "", "PDF nie zawiera tekstu Braille"
                else:
                    obrazy = pdf_na_obrazy(sciezka, dpi=300)
                    ascii_all = []

                    for i, img in enumerate(obrazy):
                        ascii_txt = rozpoznaj_obraz(img)
                        if ascii_txt.strip():
                            ascii_all.append(ascii_txt)

                    tekst_wynikowy = "\n\n".join(ascii_all)

                    if tekst_wynikowy.strip():
                        self.menadzer.utworz_nowy_dokument(tekst_wynikowy)
                        return True, tekst_wynikowy, None
                    else:
                        return False, "", "Nie rozpoznano tekstu Braille w PDF"

            else:
                img = cv2.imread(sciezka)
                if img is None:
                    return False, "", f"Nie można wczytać obrazu: {sciezka}"

                ascii_txt = rozpoznaj_obraz(img)

                if ascii_txt.strip():
                    self.menadzer.utworz_nowy_dokument(ascii_txt)
                    return True, ascii_txt, None
                else:
                    return False, "", "Nie rozpoznano tekstu Braille na obrazie"

        except ImportError as e:
            return False, "", f"Brak wymaganych bibliotek OCR: {e}\n\nZainstaluj: pip install opencv-python scikit-learn PyMuPDF"
        except Exception as e:
            return False, "", f"Błąd rozpoznawania Braille: {str(e)}"

    def przetlumacz(self):
        try:
            sciezka_zrodla = None
            typ_zrodla = "tekst"

            if self.kierunek == 'pl_br':
                if self.ui.stackedWidget_wewnetrzny.currentIndex() == 0:
                    tekst = self.ui.textEdit_pl_tekst.toPlainText()
                    if not tekst.strip():
                        QMessageBox.warning(self, 'Uwaga', 'Pole tekstowe jest puste!')
                        return
                    sukces, przetlumaczony, komunikat = self.procesor.przetlumacz_tekst(tekst, self.kierunek)
                    typ_zrodla = "tekst"
                else:
                    if not self.menadzer.czy_ma_dokument():
                        QMessageBox.warning(self, 'Uwaga', 'Nie zaimportowano żadnego pliku!')
                        return
                    sukces, przetlumaczony, komunikat = self.procesor.przetlumacz_dokument(self.kierunek)
                    meta = self.menadzer.pobierz_metadane()
                    if meta:
                        sciezka_zrodla = meta.get('sciezka', '')
                    typ_zrodla = "plik"

            else:
                if self.ui.stackedWidget_wewnetrzny_br.currentIndex() == 0:
                    tekst = self.tekst_przed_tlumaczeniem_br

                    if not tekst.strip():
                        QMessageBox.warning(self, 'Uwaga', 'Pole tekstowe jest puste!')
                        return

                    sukces_br, tekst_braille, _ = self.tlumacz.polski_na_braille(tekst)
                    if not sukces_br:
                        QMessageBox.critical(self, 'Błąd', 'Nie udało się przetłumaczyć na Braille')
                        return

                    sukces, przetlumaczony, komunikat = self.tlumacz.braille_na_polski(tekst_braille)
                    if sukces:
                        self.procesor.przetlumaczony_tekst = przetlumaczony
                        self.procesor.kierunek_tlumaczenia = self.kierunek
                    typ_zrodla = "tekst"
                else:
                    if not self.menadzer.czy_ma_dokument():
                        QMessageBox.warning(self, 'Uwaga', 'Nie zaimportowano żadnego pliku!')
                        return
                    sukces, przetlumaczony, komunikat = self.procesor.przetlumacz_dokument(self.kierunek)
                    meta = self.menadzer.pobierz_metadane()
                    if meta:
                        sciezka_zrodla = meta.get('sciezka', '')
                    typ_zrodla = "plik"

            if sukces:
                info = 'Tłumaczenie zakończone!\n\nKliknij "Podgląd" aby zobaczyć wynik.'
                if komunikat:
                    info += f'\n\n{komunikat}'

                if self.kierunek == 'pl_br':
                    tekst_zrodlowy = (self.ui.textEdit_pl_tekst.toPlainText()
                                      if self.ui.stackedWidget_wewnetrzny.currentIndex() == 0
                                      else self.menadzer.pobierz_zawartosc())
                else:
                    tekst_zrodlowy = (self.tekst_przed_tlumaczeniem_br
                                      if self.ui.stackedWidget_wewnetrzny_br.currentIndex() == 0
                                      else self.menadzer.pobierz_zawartosc())

                if tekst_zrodlowy:
                    info += f'\n\nZnaków wejściowych: {len(tekst_zrodlowy)}'
                    info += f'\nZnaków wyjściowych: {len(przetlumaczony)}'

                    self.dodaj_do_historii(
                        sciezka_zrodla or "Tekst ręczny",
                        self.kierunek,
                        tekst_zrodlowy,
                        przetlumaczony,
                        typ_zrodla
                    )

                QMessageBox.information(self, 'Sukces', info)
            else:
                QMessageBox.critical(self, 'Błąd tłumaczenia', komunikat)

        except Exception as e:
            QMessageBox.critical(self, 'Błąd', f'Wystąpił błąd: {str(e)}')
            import traceback
            traceback.print_exc()

    def pokaz_podglad(self):
        przetlumaczony = self.procesor.pobierz_przetlumaczony()

        if not przetlumaczony:
            QMessageBox.warning(
                self,
                'Brak tłumaczenia',
                'Najpierw przetłumacz tekst za pomocą przycisku "Przetłumacz"'
            )
            return

        okno_podgladu = OknoPodgladu(przetlumaczony, self.kierunek, self)
        okno_podgladu.exec()

    def podglad_zrodlowego_pliku(self):
        if not self.menadzer.czy_ma_dokument():
            QMessageBox.warning(
                self,
                'Brak pliku',
                'Nie załadowano żadnego pliku do podglądu.'
            )
            return

        zawartosc = self.menadzer.pobierz_zawartosc()
        if not zawartosc:
            QMessageBox.warning(
                self,
                'Pusty plik',
                'Załadowany plik jest pusty.'
            )
            return

        meta = self.menadzer.pobierz_metadane()
        nazwa_pliku = meta.get('nazwa_pliku', 'Plik') if meta else 'Plik'

        okno = QDialog(self)
        okno.setWindowTitle(f'Podgląd: {nazwa_pliku}')
        okno.setMinimumSize(700, 500)

        layout = QVBoxLayout()

        pole_tekstu = QTextEdit()
        pole_tekstu.setReadOnly(True)
        pole_tekstu.setPlainText(zawartosc)
        pole_tekstu.setFont(QFont("Arial", 12))
        layout.addWidget(pole_tekstu)

        btn_zamknij = QPushButton("Zamknij")
        btn_zamknij.clicked.connect(okno.accept)
        layout.addWidget(btn_zamknij)

        okno.setLayout(layout)
        okno.exec()

    def zapisz_wynik(self):
        przetlumaczony = self.procesor.pobierz_przetlumaczony()

        if not przetlumaczony:
            QMessageBox.warning(
                self,
                'Brak tłumaczenia',
                'Najpierw przetłumacz tekst za pomocą przycisku "Przetłumacz".'
            )
            return

        if self.kierunek == 'pl_br':
            filtry = (
                'Plik Braille (*.brf);;'
                'Plik Braille BES (*.bes);;'
                'Plik Braille BSE (*.bse);;'
                'Plik tekstowy (*.txt);;'
                'Dokument PDF (*.pdf);;'
                'Wszystkie pliki (*.*)'
            )
        else:
            filtry = (
                'Plik tekstowy (*.txt);;'
                'Dokument PDF (*.pdf);;'
                'Dokument Word (*.docx);;'
                'OpenDocument (*.odt);;'
                'Rich Text Format (*.rtf);;'
                'Wszystkie pliki (*.*)'
            )

        sciezka_zapisu, _ = QFileDialog.getSaveFileName(
            self,
            'Zapisz przetłumaczony tekst',
            '',
            filtry
        )

        if not sciezka_zapisu:
            return

        try:
            if self.menadzer.czy_ma_dokument():
                self.menadzer.ustaw_zawartosc(przetlumaczony)
            else:
                self.menadzer.utworz_nowy_dokument(przetlumaczony)

            if self.kierunek == 'pl_br':
                sukces, blad = self.import_export_pl_br.eksportuj_plik(sciezka_zapisu)
            else:
                sukces, blad = self.import_export_br_pl.eksportuj_plik(sciezka_zapisu)

            if sukces:
                QMessageBox.information(
                    self,
                    'Zapisano',
                    f'Plik zapisany:\n{sciezka_zapisu}'
                )
            else:
                QMessageBox.critical(
                    self,
                    'Błąd zapisu',
                    blad or "Nie udało się zapisać pliku"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Błąd zapisu',
                f'Wystąpił błąd: {str(e)}'
            )
            import traceback
            traceback.print_exc()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    domyslna_czcionka = QFont("Arial", 11)
    app.setFont(domyslna_czcionka)
    okno = OknoGlowne()
    okno.show()
    sys.exit(app.exec())
>>>>>>> 6ecdc4fe137fd6bdbf48b60475110ab816c0aca2
