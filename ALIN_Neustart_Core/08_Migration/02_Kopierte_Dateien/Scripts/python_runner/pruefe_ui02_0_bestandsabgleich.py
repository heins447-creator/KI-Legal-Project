#!/usr/bin/env python3
"""Pruefscript fuer UI02-0 Bestandsabgleich Tuerschwelle"""
import sys, json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung/UI02_0_Bestandsabgleich_Tuerschwelle"

FEHLER = 0
WARNUNGEN = 0
PRUEFUNGEN = 0

def pruefe(bez, bed, kritisch=True):
    global FEHLER, WARNUNGEN, PRUEFUNGEN
    PRUEFUNGEN += 1
    if bed:
        print(f"  [OK] {bez}")
    else:
        if kritisch:
            FEHLER += 1
            print(f"  [FEHLER] {bez}")
        else:
            WARNUNGEN += 1
            print(f"  [WARNUNG] {bez}")

PFADE = {
    "Status": "02_Status/UI02_0_STATUS.json",
    "Bericht": "03_Berichte/UI02_0_BESTANDSABGLEICH.txt",
    "Matrix JSON": "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.json",
    "Matrix CSV": "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.csv",
    "Luecken JSON": "05_Luecken/UI02_0_LUECKENLISTE.json",
    "Luecken TXT": "05_Luecken/UI02_0_LUECKENLISTE.txt",
    "Modulkarte": "06_Modulkarte/UI02_0_MODULKARTE.json",
    "UI01 Auswertung": "07_UI01_Auswertung/UI02_0_UI01_AUSWERTUNG.json",
    "Empfehlung": "08_Empfehlung/UI02_0_NAECHSTER_AUFTRAG_UI02.txt",
    "Fehler": "05_Fehler/UI02_0_FEHLER.txt",
    "Manifest": "07_Manifest/UI02_0_MANIFEST.json",
}

print("UI02-0 PRUEFUNG =========================================")
for bez, rel in PFADE.items():
    p = SCHREIBBEREICH / rel
    pruefe(f"Datei {bez}: {rel}", p.exists())

# Inhaltlich pruefen
status_p = SCHREIBBEREICH / "02_Status/UI02_0_STATUS.json"
if status_p.exists():
    status = json.loads(status_p.read_text(encoding="utf-8-sig"))
    pruefe("Status.modul == UI02_0", status.get("modul") == "UI02_0")
    pruefe("Status.luecken_anzahl > 0", status.get("luecken_anzahl", 0) > 0)
    pruefe("Status.dokumente_gefunden >= 3", status.get("dokumente_gefunden", 0) >= 3)
    pruefe("Status.grenzen_eingehalten == True", status.get("grenzen_eingehalten") == True)

matrix_p = SCHREIBBEREICH / "04_Wiederverwendung/UI02_0_WIEDERVERWENDUNGSMATRIX.json"
if matrix_p.exists():
    matrix_d = json.loads(matrix_p.read_text(encoding="utf-8-sig"))
    matrix = matrix_d.get("matrix", [])
    pruefe(f"Matrix hat {len(matrix)} Eintraege (>=15)", len(matrix) >= 15)

luecken_p = SCHREIBBEREICH / "05_Luecken/UI02_0_LUECKENLISTE.json"
if luecken_p.exists():
    luecken_d = json.loads(luecken_p.read_text(encoding="utf-8-sig"))
    luecken = luecken_d.get("luecken", [])
    pruefe(f"Lueckenliste hat {len(luecken)} Eintraege (>=5)", len(luecken) >= 5)

modul_p = SCHREIBBEREICH / "06_Modulkarte/UI02_0_MODULKARTE.json"
if modul_p.exists():
    modul_d = json.loads(modul_p.read_text(encoding="utf-8-sig"))
    mk = modul_d.get("modulkarte", {})
    pruefe(f"Modulkarte hat {len(mk)} Module (>=5)", len(mk) >= 5)
    pruefe("KM12 in Modulkarte", "KM12" in mk)
    pruefe("KM14 in Modulkarte", "KM14" in mk)
    pruefe("UI01 in Modulkarte", "UI01" in mk)

print(f"\nPruefungen: {PRUEFUNGEN}, Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
if FEHLER > 0:
    print("PRUEFUNG NICHT BESTANDEN")
    sys.exit(1)
else:
    print("PRUEFUNG BESTANDEN")
    sys.exit(0)
