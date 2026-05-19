#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-09 – Prüfdatei für Modulregister-Vervollständigung
Prüft:
1. Schema-Version
2. Pflichtfelder je Modul
3. Eindeutigkeit der modul_id
4. Konsistenz von abhaengigkeiten und liefert_an
5. Pfad-Existenz (nur Warnung, keine Fehler, da Altbestand)
6. Status-Konsistenz (gesperrt => darf_aufgerufen_werden = false)
7. Verwendungsgrenzen-Konsistenz
8. Bereich und Modultyp sind gültige Enum-Werte
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path("ALIN_Neustart_Core")
REGISTER_DIR = BASE_DIR / "01_Register"
REPORTS_DIR = BASE_DIR / "Reports"

MODULREGISTER_PATH = REGISTER_DIR / "modulregister.json"
SCHEMA_PATH = REGISTER_DIR / "modulregister.schema.json"
REPORT_PATH = REPORTS_DIR / "ALIN_CORE09_PRUEFBERICHT.txt"

# Gültige Enum-Werte aus Schema
GUELTIGE_MODULTYPEN = ["python_runner", "powershell_starter", "datenbank_migration", "windows_app", "pruefdatei", "patch", "unbekannt"]
GUELTIGE_BEREICHE = ["posteingang", "vorzimmer", "anwalt", "agent", "ocr", "sprache", "quellen", "ui", "schnittstellen", "healthcheck", "windows_app", "register", "backup", "test", "unbekannt", "Allgemein"]
GUELTIGE_STATUS = ["produktiv", "testbar", "entwicklung", "revision", "gesperrt", "ersetzt"]
GUELTIGE_TESTSTATUS = ["getestet", "teilweise_getestet", "ungeprueft", "fehlgeschlagen", "manuell_pruefen"]
GUELTIGE_VERSION_STATUS = ["fest", "schaetzung", "unbekannt", "zu_pruefen"]

PFLICHTFELDER = [
    "modul_id", "modulname", "pfad", "modultyp", "bereich", "kurzbeschreibung",
    "version", "version_status", "eingabe", "ausgabe", "benoetigte_tools",
    "benoetigte_ressourcen", "benoetigte_skills", "benoetigte_quellen",
    "abhaengigkeiten", "liefert_an", "status", "teststatus",
    "darf_aufgerufen_werden", "darf_originale_veraendern", "darf_datenbank_aendern",
    "darf_online_gehen", "darf_rechtsbewerten", "darf_beweiswuerdigen",
    "warnungen", "naechster_pruefbedarf"
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pruefe():
    print("CORE-09 – Prüfung Modulregister")
    print("=" * 50)

    fehler = []
    warnungen = []
    infos = []

    # 1. Dateien existieren
    if not MODULREGISTER_PATH.exists():
        fehler.append(f"Modulregister nicht gefunden: {MODULREGISTER_PATH}")
        return fehler, warnungen, infos
    if not SCHEMA_PATH.exists():
        warnungen.append(f"Schema nicht gefunden: {SCHEMA_PATH}")

    modulregister = load_json(MODULREGISTER_PATH)
    eintraege = modulregister.get("eintraege", [])
    schema_version = modulregister.get("schema_version", "")

    # 2. Schema-Version
    if schema_version != "1.1.0":
        warnungen.append(f"Schema-Version ist {schema_version}, erwartet 1.1.0")
    else:
        infos.append("Schema-Version korrekt: 1.1.0")

    # 3. Eindeutigkeit modul_id
    ids = [e["modul_id"] for e in eintraege]
    if len(ids) != len(set(ids)):
        dupes = [i for i in ids if ids.count(i) > 1]
        fehler.append(f"Doppelte modul_ids gefunden: {set(dupes)}")
    else:
        infos.append(f"Alle {len(ids)} modul_ids sind eindeutig.")

    # 4. Pflichtfelder und Enum-Werte je Eintrag
    module_mit_beschreibung = 0
    module_mit_version = 0
    module_mit_abhaengigkeiten = 0
    gesperrte_module = 0
    wiederverwendbare = 0
    manueller_pruefbedarf = 0
    bereich_counts = {}

    for idx, eintrag in enumerate(eintraege):
        modul_id = eintrag.get("modul_id", f"Eintrag_{idx}")
        prefix = f"[{modul_id}]"

        # Pflichtfelder
        for feld in PFLICHTFELDER:
            if feld not in eintrag:
                fehler.append(f"{prefix} Pflichtfeld fehlt: {feld}")

        # Typ-Prüfungen
        if eintrag.get("modultyp") not in GUELTIGE_MODULTYPEN:
            fehler.append(f"{prefix} Ungültiger modultyp: {eintrag.get('modultyp')}")
        if eintrag.get("bereich") not in GUELTIGE_BEREICHE:
            fehler.append(f"{prefix} Ungültiger bereich: {eintrag.get('bereich')}")
        if eintrag.get("status") not in GUELTIGE_STATUS:
            fehler.append(f"{prefix} Ungültiger status: {eintrag.get('status')}")
        if eintrag.get("teststatus") not in GUELTIGE_TESTSTATUS:
            fehler.append(f"{prefix} Ungültiger teststatus: {eintrag.get('teststatus')}")
        if eintrag.get("version_status") not in GUELTIGE_VERSION_STATUS:
            fehler.append(f"{prefix} Ungültiger version_status: {eintrag.get('version_status')}")

        # Boolean-Prüfungen
        for bool_feld in ["darf_aufgerufen_werden", "darf_originale_veraendern", "darf_datenbank_aendern",
                          "darf_online_gehen", "darf_rechtsbewerten", "darf_beweiswuerdigen"]:
            if bool_feld in eintrag and not isinstance(eintrag[bool_feld], bool):
                fehler.append(f"{prefix} {bool_feld} ist kein Boolean: {type(eintrag[bool_feld])}")

        # Array-Prüfungen
        for arr_feld in ["benoetigte_tools", "benoetigte_ressourcen", "benoetigte_skills",
                         "benoetigte_quellen", "abhaengigkeiten", "liefert_an", "warnungen"]:
            if arr_feld in eintrag and not isinstance(eintrag[arr_feld], list):
                fehler.append(f"{prefix} {arr_feld} ist keine Liste: {type(eintrag[arr_feld])}")

        # Konsistenz: gesperrt/entwicklung => darf_aufgerufen_werden = false
        if eintrag.get("status") in ("gesperrt", "entwicklung", "ersetzt"):
            if eintrag.get("darf_aufgerufen_werden") is True:
                fehler.append(f"{prefix} Status ist '{eintrag['status']}', aber darf_aufgerufen_werden ist true")
            gesperrte_module += 1
        elif eintrag.get("status") == "produktiv":
            if eintrag.get("darf_aufgerufen_werden") is False and eintrag.get("modultyp") not in ("windows_app", "patch"):
                warnungen.append(f"{prefix} Status produktiv, aber darf_aufgerufen_werden ist false")

        # Konsistenz: darf_rechtsbewerten und darf_beweiswuerdigen müssen false sein (AGENTS.md)
        if eintrag.get("darf_rechtsbewerten") is True:
            fehler.append(f"{prefix} darf_rechtsbewerten ist true – verstößt gegen AGENTS.md")
        if eintrag.get("darf_beweiswuerdigen") is True:
            fehler.append(f"{prefix} darf_beweiswuerdigen ist true – verstößt gegen AGENTS.md")

        # Statistiken
        kb = eintrag.get("kurzbeschreibung", "")
        if kb and "unklar" not in kb.lower() and "manuelle prüfung" not in kb.lower():
            module_mit_beschreibung += 1
        if eintrag.get("version") and eintrag.get("version") != "1.0.0":
            module_mit_version += 1
        if eintrag.get("abhaengigkeiten"):
            module_mit_abhaengigkeiten += 1
        if eintrag.get("darf_aufgerufen_werden") is True and eintrag.get("modultyp") in ("python_runner", "powershell_starter"):
            wiederverwendbare += 1
        if eintrag.get("teststatus") in ("manuell_pruefen", "ungeprueft"):
            manueller_pruefbedarf += 1
        bereich_counts[eintrag.get("bereich", "unbekannt")] = bereich_counts.get(eintrag.get("bereich", "unbekannt"), 0) + 1

    # 5. Abhängigkeiten-Konsistenz (bidirektional)
    id_set = set(ids)
    for eintrag in eintraege:
        modul_id = eintrag["modul_id"]
        for dep in eintrag.get("abhaengigkeiten", []):
            if dep not in id_set:
                warnungen.append(f"[{modul_id}] Abhängigkeit '{dep}' existiert nicht im Register")
        for liefert in eintrag.get("liefert_an", []):
            if liefert not in id_set:
                warnungen.append(f"[{modul_id}] liefert_an '{liefert}' existiert nicht im Register")

    # Bidirektionale Prüfung
    for eintrag in eintraege:
        modul_id = eintrag["modul_id"]
        for dep in eintrag.get("abhaengigkeiten", []):
            dep_eintrag = next((e for e in eintraege if e["modul_id"] == dep), None)
            if dep_eintrag and modul_id not in dep_eintrag.get("liefert_an", []):
                warnungen.append(f"[{modul_id}] Abhängigkeit zu '{dep}' nicht bidirektional (liefert_an fehlt in {dep})")

    # 6. Pfad-Prüfung (nur Warnung, da Altbestand)
    for eintrag in eintraege:
        pfad = eintrag.get("pfad", "")
        full_path = Path(".") / pfad
        if not full_path.exists():
            warnungen.append(f"[{eintrag['modul_id']}] Pfad nicht gefunden: {pfad} (Altbestand, nur Warnung)")

    # Zusammenfassung
    print(f"Geprüfte Module: {len(eintraege)}")
    print(f"Fehler: {len(fehler)}")
    print(f"Warnungen: {len(warnungen)}")
    print(f"Infos: {len(infos)}")

    # Bericht schreiben
    bericht = []
    bericht.append("=" * 60)
    bericht.append("CORE-09 – PRÜFBERICHT MODULREGISTER")
    bericht.append("=" * 60)
    bericht.append(f"Zeitstempel: {datetime.now(timezone.utc).isoformat()}")
    bericht.append(f"Geprüfte Module: {len(eintraege)}")
    bericht.append("")
    bericht.append("ZUSAMMENFASSUNG")
    bericht.append(f"  Fehler:   {len(fehler)}")
    bericht.append(f"  Warnungen: {len(warnungen)}")
    bericht.append(f"  Infos:    {len(infos)}")
    bericht.append("")
    bericht.append("STATISTIKEN")
    bericht.append(f"  Module mit Beschreibung: {module_mit_beschreibung} / {len(eintraege)}")
    bericht.append(f"  Module mit Version: {module_mit_version} / {len(eintraege)}")
    bericht.append(f"  Module mit Abhängigkeiten: {module_mit_abhaengigkeiten} / {len(eintraege)}")
    bericht.append(f"  Gesperrte Module: {gesperrte_module}")
    bericht.append(f"  Wiederverwendbare Module: {wiederverwendbare}")
    bericht.append(f"  Manueller Prüfbedarf: {manueller_pruefbedarf}")
    bericht.append("")
    bericht.append("MODULE NACH BEREICHEN")
    for b, c in sorted(bereich_counts.items()):
        bericht.append(f"  {b}: {c}")
    bericht.append("")

    if fehler:
        bericht.append("FEHLER")
        for f in fehler:
            bericht.append(f"  [FEHLER] {f}")
        bericht.append("")

    if warnungen:
        bericht.append("WARNUNGEN")
        for w in warnungen:
            bericht.append(f"  [WARNUNG] {w}")
        bericht.append("")

    if infos:
        bericht.append("INFOS")
        for i in infos:
            bericht.append(f"  [INFO] {i}")
        bericht.append("")

    bericht.append("=" * 60)
    bericht.append("ENDE PRÜFBERICHT")
    bericht.append("=" * 60)

    report_text = "\n".join(bericht)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nPrüfbericht geschrieben: {REPORT_PATH}")

    if fehler:
        print("\nPRÜFUNG FEHLGESCHLAGEN – Fehler gefunden.")
        return 1
    else:
        print("\nPRÜFUNG ERFOLGREICH – Keine Fehler.")
        return 0


if __name__ == "__main__":
    exit(pruefe())
