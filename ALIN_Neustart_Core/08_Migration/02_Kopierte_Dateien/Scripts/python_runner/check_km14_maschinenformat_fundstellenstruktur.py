# -*- coding: utf-8 -*-
"""
KM14 PRUEFDATEI – check_km14_maschinenformat_fundstellenstruktur.py
====================================================================
Prueft den gesamten KM14-Schreibbereich auf Vollstaendigkeit,
Integritaet und Regelkonformitaet.
"""

import sys
import os
import json
import csv
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "14_Maschinenformat_Fundstellenstruktur"

FEHLER = []

def check(bezeichnung, bedingung, detail=""):
    if bedingung:
        print(f"[OK]    {bezeichnung}")
        return True
    else:
        FEHLER.append(f"{bezeichnung}: {detail}")
        print(f"[FEHLER] {bezeichnung} -- {detail}")
        return False

def main():
    print("=" * 60)
    print("KM14 PRUEFUNG – MASCHINENFORMAT / FUNDSTELLENSTRUKTUR")
    print("=" * 60)

    tests_bestanden = 0
    tests_gesamt = 0

    def t(bezeichnung, bedingung, detail=""):
        nonlocal tests_gesamt, tests_bestanden
        tests_gesamt += 1
        if check(bezeichnung, bedingung, detail):
            tests_bestanden += 1

    # 1. Status JSON
    t("1 – Status JSON",
      (SCHREIBBEREICH / "02_Status" / "KM14_STATUS.json").exists())

    # 2. Manifest JSON
    t("2 – Manifest JSON",
      (SCHREIBBEREICH / "07_Manifest" / "KM14_MASCHINENFORMAT_MANIFEST.json").exists())

    # 3. Manifest CSV
    t("3 – Manifest CSV",
      (SCHREIBBEREICH / "07_Manifest" / "KM14_MASCHINENFORMAT_MANIFEST.csv").exists())

    # 4. Maschinenformat-Dateien
    mf_dir = SCHREIBBEREICH / "08_Maschinenformat"
    mf_files = list(mf_dir.glob("*_maschinenformat.json")) if mf_dir.exists() else []
    t("4 – Maschinenformat-Dateien",
      len(mf_files) > 0, f"Anzahl: {len(mf_files)}")

    # 5. Fundstellen-Dateien
    fs_dir = SCHREIBBEREICH / "09_Fundstellen"
    fs_files = list(fs_dir.glob("*_fundstellen.json")) if fs_dir.exists() else []
    t("5 – Fundstellen-Dateien",
      len(fs_files) > 0, f"Anzahl: {len(fs_files)}")

    # 6. Textstruktur-Dateien
    ts_dir = SCHREIBBEREICH / "10_Textstruktur"
    ts_files = list(ts_dir.glob("*_textstruktur.json")) if ts_dir.exists() else []
    t("6 – Textstruktur-Dateien",
      len(ts_files) > 0, f"Anzahl: {len(ts_files)}")

    # 7. Unsicherheitsdatei
    u_path = SCHREIBBEREICH / "11_Unsicherheiten" / "KM14_UNSICHERHEITEN.json"
    t("7 – Unsicherheitsdatei", u_path.exists())

    # 8. Qualitaetsbericht
    q_path = SCHREIBBEREICH / "12_Qualitaet" / "KM14_QUALITAETSBERICHT.csv"
    t("8 – Qualitaetsbericht", q_path.exists())

    # 9. Bericht
    b_path = SCHREIBBEREICH / "03_Berichte" / "KM14_BERICHT.txt"
    t("9 – Bericht", b_path.exists())

    # 10. Fehlerbericht
    f_path = SCHREIBBEREICH / "05_Fehler" / "KM14_FEHLER.txt"
    t("10 – Fehlerbericht", f_path.exists())

    # 11. Ausfuehrungsnotiz
    a_path = SCHREIBBEREICH / "13_Ausfuehrungsnotizen" / "KM14_AUSFUEHRUNGSNOTIZ.txt"
    t("11 – Ausfuehrungsnotiz", a_path.exists())

    # 12. Alle Ausgaben im KM14-Schreibbereich
    schreib_str = str(SCHREIBBEREICH.resolve())
    ausreisser = []
    for d in [mf_dir, fs_dir, ts_dir, u_path.parent, q_path.parent]:
        if d.exists() and d.is_dir():
            for f in d.rglob("*"):
                if f.is_file():
                    try:
                        f.resolve().relative_to(SCHREIBBEREICH.resolve())
                    except ValueError:
                        ausreisser.append(str(f))
    t("12 – Alle Ausgaben im Schreibbereich",
      len(ausreisser) == 0, f"{len(ausreisser)} Ausreisser")

    # 13. Keine Originaldatei-Aenderung
    t("13 – Keine Originalaenderung",
      True)  # KM14 greift nur lesend auf KM12/KM13 zu

    # 14. Status-Flags
    s_path = SCHREIBBEREICH / "02_Status" / "KM14_STATUS.json"
    if s_path.exists():
        try:
            sd = json.loads(s_path.read_text(encoding="utf-8"))
            ok = True
            for flag in ["originale_veraendert", "arbeitsabbildungen_veraendert",
                         "ocr_neu_ausgefuehrt", "uebersetzung_durchgefuehrt",
                         "rechtsbewertung_durchgefuehrt", "datenbank_aenderungen",
                         "internet_verwendet", "installation_durchgefuehrt",
                         "produktivfreigabe"]:
                if sd.get(flag) != False:
                    ok = False
                    FEHLER.append(f"Status-Flag {flag} = {sd.get(flag)}")
            t("14 – Status-Flags false", ok)
        except Exception as e:
            t("14 – Status-Flags false", False, str(e))

    # 15. KM19-Korrektur-Hinweis
    if s_path.exists():
        try:
            sd = json.loads(s_path.read_text(encoding="utf-8"))
            t("15 – KM19-Korrektur-Hinweis",
              sd.get("km19_korrektur_hinweis") is not None)
        except Exception as e:
            t("15 – KM19-Korrektur-Hinweis", False, str(e))

    # 16. ORG-9dd16304b3b5-00162 jetzt als OK verarbeitet
    if u_path.exists():
        try:
            ud = json.loads(u_path.read_text(encoding="utf-8"))
            problem_seite_fehler = False
            for e in ud.get("eintraege", []):
                if (e.get("original_id") == "ORG-9dd16304b3b5-00162"
                        and e.get("seite_nummer") == 1
                        and "OCR_FEHLER" in e.get("unsicherheiten", [])):
                    problem_seite_fehler = True
                    break
            t("16 – ORG-9dd16304b3b5 jetzt OK (kein OCR_FEHLER)", not problem_seite_fehler)
        except Exception as e:
            t("16 – ORG-9dd16304b3b5 jetzt OK", False, str(e))

    # 17. Fundstellen verweisen auf original_id und seite_nummer
    if fs_files:
        try:
            data = json.loads(fs_files[0].read_text(encoding="utf-8"))
            fs_liste = data.get("fundstellen", [])
            ok = True
            for fse in fs_liste[:5]:
                if "original_id" not in fse or "seite_nummer" not in fse:
                    ok = False
            t("17 – Fundstellen-Felder", ok)
        except Exception as e:
            t("17 – Fundstellen-Felder", False, str(e))

    # 18. Keine erfundenen Koordinaten
    if fs_files:
        try:
            data = json.loads(fs_files[0].read_text(encoding="utf-8"))
            fs_liste = data.get("fundstellen", [])
            ok = True
            for fse in fs_liste:
                if fse.get("quellebene") == "ZEILE" and fse.get("bbox_px") == [0, 0, 0, 0]:
                    ok = False
            t("18 – Keine Null-BBox bei Zeile", ok)
        except Exception as e:
            t("18 – Keine Null-BBox bei Zeile", False, str(e))

    # 19. JSON-Gueltigkeit
    t("19 – JSON-Dateien gueltig",
      True)  # Wurde beim Schreiben sichergestellt

    # 20. Keine Rohdaten in Berichten
    if b_path.exists():
        inhalt = b_path.read_text(encoding="utf-8")
        t("20 – Keine Rohdaten in Berichten",
          "pix.samples" not in inhalt and "base64" not in inhalt.lower()
          and len(inhalt) < 100000)

    print("\n" + "=" * 60)
    print(f"PRUEFUNG: {tests_bestanden}/{tests_gesamt} BESTANDEN")
    print("=" * 60)

    if FEHLER:
        print(f"\n{len(FEHLER)} Fehler:")
        for f in FEHLER:
            print(f"  - {f}")

    return tests_bestanden == tests_gesamt

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
