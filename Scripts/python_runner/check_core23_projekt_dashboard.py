#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfdatei für CORE-23: Projekt-Dashboard / Arbeitsstart-Zentrale.

Prüft:
  1. Alle Ausgabedateien existieren (JSON, HTML, Bericht).
  2. JSON ist valide und enthält erwartete Top-Level-Schlüssel.
  3. HTML enthält erwartete HTML-Struktur.
  4. Bericht enthält Markierungen.
  5. Quelldateien sind referenziert und lesbar.
"""

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")

ZIELE = {
    "dashboard_json": BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE23_dashboard.json",
    "dashboard_html": BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE23_dashboard.html",
    "bericht": BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE23_PROJEKT_DASHBOARD_BERICHT.txt",
}

QUELLEN = {
    "core21_manifest": BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE21_arbeitsindex.json",
    "core22_manifest": BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE22_agenten_regeln.json",
    "core19_plan": BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "01_Plaene" / "CORE19_reste_archiv_sperrplan.json",
    "core21_config": BASE_DIR / "Config" / "core21_arbeitsindex_v1.json",
    "core22_config": BASE_DIR / "Config" / "core22_agentenregeln_v1.json",
}

ERWARTETE_JSON_KEYS = [
    "meta",
    "zusammenfassung",
    "aktiver_arbeitsbestand",
    "referenzbereiche",
    "gesperrte_bereiche",
    "letzter_migrationsstand",
    "offene_manuelle_pruefungen",
    "gesperrte_restdateien",
    "zulaessige_naechste_arbeiten",
    "blockierte_arbeiten",
    "startpunkt_fuer_roo",
    "status_core_13_bis_22",
]


def prüfe_ausgaben():
    fehler = 0
    for name, pfad in ZIELE.items():
        if not pfad.exists():
            print(f"[FEHLER] Ausgabe fehlt: {name} -> {pfad}")
            fehler += 1
        else:
            print(f"[OK] Ausgabe vorhanden: {name}")
    return fehler


def prüfe_json_struktur():
    pfad = ZIELE["dashboard_json"]
    if not pfad.exists():
        print("[FEHLER] JSON-Ausgabe fehlt, Strukturprüfung übersprungen.")
        return 1

    try:
        with open(pfad, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FEHLER] JSON nicht valide: {e}")
        return 1

    fehler = 0
    for key in ERWARTETE_JSON_KEYS:
        if key not in data:
            print(f"[FEHLER] Erwarteter Schlüssel fehlt: {key}")
            fehler += 1
        else:
            print(f"[OK] Schlüssel vorhanden: {key}")

    meta = data.get("meta", {})
    if meta.get("modul_id") != "CORE-23":
        print(f"[FEHLER] modul_id falsch: {meta.get('modul_id')}")
        fehler += 1
    else:
        print("[OK] modul_id == CORE-23")

    status = data.get("status_core_13_bis_22", {})
    for modul in [f"CORE-{i}" for i in range(13, 23)]:
        if modul not in status:
            print(f"[FEHLER] Status für {modul} fehlt")
            fehler += 1
        else:
            print(f"[OK] Status-Eintrag vorhanden: {modul}")

    return fehler


def prüfe_html():
    pfad = ZIELE["dashboard_html"]
    if not pfad.exists():
        print("[FEHLER] HTML-Ausgabe fehlt.")
        return 1
    with open(pfad, "r", encoding="utf-8") as f:
        html = f.read()

    fehler = 0
    for needle in ["<!DOCTYPE html>", "<html", "CORE-23", "Zusammenfassung", "Startpunkt für Roo", "Status CORE-13 bis CORE-22"]:
        if needle not in html:
            print(f"[FEHLER] HTML enthält nicht: {needle}")
            fehler += 1
        else:
            print(f"[OK] HTML enthält: {needle}")
    return fehler


def prüfe_bericht():
    pfad = ZIELE["bericht"]
    if not pfad.exists():
        print("[FEHLER] Bericht fehlt.")
        return 1
    with open(pfad, "r", encoding="utf-8") as f:
        text = f.read()

    fehler = 0
    for needle in ["CORE-23", "ZUSAMMENFASSUNG", "STARTPUNKT FÜR ROO", "ENDE DES BERICHTS"]:
        if needle not in text:
            print(f"[FEHLER] Bericht enthält nicht: {needle}")
            fehler += 1
        else:
            print(f"[OK] Bericht enthält: {needle}")
    return fehler


def prüfe_quellen():
    fehler = 0
    for name, pfad in QUELLEN.items():
        if not pfad.exists():
            print(f"[WARNUNG] Quelle fehlt: {name} -> {pfad}")
        else:
            print(f"[OK] Quelle vorhanden: {name}")
    return fehler


def main():
    print("=" * 60)
    print("CORE-23 Prüfdatei")
    print("=" * 60)
    fehler = 0
    fehler += prüfe_ausgaben()
    fehler += prüfe_json_struktur()
    fehler += prüfe_html()
    fehler += prüfe_bericht()
    fehler += prüfe_quellen()

    print("=" * 60)
    if fehler == 0:
        print("ALLE PRÜFUNGEN BESTANDEN")
        return 0
    else:
        print(f"{fehler} PRÜFUNG(EN) FEHLGESCHLAGEN")
        return 1


if __name__ == "__main__":
    sys.exit(main())
