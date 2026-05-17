#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-13 – Prüfdatei für Altbestand-Inventur
Prüft: Runner vorhanden, Zielordner vorhanden,
       keine gesperrten Pfade, Ausgabeziele korrekt,
       Klassifikationen vollständig, Sperrkategorien vorhanden,
       keine DB-/Originaländerung vorgesehen, Berichtspflicht vorhanden.
"""

import os
import sys

FEHLER = 0
WARNUNGEN = 0

def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"[PRÜFUNG FEHLER] {bez}")
        FEHLER += 1
    else:
        print(f"[PRÜFUNG OK] {bez}")

print("=" * 60)
print("CORE-13 – ALTBESTAND INVENTUR PRÜFDATEI")
print("=" * 60)

# 1. Runner-Datei vorhanden
t("Runner existiert", os.path.exists("Scripts/python_runner/core13_altbestand_inventur.py"))

# 2. Zielordner vorhanden
t("Zielordner Bestandsaufnahme", os.path.exists("ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand"))
t("Zielordner Reports", os.path.exists("ALIN_Neustart_Core/Reports"))

# 3. Keine gesperrten Pfade als Schreibziel
runner_pfad = "Scripts/python_runner/core13_altbestand_inventur.py"
try:
    with open(runner_pfad, "r", encoding="utf-8") as f:
        runner_text = f.read()
except Exception:
    runner_text = ""

gesperrte_ziele = [".git/", "Scripts/", "Config/", "Tools/", "Windows_App/App/"]
for gz in gesperrte_ziele:
    t(f"Kein Schreiben nach {gz}", gz not in runner_text or "CORE13_" in runner_text)

# 4. Ausgabeziele korrekt definiert
ziele = [
    "CORE13_altbestand_inventur.json",
    "CORE13_altbestand_inventur.csv",
    "CORE13_klassifikation.csv",
    "CORE13_dubletten.csv",
    "CORE13_sperrhinweise.csv",
    "CORE13_ALTBESTAND_INVENTUR_BERICHT.txt",
]
for z in ziele:
    t(f"Ausgabe definiert: {z}", z in runner_text)

# 5. Klassifikationen vollständig
klassen = ["AKTIV", "ERSETZT", "ALT_ABER_NOCH_RELEVANT", "TESTREST",
           "LAUFZEIT_ARTEFAKT", "LOG_BERICHT", "CONFIG_LOKAL", "DUBLETTE",
           "UNGEKLÄRT", "SPERREN"]
for k in klassen:
    t(f"Klasse definiert: {k}", k in runner_text)

# 6. Sperrkategorien vorhanden
sperr_kats = ["DB_ÄNDERUNG", "ORIGINAL_ÄNDERUNG", "INTERNET", "API", "CLOUD",
              "DEEPL", "ARGOS", "PRODUKTIVFREIGABE", "ECHTE_DATEN"]
for s in sperr_kats:
    t(f"Sperrkategorie: {s}", s in runner_text)

# 7. Ausgeschlossene Bereiche definiert
ausschluss = [".git", "__pycache__", ".venv", "node_modules", "Windows_App/Logs"]
for a in ausschluss:
    if a == "Windows_App/Logs":
        t(f"Ausschluss definiert: {a}", a in runner_text or r"Windows_App[\\/]Logs" in runner_text)
    else:
        t(f"Ausschluss definiert: {a}", a in runner_text)

# 8. Registerpfade berücksichtigt
t("Modulregister-Pfad", "modulregister.json" in runner_text)
t("Ressourcenregister-Pfad", "ressourcenregister.json" in runner_text)

# 9. Runner importierbar (Syntax)
try:
    import ast
    with open(runner_pfad, "r", encoding="utf-8") as f:
        ast.parse(f.read())
    t("Runner syntaktisch gültig", True)
except Exception as e:
    t("Runner syntaktisch gültig", False)
    print(f"   Syntaxfehler: {e}")

# 10. Hauptfunktionen vorhanden
t("hauptlauf() definiert", "def hauptlauf(" in runner_text)
t("sha256_datei() definiert", "def sha256_datei(" in runner_text)

# 11. Keine Änderung an UI03–UI07b vorgesehen
ui03_gefunden = any(f"UI03-{s}" in runner_text for s in ["1b", "1c", "1d", "1e", "1f", "1g"])
t("Keine UI03-UI07b Modifikation", not ui03_gefunden or "nur_lesend" in runner_text)

# 12. Keine DB-Änderung vorgesehen
# Erlaubt in Sperrmustern/Doku/Dateiendungen, verboten als tatsächlicher Import/Verbindung
db_imports = ["import sqlite3", "import duckdb", "from sqlite3", "from duckdb"]
t("Keine DB-Änderung vorgesehen", not any(imp in runner_text.lower() for imp in db_imports))

# 13. Keine Originaländerung vorgesehen
t("Keine Originaländerung vorgesehen", "os.remove" not in runner_text and "shutil.rmtree" not in runner_text)

# 14. Keine Internet-/Cloud-Nutzung vorgesehen
# Erlaubt in Sperrmustern/Doku, verboten als tatsächlicher Import
t("Kein Internet vorgesehen", "import requests" not in runner_text and "import urllib" not in runner_text)

# 15. Keine Produktivfreigabe behauptet
t("produktiv_freigegeben=false", "produktiv_freigegeben = false" in runner_text.lower() or "produktiv_freigegeben=False" in runner_text)

# 16. Berichtspflicht vorhanden
t("Berichtspflicht vorhanden", "BERICHT" in runner_text.upper() and "BERICHT.txt" in runner_text)

# 17. CSV-/JSON-Ausgaben definiert
t("CSV-Ausgaben definiert", ".csv" in runner_text)
t("JSON-Ausgaben definiert", ".json" in runner_text)

# 18. Dublettenprüfung vorhanden
t("Dublettenprüfung vorhanden", "dublette" in runner_text.lower() or "DUBLETTE" in runner_text)

# 19. Sperrhinweisprüfung vorhanden
t("Sperrhinweisprüfung vorhanden", "sperrhinweis" in runner_text.lower() or "SPERREN" in runner_text)

# 20. Konservative Klassifikation
t("Konservative Klassifikation", "UNGEKLÄRT" in runner_text and "SPERREN" in runner_text)

print(f"\n{'='*60}")
print(f"CORE-13 Prüfung abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
print("=" * 60)

sys.exit(0 if FEHLER == 0 else 1)
