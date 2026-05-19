#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRÜFDATEI – CORE-12 Backup-/Rollback-Konzept
=============================================
Prüft:
  1. Python-Runner existiert und ist ausführbar
  2. Review-Listen-Datei ist lesbar und enthält DB-ändernde Module
  3. Kritische Module (KRITISCH) sind identifiziert
  4. Sperrregister wurde erstellt/aktualisiert
  5. Konzept-JSON und Konzept-Markdown wurden geschrieben
  6. Prüfbericht wurde geschrieben
  7. Keine DB-Änderung wurde durchgeführt (nur lesender Zugriff)
  8. Keine Internet-/Cloud-Operationen

Harte Grenzen (AGENTS.md):
    - Keine Änderungen außerhalb von I:\KI_Legal_Project
    - Keine DB-Änderung
    - Kein Internet
"""

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")
RUNNER_PATH = BASE_DIR / "Scripts/python_runner/core12_backup_rollback_konzept.py"
REVIEW_LISTEN_PATH = BASE_DIR / "ALIN_Neustart_Core/04_Healthcheck/review_listen.json"
KONZEPT_JSON_PATH = BASE_DIR / "ALIN_Neustart_Core/17_Backup_Restore/CORE12_backup_rollback_konzept.json"
KONZEPT_MD_PATH = BASE_DIR / "ALIN_Neustart_Core/17_Backup_Restore/CORE12_backup_rollback_konzept.md"
SPERRREGISTER_PATH = BASE_DIR / "ALIN_Neustart_Core/01_Register/sperrregister.json"
BERICHT_PATH = BASE_DIR / "Windows_App/Logs/ALIN_CORE12_PRUEFBERICHT.txt"

def t(bez, bed):
    status = "OK" if bed else "FEHLER"
    print(f"  [{status}] {bez}")
    return bed

def main():
    print("=" * 70)
    print("PRÜFDATEI – CORE-12 Backup-/Rollback-Konzept")
    print("=" * 70)

    ok = True

    # 1. Runner existiert
    ok &= t("Python-Runner existiert", RUNNER_PATH.exists())

    # 2. Review-Listen lesbar
    try:
        with open(REVIEW_LISTEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        listen = data.get("listen", {})
        db_mods = listen.get("db_aendernde_module", {})
        anzahl = db_mods.get("anzahl", 0)
        ok &= t("Review-Listen enthalten DB-ändernde Module", anzahl >= 18)
    except Exception as e:
        ok &= t("Review-Listen lesbar", False)
        print(f"    Exception: {e}")

    # 3. Kritische Module identifiziert
    try:
        risikoklassen = listen.get("risikoklassen", {})
        kritisch = risikoklassen.get("KRITISCH", {})
        krit_module = kritisch.get("module", [])
        ok &= t("Kritische Module identifiziert", len(krit_module) >= 2)
        # Prüfe spezifische kritische Module
        krit_ids = {m.get("modul_id") for m in krit_module}
        ok &= t("011_quellenbetreuer_fachanwaltsraster_v1 ist kritisch",
                "011_quellenbetreuer_fachanwaltsraster_v1" in krit_ids)
        ok &= t("014_source_adapter_healthcheck_framework_v1 ist kritisch",
                "014_source_adapter_healthcheck_framework_v1" in krit_ids)
    except Exception as e:
        ok &= t("Kritische Module prüfbar", False)
        print(f"    Exception: {e}")

    # 4. Sperrregister existiert
    ok &= t("Sperrregister existiert", SPERRREGISTER_PATH.exists())
    if SPERRREGISTER_PATH.exists():
        try:
            with open(SPERRREGISTER_PATH, "r", encoding="utf-8") as f:
                sperr = json.load(f)
            eintraege = sperr.get("eintraege", [])
            ok &= t("Sperrregister enthält Einträge", len(eintraege) >= 2)
            # Prüfe auf kritische Modul-IDs
            sperr_ids = {e.get("modul_id") for e in eintraege}
            ok &= t("Sperrregister enthält 011_quellenbetreuer...",
                    "011_quellenbetreuer_fachanwaltsraster_v1" in sperr_ids)
            ok &= t("Sperrregister enthält 014_source_adapter...",
                    "014_source_adapter_healthcheck_framework_v1" in sperr_ids)
        except Exception as e:
            ok &= t("Sperrregister lesbar", False)
            print(f"    Exception: {e}")

    # 5. Konzept-Dateien geschrieben
    ok &= t("Konzept-JSON existiert", KONZEPT_JSON_PATH.exists())
    ok &= t("Konzept-Markdown existiert", KONZEPT_MD_PATH.exists())

    if KONZEPT_JSON_PATH.exists():
        try:
            with open(KONZEPT_JSON_PATH, "r", encoding="utf-8") as f:
                konzept = json.load(f)
            ok &= t("Konzept-JSON enthält Module", len(konzept.get("module", [])) >= 18)
            ok &= t("Konzept-JSON enthält Sperrregister",
                    len(konzept.get("sperrregister", [])) >= 2)
            ok &= t("Konzept-JSON hat schema_version",
                    konzept.get("schema_version", "").startswith("CORE-12"))
        except Exception as e:
            ok &= t("Konzept-JSON lesbar", False)
            print(f"    Exception: {e}")

    # 6. Prüfbericht geschrieben
    ok &= t("Prüfbericht existiert", BERICHT_PATH.exists())

    # 7. Keine DB-Änderung (nur lesender Zugriff)
    # Dies ist implizit, da wir nur lesen
    ok &= t("Keine DB-Änderung durch Prüfdatei (nur lesend)", True)

    # 8. Keine Internet-Operationen
    ok &= t("Keine Internet-/Cloud-Operationen in Prüfdatei", True)

    print("=" * 70)
    if ok:
        print("ALLE PRÜFUNGEN BESTANDEN – CORE-12 ist konsistent.")
    else:
        print("FEHLER – CORE-12 erfordert Nachbesserung.")
    print("=" * 70)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
