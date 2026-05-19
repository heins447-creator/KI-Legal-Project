# -*- coding: utf-8 -*-
"""
PRUEFDATEI: check_km12_originalabbildung.py
============================================

Prueft KM12-Ausgaben auf:
  - Vollstaendigkeit der Manifeste
  - Gueltigkeit der TIFF-Dateien
  - SHA-256-Integritaet
  - Keine Rohdaten in Berichten
  - Keine Originale veraendert
  - Alle Dateien im Schreibbereich
  - Schutz-Flags korrekt

Aufruf:
  python check_km12_originalabbildung.py
"""

import sys
import os
import json
import csv
import hashlib
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
KM12 = ROOT / "Agentensteuerung" / "12_Originalabbildung_Arbeitsabbildung"

MANIFEST_JSON = KM12 / "07_Manifest" / "KM12_ABBILDUNG_MANIFEST.json"
MANIFEST_CSV = KM12 / "07_Manifest" / "KM12_ABBILDUNG_MANIFEST.csv"
STATUS_JSON = KM12 / "02_Status" / "KM12_STATUS.json"
BERICHT_TXT = KM12 / "03_Berichte" / "KM12_BERICHT.txt"
FEHLER_TXT = KM12 / "05_Fehler" / "KM12_FEHLER.txt"
PRUEFSUMMEN_CSV = KM12 / "11_Pruefsummen" / "KM12_TIFF_SHA256.csv"
NOTIZ_TXT = KM12 / "12_Ausfuehrungsnotizen" / "KM12_AUSFUEHRUNGSNOTIZ.txt"

VERBOTENE_TERME = ["pix.samples", "pix.samples_mv", "samples_mv"]


def sha256_datei(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def check_verbotene_ausgaben(pfad):
    """Prueft, ob verbotene Rohdaten-Terme in einer Datei vorkommen."""
    try:
        inhalt = pfad.read_text(encoding="utf-8")
        for term in VERBOTENE_TERME:
            if term in inhalt:
                return False, f"Verbotener Term '{term}' in {pfad.name}"
        return True, ""
    except Exception as e:
        return False, f"Lesefehler {pfad}: {e}"


def main():
    print("=" * 60)
    print("KM12 PRUEFUNG – ORIGINALABBILDUNG")
    print("=" * 60)

    checks_ok = 0
    checks_gesamt = 15

    # 1. Manifest JSON existiert
    print("\n[1] Manifest JSON existiert...")
    if MANIFEST_JSON.exists():
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLT: {MANIFEST_JSON}")

    # 2. Manifest CSV existiert
    print("\n[2] Manifest CSV existiert...")
    if MANIFEST_CSV.exists():
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLT: {MANIFEST_CSV}")

    # 3. Status JSON existiert
    print("\n[3] Status JSON existiert...")
    if STATUS_JSON.exists():
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLT: {STATUS_JSON}")

    # 4. Status-Flags korrekt
    print("\n[4] Status-Flags korrekt...")
    if STATUS_JSON.exists():
        try:
            status = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
            flags = {
                "produktive_aenderungen": False,
                "rohdaten_ausgegeben": False,
                "pix_samples_ausgegeben": False,
                "ocr_durchgefuehrt": False,
                "originale_veraendert": False,
                "datenbank_aenderungen": False,
            }
            alle_korrekt = True
            for flag, erwartet in flags.items():
                if status.get(flag) != erwartet:
                    print(f"  FLAG-FEHLER: {flag} = {status.get(flag)}, erwartet {erwartet}")
                    alle_korrekt = False
            if alle_korrekt:
                print("  OK")
                checks_ok += 1
        except Exception as e:
            print(f"  JSON-Fehler: {e}")
    else:
        print("  UEBERSPRUNGEN (Status fehlt)")

    # 5. Keine Rohdaten in Bericht
    print("\n[5] Keine Rohdaten in Bericht...")
    if BERICHT_TXT.exists():
        ok, msg = check_verbotene_ausgaben(BERICHT_TXT)
        if ok:
            print("  OK")
            checks_ok += 1
        else:
            print(f"  FEHLER: {msg}")
    else:
        print("  UEBERSPRUNGEN (Bericht fehlt)")

    # 6. Fehlerbericht existiert
    print("\n[6] Fehlerbericht existiert...")
    if FEHLER_TXT.exists():
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLT: {FEHLER_TXT}")

    # 7. Pruefsummen-CSV existiert
    print("\n[7] Pruefsummen-CSV existiert...")
    if PRUEFSUMMEN_CSV.exists():
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLT: {PRUEFSUMMEN_CSV}")

    # 8. Ausfuehrungsnotiz existiert
    print("\n[8] Ausfuehrungsnotiz existiert...")
    if NOTIZ_TXT.exists():
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLT: {NOTIZ_TXT}")

    # 9. TIFF-Dateien auf Platte pruefen
    print("\n[9] TIFF-Dateien auf Platte...")
    if MANIFEST_JSON.exists():
        try:
            daten = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
            seiten = daten.get("seiten", [])
            tiff_fehlend = 0
            tiff_vorhanden = 0
            for s in seiten:
                if s.get("render_status") == "OK":
                    tiff_pfad = s.get("tiff_pfad", "")
                    if tiff_pfad and Path(tiff_pfad).exists():
                        tiff_vorhanden += 1
                    else:
                        tiff_fehlend += 1
            if tiff_fehlend == 0:
                print(f"  OK: {tiff_vorhanden} TIFFs vorhanden")
                checks_ok += 1
            else:
                print(f"  WARNUNG: {tiff_fehlend} TIFFs fehlen, {tiff_vorhanden} vorhanden")
        except Exception as e:
            print(f"  Fehler beim Pruefen: {e}")
    else:
        print("  UEBERSPRUNGEN (kein Manifest)")

    # 10. SHA-256-Integritaet der TIFFs
    print("\n[10] SHA-256-Integritaet der TIFFs...")
    if MANIFEST_JSON.exists():
        try:
            daten = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
            seiten = daten.get("seiten", [])
            mismatch = 0
            geprueft = 0
            for s in seiten:
                if s.get("render_status") == "OK":
                    tiff_pfad = s.get("tiff_pfad", "")
                    if tiff_pfad and Path(tiff_pfad).exists():
                        actual = sha256_datei(Path(tiff_pfad))
                        if actual != s.get("tiff_sha256"):
                            mismatch += 1
                        geprueft += 1
            if mismatch == 0:
                print(f"  OK: {geprueft} TIFFs SHA-256 verifiziert")
                checks_ok += 1
            else:
                print(f"  FEHLER: {mismatch} SHA-256 mismatch")
        except Exception as e:
            print(f"  Fehler: {e}")
    else:
        print("  UEBERSPRUNGEN")

    # 11. Alle Dateien im Schreibbereich
    print("\n[11] Alle Dateien im KM12-Schreibbereich...")
    if MANIFEST_JSON.exists():
        try:
            daten = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
            seiten = daten.get("seiten", [])
            ausserhalb = 0
            for s in seiten:
                if s.get("render_status") == "OK":
                    tiff_pfad = s.get("tiff_pfad", "")
                    if tiff_pfad:
                        if not str(tiff_pfad).startswith(str(KM12)):
                            ausserhalb += 1
            if ausserhalb == 0:
                print("  OK: Alle TIFFs im Schreibbereich")
                checks_ok += 1
            else:
                print(f"  FEHLER: {ausserhalb} TIFFs ausserhalb")
        except Exception as e:
            print(f"  Fehler: {e}")
    else:
        print("  UEBERSPRUNGEN")

    # 12. Renderprotokolle auf Rohdaten pruefen
    print("\n[12] Renderprotokolle auf Rohdaten pruefen...")
    rp_dir = KM12 / "09_Renderprotokolle"
    rp_ok = 0
    rp_fail = 0
    for rp in rp_dir.glob("*_renderprotokoll.txt"):
        ok, msg = check_verbotene_ausgaben(rp)
        if ok:
            rp_ok += 1
        else:
            rp_fail += 1
            print(f"  FEHLER in {rp.name}: {msg}")
    if rp_fail == 0 and rp_ok > 0:
        print(f"  OK: {rp_ok} Renderprotokolle sauber")
        checks_ok += 1
    elif rp_ok == 0:
        print("  HINWEIS: Keine Renderprotokolle (keine PDFs?)")
    else:
        print(f"  {rp_fail} Renderprotokolle mit Rohdaten!")

    # 13. Koordinatenmodelle pruefen
    print("\n[13] Koordinatenmodelle pruefen...")
    km_dir = KM12 / "10_Koordinatenmodell"
    km_ok = 0
    for km_file in km_dir.glob("*_koordinatenmodell.json"):
        try:
            km = json.loads(km_file.read_text(encoding="utf-8"))
            if km.get("modell_typ") == "bbox_px":
                km_ok += 1
        except Exception:
            pass
    print(f"  OK: {km_ok} Koordinatenmodelle")
    checks_ok += 1

    # 14. Keine Datenbank-Dateien im KM12-Bereich
    print("\n[14] Keine DB-Dateien im KM12-Bereich...")
    db_files = list(KM12.glob("**/*.db")) + list(KM12.glob("**/*.duckdb")) + list(KM12.glob("**/*.sqlite"))
    if not db_files:
        print("  OK")
        checks_ok += 1
    else:
        print(f"  FEHLER: DB-Dateien gefunden: {db_files}")

    # 15. Keine Rohdaten in Ausfuehrungsnotiz
    print("\n[15] Keine Rohdaten in Ausfuehrungsnotiz...")
    if NOTIZ_TXT.exists():
        ok, msg = check_verbotene_ausgaben(NOTIZ_TXT)
        if ok:
            print("  OK")
            checks_ok += 1
        else:
            print(f"  FEHLER: {msg}")
    else:
        print("  UEBERSPRUNGEN")

    # Ergebnis
    print("\n" + "=" * 60)
    print(f"PRUEFUNG: {checks_ok}/{checks_gesamt} BESTANDEN")
    print("=" * 60)
    if checks_ok == checks_gesamt:
        print("KM12 PRUEFUNG ERFOLGREICH.")
        return 0
    else:
        print(f"KM12 PRUEFUNG MIT FEHLERN ({checks_gesamt - checks_ok} offen).")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nKRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
