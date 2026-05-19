# -*- coding: utf-8 -*-
"""
CORE-21 ARBEITSINDEX
Umschalt- und Arbeitsindex für ALIN_Neustart_Core

Liest:
- CORE17_kopierte_dateien_manifest.json (311 Einträge)
- CORE19_reste_archiv_sperrplan.json
- CORE14_auswertung.csv
- CORE20_MASTER_UMBAU_BERICHT.txt

Erzeugt:
- CORE21_arbeitsindex.json (Arbeitsindex mit Kategorien)
- CORE21_ARBEITSINDEX_BERICHT.txt (Textbericht)
- Git-Status-Protokoll
"""

import json
import csv
import sys
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ── Konfiguration ───────────────────────────────────────────────────────────
PROJEKT_ROOT = Path("I:/KI_Legal_Project")

MANIFEST_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json"
SPERRPLAN_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE19_reste_archiv_sperrplan.json"
AUSWERTUNG_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.csv"
MASTER_BERICHT_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/Reports/CORE20_MASTER_UMBAU_BERICHT.txt"

ARBEITSINDEX_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_arbeitsindex.json"
BERICHT_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt"
KONFIG_PFAD = PROJEKT_ROOT / "Config/core21_arbeitsindex_v1.json"

GIT_STATUS_VOR = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_git_status_vor.txt"
GIT_STATUS_NACH = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_git_status_nach.txt"


def zeitstempel():
    return datetime.now(timezone.utc).isoformat()


def sha256_pfad(pfad: Path) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status_ausgeben(ausgabe_pfad: Path):
    """Speichert git status in Datei."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=PROJEKT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        with open(ausgabe_pfad, "w", encoding="utf-8") as f:
            f.write(f"Git-Status: {zeitstempel()}\n")
            f.write(result.stdout if result.stdout else "(keine Änderungen)\n")
            if result.stderr:
                f.write("\nSTDERR:\n" + result.stderr)
    except Exception as e:
        with open(ausgabe_pfad, "w", encoding="utf-8") as f:
            f.write(f"Git-Status-Fehler: {e}\n")


def lade_manifest():
    with open(MANIFEST_PFAD, "r", encoding="utf-8") as f:
        return json.load(f)


def lade_sperrplan():
    with open(SPERRPLAN_PFAD, "r", encoding="utf-8") as f:
        return json.load(f)


def lade_auswertung():
    eintraege = []
    with open(AUSWERTUNG_PFAD, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eintraege.append(row)
    return eintraege


def kategorisiere_manifest_datei(rel_pfad: str) -> str:
    """
    Ordnet eine kopiert Datei einer Kategorie im Arbeitsindex zu.
    """
    p = rel_pfad.lower()
    if ".md" in p and ("dokumentation" in p or "auftrag" in p or "planung" in p):
        return "dokumentation"
    if ".json" in p and ("register" in p or "schema" in p):
        return "register"
    if ".json" in p and ("status" in p or "healthcheck" in p or "resolver" in p):
        return "schema_status"
    if ".py" in p and "scripts" in p:
        return "script"
    if ".ps1" in p:
        return "starter"
    if "bericht" in p or "report" in p or ".txt" in p:
        return "bericht"
    if "migration" in p or "plan" in p:
        return "planung"
    if "config" in p or "profil" in p:
        return "konfiguration"
    if "test" in p or "pruef" in p:
        return "test"
    if "sql" in p:
        return "migration_sql"
    return "sonstige"


def arbeitsindex_bauen():
    manifest = lade_manifest()
    sperrplan = lade_sperrplan()
    auswertung = lade_auswertung()

    # ── 1. Arbeitsbestand aus den 311 kopierten Dateien ─────────────────────
    arbeitsbestand = []
    referenzbestand = []

    for eintrag in manifest.get("kopierte_dateien", []):
        rel_pfad = eintrag["relativer_pfad"]
        ziel_pfad = eintrag["ziel_pfad"]
        kategorie = kategorisiere_manifest_datei(rel_pfad)

        # Prüfe ob Original noch existiert
        original_pfad = PROJEKT_ROOT / rel_pfad
        original_existiert = original_pfad.exists()

        arbeitsbestand.append({
            "relativer_pfad": rel_pfad,
            "kategorie": kategorie,
            "groesse": eintrag["groesse"],
            "sha256": eintrag["sha256"],
            "original_existiert": original_existiert,
            "bemerkung": "aktiv" if original_existiert else "nur in Migration vorhanden"
        })

        referenzbestand.append({
            "relativer_pfad": rel_pfad,
            "ziel_pfad": ziel_pfad,
            "kategorie": kategorie,
            "groesse": eintrag["groesse"],
            "sha256": eintrag["sha256"],
            "bemerkung": "Kopie aus CORE-17, nur Referenz"
        })

    # ── 2. Gesperrte Pfade aus Sperrplan ────────────────────────────────────
    gesperrte_pfade = {
        "gesperrt": [],
        "manuell": [],
        "archiv": [],
        "dublette": [],
        "testrest": [],
        "laufzeit": []
    }

    plaene = sperrplan.get("plaene", {})
    for schluessel, ziel_liste in plaene.items():
        if schluessel in gesperrte_pfade:
            for item in ziel_liste:
                gesperrte_pfade[schluessel].append({
                    "relativer_pfad": item.get("relativer_pfad", ""),
                    "dateiname": item.get("dateiname", ""),
                    "klassifikation": item.get("klassifikation", ""),
                    "zielentscheidung": item.get("zielentscheidung", ""),
                    "begruendung": item.get("begruendung", "")
                })

    # ── 3. Alte und neue Arbeitsbereiche ────────────────────────────────────
    alte_arbeitsbereiche = [
        "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/",
        "ALIN_Neustart_Core/08_Migration/01_Plaene/",
        "ALIN_Neustart_Core/08_Migration/02_Kopierte_Dateien/",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/",
        "Agentensteuerung/",
        "07_Berichte/",
        "10_Tool_Inventar/"
    ]

    neue_arbeitsbereiche = [
        "ALIN_Neustart_Core/00_Dokumentation/",
        "ALIN_Neustart_Core/01_Register/",
        "ALIN_Neustart_Core/02_Statusmodell/",
        "ALIN_Neustart_Core/03_Schnittstellen/",
        "ALIN_Neustart_Core/04_Healthcheck/",
        "ALIN_Neustart_Core/05_Resolver/",
        "ALIN_Neustart_Core/06_Audit_Protokoll/",
        "ALIN_Neustart_Core/10_Update_Ueberwachung/",
        "ALIN_Neustart_Core/12_Dokumentation_Hilfe_Infofelder/",
        "ALIN_Neustart_Core/13_Anforderungen_Abnahme/",
        "ALIN_Neustart_Core/14_Architekturentscheidungen/",
        "ALIN_Neustart_Core/15_Teststrategie/",
        "ALIN_Neustart_Core/23_Import_Export/",
        "ALIN_Neustart_Core/24_Konfigurationsprofile/",
        "ALIN_Neustart_Core/Config/",
        "ALIN_Neustart_Core/Scripts/",
        "ALIN_Neustart_Core/Reports/",
        "Projektplanung/",
        "Scripts/python_runner/",
        "Config/",
        "Database/Migrations/",
        "Windows_App/"
    ]

    # ── 4. Maßgebliche Skripte ──────────────────────────────────────────────
    massgebliche_skripte = []
    for eintrag in arbeitsbestand:
        if eintrag["kategorie"] in ("script", "starter"):
            massgebliche_skripte.append({
                "pfad": eintrag["relativer_pfad"],
                "kategorie": eintrag["kategorie"],
                "bemerkung": "maßgeblicher Bestand"
            })

    # Auch aktuelle Scripts/python_runner/ hinzufügen, die nicht im Manifest sind
    python_runner_dir = PROJEKT_ROOT / "Scripts/python_runner"
    if python_runner_dir.exists():
        for py_file in sorted(python_runner_dir.glob("*.py")):
            rel = str(py_file.relative_to(PROJEKT_ROOT)).replace("\\", "/")
            if not any(m["pfad"] == rel for m in massgebliche_skripte):
                massgebliche_skripte.append({
                    "pfad": rel,
                    "kategorie": "script",
                    "bemerkung": "aktueller Bestand (nicht im Manifest)"
                })

    # ── 5. Empfohlener Start ────────────────────────────────────────────────
    empfohlener_start = {
        "datei": "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
        "bemerkung": "Erste Datei die Roo lesen sollte: Masterauftrag Neustart Core",
        "alternativen": [
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_PROFESSIONELLE_SOFTWARE_KONSTRUKTION.md"
        ]
    }

    # ── 6. Altdateien die nicht mehr direkt benutzt werden ──────────────────
    altdateien_sperre = []
    for schluessel, liste in gesperrte_pfade.items():
        for item in liste[:20]:  # Beispiele, nicht alle 90k
            altdateien_sperre.append({
                "pfad": item["relativer_pfad"],
                "status": schluessel,
                "begruendung": item["begruendung"]
            })

    # ── Arbeitsindex zusammenbauen ──────────────────────────────────────────
    arbeitsindex = {
        "meta": {
            "modul_id": "CORE-21",
            "name": "Umschalt- und Arbeitsindex ALIN_Neustart_Core",
            "version": "1.0.0",
            "zeitstempel": zeitstempel(),
            "produktiv_freigegeben": False,
            "quellen": {
                "manifest": str(MANIFEST_PFAD.relative_to(PROJEKT_ROOT)),
                "sperrplan": str(SPERRPLAN_PFAD.relative_to(PROJEKT_ROOT)),
                "auswertung": str(AUSWERTUNG_PFAD.relative_to(PROJEKT_ROOT)),
                "master_bericht": str(MASTER_BERICHT_PFAD.relative_to(PROJEKT_ROOT))
            }
        },
        "zusammenfassung": {
            "arbeitsbestand_anzahl": len(arbeitsbestand),
            "referenzbestand_anzahl": len(referenzbestand),
            "gesperrt_gesamt": sum(len(v) for v in gesperrte_pfade.values()),
            "massgebliche_skripte": len(massgebliche_skripte),
            "alte_bereiche": len(alte_arbeitsbereiche),
            "neue_bereiche": len(neue_arbeitsbereiche)
        },
        "empfohlener_start": empfohlener_start,
        "arbeitsbestand": arbeitsbestand,
        "referenzbestand": referenzbestand,
        "gesperrte_pfade": gesperrte_pfade,
        "massgebliche_skripte": massgebliche_skripte,
        "alte_arbeitsbereiche": alte_arbeitsbereiche,
        "neue_arbeitsbereiche": neue_arbeitsbereiche,
        "altdateien_sperre_beispiele": altdateien_sperre
    }

    return arbeitsindex


def speichere_json(pfad: Path, daten):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)


def bericht_schreiben(arbeitsindex: dict):
    meta = arbeitsindex["meta"]
    zus = arbeitsindex["zusammenfassung"]
    start = arbeitsindex["empfohlener_start"]

    lines = []
    lines.append("=" * 70)
    lines.append("CORE-21 ARBEITSINDEX-BERICHT")
    lines.append("Umschalt- und Arbeitsindex für ALIN_Neustart_Core")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Modul-ID:      {meta['modul_id']}")
    lines.append(f"Version:       {meta['version']}")
    lines.append(f"Zeitstempel:   {meta['zeitstempel']}")
    lines.append(f"Freigegeben:   {meta['produktiv_freigegeben']}")
    lines.append("")
    lines.append("QUELLEN")
    lines.append("-" * 70)
    for k, v in meta["quellen"].items():
        lines.append(f"  {k:20s} {v}")
    lines.append("")
    lines.append("ZUSAMMENFASSUNG")
    lines.append("-" * 70)
    lines.append(f"  Arbeitsbestand ( aktiv):        {zus['arbeitsbestand_anzahl']:>6d}")
    lines.append(f"  Referenzbestand (Migration):    {zus['referenzbestand_anzahl']:>6d}")
    lines.append(f"  Gesperrte Pfade gesamt:         {zus['gesperrt_gesamt']:>6d}")
    lines.append(f"  Maßgebliche Skripte:            {zus['massgebliche_skripte']:>6d}")
    lines.append(f"  Alte Arbeitsbereiche:           {zus['alte_bereiche']:>6d}")
    lines.append(f"  Neue Arbeitsbereiche:           {zus['neue_bereiche']:>6d}")
    lines.append("")

    # Kategorien im Arbeitsbestand
    kat_counts = {}
    for item in arbeitsindex["arbeitsbestand"]:
        kat_counts[item["kategorie"]] = kat_counts.get(item["kategorie"], 0) + 1
    lines.append("ARBEITSBESTAND KATEGORIEN")
    lines.append("-" * 70)
    for kat in sorted(kat_counts.keys()):
        lines.append(f"  {kat:25s} {kat_counts[kat]:>6d}")
    lines.append("")

    lines.append("EMPFOHLENER START")
    lines.append("-" * 70)
    lines.append(f"  Primär:   {start['datei']}")
    lines.append(f"  Bemerkung: {start['bemerkung']}")
    lines.append("  Alternativen:")
    for alt in start["alternativen"]:
        lines.append(f"    - {alt}")
    lines.append("")

    lines.append("MAßGEBLICHE SKRIPTE (Auswahl)")
    lines.append("-" * 70)
    for skript in arbeitsindex["massgebliche_skripte"][:30]:
        lines.append(f"  [{skript['kategorie']:10s}] {skript['pfad']}")
    if len(arbeitsindex["massgebliche_skripte"]) > 30:
        lines.append(f"  ... und {len(arbeitsindex['massgebliche_skripte'])-30} weitere")
    lines.append("")

    lines.append("ALTE ARBEITSBEREICHE (nicht mehr aktiv bearbeiten)")
    lines.append("-" * 70)
    for bereich in arbeitsindex["alte_arbeitsbereiche"]:
        lines.append(f"  [ALT] {bereich}")
    lines.append("")

    lines.append("NEUE ARBEITSBEREICHE (zukünftige Arbeit)")
    lines.append("-" * 70)
    for bereich in arbeitsindex["neue_arbeitsbereiche"]:
        lines.append(f"  [NEU] {bereich}")
    lines.append("")

    lines.append("GESPERRTE PFADE (Status-Übersicht)")
    lines.append("-" * 70)
    for status, liste in arbeitsindex["gesperrte_pfade"].items():
        lines.append(f"  {status:12s} {len(liste):>7d} Einträge")
    lines.append("")

    lines.append("ALTDATEIEN-SPERRE (Beispiele)")
    lines.append("-" * 70)
    for alt in arbeitsindex["altdateien_sperre_beispiele"][:20]:
        lines.append(f"  [{alt['status']:10s}] {alt['pfad']}")
    lines.append("")

    lines.append("PRÜFUNGEN")
    lines.append("-" * 70)
    ok = (
        zus["arbeitsbestand_anzahl"] == 311
        and zus["referenzbestand_anzahl"] == 311
        and len(arbeitsindex["gesperrte_pfade"]["gesperrt"]) > 0
    )
    lines.append(f"  Arbeitsbestand = 311:           {'OK' if zus['arbeitsbestand_anzahl']==311 else 'FEHLER'}")
    lines.append(f"  Referenzbestand = 311:          {'OK' if zus['referenzbestand_anzahl']==311 else 'FEHLER'}")
    lines.append(f"  Gesperrte Pfade vorhanden:      {'OK' if len(arbeitsindex['gesperrte_pfade']['gesperrt'])>0 else 'WARNUNG'}")
    lines.append(f"  Manifest lesbar:                OK")
    lines.append(f"  Sperrplan lesbar:               OK")
    lines.append(f"  Gesamtprüfung:                  {'BESTANDEN' if ok else 'FEHLER'}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("ENDE CORE-21 ARBEITSINDEX-BERICHT")
    lines.append("=" * 70)

    BERICHT_PFAD.parent.mkdir(parents=True, exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return ok


def konfig_schreiben(arbeitsindex: dict):
    konfig = {
        "modul_id": "CORE-21",
        "version": "1.0.0",
        "zeitstempel": zeitstempel(),
        "arbeitsmodus": {
            "name": "ALIN_Neustart_Core_Arbeitsindex",
            "empfohlener_start": arbeitsindex["empfohlener_start"]["datei"],
            "erste_lese_dateien": arbeitsindex["empfohlener_start"]["alternativen"]
        },
        "bereiche": {
            "aktiv": arbeitsindex["neue_arbeitsbereiche"],
            "referenz": arbeitsindex["alte_arbeitsbereiche"],
            "gesperrt": list(arbeitsindex["gesperrte_pfade"].keys())
        },
        "skript_prioritaet": [
            "Scripts/python_runner/",
            "ALIN_Neustart_Core/Scripts/",
            "Scripts/"
        ],
        "pruefregeln": {
            "manifest_anzahl": 311,
            "arbeitsbestand_muss_manifest_entsprechen": True,
            "keine_dubletten_in_arbeitsbestand": True,
            "gesperrte_pfade_nicht_bearbeiten": True
        }
    }
    KONFIG_PFAD.parent.mkdir(parents=True, exist_ok=True)
    with open(KONFIG_PFAD, "w", encoding="utf-8") as f:
        json.dump(konfig, f, ensure_ascii=False, indent=2)


def main():
    print("[CORE-21] Umschalt- und Arbeitsindex wird erstellt ...")

    # Git-Status vorher
    git_status_ausgeben(GIT_STATUS_VOR)
    print(f"  -> Git-Status vorher: {GIT_STATUS_VOR}")

    # Prüfe Eingabedateien
    fehler = []
    for pfad, name in [
        (MANIFEST_PFAD, "Manifest"),
        (SPERRPLAN_PFAD, "Sperrplan"),
        (AUSWERTUNG_PFAD, "Auswertung"),
        (MASTER_BERICHT_PFAD, "Master-Bericht")
    ]:
        if not pfad.exists():
            fehler.append(f"Eingabedatei fehlt: {name} ({pfad})")

    if fehler:
        print("FEHLER:")
        for f in fehler:
            print(f"  {f}")
        sys.exit(1)

    print("  -> Alle Eingabedateien vorhanden.")

    # Arbeitsindex bauen
    arbeitsindex = arbeitsindex_bauen()
    speichere_json(ARBEITSINDEX_PFAD, arbeitsindex)
    print(f"  -> Arbeitsindex gespeichert: {ARBEITSINDEX_PFAD}")

    # Bericht schreiben
    ok = bericht_schreiben(arbeitsindex)
    print(f"  -> Bericht gespeichert: {BERICHT_PFAD}")

    # Konfig schreiben
    konfig_schreiben(arbeitsindex)
    print(f"  -> Konfiguration gespeichert: {KONFIG_PFAD}")

    # Git-Status nachher
    git_status_ausgeben(GIT_STATUS_NACH)
    print(f"  -> Git-Status nachher: {GIT_STATUS_NACH}")

    if ok:
        print("[CORE-21] ERFOGREICH - Arbeitsindex und Bericht erstellt.")
        sys.exit(0)
    else:
        print("[CORE-21] FEHLER - Pruefung nicht bestanden.")
        sys.exit(2)


if __name__ == "__main__":
    main()
