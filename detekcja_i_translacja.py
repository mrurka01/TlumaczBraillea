# -*- coding: utf-8 -*-
import os, sys, math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import numpy as np
import cv2
from sklearn.cluster import KMeans
try:
    import fitz
except Exception:
    fitz = None
from tablica_unicode import maska_na_tekst, maska_na_unicode, MAPA_CYFR, ZNAK_LICZBY, ZNAK_KAPITAL

POZ_BIT = {(0,0):0,(1,0):1,(2,0):2,(0,1):3,(1,1):4,(2,1):5}

def komorka_na_maske(kom: List[List[bool]]) -> int:
    m = 0
    for r in range(3):
        for c in range(2):
            if kom[r][c]:
                m |= 1 << POZ_BIT[(r,c)]
    return m

@dataclass
class Kropka:
    x: float; y: float; r: float

@dataclass
class Kolumna:
    x: float; kropki: List[Kropka]

def binarka(img_bgr: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (3,3), 0)
    _, b = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return b

def znajdz_kropki(b: np.ndarray) -> List[Kropka]:
    cnts, _ = cv2.findContours(b, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    pts = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 10: continue
        p = cv2.arcLength(c, True) or 1.0
        circ = 4.0 * math.pi * a / (p*p)
        if circ < 0.6: continue
        (x,y), r = cv2.minEnclosingCircle(c)
        pts.append((x,y,r))
    if not pts: return []
    rmed = float(np.median([r for _,_,r in pts]))
    rlo, rhi = max(1.0, 0.5*rmed), 2.0*rmed
    return [Kropka(float(x), float(y), float(r)) for (x,y,r) in pts if rlo <= r <= rhi]

def iou1d(a, b):
    y1, y2 = a; u1, u2 = b
    inter = max(0.0, min(y2,u2) - max(y1,u1))
    union = (y2-y1) + (u2-u1) - inter + 1e-6
    return inter/union

def segmentuj_wiersze(b: np.ndarray, kropki: List[Kropka]):
    if not kropki: return []
    H,W = b.shape[:2]
    m = np.zeros((H,W), np.uint8)
    for d in kropki:
        cv2.circle(m, (int(round(d.x)), int(round(d.y))), max(1,int(round(d.r*1.2))), 255, -1)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_RECT,(1,3)), 1)
    rmed = float(np.median([d.r for d in kropki]))
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_RECT,(max(25,int(round(18*rmed))),1)), 1)
    cnts,_ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    kand = []
    for c in cnts:
        x,y,w,h = cv2.boundingRect(c)
        if w < 0.03*W or h < 0.015*H: 
            continue
        y1 = max(0, int(y - 4*rmed))
        y2 = min(H-1, int(y + h + 4*rmed))
        wi = [d for d in kropki if y1 <= d.y <= y2]
        if wi: kand.append((wi,(y1,y2)))
    kand.sort(key=lambda it: it[1][0])
    final = []
    for pts,rng in kand:
        if not final:
            final.append((pts,rng)); continue
        merged = False
        for j,(p2,r2) in enumerate(final):
            if iou1d(rng,r2) >= 0.60:
                if len(pts) > len(p2): final[j] = (pts,rng)
                merged = True; break
        if not merged: final.append((pts,rng))
    if final:
        counts = [len(p) for p,_ in final]
        mx = float(max(counts))
        med = float(np.median(counts))
        thr_twardy = max(8.0, 0.45*mx, 0.50*med)
        thr_miekki = max(6.0, 0.18*mx)
        mocne = [(p,r) for (p,r) in final if len(p) >= thr_twardy]
        reszta = [(p,r) for (p,r) in final if len(p) < thr_twardy]
        reszta.sort(key=lambda it: len(it[0]), reverse=True)
        for p,r in reszta:
            if len(mocne) >= 3: break
            if len(p) >= thr_miekki:
                mocne.append((p,r))
        if mocne:
            final = mocne
        else:
            final = sorted(final, key=lambda it: len(it[0]), reverse=True)[:1]
    if not final and kropki:
        ys = [d.y for d in kropki]
        final = [(kropki,(int(min(ys)-4*rmed), int(max(ys)+4*rmed)))]
    final.sort(key=lambda it: it[1][0])
    return final

def srodki_rzedow(kropki: List[Kropka]) -> List[float]:
    ys = np.array([d.y for d in kropki], dtype=np.float32).reshape(-1,1)
    if len(ys) < 6:
        q = np.quantile(ys.ravel(), [0.17,0.5,0.83]).tolist()
        return sorted(map(float,q))
    km = KMeans(n_clusters=3, n_init=10, random_state=0).fit(ys)
    s = sorted(float(c[0]) for c in km.cluster_centers_)
    if min(s[1]-s[0], s[2]-s[1]) < 2.0:
        q = np.quantile(ys.ravel(), [0.17,0.5,0.83]).tolist()
        return sorted(map(float,q))
    return s

def est_scalenie(kropki: List[Kropka]) -> float:
    xs = sorted([d.x for d in kropki])
    dx = np.diff(xs); dx = dx[dx > 0]
    if len(dx) == 0: return 3.0
    return max(2.0, float(np.percentile(dx, 7)))

def zbuduj_kolumny(kropki: List[Kropka], sklej_px: float) -> List[Kolumna]:
    posort = sorted(kropki, key=lambda d:d.x)
    kolumny: List[Kolumna] = []
    for d in posort:
        if not kolumny or abs(d.x - kolumny[-1].x) > sklej_px:
            kolumny.append(Kolumna(x=d.x, kropki=[d]))
        else:
            kolumny[-1].kropki.append(d)
            kolumny[-1].x = float(np.mean([p.x for p in kolumny[-1].kropki]))
    return kolumny

def progi_z_odstepow(xs: List[float], mnoz_slowa: float=1.6):
    dx = np.diff(sorted(xs))
    if len(dx)==0: return float("inf"), float("inf")
    med = float(np.median(dx))
    q1,q3 = np.quantile(dx,[0.25,0.75]); iqr = float(q3-q1)
    p90 = float(np.quantile(dx,0.90))
    k = min(3, len(dx))
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(dx.reshape(-1,1))
    c = sorted(float(v[0]) for v in km.cluster_centers_)
    if k==1:
        t_l = max(med*1.25, q3+0.20*iqr); t_w = max(t_l*mnoz_slowa, p90, q3+1.0*iqr); return t_l, t_w
    if k==2:
        t_l = (c[0]+c[1])/2.0; t_w = max(t_l*mnoz_slowa, p90, q3+1.0*iqr); return t_l, t_w
    male,sred,duze = c
    t_l = (male+sred)/2.0; t_w = max((sred+duze)/2.0, t_l*mnoz_slowa, p90, q3+1.0*iqr); return t_l, t_w

def komorka_litery(kol_lit: List[Kolumna], srodki: List[float]):
    kom = [[False,False],[False,False],[False,False]]
    xs = sorted([c.x for c in kol_lit]); lewy,prawy = xs[0], xs[-1]
    for kol in kol_lit:
        for d in kol.kropki:
            cid = 0 if abs(d.x - lewy) <= abs(d.x - prawy) else 1
            rid = int(np.argmin([abs(d.y - rc) for rc in srodki]))
            if 0 <= rid <= 2: kom[rid][cid] = True
    return kom

def prawy_x(lit: List[Kolumna]) -> float: return max(c.x for c in lit)
def lewy_x(lit: List[Kolumna]) -> float: return min(c.x for c in lit)

def maska_z_kontekstem(slowo: List[List[Kolumna]], i: int, srodki: List[float], med_przerwa_kol: float):
    lit = slowo[i]
    if len(lit) >= 2:
        kom = komorka_litery(lit, srodki); return komorka_na_maske(kom), kom
    kol = lit[0]; cid = 0
    d_next = 1e9; d_prev = 1.0e9
    if i+1 < len(slowo): d_next = max(0.0, lewy_x(slowo[i+1]) - kol.x)
    if i-1 >= 0:        d_prev = max(0.0, kol.x - prawy_x(slowo[i-1]))
    if (d_next <= 1.25*max(2.0, med_przerwa_kol)) and (d_next <= d_prev*1.1 or d_prev == 0.0):
        cid = 1
    kom = [[False,False],[False,False],[False,False]]
    for d in kol.kropki:
        rid = int(np.argmin([abs(d.y - rc) for rc in srodki]))
        if 0 <= rid <= 2: kom[rid][cid] = True
    return komorka_na_maske(kom), kom

def grupuj_litery_i_slowa(kolumny: List[Kolumna], t_litera: float, t_slowo: float, srodki: List[float], mnoz_a: float=1.35):
    A_MASKI = {1, 1|32}
    def czy_a(lc: List[Kolumna]) -> bool:
        try: return (komorka_na_maske(komorka_litery(lc, srodki)) & 0x3F) in A_MASKI
        except Exception: return False
    def waska(lc: List[Kolumna]) -> bool: return len(lc) == 1
    slowa, cur_s, cur_l = [], [], [kolumny[0]]
    for i in range(len(kolumny)-1):
        od = kolumny[i+1].x - kolumny[i].x
        t_loc = t_slowo * (mnoz_a if (waska(cur_l) or czy_a(cur_l)) else 1.0)
        if od >= t_loc:
            cur_s.append(cur_l); slowa.append(cur_s); cur_s, cur_l = [], [kolumny[i+1]]
        elif od >= t_litera:
            cur_s.append(cur_l); cur_l = [kolumny[i+1]]
        else:
            cur_l.append(kolumny[i+1])
    cur_s.append(cur_l); slowa.append(cur_s)
    return slowa

def wymus_podzial_przed_liczba(slowa, srodki, med_przerwa_kol):
    cel = (ZNAK_LICZBY & 0x3F)
    wynik = []
    for w in slowa:
        cur = w
        while True:
            idx = None
            for i in range(len(cur)):
                m,_ = maska_z_kontekstem(cur,i,srodki,med_przerwa_kol)
                if m == cel and i > 0: idx = i; break
            if idx is None: wynik.append(cur); break
            lew, praw = cur[:idx], cur[idx:]
            if lew: wynik.append(lew)
            cur = praw
    return wynik

def odseparuj_koncowe_w(slowa, srodki, t_litera, med_lit, med_przerwa_kol):
    W_MASK = (2|8|16|32); out, i = [], 0
    while i < len(slowa):
        w = slowa[i]
        if i+1 < len(slowa) and len(w) >= 2:
            m_next,_ = maska_z_kontekstem(slowa[i+1],0,srodki,med_przerwa_kol)
            if (m_next & 0x3F) == (ZNAK_LICZBY & 0x3F):
                m_last,_ = maska_z_kontekstem(w,len(w)-1,srodki,med_przerwa_kol)
                if m_last == W_MASK:
                    out.append(w[:-1]); out.append([w[-1]]); i+=1; continue
        out.append(w); i+=1
    return out

def sklejanie_post(slowa, t_litera, t_slowo, srodki, med_lit, med_przerwa_kol, tryb="light", mnoz_a=1.25):
    if not slowa or tryb=="off": return slowa
    A_MASKI = {1,1|32}
    polaczone = [slowa[0]]
    for w2 in slowa[1:]:
        w1 = polaczone[-1]
        try: p_last = w1[-1][-1]; n_first = w2[0][0]
        except Exception: polaczone.append(w2); continue
        od = float(n_first.x - p_last.x)
        m_l,_ = maska_z_kontekstem(w1,len(w1)-1,srodki,med_przerwa_kol)
        m_r,_ = maska_z_kontekstem(w2,0,srodki,med_przerwa_kol)
        thr_w = {"off":0.0,"light":0.55,"strong":0.80}[tryb]
        thr_med = {"off":0.0,"light":1.15,"strong":1.30}[tryb]
        thr_tl = {"off":0.0,"light":1.10,"strong":1.35}[tryb]
        baza = min(t_slowo*thr_w, med_lit*thr_med, t_litera*thr_tl)
        w1_waska = (len(w1[-1])==1) or ((m_l & 0x3F) in A_MASKI)
        w2_waska = (len(w2[0])==1) or ((m_r & 0x3F) in A_MASKI)
        dop = baza * (mnoz_a if (w1_waska or w2_waska) else 1.0)
        if (m_r & 0x3F) in {ZNAK_LICZBY & 0x3F, ZNAK_KAPITAL & 0x3F}:
            polaczone.append(w2); continue
        if od <= dop: w1.extend(w2)
        else: polaczone.append(w2)
    return polaczone

def srodek_x_lit(lit: List[Kolumna]) -> float:
    xs = [p.x for c in lit for p in c.kropki]
    return float(np.mean(xs)) if xs else 0.0

def prawa_przewaga_silna(lit: List[Kolumna]) -> bool:
    xs = [p.x for c in lit for p in c.kropki]
    if len(xs) < 2: return False
    x_min, x_max = min(xs), max(xs)
    if x_max - x_min < 1e-3: return False
    prog = x_min + 0.55 * (x_max - x_min)
    return min(xs) >= prog

def prawa_przewaga(lit: List[Kolumna]) -> float:
    xs = [p.x for c in lit for p in c.kropki]
    if len(xs) < 2: return 0.5
    x_min, x_max = min(xs), max(xs)
    if x_max - x_min < 1e-3: return 0.5
    return (float(np.mean(xs)) - x_min) / (x_max - x_min)

def kanonizuj_kapitalizacje(slowo: List[List[Kolumna]], srodki: List[float], med_przerwa_kol: float):
    odstepy = []
    for j in range(len(slowo) - 1):
        od = lewy_x(slowo[j+1]) - prawy_x(slowo[j])
        if od > 0:
            odstepy.append(float(od))
    med_odstep = float(np.median(odstepy)) if odstepy else 1.2 * max(2.0, med_przerwa_kol)
    PROG_RATIO = 0.58
    PROG_BLISKO = 1.10
    wynik = []
    poprzednia = False
    for i in range(len(slowo)):
        m, kom = maska_z_kontekstem(slowo, i, srodki, med_przerwa_kol)
        topL, topR = kom[0][0], kom[0][1]
        midL, midR = kom[1][0], kom[1][1]
        botL, botR = kom[2][0], kom[2][1]
        ma_gore = topL or topR
        ma_srodek = midL or midR
        ma_dol = botL or botR
        kol_lewa = topL or midL or botL
        kol_prawa = topR or midR or botR
        jedna = (kol_lewa ^ kol_prawa)
        pocz = (i == 0) or (i == 1 and poprzednia)
        zmien = False
        if pocz and jedna and ma_gore and ma_dol and not ma_srodek:
            if prawa_przewaga_silna(slowo[i]):
                zmien = True
            else:
                r = prawa_przewaga(slowo[i])
                if r >= PROG_RATIO:
                    zmien = True
                elif i + 1 < len(slowo):
                    dx = max(0.0, lewy_x(slowo[i+1]) - srodek_x_lit(slowo[i]))
                    if dx <= PROG_BLISKO * max(med_przerwa_kol, med_odstep):
                        zmien = True
        if zmien:
            nowa = [[False, False], [False, False], [False, False]]
            nowa[0][1] = True; nowa[2][1] = True
            kom = nowa
            m = (ZNAK_KAPITAL & 0x3F)
            poprzednia = True
        else:
            poprzednia = (m & 0x3F) == (ZNAK_KAPITAL & 0x3F)
        wynik.append((m, kom))
    return wynik

def filtr_linii(wiersze: List[str]) -> List[str]:
    if not wiersze: return []
    max_len = max(len(s.strip()) for s in wiersze) or 1
    sam = set("aeiouyąęóAEIOUYĄĘÓ")
    dob = []
    for s in wiersze:
        t = "".join(ch for ch in s if not ch.isspace())
        if len(t) < 3: continue
        lit = sum(1 for ch in t if ch.isalpha() or ch.isdigit())
        interp = sum(1 for ch in t if ch in ",.;:!?*-/—–'\"\\[]()")
        niezn = sum(1 for ch in t if not (ch.isalpha() or ch.isdigit() or ch in ",.;:!?*-/—–'\"\\[]()"))
        if lit == 0: continue
        udz_lit = lit / len(t)
        najcz = max(t.count(c) for c in set(t))
        if udz_lit < 0.70:
            if not (len(t) >= 25 and udz_lit >= 0.60 and interp <= 0.25*len(t)):
                continue
        if najcz / len(t) >= 0.55 and len(t) >= 10:
            continue
        if interp >= 0.35*len(t) and len(t) < 20:
            continue
        if niezn >= 0.15*len(t) and len(t) < 20:
            continue
        if sum(1 for ch in t if ch in sam) == 0 and lit >= 4:
            continue
        if len(s.strip()) < 0.35 * max_len and lit < 6:
            continue
        dob.append(s)
    return dob

def rozpoznaj_obraz(img_bgr: np.ndarray) -> str:
    b = binarka(img_bgr)
    kropki = znajdz_kropki(b)
    if not kropki: return ""
    linie = segmentuj_wiersze(b, kropki)
    if not linie:
        ys = [d.y for d in kropki]
        rmed = float(np.median([d.r for d in kropki])) if kropki else 3.0
        linie = [(kropki,(int(min(ys)-4*rmed), int(max(ys)+4*rmed)))]
    ascii_all = []
    for (lk,(y1,y2)) in linie:
        srodki = srodki_rzedow(lk)
        scalenie = est_scalenie(lk)
        kol = zbuduj_kolumny(lk, scalenie)
        t_l, t_w = progi_z_odstepow([c.x for c in kol], mnoz_slowa=1.6)
        slowa = grupuj_litery_i_slowa(kol, t_l, t_w, srodki, mnoz_a=1.35)
        przerwy = []
        for w in slowa:
            for lit in w:
                if len(lit) >= 2: przerwy.append(lit[-1].x - lit[0].x)
        med_przerwa_kol = float(np.median(przerwy)) if przerwy else max(4.0, 0.8*t_l)
        slowa = wymus_podzial_przed_liczba(slowa, srodki, med_przerwa_kol)
        slowa = sklejanie_post(slowa, t_l, t_w, srodki, t_l, med_przerwa_kol, tryb="light", mnoz_a=1.25)
        slowa = odseparuj_koncowe_w(slowa, srodki, t_l, t_l, med_przerwa_kol)
        wiersz_ascii = []
        stan = {"liczbowe":False,"kap_nastepna":False,"kap_oczekiwanie":0,"kap_slowo":False,"nawias_bal":0}
        for wi,w in enumerate(slowa):
            if wi>0:
                nast_cyfra = False
                try:
                    m_nf,_ = maska_z_kontekstem(w,0,srodki,med_przerwa_kol)
                    nast_cyfra = (m_nf in MAPA_CYFR)
                except Exception:
                    pass
            if wi>0 and not (stan.get("liczbowe",False) and nast_cyfra):
                wiersz_ascii.append(" "); stan["liczbowe"] = False
            kan = kanonizuj_kapitalizacje(w, srodki, med_przerwa_kol)
            for m,_kom in kan:
                wiersz_ascii.append(maska_na_tekst(m, stan))
        ascii_all.append("".join(wiersz_ascii))
    ascii_all = filtr_linii(ascii_all)
    return "\n".join(ascii_all)

def pdf_ma_unicode_braille(sciezka: str) -> bool:
    if fitz is None: return False
    try:
        with fitz.open(sciezka) as d:
            for p in d:
                t = p.get_text()
                if any(0x2800 <= ord(ch) <= 0x28FF for ch in t):
                    return True
    except Exception:
        return False
    return False

def pdf_blyskawicznie(sciezka: str) -> str:
    if fitz is None: return ""
    A = []
    with fitz.open(sciezka) as d:
        for p in d:
            txt = p.get_text()
            stan = {"liczbowe":False,"kap_nastepna":False,"kap_oczekiwanie":0,"kap_slowo":False,"nawias_bal":0}
            buf = []
            i, n = 0, len(txt)
            while i < n:
                ch = txt[i]; code = ord(ch)
                if 0x2800 <= code <= 0x283F:
                    m = code - 0x2800
                    if m == (ZNAK_KAPITAL & 0x3F):
                        if i+1 < n and ord(txt[i+1]) == (0x2800 + (ZNAK_KAPITAL & 0x3F)):
                            stan["kap_slowo"] = True; stan["kap_nastepna"] = False; i += 2; continue
                        else:
                            stan["kap_nastepna"] = True; i += 1; continue
                    buf.append(maska_na_tekst(m, stan)); i += 1; continue
                if 0x2840 <= code <= 0x28FF:
                    buf.append("?"); i += 1; continue
                if stan.get("kap_slowo") and ch in " \t\r\n\u00A0-–—,.;:!?()[]{}\"'…/\\":
                    stan["kap_slowo"] = False
                buf.append(ch.upper() if (stan.get("kap_slowo") and ch.isalpha()) else ch); i += 1
            A.append("".join(buf))
    return "\n".join(A)

def pdf_na_obrazy(sciezka: str, dpi: int=300) -> List[np.ndarray]:
    if fitz is None: return []
    obrazy = []
    with fitz.open(sciezka) as doc:
        for p in doc:
            mat = fitz.Matrix(dpi/72.0, dpi/72.0)
            pix = p.get_pixmap(matrix=mat, alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            obrazy.append(img)
    return obrazy

def rozpoznaj_sciezke(sciezka: str) -> str:
    ext = os.path.splitext(sciezka)[1].lower()
    if ext == ".pdf":
        if pdf_ma_unicode_braille(sciezka):
            return pdf_blyskawicznie(sciezka)
        obrazy = pdf_na_obrazy(sciezka)
        A = []
        for img in obrazy:
            A.append(rozpoznaj_obraz(img))
        return "\n".join([s for s in A if s.strip()])
    else:
        img = cv2.imread(sciezka, cv2.IMREAD_COLOR)
        if img is None: return ""
        return rozpoznaj_obraz(img)

def main():
    if len(sys.argv) < 2:
        print("Użycie: python detekcja_i_translacja.py <ścieżka_do_png_jpg_pdf>")
        sys.exit(1)
    sc = sys.argv[1]
    if not os.path.exists(sc):
        print(f"Brak pliku: {sc}", file=sys.stderr); sys.exit(2)
    print(rozpoznaj_sciezke(sc))

if __name__ == "__main__":
    main()
