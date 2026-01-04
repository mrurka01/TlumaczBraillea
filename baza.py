import sqlite3
import os
from datetime import datetime

class BazaDanych:
    def __init__(self, plik_bazy="historia.db"):
        self.sciezka_bazy = os.path.abspath(plik_bazy)
        self.polacz()
        self.utworz_tabele()
        self.migruj_baze()

    def polacz(self):
        self.conn = sqlite3.connect(self.sciezka_bazy)
        self.cur = self.conn.cursor()

    def utworz_tabele(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS zrodla (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sciezka TEXT,
                kierunek TEXT,
                zawartosc_zrodlowa TEXT,
                typ_zrodla TEXT DEFAULT 'tekst',
                data_dodania TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS tlumaczenia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_zrodla INTEGER,
                kierunek TEXT,
                wynik TEXT,
                data_tlumaczenia TEXT,
                FOREIGN KEY(id_zrodla) REFERENCES zrodla(id)
            )
        """)
        self.conn.commit()

    def migruj_baze(self):
        try:
            self.cur.execute("PRAGMA table_info(zrodla)")
            kolumny = [info[1] for info in self.cur.fetchall()]

            if 'typ_zrodla' not in kolumny:
                print("Migracja: Dodawanie kolumny typ_zrodla...")
                self.cur.execute("""
                    ALTER TABLE zrodla 
                    ADD COLUMN typ_zrodla TEXT DEFAULT 'tekst'
                """)
                self.cur.execute("""
                    UPDATE zrodla 
                    SET typ_zrodla = CASE 
                        WHEN sciezka LIKE '%.%' THEN 'plik'
                        ELSE 'tekst'
                    END
                    WHERE typ_zrodla IS NULL OR typ_zrodla = 'tekst'
                """)
                self.conn.commit()
                print("Kolumna typ_zrodla dodana!")

            self.cur.execute("PRAGMA table_info(zrodla)")
            kolumny = [info[1] for info in self.cur.fetchall()]

            if 'zawartosc' in kolumny and 'zawartosc_zrodlowa' not in kolumny:
                print("Migracja: Zmiana nazwy kolumny zawartosc → zawartosc_zrodlowa...")
                self.cur.execute("""
                    CREATE TABLE zrodla_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sciezka TEXT,
                        kierunek TEXT,
                        zawartosc_zrodlowa TEXT,
                        typ_zrodla TEXT DEFAULT 'tekst',
                        data_dodania TEXT
                    )
                """)
                self.cur.execute("""
                    INSERT INTO zrodla_new (id, sciezka, kierunek, zawartosc_zrodlowa, typ_zrodla, data_dodania)
                    SELECT id, sciezka, kierunek, zawartosc, typ_zrodla, data_dodania
                    FROM zrodla
                """)
                self.cur.execute("DROP TABLE zrodla")
                self.cur.execute("ALTER TABLE zrodla_new RENAME TO zrodla")
                self.conn.commit()
                print("Kolumna zawartosc_zrodlowa utworzona!")

            elif 'zawartosc_zrodlowa' not in kolumny:
                print("Migracja: Dodawanie kolumny zawartosc_zrodlowa...")
                self.cur.execute("""
                    ALTER TABLE zrodla 
                    ADD COLUMN zawartosc_zrodlowa TEXT DEFAULT ''
                """)
                self.conn.commit()
                print("Kolumna zawartosc_zrodlowa dodana!")

            print("Migracja zakończona pomyślnie!")
        except Exception as e:
            print(f"Błąd migracji: {e}")
            self.conn.rollback()

    def dodaj_zrodlo(self, sciezka, kierunek, zawartosc_zrodlowa, typ_zrodla="tekst"):
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cur.execute("""
            INSERT INTO zrodla (sciezka, kierunek, zawartosc_zrodlowa, typ_zrodla, data_dodania)
            VALUES (?, ?, ?, ?, ?)
        """, (sciezka, kierunek, zawartosc_zrodlowa, typ_zrodla, data))
        self.conn.commit()

        id_zrodla = self.cur.lastrowid
        print(f"[BAZA] Dodano źródło #{id_zrodla}: {typ_zrodla}, {len(zawartosc_zrodlowa)} znaków")
        return id_zrodla

    def dodaj_tlumaczenie(self, sciezka, kierunek, zawartosc_zrodlowa, wynik, typ_zrodla="tekst"):
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        id_zrodla = self.dodaj_zrodlo(sciezka, kierunek, zawartosc_zrodlowa, typ_zrodla)

        self.cur.execute("""
            INSERT INTO tlumaczenia (id_zrodla, kierunek, wynik, data_tlumaczenia)
            VALUES (?, ?, ?, ?)
        """, (id_zrodla, kierunek, wynik, data))
        self.conn.commit()

        print(f"[BAZA] Dodano tłumaczenie #{id_zrodla}: {len(zawartosc_zrodlowa)} → {len(wynik)} znaków")
        return id_zrodla

    def pobierz_tlumaczenia(self):
        try:
            self.cur.execute("PRAGMA table_info(zrodla)")
            kolumny = [info[1] for info in self.cur.fetchall()]

            if 'zawartosc_zrodlowa' in kolumny:
                self.cur.execute("""
                    SELECT z.id, z.sciezka, z.kierunek, z.typ_zrodla, z.zawartosc_zrodlowa, t.wynik, t.data_tlumaczenia
                    FROM zrodla z
                    JOIN tlumaczenia t ON z.id = t.id_zrodla
                    ORDER BY t.data_tlumaczenia DESC
                """)
            elif 'zawartosc' in kolumny:
                self.cur.execute("""
                    SELECT z.id, z.sciezka, z.kierunek, z.typ_zrodla, z.zawartosc, t.wynik, t.data_tlumaczenia
                    FROM zrodla z
                    JOIN tlumaczenia t ON z.id = t.id_zrodla
                    ORDER BY t.data_tlumaczenia DESC
                """)
            else:
                self.cur.execute("""
                    SELECT z.id, z.sciezka, z.kierunek, z.typ_zrodla, '' as zawartosc_zrodlowa, t.wynik, t.data_tlumaczenia
                    FROM zrodla z
                    JOIN tlumaczenia t ON z.id = t.id_zrodla
                    ORDER BY t.data_tlumaczenia DESC
                """)

            wyniki = self.cur.fetchall()
            print(f"[BAZA] Pobrano {len(wyniki)} tłumaczeń z historii")
            return wyniki

        except Exception as e:
            print(f"[BAZA] Błąd pobierania tłumaczeń: {e}")
            return []

    def pobierz_zrodla(self):
        self.cur.execute("""
            SELECT * FROM zrodla ORDER BY data_dodania DESC
        """)
        return self.cur.fetchall()

    def wyczysc_historie(self):
        self.cur.execute("DELETE FROM tlumaczenia")
        self.cur.execute("DELETE FROM zrodla")
        self.conn.commit()
        print("[BAZA] Historia wyczyszczona")

    def pobierz_statystyki_bazy(self):
        self.cur.execute("SELECT COUNT(*) FROM zrodla")
        liczba_zrodel = self.cur.fetchone()[0]

        self.cur.execute("SELECT COUNT(*) FROM tlumaczenia")
        liczba_tlumaczen = self.cur.fetchone()[0]

        self.cur.execute("SELECT SUM(LENGTH(zawartosc_zrodlowa)) FROM zrodla")
        rozmiar_zrodel = self.cur.fetchone()[0] or 0

        self.cur.execute("SELECT SUM(LENGTH(wynik)) FROM tlumaczenia")
        rozmiar_tlumaczen = self.cur.fetchone()[0] or 0

        return {
            'liczba_zrodel': liczba_zrodel,
            'liczba_tlumaczen': liczba_tlumaczen,
            'rozmiar_zrodel_znaki': rozmiar_zrodel,
            'rozmiar_tlumaczen_znaki': rozmiar_tlumaczen,
            'rozmiar_calkowity_kb': (rozmiar_zrodel + rozmiar_tlumaczen) / 1024
        }