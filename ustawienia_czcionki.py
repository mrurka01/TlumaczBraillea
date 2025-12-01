from PyQt6.QtWidgets import (
    QDialog, QMessageBox, QWidget, QPushButton, QLabel,
    QComboBox, QSpinBox, QApplication, QTextEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from czcionka_ui import Ui_Dialog


class MenadzerCzcionek:
    """Klasa zarządzająca ustawieniami czcionki w aplikacji."""

    def __init__(self):
        self.czcionka = QFont("Arial", 11)  # Domyślnie 11pt (było 12)
        self.odstep_liter = 0
        self.odstep_wyrazy = 0

    def pobierz_czcionke(self):
        return self.czcionka

    def ustaw_czcionke(self, nazwa: str, rozmiar: int, odstep_liter: int, odstep_wyrazy: int):
        self.czcionka = QFont(nazwa, rozmiar)
        self.odstep_liter = odstep_liter
        self.odstep_wyrazy = odstep_wyrazy
        if odstep_liter != 0:
            self.czcionka.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 100 + odstep_liter)
        if odstep_wyrazy != 0:
            self.czcionka.setWordSpacing(odstep_wyrazy)

    def zastosuj_do_widgetu(self, widget, minimalna_wysokosc_przycisku=28):
        print(f"[DEBUG] Aplikowanie czcionki: {self.czcionka.family()}, rozmiar: {self.czcionka.pointSize()}")

        widget.setFont(self.czcionka)

        for przycisk in widget.findChildren(QPushButton):
            przycisk.setFont(self.czcionka)
            metryki = przycisk.fontMetrics()
            przycisk.setMinimumHeight(metryki.height() + 12)
            przycisk.setStyleSheet("")
            przycisk.adjustSize()

        for etykieta in widget.findChildren(QLabel):
            etykieta.setFont(self.czcionka)

        for combo in widget.findChildren(QComboBox):
            combo.setFont(self.czcionka)
            metryki = combo.fontMetrics()
            combo.setMinimumHeight(metryki.height() + 8)
            combo.setStyleSheet("")

        for spin in widget.findChildren(QSpinBox):
            spin.setFont(self.czcionka)
            metryki = spin.fontMetrics()
            spin.setMinimumHeight(metryki.height() + 8)
            spin.setStyleSheet("")

        for text_edit in widget.findChildren(QTextEdit):
            text_edit.setFont(self.czcionka)
            spin.setStyleSheet("")

        for text_edit in widget.findChildren(QTextEdit):
            text_edit.setFont(self.czcionka)
            text_edit.setStyleSheet("")

        for menu in widget.findChildren(QWidget):
            if hasattr(menu, 'setFont'):
                menu.setFont(self.czcionka)

        print(f"[DEBUG] Czcionka zastosowana")


class OknoCzcionka(QDialog):

    def __init__(self, menadzer_czcionek: MenadzerCzcionek, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.menadzer_czcionek = menadzer_czcionek

        # Połączenia przycisków
        self.ui.pushButton.clicked.connect(self.zatwierdz)
        self.ui.pushButton_2.clicked.connect(self.reject)

        # Dodaj czcionki do ComboBox
        self._inicjalizuj_czcionki()

        # Załaduj aktualne ustawienia
        self._zaladuj_aktualne_ustawienia()

        # Ustaw zakresy dla SpinBox
        self._ustaw_zakresy()

    def _inicjalizuj_czcionki(self):
        """Inicjalizuje listę dostępnych czcionek."""
        czcionki = [
            "Arial",
            "Times New Roman",
            "Verdana",
            "Courier New",
            "Tahoma",
            "Calibri",
            "Segoe UI",
            "Comic Sans MS",
            "Georgia",
            "Trebuchet MS"
        ]
        self.ui.comboBox_czcionka.clear()
        self.ui.comboBox_czcionka.addItems(czcionki)

    def _zaladuj_aktualne_ustawienia(self):
        """Ładuje aktualne ustawienia czcionki do kontrolek."""
        czcionka = self.menadzer_czcionek.pobierz_czcionke()

        # Ustaw rodzaj czcionki
        indeks = self.ui.comboBox_czcionka.findText(czcionka.family())
        if indeks >= 0:
            self.ui.comboBox_czcionka.setCurrentIndex(indeks)

        # Ustaw rozmiar
        self.ui.spinBox_rozmiar.setValue(czcionka.pointSize())

        # Ustaw odstępy
        self.ui.spinBox_odstep_liter.setValue(self.menadzer_czcionek.odstep_liter)
        self.ui.spinBox_odstep_wyrazy.setValue(self.menadzer_czcionek.odstep_wyrazy)

    def _ustaw_zakresy(self):
        """
        Ustawia zakresy wartości dla SpinBox.
        WAŻNE: Maksymalny rozmiar to 16pt (18pt dla osób słabowidzących)
        """
        # Rozmiar czcionki: 9-16 (max 18 dla dostępności)
        self.ui.spinBox_rozmiar.setMinimum(9)
        self.ui.spinBox_rozmiar.setMaximum(18)  # OGRANICZONO z 72 do 18!
        self.ui.spinBox_rozmiar.setValue(11)  # Domyślnie 11pt

        # Odstęp między literami: -5 do 10
        self.ui.spinBox_odstep_liter.setMinimum(-5)
        self.ui.spinBox_odstep_liter.setMaximum(10)

        # Odstęp między wyrazami: 0 do 5
        self.ui.spinBox_odstep_wyrazy.setMinimum(0)
        self.ui.spinBox_odstep_wyrazy.setMaximum(5)

    def zatwierdz(self):
        """Zatwierdza zmiany czcionki."""
        try:
            # Pobierz wartości z kontrolek
            nazwa = self.ui.comboBox_czcionka.currentText()
            rozmiar = self.ui.spinBox_rozmiar.value()
            odstep_liter = self.ui.spinBox_odstep_liter.value()
            odstep_wyrazy = self.ui.spinBox_odstep_wyrazy.value()

            # Walidacja - ŚCISŁA
            if rozmiar < 9 or rozmiar > 18:
                QMessageBox.warning(
                    self,
                    "Nieprawidłowy rozmiar",
                    "Rozmiar czcionki musi być między 9 a 18 punktami.\n\n"
                    "Dla lepszej czytelności zalecamy 11-14pt."
                )
                return

            # Ostrzeżenie dla dużych rozmiarów
            if rozmiar > 16:
                odpowiedz = QMessageBox.question(
                    self,
                    "Duży rozmiar czcionki",
                    f"Wybrałeś rozmiar {rozmiar}pt. To może spowodować problemy z układem.\n\n"
                    "Zalecamy maksymalnie 16pt.\n\n"
                    "Czy na pewno chcesz kontynuować?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if odpowiedz != QMessageBox.StandardButton.Yes:
                    return

            # Zapisz w menadżerze
            self.menadzer_czcionek.ustaw_czcionke(nazwa, rozmiar, odstep_liter, odstep_wyrazy)

            # Zaakceptuj dialog
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Błąd",
                f"Nie udało się ustawić czcionki:\n{e}"
            )