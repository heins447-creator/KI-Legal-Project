# -*- coding: utf-8 -*-
"""
KM13 PRUEFDATEI – check_km13_ocr_pipeline.py
=============================================
Prueft den gesamten KM13-Schreibbereich auf Vollstaendigkeit,
Integritaet und Regelkonformitaet.
"""

import sys
import os
import json
import csv
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "13_OCR_Pipeline"
KM12_BEREICH = ROOT / "Agentensteuerung" / "12_Originalabbildung_Arbeitsabbildung"

FEHLER = []
WARNUNGEN = []

def check(bezeichnung, bedingung, detail=""):
    """Hilfsfunktion fuer einzelne Pruefungen."""
    if bedingung:
        print(f"[OK]    {bezeichnung}")
        return True
    else:
        FEHLER.append(f"{bezeichnung}: {detail}")
        print(f"[FEHLER] {bezeichnung} -- {detail}")
        return False

def main():
    print("=" * 60)
    print("KM13 PRUEFUNG – OCR-PIPELINE")
    print("=" * 60)

    tests_bestanden = 0
    tests_gesamt = 0

    # 1. Manifest JSON existiert
    tests_gesamt += 1
    print(f"\n[1] Manifest JSON existiert...")
    mj = SCHREIBBEREICH / "07_Manifest" / "KM13_OCR_MANIFEST.json"
    if check("Manifest JSON", mj.exists()):
        tests_bestanden += 1

    # 2. Manifest CSV existiert
    tests_gesamt += 1
    print(f"\n[2] Manifest CSV existiert...")
    mc = SCHREIBBEREICH / "07_Manifest" / "KM13_OCR_MANIFEST.csv"
    if check("Manifest CSV", mc.exists()):
        tests_bestanden += 1

    # 3. Status JSON existiert
    tests_gesamt += 1
    print(f"\n[3] Status JSON existiert...")
    st = SCHREIBBEREICH / "02_Status" / "KM13_STATUS.json"
    if check("Status JSON", st.exists()):
        tests_bestanden += 1

    # 4. Status-Flags korrekt
    tests_gesamt += 1
    print(f"\n[4] Status-Flags korrekt...")
    if st.exists():
        try:
            sd = json.loads(st.read_text(encoding="utf-8"))
            ok = True
            for flag in ["originaldateien_verwendet", "datenbank_aenderungen",
                         "rohdaten_ausgegeben", "ocr_volltext_ausgegeben",
                         "uebersetzung_erzeugt", "rechtsbewertung_vorgenommen"]:
                if sd.get(flag) != False:
                    ok = False
                    FEHLER.append(f"Status-Flag {flag} ist {sd.get(flag)}, nicht False")
            if check("Status-Flags", ok):
                tests_bestanden += 1
        except Exception as e:
            check("Status-Flags", False, str(e))

    # 5. Keine Rohdatenbegriffe in Berichten
    tests_gesamt += 1
    print(f"\n[5] Keine Rohdaten in Berichten...")
    bericht = SCHREIBBEREICH / "03_Berichte" / "KM13_BERICHT.txt"
    if bericht.exists():
        inhalt = bericht.read_text(encoding="utf-8")
        ok = "pix.samples" not in inhalt and "samples" not in inhalt.lower()
        if check("Keine Rohdaten im Bericht", ok):
            tests_bestanden += 1
    else:
        check("Keine Rohdaten im Bericht", False, "Bericht fehlt")

    # 6. Fehlerbericht existiert
    tests_gesamt += 1
    print(f"\n[6] Fehlerbericht existiert...")
    fb = SCHREIBBEREICH / "05_Fehler" / "KM13_FEHLER.txt"
    if check("Fehlerbericht", fb.exists()):
        tests_bestanden += 1

    # 7. Qualitaetswerte existieren
    tests_gesamt += 1
    print(f"\n[7] Qualitaetswerte existieren...")
    qw = SCHREIBBEREICH / "13_Qualitaetswerte" / "KM13_QUALITAETSWERTE.csv"
    if check("Qualitaetswerte", qw.exists()):
        tests_bestanden += 1

    # 8. Ausfuehrungsnotiz existiert
    tests_gesamt += 1
    print(f"\n[8] Ausfuehrungsnotiz existiert...")
    an = SCHREIBBEREICH / "14_Ausfuehrungsnotizen" / "KM13_AUSFUEHRUNGSNOTIZ.txt"
    if check("Ausfuehrungsnotiz", an.exists()):
        tests_bestanden += 1

    # 9. Manifest-Eintraege haben JSON-Struktur
    tests_gesamt += 1
    print(f"\n[9] JSON-Struktur vollstaendig...")
    if mj.exists():
        try:
            data = json.loads(mj.read_text(encoding="utf-8"))
            ergebnisse = data.get("ergebnisse", [])
            pflichtfelder = ["original_id", "seite_nummer", "ocr_status", "zeichenanzahl",
                           "wortanzahl", "text_pfad", "json_pfad"]
            fehlende = []
            for e in ergebnisse:
                for feld in pflichtfelder:
                    if feld not in e:
                        fehlende.append(f"Eintrag {e.get('original_id','?')} Seite {e.get('seite_nummer','?')}: {feld} fehlt")
            ok = len(fehlende) == 0
            if check(f"JSON-Struktur ({len(ergebnisse)} Eintraege)", ok, "; ".join(fehlende[:5])):
                tests_bestanden += 1
        except Exception as e:
            check("JSON-Struktur", False, str(e))

    # 10. TIFF-SHA-256 gegen KM12 geprueft (wurde bei Verarbeitung gemacht)
    tests_gesamt += 1
    print(f"\n[10] TIFF-SHA-256-Referenz zu KM12...")
    km12_manifest = KM12_BEREICH / "07_Manifest" / "KM12_ABBILDUNG_MANIFEST.json"
    if km12_manifest.exists() and mj.exists():
        try:
            km12_data = json.loads(km12_manifest.read_text(encoding="utf-8"))
            km13_data = json.loads(mj.read_text(encoding="utf-8"))
            km12_hashes = {}
            for s in km12_data.get("seiten", []):
                oid = s.get("original_id", "")
                sn = s.get("seite_nummer", 0)
                km12_hashes[(oid, sn)] = s.get("tiff_sha256", "")

            mismatch = 0
            for e in km13_data.get("ergebnisse", []):
                oid = e.get("original_id", "")
                sn = e.get("seite_nummer", 0)
                km12_hash = km12_hashes.get((oid, sn), "")
                km13_hash = e.get("tiff_sha256", "")
                if km12_hash and km13_hash and km12_hash != km13_hash:
                    mismatch += 1
            ok = mismatch == 0
            if check(f"TIFF-SHA-256-Referenz ({len(km13_data.get('ergebnisse',[]))} Seiten)", ok,
                     f"{mismatch} Mismatch(es)"):
                tests_bestanden += 1
        except Exception as e:
            check("TIFF-SHA-256-Referenz", False, str(e))
    else:
        check("TIFF-SHA-256-Referenz", False, "Manifest fehlt")

    # 11. Keine Ausgaben ausserhalb KM13 (ausser lesender KM12-Zugriff)
    tests_gesamt += 1
    print(f"\n[11] Ausgaben im KM13-Schreibbereich...")
    schreibbereich_str = str(SCHREIBBEREICH.resolve())
    ausreisser = []
    for d in [SCHREIBBEREICH / "08_OCR_Text", SCHREIBBEREICH / "09_OCR_JSON",
              SCHREIBBEREICH / "10_OCR_HOCR", SCHREIBBEREICH / "11_OCR_TSV",
              SCHREIBBEREICH / "12_OCR_Protokolle"]:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file():
                    try:
                        f.resolve().relative_to(SCHREIBBEREICH.resolve())
                    except ValueError:
                        ausreisser.append(str(f))
    ok = len(ausreisser) == 0
    if check(f"Alle Ausgaben im Schreibbereich", ok, f"{len(ausreisser)} Ausreisser"):
        tests_bestanden += 1

    # 12. Keine Originalpfade als OCR-Eingang
    tests_gesamt += 1
    print(f"\n[12] Keine Originalpfade als OCR-Eingang...")
    if mj.exists():
        try:
            data = json.loads(mj.read_text(encoding="utf-8"))
            original_pfade_gefunden = 0
            for e in data.get("ergebnisse", []):
                tiff = e.get("tiff_pfad", "")
                # KM12-TIFFs sind unter 08_Arbeitsabbildungen
                if "original" in tiff.lower() and "arbeitsabbildung" not in tiff.lower():
                    original_pfade_gefunden += 1
            ok = original_pfade_gefunden == 0
            if check("Keine Originalpfade", ok, f"{original_pfade_gefunden} gefunden"):
                tests_bestanden += 1
        except Exception as e:
            check("Keine Originalpfade", False, str(e))

    # 13. Keine DB-Dateien im KM13-Bereich
    tests_gesamt += 1
    print(f"\n[13] Keine DB-Dateien...")
    db_files = list(SCHREIBBEREICH.glob("**/*.db")) + list(SCHREIBBEREICH.glob("**/*.sqlite"))
    ok = len(db_files) == 0
    if check(f"Keine DB-Dateien", ok, f"{len(db_files)} gefunden"):
        tests_bestanden += 1

    # 14. Keine grossen Volltextbloecke in Berichten
    tests_gesamt += 1
    print(f"\n[14] Keine Volltextbloecke in Berichten...")
    ok = True
    for bericht_pfad in [bericht, fb, an]:
        if bericht_pfad.exists():
            inhalt = bericht_pfad.read_text(encoding="utf-8")
            # Pruefe auf typische OCR-Volltextmengen (sehr lange Zeilen)
            for line in inhalt.split("\n"):
                if len(line) > 500:
                    ok = False
                    FEHLER.append(f"Lange Zeile in {bericht_pfad.name}: {len(line)} Zeichen")
                    break
    if check("Keine Volltextbloecke", ok):
        tests_bestanden += 1

    # 15. Schutzflags korrekt gesetzt
    tests_gesamt += 1
    print(f"\n[15] Schutzflags in Status...")
    if st.exists():
        try:
            sd = json.loads(st.read_text(encoding="utf-8"))
            schutz_ok = (
                sd.get("rohdaten_ausgegeben") == False and
                sd.get("ocr_volltext_ausgegeben") == False and
                sd.get("originaldateien_verwendet") == False
            )
            if check("Schutzflags", schutz_ok):
                tests_bestanden += 1
        except Exception as e:
            check("Schutzflags", False, str(e))

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
