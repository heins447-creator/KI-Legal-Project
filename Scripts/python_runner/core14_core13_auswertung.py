#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-14 – Auswertung der CORE-13 Altbestand-Inventur
Erstellt Zielentscheidungen fuer jede Datei auf Basis der CORE-13 Klassifikation.
Nur lesend. Keine Dateien werden verschoben, geloescht oder umbenannt.
"""

import json
import csv
import os
import sys
from datetime import datetime
from collections import defaultdict

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
INVENTUR_PFAD = os.path.join(ALIN_CORE, "07_Bestandsaufnahme_Altbestand", "CORE13_altbestand_inventur.json")
SPERRHINWEISE_PFAD = os.path.join(ALIN_CORE, "07_Bestandsaufnahme_Altbestand", "CORE13_sperrhinweise.csv")
AUSGABE_DIR = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE14_AUSWERTUNG_BERICHT.txt")

ZIELKLASSEN = [
    "UEBERNEHMEN_KOPIEREND",
    "NICHT_UEBERNEHMEN_ERSETZT",
    "ARCHIV_VORSCHLAG",
    "DUBLETTE_NICHT_KOPIEREN",
    "TESTREST_NICHT_KOPIEREN",
    "LAUFZEITARTEFAKT_NICHT_KOPIEREN",
    "CONFIG_LOKAL_MANUELL",
    "SPERREN_NICHT_KOPIEREN",
    "MANUELL_PRUEFEN",
]

KLASSIFIKATION_ZU_ZIEL = {
    "AKTIV": "UEBERNEHMEN_KOPIEREND",
    "ERSETZT": "NICHT_UEBERNEHMEN_ERSETZT",
    "ALT_ABER_NOCH_RELEVANT": "ARCHIV_VORSCHLAG",
    "TESTREST": "TESTREST_NICHT_KOPIEREN",
    "LAUFZEIT_ARTEFAKT": "LAUFZEITARTEFAKT_NICHT_KOPIEREN",
    "LOG_BERICHT": "ARCHIV_VORSCHLAG",
    "CONFIG_LOKAL": "CONFIG_LOKAL_MANUELL",
    "DUBLETTE": "DUBLETTE_NICHT_KOPIEREN",
    "UNGEKLÄRT": "MANUELL_PRUEFEN",
    "SPERREN": "SPERREN_NICHT_KOPIEREN",
}


def log(msg):
    print(f"[CORE-14] {msg}")


def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def lade_sperrhinweise(pfad):
    sperren = {}
    if not os.path.exists(pfad):
        log(f"WARNUNG: Sperrhinweise nicht gefunden: {pfad}")
        global WARNUNGEN
        WARNUNGEN += 1
        return sperren
    with open(pfad, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel = row.get("relativer_pfad", "").strip()
            if not rel:
                continue
            if rel not in sperren:
                sperren[rel] = []
            sperren[rel].append({
                "grund": row.get("grund", ""),
                "schweregrad": row.get("schweregrad", ""),
                "empfehlung": row.get("empfehlung", ""),
            })
    return sperren


def bestimme_zielentscheidung(datei, sperrhinweise):
    """
    Bestimmt die Zielentscheidung fuer eine einzelne Datei.
    Rueckgabe: (zielentscheidung, begruendung, gesperrt)
    """
    rel_pfad = datei.get("relativer_pfad", "")
    klass = datei.get("klassifikation", "UNGEKLÄRT")
    ist_sicherheitsrelevant = datei.get("ist_sicherheitsrelevant", False)

    # Grundentscheidung aus Klassifikation
    ziel = KLASSIFIKATION_ZU_ZIEL.get(klass, "MANUELL_PRUEFEN")
    begruendung = f"Klassifikation={klass}"
    gesperrt = False

    # Sperrhinweise pruefen
    hinweise = sperrhinweise.get(rel_pfad, [])
    kritisch_hoch = [h for h in hinweise if h["schweregrad"] in ("KRITISCH", "HOCH")]

    if klass == "SPERREN":
        gesperrt = True
        begruendung += "; explizit als SPERREN klassifiziert"
    elif kritisch_hoch:
        gesperrt = True
        ziel = "SPERREN_NICHT_KOPIEREN"
        begruendung += f"; Sperrhinweis {kritisch_hoch[0]['schweregrad']}: {kritisch_hoch[0]['grund']}"

    # Sicherheitsrelevante Dateien erhalten Hinweis
    if ist_sicherheitsrelevant and not gesperrt:
        begruendung += "; sicherheitsrelevant"

    return ziel, begruendung, gesperrt


def erstelle_auswertung(inventur, sperrhinweise):
    auswertungen = []
    statistik = defaultdict(int)
    gesperrt_count = 0

    for datei in inventur.get("dateien", []):
        ziel, begruendung, gesperrt = bestimme_zielentscheidung(datei, sperrhinweise)

        auswertung = {
            "relativer_pfad": datei.get("relativer_pfad", ""),
            "dateiname": datei.get("dateiname", ""),
            "dateiendung": datei.get("dateiendung", ""),
            "dateigroesse": datei.get("dateigroesse", 0),
            "sha256": datei.get("sha256", ""),
            "klassifikation": datei.get("klassifikation", "UNGEKLÄRT"),
            "zielentscheidung": ziel,
            "begruendung": begruendung,
            "gesperrt": gesperrt,
            "sperrhinweise": sperrhinweise.get(datei.get("relativer_pfad", ""), []),
            "sicherheitsrelevant": datei.get("ist_sicherheitsrelevant", False),
        }
        auswertungen.append(auswertung)
        statistik[ziel] += 1
        if gesperrt:
            gesperrt_count += 1

    return auswertungen, dict(statistik), gesperrt_count


def schreibe_json(auswertungen, statistik, gesperrt_count):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE14_auswertung.json")
    out = {
        "meta": {
            "modul_id": "CORE-14",
            "name": "CORE-13 Auswertung und Zielentscheidungen",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_lesend": True,
        },
        "zusammenfassung": {
            "anzahl_dateien": len(auswertungen),
            "zielentscheidungen": statistik,
            "anzahl_gesperrt": gesperrt_count,
        },
        "auswertungen": auswertungen,
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"JSON geschrieben: {pfad}")
    return pfad


def schreibe_csv(auswertungen):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE14_auswertung.csv")
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "relativer_pfad", "dateiname", "dateiendung", "dateigroesse",
                "sha256", "klassifikation", "zielentscheidung", "begruendung",
                "gesperrt", "sicherheitsrelevant",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        for a in auswertungen:
            row = dict(a)
            row["gesperrt"] = str(row["gesperrt"])
            row["sicherheitsrelevant"] = str(row["sicherheitsrelevant"])
            writer.writerow(row)
    log(f"CSV geschrieben: {pfad}")
    return pfad


def schreibe_bericht(auswertungen, statistik, gesperrt_count):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-14 AUSWERTUNG BERICHT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        f.write(f"Gesamtdateien: {len(auswertungen)}\n")
        f.write(f"Gesperrte Dateien: {gesperrt_count}\n\n")
        f.write("Zielentscheidungen:\n")
        f.write("-" * 40 + "\n")
        for ziel in ZIELKLASSEN:
            anzahl = statistik.get(ziel, 0)
            prozent = (anzahl / len(auswertungen) * 100) if auswertungen else 0
            f.write(f"  {ziel:<45} {anzahl:>6} ({prozent:5.2f}%)\n")
        f.write("\n")
        f.write("Top 20 MANUELL_PRUEFEN (Prio):\n")
        f.write("-" * 40 + "\n")
        manuell = [a for a in auswertungen if a["zielentscheidung"] == "MANUELL_PRUEFEN"]
        for a in manuell[:20]:
            f.write(f"  {a['relativer_pfad']}\n")
        if len(manuell) > 20:
            f.write(f"  ... und {len(manuell) - 20} weitere\n")
        f.write("\n")
        f.write("Top 20 SPERREN_NICHT_KOPIEREN:\n")
        f.write("-" * 40 + "\n")
        gesperrt = [a for a in auswertungen if a["zielentscheidung"] == "SPERREN_NICHT_KOPIEREN"]
        for a in gesperrt[:20]:
            f.write(f"  {a['relativer_pfad']} – {a['begruendung']}\n")
        if len(gesperrt) > 20:
            f.write(f"  ... und {len(gesperrt) - 20} weitere\n")
        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("ENDE BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def hauptlauf():
    log("Starte CORE-14 Auswertung...")

    if not os.path.exists(INVENTUR_PFAD):
        log(f"FEHLER: Inventur nicht gefunden: {INVENTUR_PFAD}")
        global FEHLER
        FEHLER += 1
        return

    log(f"Lade Inventur: {INVENTUR_PFAD}")
    inventur = lade_json(INVENTUR_PFAD)
    anzahl_dateien = len(inventur.get("dateien", []))
    log(f"Inventur geladen: {anzahl_dateien} Dateien")

    log(f"Lade Sperrhinweise: {SPERRHINWEISE_PFAD}")
    sperrhinweise = lade_sperrhinweise(SPERRHINWEISE_PFAD)
    log(f"Sperrhinweise geladen: {len(sperrhinweise)} Dateien betroffen")

    log("Erstelle Auswertung...")
    auswertungen, statistik, gesperrt_count = erstelle_auswertung(inventur, sperrhinweise)

    schreibe_json(auswertungen, statistik, gesperrt_count)
    schreibe_csv(auswertungen)
    schreibe_bericht(auswertungen, statistik, gesperrt_count)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Gesamtdateien: {len(auswertungen)}")
    log(f"Gesperrt: {gesperrt_count}")
    for ziel in ZIELKLASSEN:
        anzahl = statistik.get(ziel, 0)
        prozent = (anzahl / len(auswertungen) * 100) if auswertungen else 0
        log(f"  {ziel:<45} {anzahl:>6} ({prozent:5.2f}%)")
    log("=" * 60)
    log("CORE-14 AUSWERTUNG ABGESCHLOSSEN")


def selbsttest():
    print("CORE-14 SELBSTTEST =====================================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    def t(bez, bed):
        global FEHLER
        if not bed:
            print(f"  [FAIL] {bez}")
            FEHLER += 1
        else:
            print(f"  [OK]   {bez}")

    t("Zielklassen definiert", len(ZIELKLASSEN) == 9)
    t("Mapping vollstaendig", len(KLASSIFIKATION_ZU_ZIEL) == 10)
    t("Projektwurzel existiert", os.path.isdir(PROJEKT_WURZEL))
    t("ALIN_Neustart_Core existiert", os.path.isdir(ALIN_CORE))

    # Test bestimme_zielentscheidung
    test_datei = {"relativer_pfad": "test.py", "klassifikation": "AKTIV", "ist_sicherheitsrelevant": False}
    ziel, begr, gesp = bestimme_zielentscheidung(test_datei, {})
    t("AKTIV -> UEBERNEHMEN_KOPIEREND", ziel == "UEBERNEHMEN_KOPIEREND")

    test_datei2 = {"relativer_pfad": "test.py", "klassifikation": "DUBLETTE", "ist_sicherheitsrelevant": False}
    ziel2, _, _ = bestimme_zielentscheidung(test_datei2, {})
    t("DUBLETTE -> DUBLETTE_NICHT_KOPIEREN", ziel2 == "DUBLETTE_NICHT_KOPIEREN")

    test_datei3 = {"relativer_pfad": "secret.py", "klassifikation": "AKTIV", "ist_sicherheitsrelevant": False}
    sperren = {"secret.py": [{"grund": "API_KEY", "schweregrad": "KRITISCH", "empfehlung": "Pruefen"}]}
    ziel3, _, gesp3 = bestimme_zielentscheidung(test_datei3, sperren)
    t("KRITISCH -> SPERREN_NICHT_KOPIEREN", ziel3 == "SPERREN_NICHT_KOPIEREN")
    t("KRITISCH -> gesperrt=True", gesp3 is True)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
