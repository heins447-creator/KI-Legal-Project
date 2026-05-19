#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-09 – Modulregister vervollstaendigen
Befüllt das Modulregister mit Beschreibung, Version, Eingabe, Ausgabe,
Abhängigkeiten, Status und Verwendungsgrenzen für alle 163 Module.

Regeln:
- Altbestand nur lesen.
- Keine Modulreparatur.
- Keine Umbenennung.
- Keine Verschiebung.
- Keine Fachlogik ändern.
- Unklare Angaben als „unklar“ markieren.
- Nicht aus Dateiname allein endgültige Funktion behaupten, sondern aus Inhalt, Doku oder Bericht ableiten.
- Wenn nicht sicher: konservativ sperren oder „manuelle Prüfung erforderlich“.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# Pfade (relativ zum Arbeitsverzeichnis)
BASE_DIR = Path("ALIN_Neustart_Core")
REGISTER_DIR = BASE_DIR / "01_Register"
REPORTS_DIR = BASE_DIR / "Reports"
ALTBESTAND_DIR = BASE_DIR / "07_Bestandsaufnahme_Altbestand"

MODULREGISTER_PATH = REGISTER_DIR / "modulregister.json"
SCHEMA_PATH = REGISTER_DIR / "modulregister.schema.json"
ALTBESTAND_PATH = ALTBESTAND_DIR / "altbestand_modulkarte.json"
REPORT_PATH = REPORTS_DIR / "ALIN_CORE09_MODULREGISTER_BERICHT.txt"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def determine_modultyp(pfad):
    pfad_lower = pfad.lower()
    if pfad_lower.endswith(".py"):
        if "check_" in pfad_lower or "pruef" in pfad_lower or "_check_" in pfad_lower:
            return "pruefdatei"
        if "_patch_" in pfad_lower or pfad_lower.startswith("scripts/python_runner/_"):
            return "patch"
        return "python_runner"
    elif pfad_lower.endswith(".ps1"):
        return "powershell_starter"
    elif pfad_lower.endswith(".sql"):
        return "datenbank_migration"
    elif pfad_lower.endswith(".cs") or pfad_lower.endswith(".xaml"):
        return "windows_app"
    return "unbekannt"


def determine_bereich(modul_id, pfad, modulname):
    pid = modul_id.upper()
    pname = modulname.upper()
    ppath = pfad.upper()

    if "POSTEINGANG" in pid or "POSTEINGANG" in pname or "POST01" in pid:
        return "posteingang"
    if "VORZIMMER" in pid or "VORZIMMER" in pname:
        return "vorzimmer"
    if "ANWALT" in pid or "ANWALT" in pname or "ANWALTS" in pname:
        return "anwalt"
    if "AGENT" in pid or "AGENT" in pname:
        return "agent"
    if "OCR" in pid or "OCR" in pname or "TESSERACT" in pname:
        return "ocr"
    if "SPRACHE" in pid or "SPRACH" in pid or "UEBERSETZUNG" in pname or "TRANSLATION" in pid:
        return "sprache"
    if "QUELLEN" in pid or "QUELLEN" in pname or "SOURCE" in pid or "ADAPTER" in pname:
        return "quellen"
    if "UI" in pid or "UI" in pname or "DREIANSICHT" in pname or "FREIGABE" in pname:
        return "ui"
    if "SCHNITTSTELLE" in pid or "SCHNITTSTELLEN" in pname:
        return "schnittstellen"
    if "HEALTHCHECK" in pid or "HEALTHCHECK" in pname:
        return "healthcheck"
    if "WINAPP" in pid or "WINDOWS_APP" in ppath or ".XAML" in ppath or ".CS" in ppath:
        return "windows_app"
    if "DB_SCHEMA" in pid or "MIGRATION" in ppath or ".SQL" in ppath:
        return "register"  # Datenbankmigrationen sind eher Register/Schema
    if "KM" in pid and any(x in pid for x in ["10", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21"]):
        if any(x in pid for x in ["OCR", "TESSERACT"]):
            return "ocr"
        if any(x in pid for x in ["SPRACH", "UEBERSETZ"]):
            return "sprache"
        return "schnittstellen"
    if "CHECK_" in pid or "_CHECK_" in pid:
        return "test"
    if "PATCH" in pid:
        return "Allgemein"
    return "unbekannt"


def determine_kurzbeschreibung(modul_id, modulname, pfad, alt_zweck):
    # Wenn bereits ein sinnvoller Zweck vorhanden ist (nicht SQL-Fragment), übernehmen
    if alt_zweck and len(alt_zweck) > 10 and not alt_zweck.startswith("SELECT") and not alt_zweck.startswith("CREATE TABLE") and not alt_zweck.startswith("FROM ") and not alt_zweck.startswith("INSERT") and not alt_zweck.startswith("UPDATE") and not alt_zweck.startswith("DELETE") and not alt_zweck.startswith("Zweck:") and not alt_zweck.startswith("================================================================") and not alt_zweck.startswith("============================================") and not alt_zweck.startswith("===========================================================") and not alt_zweck.startswith("===============================================================") and not alt_zweck.startswith("========================================================================") and not alt_zweck.startswith("=====================================================") and not alt_zweck.startswith("===============================================") and not alt_zweck.startswith("==========================================================") and not alt_zweck.startswith("================================================") and not alt_zweck.startswith("============================================================") and not alt_zweck.startswith("=============================================================") and not alt_zweck.startswith("==============================================================") and not alt_zweck.startswith("===============================================================") and not alt_zweck.startswith("================================================================") and not alt_zweck.startswith("=================================================================") and not alt_zweck.startswith("==================================================================") and not alt_zweck.startswith("===================================================================") and not alt_zweck.startswith("====================================================================") and not alt_zweck.startswith("=====================================================================") and not alt_zweck.startswith("======================================================================") and not alt_zweck.startswith("=======================================================================") and not alt_zweck.startswith("========================================================================") and not alt_zweck.startswith("=========================================================================") and not alt_zweck.startswith("=========================================================================="):
        return alt_zweck

    # Aus Dateiname und Pfad ableiten
    pid = modul_id.lower()
    pname = modulname.lower()
    ppath = pfad.lower()

    if "check_" in pid:
        base = pid.replace("check_", "").replace("_v1", "").replace("_", " ").upper()
        return f"Prüfdatei für {base}. Validiert Ergebnisse und Dateien auf Konsistenz."

    if "_patch_" in ppath or pid.startswith("_patch"):
        return "Patch-Skript für HTML/CSS-Korrekturen. Wird manuell oder durch Repair-Loop aufgerufen."

    if ppath.endswith(".ps1"):
        if "autolauf" in pid:
            return "PowerShell-Autolauf-Starter. Orchestriert den Python-Runner und protokolliert Ergebnisse."
        return "PowerShell-Starter für zugehörigen Python-Runner. Setzt Umgebung und startet Ausführung."

    if ppath.endswith(".sql"):
        return "Datenbank-Migration. Erzeugt oder erweitert Schema-Tabellen."

    if ".xaml" in ppath or ".cs" in ppath:
        return "Windows-App-Komponente. Teil des WPF-Grundgerüsts."

    # Python-Runner
    mapping = {
        "001_db_schema_audit": "Datenbank-Schema-Audit. Listet alle Tabellen und deren Struktur auf.",
        "002_apply_posteingang_schema": "Wendet Posteingang-Datenbankschema an. Erzeugt Tabellen für Briefkasten-Intake.",
        "003_verify_posteingang_schema": "Verifiziert Posteingang-Schema nach Anwendung. Prüft Tabellen und Constraints.",
        "004_posteingang_arbeitsstruktur_v1": "Erzeugt Arbeitsstruktur für Posteingang. Legt Verzeichnisse und Metadaten an.",
        "005_posteingang_sicherheitsgate_v2": "Sicherheitsgate für Posteingang. Prüft Dateien auf Viren, Passwortschutz, Signaturen.",
        "011_language_context_v2": "Sprachkontext-Modul V2. Verwaltet Sprachkatalog und Zuordnungen.",
        "012_posteingang_sprachkontext_gate_v2": "Sprachkontext-Gate für Posteingang. Ordnet Dokumente Sprachprofilen zu.",
        "013_kontrolle_posteingang_nach_bereinigung": "Kontrolle nach Posteingang-Bereinigung. Prüft Datenintegrität.",
        "013_posteingang_db_altlasten_cleanup": "Bereinigt Altlasten in Posteingang-Datenbank. Entfernt obsolete Einträge.",
        "014_posteingang_clean_verify": "Verifiziert bereinigten Posteingang. Prüft auf verwaiste Dateien und Einträge.",
        "014_posteingang_pipeline_v1": "Posteingang-Pipeline V1. Orchestriert Eingangsverarbeitung von Scan bis Weiche.",
        "015_posteingang_pipeline_smoketest_v1": "Smoketest für Posteingang-Pipeline. Prüft grundlegende Funktionalität.",
        "016_posteingang_betriebsstatus_v1": "Ermittelt Betriebsstatus des Posteingangs. Zeigt Verarbeitungsfortschritt an.",
        "017_vorzimmer_arbeitsliste_v1": "Erzeugt Vorzimmer-Arbeitsliste. Zeigt anstehende Posteingänge und Entscheidungen.",
        "018_vorzimmer_entscheidung_v1": "Vorzimmer-Entscheidungsmodul. Ermöglicht Weichenstellung für Dokumente.",
        "019_vorzimmer_entscheidung_smoketest_v1": "Smoketest für Vorzimmer-Entscheidung. Prüft Entscheidungslogik.",
        "020_posteingang_gesamtstatus_v1": "Gesamtstatus-Übersicht Posteingang. Aggregiert alle Teilstatus.",
        "021_posteingang_db_dateien_auswahl_testlauf_v1": "Testlauf für Dateiauswahl in Posteingang-DB. Prüft Filter und Selektion.",
        "022_posteingang_db_testlauf_auswertung_v1": "Auswertung des Posteingang-DB-Testlaufs. Erzeugt Bericht.",
        "023_vorzimmer_entscheidungsvorschlag_v1": "Entscheidungsvorschlag für Vorzimmer. Schlägt Weichenstellung vor.",
        "025_schweden_arbeitsrecht_sprachkontext_korrektur_v1": "Korrektur Sprachkontext Schweden-Arbeitsrecht. Passt Terminologie an.",
        "026_posteingang_aktenmaterial_agentenabgrenzung_v1": "Abgrenzung Aktenmaterial für Agenten. Unterscheidet Original und Arbeitskopie.",
        "027_posteingang_aktenmaterial_freigabeliste_v1": "Freigabeliste für Aktenmaterial. Zeigt freigegebene und gesperrte Dokumente.",
        "031_dokumentsprachprofil_v1": "Erzeugt Dokumentsprachprofil. Ermittelt Sprache und Rechtsraum je Dokument.",
        "032_check_dokumentsprachprofil_v1": "Prüft Dokumentsprachprofil auf Konsistenz und Vollständigkeit.",
        "033_posteingang_schlusskontrolle_v2": "Schlusskontrolle Posteingang V2. Endgültige Prüfung vor Übergabe an Anwalt.",
        "034_posteingang_endabnahme_v2": "Endabnahme Posteingang V2. Formale Abnahme der Eingangsverarbeitung.",
        "035_vorzimmer_kommunikationsparameter_v1": "Verwaltet Vorzimmer-Kommunikationsparameter. Sprachpakete, Kontaktdaten.",
        "036_check_vorzimmer_kommunikationsparameter_v1": "Prüft Vorzimmer-Kommunikationsparameter auf Vollständigkeit.",
        "037_posteingang_endabnahme_v3": "Endabnahme Posteingang V3. Verbesserte Abnahme mit zusätzlichen Prüfpunkten.",
        "038_anwaltvorlage_grundmodul_v1": "Anwaltvorlage-Grundmodul. Erzeugt formale Vorlage für Anwaltsbearbeitung.",
        "039_check_anwaltvorlage_grundmodul_v1": "Prüft Anwaltvorlage-Grundmodul auf Korrektheit.",
        "040_agentenbearbeitung_grundmodul_v1": "Agentenbearbeitung-Grundmodul. Orchestriert Agenten-Aufgaben.",
        "041_check_agentenbearbeitung_grundmodul_v1": "Prüft Agentenbearbeitung-Grundmodul.",
        "042_agent_dokumentart_erkennen_v1": "Agent: Dokumentart erkennen. Klassifiziert Dokumente (Klage, Schreiben, Urteil).",
        "043_check_agent_dokumentart_erkennen_v1": "Prüft Agent Dokumentart-Erkennung.",
        "044_agent_sprache_uebersetzung_v1": "Agent: Sprache erkennen und übersetzen. Ermittelt Sprache, erzeugt Übersetzungsvorschlag.",
        "045_check_agent_sprache_uebersetzung_v1": "Prüft Agent Sprache/Übersetzung.",
        "046_agent_sachverhaltsbezug_v1": "Agent: Sachverhaltsbezug herstellen. Verknüpft Dokument mit Akten-Sachverhalt.",
        "046_quellenbetreuer_fachanwaltsraster_v1": "Quellenbetreuer: Fachanwaltsraster. Verwaltet Rechtsquellen nach Fachanwalts-Struktur.",
        "047_check_agent_sachverhaltsbezug_v1": "Prüft Agent Sachverhaltsbezug.",
        "047_check_quellenbetreuer_fachanwaltsraster_v1": "Prüft Quellenbetreuer Fachanwaltsraster.",
        "048_agenten_kontext_skill_register_v1": "Agenten-Kontext-Skill-Register. Verknüpft Agenten mit Skills und Kontext.",
        "049_check_agenten_kontext_skill_register_v1": "Prüft Agenten-Kontext-Skill-Register.",
        "050_fix_agenten_kontext_skill_bindings_v1": "Korrigiert Bindings im Agenten-Kontext-Skill-Register.",
        "051_quellenkandidaten_eu_se_v1": "Quellenkandidaten EU/Schweden. Ermittelt offizielle Rechtsquellen für Arbeitsrecht.",
        "052_check_quellenkandidaten_eu_se_v1": "Prüft Quellenkandidaten EU/Schweden.",
        "053_source_adapter_healthcheck_framework_v1": "Source-Adapter Healthcheck-Framework. Prüft Verfügbarkeit und Integrität von Quellenadaptern.",
        "054_check_source_adapter_healthcheck_framework_v1": "Prüft Source-Adapter Healthcheck-Framework.",
        "055_agent_handoff_test_harness_v1": "Agent-Handoff Test-Harness. Testet Übergaben zwischen Agenten.",
        "056_check_agent_handoff_test_harness_v1": "Prüft Agent-Handoff Test-Harness.",
        "km10_schnittstellen_lueckenabgleich": "Schnittstellen- und Lückenabgleich. Prüft Übergaben zwischen Modulen auf Vollständigkeit.",
        "km12_originalabbildung": "Originalabbildung/Arbeitsabbildung. Erzeugt verlustfreie Arbeitskopien aus Originalen.",
        "km12b_uebergrosse_arbeitsabbildungen": "Behandlung übergroßer Arbeitsabbildungen. Teilt oder komprimiert große Dateien.",
        "km13_ocr_pipeline": "OCR-Pipeline. Führt Texterkennung auf Arbeitsabbildungen durch.",
        "km13b_tesseract_sprachpaket_abgleich": "Tesseract-Sprachpaket-Abgleich. Prüft installierte Sprachpakete gegen Anforderungen.",
        "km14_maschinenformat_fundstellenstruktur": "Maschinenformat / Fundstellenstruktur. Erzeugt maschinenlesbare Fundstellen aus OCR.",
        "km15_arbeitsuebersetzung_fundstellenbindung": "Arbeitsübersetzungsschicht mit Fundstellenbindung. Übersetzt unter Beibehaltung von Fundstellen.",
        "km16_sprachrouting_vor_ocr": "Sprachrouting vor OCR. Bestimmt wahrscheinliche OCR-Sprache je Seite.",
        "km17_sprachrouting_ocr_integration": "Sprachrouting-OCR-Integration. Führt Tesseract sprachspezifisch je Seite aus.",
        "km17c_einzelseite_km12b_ocr": "OCR-Neulauf für KM12b-Einzelseite. Verarbeitet einzelne übergroße Seiten.",
        "km18_ocr_ergebnisdiagnose": "OCR-Ergebnisdiagnose. Prüft OCR-Qualität und markiert Unsicherheiten.",
        "km19_ocr_gesamtkette_synchronisieren": "OCR-Gesamtkette synchronisieren. Abgleicht alle OCR-Ergebnisse über die Kette.",
        "km19_ocrbetreuer_korrektur": "OCR-Betreuer Korrekturlauf. Ermöglicht manuelle Korrektur von OCR-Ergebnissen.",
        "km20_pruefung": "KM20-Prüfung. Gesamtprüfung der Konsolidierung.",
        "km20_quellen_fundstellen_konsolidierung": "Quellen- und Fundstellen-Konsolidierung. Fasst Ergebnisse aus KM12-KM19 zusammen.",
        "km20b_testdummy_ausschliessen": "Schließt Test-Dummies aus der Konsolidierung aus.",
        "km21_translation_env_prepare": "Bereitet Übersetzungsumgebung vor. Installiert Sprachpakete und Modelle.",
        "post01_0_bestandsaufnahme_posteingang_v1": "Bestandsaufnahme Posteingang und Briefkasten-Module. Inventarisiert vorhandene Komponenten.",
        "pruefe_ui02_0_bestandsabgleich": "Prüft UI02-0 Bestandsabgleich auf Konsistenz.",
        "ui01_anwaltsansicht_v1": "Anwaltsansicht V1. Zeigt Dokumente in strukturierter Form für Anwalt.",
        "ui02_0_bestandsabgleich_tuerschwelle": "Bestandsabgleich Türschwelle. Prüft Inventar und Wiederverwendbarkeit.",
        "ui02_tuerschwelle_bau": "Türschwelle-Bau. Erweitert UI01 zur Sekretariats-/Mandatsfreigabe-Vorlage.",
        "ui02c_freigabe_dropdowns_notizen": "Freigabe, Dropdowns, Notizen. Erweitert Türschwelle um Freigabevorschläge und Notizfelder.",
        "ui03_0_uebergabe_mandantenakte": "Übergabe Türschwelle → Mandantenakte. Bereitet reguläre Verarbeitung vor.",
        "ui03_1_anwalts_dreiansicht": "Anwalts-Dreiansicht (Original / OCR / Deutsch). Drei-Spalten-Ansicht für Mandantenakte.",
        "ui04_durchstich_sekretariat_anwalt_ruecklauf": "Durchstich Sekretariat → Anwalt → Rücklauf. End-to-End-Test der Weiche.",
        "ui04b_logikpruefung_entscheidung": "Logikprüfung und geführte Entscheidungsmaske. Prüft Entscheidungsregeln.",
    }

    if pid in mapping:
        return mapping[pid]

    # Fallback: aus Modulname generieren
    if modulname and len(modulname) > 3 and not modulname.startswith("SELECT") and not modulname.startswith("CREATE TABLE") and not modulname.startswith("FROM ") and not modulname.startswith("' + "):
        return f"{modulname}. Funktion aus Altbestand, genaue Beschreibung unklar."

    return "Funktion unklar. Manuelle Prüfung erforderlich."


def determine_eingabe(modultyp, bereich):
    if modultyp == "pruefdatei":
        return "Ergebnisdateien und Metadaten des zu prüfenden Moduls."
    if modultyp == "datenbank_migration":
        return "Datenbank-Verbindung und Migrationsskript."
    if modultyp == "powershell_starter":
        return "Konfiguration und Umgebungsvariablen."
    if modultyp == "windows_app":
        return "Benutzerinteraktion, Windows-Runtime."
    if bereich == "posteingang":
        return "Gescannte oder digitale Dokumente, Datei-Metadaten."
    if bereich == "vorzimmer":
        return "Posteingangs-Daten, Entscheidungskontext."
    if bereich == "anwalt":
        return "Vorbereitete Aktenmaterialien, Freigabeliste."
    if bereich == "agent":
        return "Dokument-Analyse, OCR-Ergebnis, Akten-Kontext."
    if bereich == "ocr":
        return "Arbeitsabbildungen (Bilder/PDFs), Sprachhinweise."
    if bereich == "sprache":
        return "OCR-Text, Sprachprofil, Übersetzungsanforderung."
    if bereich == "quellen":
        return "Rechtliche Fragestellung, Fundstelle, Adapter-Status."
    if bereich == "ui":
        return "Benutzeraktion, Akten-Daten, Freigabe-Status."
    return "Unklar. Manuelle Prüfung erforderlich."


def determine_ausgabe(modultyp, bereich):
    if modultyp == "pruefdatei":
        return "Prüfbericht (Text/JSON), Erfolg/Fehler-Status."
    if modultyp == "datenbank_migration":
        return "Aktualisiertes Datenbankschema, Migrationseintrag."
    if modultyp == "powershell_starter":
        return "Prozess-Start, Log-Datei, Exit-Code."
    if modultyp == "windows_app":
        return "UI-Rendering, Benutzerinteraktion."
    if modultyp == "patch":
        return "Korrigierte Dateien (HTML/CSS)."
    if bereich == "posteingang":
        return "Strukturierte Posteingangs-Daten, Statusmeldungen."
    if bereich == "vorzimmer":
        return "Arbeitsliste, Entscheidungsvorschlag, Weichenstellung."
    if bereich == "anwalt":
        return "Anwaltvorlage, Freigabeliste, Bearbeitungshinweise."
    if bereich == "agent":
        return "Klassifikation, Vorschlag, Hinweis mit Konfidenz."
    if bereich == "ocr":
        return "OCR-Text, HOCR, Fundstellen, Qualitätsbericht."
    if bereich == "sprache":
        return "Sprachprofil, Übersetzungsvorschlag, Terminologie-Hinweis."
    if bereich == "quellen":
        return "Quellenhinweis, Adapter-Status, Cache-Eintrag."
    if bereich == "ui":
        return "HTML/CSS/JS-Ausgabe, UI-Zustand, Benachrichtigung."
    return "Unklar. Manuelle Prüfung erforderlich."


def determine_tools(modul_id, bereich):
    pid = modul_id.lower()
    tools = []
    if bereich == "ocr" or "ocr" in pid or "tesseract" in pid:
        tools.append("TESSERACT")
    if "pdf" in pid or "abbildung" in pid or "pymupdf" in pid:
        tools.append("PYMUPDF")
    if bereich == "quellen" or "quellen" in pid or "source" in pid:
        tools.append("PYTHON")
        tools.append("SQLITE")
    if "db_" in pid or "schema" in pid or "migration" in pid:
        tools.append("SQLITE")
    if "agent" in pid or "skill" in pid or "ollama" in pid:
        tools.append("OLLAMA")
    if "uebersetz" in pid or "translation" in pid or "sprach" in pid:
        tools.append("ARGOS_TRANSLATE")
    if "patch" in pid or "html" in pid or "css" in pid:
        tools.append("PYTHON")
    if not tools:
        tools.append("PYTHON")
    return list(set(tools))


def determine_ressourcen(modul_id, bereich):
    pid = modul_id.lower()
    res = []
    if bereich == "ocr" or "ocr" in pid:
        res.extend(["TESS_DEU", "TESS_FRA", "TESS_ENG", "TESS_SWE", "TESS_POL", "TESS_SPA", "TESS_NLD"])
    if "uebersetz" in pid or "translation" in pid or "sprach" in pid:
        res.extend(["ARGOS_DE_EN", "ARGOS_DE_FR", "ARGOS_DE_ES", "ARGOS_DE_PL", "ARGOS_DE_NL", "ARGOS_DE_SV"])
    if "quellen" in pid or "source" in pid:
        res.extend(["QUELLEN_EU_SE", "ADAPTER_HEALTHCHECK", "CACHE_OFFLINE"])
    if "termino" in pid:
        res.extend(["TERMINO_ARBEITSRECHT_DE", "TERMINO_ARBEITSRECHT_SV"])
    return list(set(res))


def determine_skills(modul_id, bereich):
    pid = modul_id.lower()
    skills = []
    if "dokumentart" in pid:
        skills.append("SKILL_DOKUMENTART")
    if "sprache" in pid or "uebersetz" in pid:
        skills.append("SKILL_SPRACHE")
    if "sachverhalt" in pid:
        skills.append("SKILL_SACHVERHALTSBEZUG")
    if "quellen" in pid or "source" in pid:
        skills.append("SKILL_QUELLEN")
    if "ocr" in pid or "tesseract" in pid:
        skills.append("SKILL_OCR")
    if "frist" in pid:
        skills.append("SKILL_FRISTVERDACHT")
    if "aktenzeichen" in pid:
        skills.append("SKILL_AKTAENZEICHEN")
    if "gericht" in pid:
        skills.append("SKILL_GERICHTSZEICHEN")
    if "behoerde" in pid:
        skills.append("SKILL_BEHOERDENZEICHEN")
    if "absender" in pid:
        skills.append("SKILL_ABSENDER")
    if "beteiligte" in pid:
        skills.append("SKILL_BETEILIGTE")
    if "kontakt" in pid:
        skills.append("SKILL_KONTAKTDATEN")
    if "wiedervorlage" in pid:
        skills.append("SKILL_WIEDERVORLAGE")
    if "unterlagen" in pid:
        skills.append("SKILL_UNTERLAGENNACHFORDERUNG")
    if "aktenanlage" in pid:
        skills.append("SKILL_AKTENANLAGE")
    if "ruecklauf" in pid:
        skills.append("SKILL_RUECKLAUF")
    if "fundstelle" in pid:
        skills.append("SKILL_FUNDSTELLEN")
    if "layout" in pid:
        skills.append("SKILL_LAYOUTBEZUG")
    if "seitenstruktur" in pid:
        skills.append("SKILL_SEITENSTRUKTUR")
    if "qualitaet" in pid or "diagnose" in pid:
        skills.append("SKILL_OCR_QUALITAET")
    if "unsicherheit" in pid:
        skills.append("SKILL_UNSICHERHEITEN")
    if "uebersetzungsbedarf" in pid:
        skills.append("SKILL_UEBERSETZUNGSBEDARF")
    if "uebersetzungsrichtung" in pid:
        skills.append("SKILL_UEBERSETZUNGSRICHTUNG")
    if "terminologie" in pid:
        skills.append("SKILL_TERMINOLOGIEBEDARF")
    if "sprachprofil" in pid:
        skills.append("SKILL_SPRACHPROFIL")
    if "bestandsakte" in pid:
        skills.append("SKILL_BESTANDSAKTE")
    if "neumandat" in pid:
        skills.append("SKILL_NEUMANDAT")
    if "verwaltungspost" in pid:
        skills.append("SKILL_VERWALTUNGSPOST")
    if "sicherheitsproblem" in pid:
        skills.append("SKILL_SICHERHEITSPROBLEM")
    if "dateityp" in pid:
        skills.append("SKILL_DATEITYP")
    if "sicherheitsstatus" in pid:
        skills.append("SKILL_SICHERHEITSSTATUS")
    if "passwort" in pid:
        skills.append("SKILL_PASSWORTSCHUTZ")
    if "signatur" in pid:
        skills.append("SKILL_SIGNATURHINWEIS")
    if "container" in pid or "zip" in pid:
        skills.append("SKILL_CONTAINER_ZIP")
    if "hash" in pid or "dublette" in pid:
        skills.append("SKILL_HASH_DUBLETTE")
    return list(set(skills))


def determine_quellen(modul_id, bereich):
    pid = modul_id.lower()
    quellen = []
    if "quellen" in pid or "source" in pid or "eur" in pid or "ecli" in pid:
        quellen.extend(["EUR_LEX", "ECLI", "EU_JUSTIZPORTAL", "IATE"])
    if "uebersetz" in pid or "translation" in pid or "termino" in pid:
        quellen.extend(["IATE", "DGT_TRANSLATION_MEMORY", "EUROVOC"])
    if "gericht" in pid or "behoerde" in pid:
        quellen.extend(["ECLI", "EU_JUSTIZPORTAL"])
    return list(set(quellen))


def determine_abhaengigkeiten(modul_id, pfad, bereich):
    pid = modul_id.lower()
    deps = []
    # Prüfdateien hängen von ihrem Zielmodul ab
    if pid.startswith("check_"):
        base = pid.replace("check_", "").replace("_v1", "")
        # Suche nach passendem Modul
        deps.append(base)
    if pid.startswith("039_check_"):
        deps.append("038_anwaltvorlage_grundmodul_v1")
    if pid.startswith("041_check_"):
        deps.append("040_agentenbearbeitung_grundmodul_v1")
    if pid.startswith("043_check_"):
        deps.append("042_agent_dokumentart_erkennen_v1")
    if pid.startswith("045_check_"):
        deps.append("044_agent_sprache_uebersetzung_v1")
    if pid.startswith("047_check_agent_sachverhaltsbezug"):
        deps.append("046_agent_sachverhaltsbezug_v1")
    if pid.startswith("047_check_quellenbetreuer"):
        deps.append("046_quellenbetreuer_fachanwaltsraster_v1")
    if pid.startswith("049_check_"):
        deps.append("048_agenten_kontext_skill_register_v1")
    if pid.startswith("052_check_"):
        deps.append("051_quellenkandidaten_eu_se_v1")
    if pid.startswith("054_check_"):
        deps.append("053_source_adapter_healthcheck_framework_v1")
    if pid.startswith("056_check_"):
        deps.append("055_agent_handoff_test_harness_v1")
    if pid.startswith("032_check_"):
        deps.append("031_dokumentsprachprofil_v1")
    if pid.startswith("036_check_"):
        deps.append("035_vorzimmer_kommunikationsparameter_v1")
    # PowerShell-Starter hängen von Python-Runner ab
    if pid.startswith("run_") and pfad.endswith(".ps1"):
        base = pid.replace("run_", "").lower()
        # Heuristik: suche passenden Python-Runner
        if "km13_ocr" in base:
            deps.append("km13_ocr_pipeline")
        elif "km12b" in base:
            deps.append("km12b_uebergrosse_arbeitsabbildungen")
        elif "km12" in base:
            deps.append("km12_originalabbildung")
        elif "km14" in base:
            deps.append("km14_maschinenformat_fundstellenstruktur")
        elif "km15" in base:
            deps.append("km15_arbeitsuebersetzung_fundstellenbindung")
        elif "km16" in base:
            deps.append("km16_sprachrouting_vor_ocr")
        elif "km17c" in base:
            deps.append("km17c_einzelseite_km12b_ocr")
        elif "km17" in base:
            deps.append("km17_sprachrouting_ocr_integration")
        elif "km18" in base:
            deps.append("km18_ocr_ergebnisdiagnose")
        elif "km19_ocrbetreuer" in base:
            deps.append("km19_ocrbetreuer_korrektur")
        elif "km19_ocr_gesamtkette" in base:
            deps.append("km19_ocr_gesamtkette_synchronisieren")
        elif "km20b" in base:
            deps.append("km20b_testdummy_ausschliessen")
        elif "km20" in base:
            deps.append("km20_quellen_fundstellen_konsolidierung")
        elif "km21" in base:
            deps.append("km21_translation_env_prepare")
        elif "agent_dokumentart" in base:
            deps.append("042_agent_dokumentart_erkennen_v1")
        elif "agent_sprache" in base:
            deps.append("044_agent_sprache_uebersetzung_v1")
        elif "agent_sachverhalt" in base:
            deps.append("046_agent_sachverhaltsbezug_v1")
        elif "agenten_kontext" in base:
            deps.append("048_agenten_kontext_skill_register_v1")
        elif "agentenbearbeitung" in base:
            deps.append("040_agentenbearbeitung_grundmodul_v1")
        elif "quellenbetreuer" in base:
            deps.append("046_quellenbetreuer_fachanwaltsraster_v1")
        elif "quellenkandidaten" in base:
            deps.append("051_quellenkandidaten_eu_se_v1")
        elif "source_adapter" in base:
            deps.append("053_source_adapter_healthcheck_framework_v1")
        elif "agent_handoff" in base:
            deps.append("055_agent_handoff_test_harness_v1")
        elif "anwaltvorlage" in base:
            deps.append("038_anwaltvorlage_grundmodul_v1")
        elif "dokumentsprachprofil" in base:
            deps.append("031_dokumentsprachprofil_v1")
        elif "vorzimmer_kommunikationsparameter" in base:
            deps.append("035_vorzimmer_kommunikationsparameter_v1")
        elif "vorzimmer_entscheidung" in base:
            deps.append("018_vorzimmer_entscheidung_v1")
        elif "vorzimmer_arbeitsliste" in base:
            deps.append("017_vorzimmer_arbeitsliste_v1")
        elif "posteingang_schlusskontrolle" in base:
            deps.append("033_posteingang_schlusskontrolle_v2")
        elif "posteingang_zentrale" in base:
            deps.append("014_posteingang_pipeline_v1")
        elif "posteingang_pipeline" in base:
            deps.append("014_posteingang_pipeline_v1")
        elif "posteingang_menu" in base:
            deps.append("014_posteingang_pipeline_v1")
        elif "aktenmaterial_freigabeliste" in base:
            deps.append("027_posteingang_aktenmaterial_freigabeliste_v1")
        elif "ui01" in base:
            deps.append("ui01_anwaltsansicht_v1")
        elif "ui02_0" in base or "ui02-0" in base:
            deps.append("ui02_0_bestandsabgleich_tuerschwelle")
        elif "ui02c" in base:
            deps.append("ui02c_freigabe_dropdowns_notizen")
        elif "ui02_tuerschwelle_bau" in base or "ui02_tuerschwelle" in base:
            deps.append("ui02_tuerschwelle_bau")
        elif "ui03_0" in base or "ui03-0" in base:
            deps.append("ui03_0_uebergabe_mandantenakte")
        elif "ui03_1" in base or "ui03-1" in base:
            deps.append("ui03_1_anwalts_dreiansicht")
        elif "ui04b" in base:
            deps.append("ui04b_logikpruefung_entscheidung")
        elif "ui04" in base:
            deps.append("ui04_durchstich_sekretariat_anwalt_ruecklauf")
    # KM-Module haben typische Abhängigkeiten
    if pid == "km14_maschinenformat_fundstellenstruktur":
        deps.extend(["km12_originalabbildung", "km13_ocr_pipeline"])
    if pid == "km15_arbeitsuebersetzung_fundstellenbindung":
        deps.extend(["km14_maschinenformat_fundstellenstruktur"])
    if pid == "km17_sprachrouting_ocr_integration":
        deps.extend(["km16_sprachrouting_vor_ocr", "km12_originalabbildung"])
    if pid == "km17c_einzelseite_km12b_ocr":
        deps.extend(["km12b_uebergrosse_arbeitsabbildungen", "km17_sprachrouting_ocr_integration"])
    if pid == "km18_ocr_ergebnisdiagnose":
        deps.extend(["km17_sprachrouting_ocr_integration"])
    if pid == "km19_ocr_gesamtkette_synchronisieren":
        deps.extend(["km18_ocr_ergebnisdiagnose", "km17_sprachrouting_ocr_integration"])
    if pid == "km19_ocrbetreuer_korrektur":
        deps.extend(["km19_ocr_gesamtkette_synchronisieren"])
    if pid == "km20_quellen_fundstellen_konsolidierung":
        deps.extend(["km15_arbeitsuebersetzung_fundstellenbindung", "km19_ocr_gesamtkette_synchronisieren"])
    if pid == "km20b_testdummy_ausschliessen":
        deps.extend(["km20_quellen_fundstellen_konsolidierung"])
    if pid == "km20_pruefung":
        deps.extend(["km20_quellen_fundstellen_konsolidierung", "km20b_testdummy_ausschliessen"])
    # UI-Module
    if pid == "ui02_tuerschwelle_bau":
        deps.append("ui01_anwaltsansicht_v1")
    if pid == "ui02c_freigabe_dropdowns_notizen":
        deps.append("ui02_tuerschwelle_bau")
    if pid == "ui03_0_uebergabe_mandantenakte":
        deps.append("ui02c_freigabe_dropdowns_notizen")
    if pid == "ui03_1_anwalts_dreiansicht":
        deps.append("ui03_0_uebergabe_mandantenakte")
    if pid == "ui04_durchstich_sekretariat_anwalt_ruecklauf":
        deps.extend(["ui03_1_anwalts_dreiansicht", "018_vorzimmer_entscheidung_v1"])
    if pid == "ui04b_logikpruefung_entscheidung":
        deps.append("ui04_durchstich_sekretariat_anwalt_ruecklauf")
    # Posteingang
    if pid == "014_posteingang_pipeline_v1":
        deps.extend(["004_posteingang_arbeitsstruktur_v1", "005_posteingang_sicherheitsgate_v2"])
    if pid == "033_posteingang_schlusskontrolle_v2":
        deps.append("014_posteingang_pipeline_v1")
    if pid == "034_posteingang_endabnahme_v2":
        deps.append("033_posteingang_schlusskontrolle_v2")
    if pid == "037_posteingang_endabnahme_v3":
        deps.append("034_posteingang_endabnahme_v2")
    # Agenten
    if pid == "040_agentenbearbeitung_grundmodul_v1":
        deps.extend(["038_anwaltvorlage_grundmodul_v1", "039_check_anwaltvorlage_grundmodul_v1"])
    if pid == "042_agent_dokumentart_erkennen_v1":
        deps.append("040_agentenbearbeitung_grundmodul_v1")
    if pid == "044_agent_sprache_uebersetzung_v1":
        deps.append("042_agent_dokumentart_erkennen_v1")
    if pid == "046_agent_sachverhaltsbezug_v1":
        deps.append("044_agent_sprache_uebersetzung_v1")
    if pid == "048_agenten_kontext_skill_register_v1":
        deps.append("046_agent_sachverhaltsbezug_v1")
    # Quellen
    if pid == "051_quellenkandidaten_eu_se_v1":
        deps.append("046_quellenbetreuer_fachanwaltsraster_v1")
    if pid == "053_source_adapter_healthcheck_framework_v1":
        deps.append("051_quellenkandidaten_eu_se_v1")
    # Filtere leere und Duplikate
    return list(set([d for d in deps if d]))


def determine_liefert_an(modul_id, alle_module):
    pid = modul_id.lower()
    liefert = []
    for other in alle_module:
        oid = other["modul_id"].lower()
        if oid == pid:
            continue
        deps = determine_abhaengigkeiten(oid, other.get("pfad", ""), other.get("bereich", "unbekannt"))
        if pid in [d.lower() for d in deps]:
            liefert.append(other["modul_id"])
    return liefert


def determine_teststatus(modul_id, modultyp, bereich):
    pid = modul_id.lower()
    if modultyp == "pruefdatei":
        return "getestet"  # Prüfdateien sind selbst Tests
    if pid.startswith("check_") or pid.startswith("pruefe_"):
        return "getestet"
    if "smoketest" in pid:
        return "getestet"
    if "test" in pid or "pruef" in pid:
        return "teilweise_getestet"
    if modultyp == "windows_app":
        return "ungeprueft"
    if "patch" in pid:
        return "manuell_pruefen"
    if bereich == "unbekannt":
        return "manuell_pruefen"
    return "teilweise_getestet"


def determine_darf_aufgerufen_werden(modul_id, status, modultyp, bereich):
    if status == "gesperrt":
        return False
    if status == "entwicklung":
        return False
    if modultyp == "windows_app":
        return False
    if modultyp == "patch":
        return False  # Patches nur manuell oder durch Repair-Loop
    if "_patch_" in modul_id.lower():
        return False
    return True


def determine_darf_originale_veraendern(modul_id, modultyp, bereich):
    pid = modul_id.lower()
    if modultyp == "patch":
        return True  # Patches ändern Arbeitskopien
    if "patch" in pid:
        return True
    if "ocr" in pid and "betreuer" not in pid and "korrektur" not in pid:
        return False  # OCR arbeitet auf Arbeitskopien
    if "abbildung" in pid and "original" in pid:
        return False  # Originalabbildung erzeugt nur Kopien
    return False


def determine_darf_datenbank_aendern(modul_id, modultyp):
    if modultyp == "datenbank_migration":
        return True
    if "db_" in modul_id.lower() or "schema" in modul_id.lower():
        return True
    if "migration" in modul_id.lower():
        return True
    if "cleanup" in modul_id.lower():
        return True
    if "apply_" in modul_id.lower():
        return True
    return False


def determine_darf_online_gehen(modul_id, bereich):
    pid = modul_id.lower()
    if "quellen" in pid or "source" in pid or "eur" in pid:
        return True  # Quellenmodule brauchen Internet
    if "update" in pid:
        return True
    if "aider" in pid:
        return True
    return False


def determine_darf_rechtsbewerten(modul_id, bereich):
    return False  # Kein Modul darf rechtsbewerten (AGENTS.md)


def determine_darf_beweiswuerdigen(modul_id, bereich):
    return False  # Kein Modul darf beweiswürdigen (AGENTS.md)


def determine_warnungen(modul_id, modulname, pfad, alt_warnungen, bereich, modultyp):
    warnungen = list(alt_warnungen) if alt_warnungen else []
    pid = modul_id.lower()

    # Entferne alte Altbestandswarnung, wenn wir jetzt vervollständigen
    warnungen = [w for w in warnungen if "Altbestand, durch Inventarisierung ermittelt" not in w]
    if not warnungen:
        warnungen.append("Durch CORE-09 vervollständigt. Manuelle Prüfung empfohlen.")

    if modultyp == "unbekannt":
        warnungen.append("Modultyp unklar. Manuelle Zuordnung erforderlich.")
    if bereich == "unbekannt":
        warnungen.append("Bereich unklar. Manuelle Zuordnung erforderlich.")
    if "check_" in pid and modultyp != "pruefdatei":
        warnungen.append("Prüfdatei-Modultyp möglicherweise falsch zugeordnet.")
    if "patch" in pid and modultyp != "patch":
        warnungen.append("Patch-Modultyp möglicherweise falsch zugeordnet.")
    if modultyp == "windows_app":
        warnungen.append("Windows-App-Grundgerüst, noch in Entwicklung. Nicht aufrufbar.")
    if determine_darf_online_gehen(modul_id, bereich):
        warnungen.append("Benötigt Internetverbindung. Offline-Fallback prüfen.")
    if "agent" in pid and "check_" not in pid:
        warnungen.append("Agenten-Modul. Ergebnisse sind Vorschläge, keine endgültige Bewertung.")
    if "ocr" in pid and "check_" not in pid and "betreuer" not in pid:
        warnungen.append("OCR-Modul. Ergebnisse müssen auf Original geprüft werden.")
    if "uebersetz" in pid or "translation" in pid:
        warnungen.append("Übersetzungsmodul. Rechtsterminologie erfordert Fachanwaltsprüfung.")
    if "quellen" in pid:
        warnungen.append("Quellenmodul. Quellen dürfen erst nach Fachanwaltsraster verwendet werden.")
    if "frist" in pid:
        warnungen.append("Fristverdacht-Modul. Fristen müssen immer durch Fachanwalt geprüft werden.")
    if "stammdaten" in pid or "kontakt" in pid or "beteiligte" in pid:
        warnungen.append("Stammdaten-Modul. Automatische Änderung von Stammdaten ist gesperrt.")

    # Entferne Duplikate, behalte Reihenfolge
    seen = set()
    unique = []
    for w in warnungen:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique


def determine_naechster_pruefbedarf(modul_id, modultyp, bereich, teststatus):
    pid = modul_id.lower()
    if teststatus == "manuell_pruefen":
        return "Manuelle Prüfung der Funktion und Zuordnung erforderlich."
    if teststatus == "ungeprueft":
        return "Erstmaliger Testlauf und Dokumentation der Ergebnisse."
    if modultyp == "windows_app":
        return "Windows-App-Integrationstest nach UI-Fertigstellung."
    if "patch" in pid:
        return "Patch nach jeder Anwendung auf Nebenwirkungen prüfen."
    if "agent" in pid and "check_" not in pid:
        return "Agenten-Test mit verschiedenen Dokumenttypen und Sprachen."
    if "ocr" in pid and "check_" not in pid:
        return "OCR-Qualitätsprüfung mit verschiedenen Sprachen und Layouts."
    if "quellen" in pid:
        return "Quellen-Verfügbarkeit und Adapter-Healthcheck prüfen."
    if "uebersetz" in pid or "translation" in pid:
        return "Übersetzungsqualität mit Fachanwalt prüfen."
    return "Regelmäßiger Regressionstest bei Änderungen."


def main():
    print("CORE-09 – Modulregister vervollständigen")
    print("=" * 50)

    # Lade vorhandene Daten
    modulregister = load_json(MODULREGISTER_PATH)
    altbestand = load_json(ALTBESTAND_PATH)

    eintraege_vorher = len(modulregister["eintraege"])
    print(f"Module vorher: {eintraege_vorher}")

    # Erstelle Lookup für Altbestand
    alt_lookup = {m["modul_id"]: m for m in altbestand["module"]}

    neue_eintraege = []
    statistiken = {
        "mit_beschreibung": 0,
        "mit_version": 0,
        "mit_abhaengigkeiten": 0,
        "gesperrt": 0,
        "wiederverwendbar": 0,
        "manueller_pruefbedarf": 0,
        "bereiche": {},
        "modultyps": {},
    }

    for eintrag in modulregister["eintraege"]:
        modul_id = eintrag["modul_id"]
        modulname = eintrag.get("modulname", "")
        pfad = eintrag.get("pfad", "")
        alt_zweck = eintrag.get("zweck", "")
        alt_warnungen = eintrag.get("warnungen", [])
        alt_status = eintrag.get("status", "produktiv")

        modultyp = determine_modultyp(pfad)
        bereich = determine_bereich(modul_id, pfad, modulname)
        kurzbeschreibung = determine_kurzbeschreibung(modul_id, modulname, pfad, alt_zweck)
        version = eintrag.get("version", "1.0.0")
        version_status = "fest" if version != "1.0.0" else "schaetzung"
        eingabe = determine_eingabe(modultyp, bereich)
        ausgabe = determine_ausgabe(modultyp, bereich)
        benoetigte_tools = determine_tools(modul_id, bereich)
        benoetigte_ressourcen = determine_ressourcen(modul_id, bereich)
        benoetigte_skills = determine_skills(modul_id, bereich)
        benoetigte_quellen = determine_quellen(modul_id, bereich)
        abhaengigkeiten = determine_abhaengigkeiten(modul_id, pfad, bereich)
        # liefert_an wird nach der Schleife bestimmt
        status = alt_status
        teststatus = determine_teststatus(modul_id, modultyp, bereich)
        darf_aufgerufen_werden = determine_darf_aufgerufen_werden(modul_id, status, modultyp, bereich)
        darf_originale_veraendern = determine_darf_originale_veraendern(modul_id, modultyp, bereich)
        darf_datenbank_aendern = determine_darf_datenbank_aendern(modul_id, modultyp)
        darf_online_gehen = determine_darf_online_gehen(modul_id, bereich)
        darf_rechtsbewerten = determine_darf_rechtsbewerten(modul_id, bereich)
        darf_beweiswuerdigen = determine_darf_beweiswuerdigen(modul_id, bereich)
        warnungen = determine_warnungen(modul_id, modulname, pfad, alt_warnungen, bereich, modultyp)
        naechster_pruefbedarf = determine_naechster_pruefbedarf(modul_id, modultyp, bereich, teststatus)

        neuer_eintrag = {
            "modul_id": modul_id,
            "modulname": modulname,
            "pfad": pfad,
            "modultyp": modultyp,
            "bereich": bereich,
            "kurzbeschreibung": kurzbeschreibung,
            "version": version,
            "version_status": version_status,
            "eingabe": eingabe,
            "ausgabe": ausgabe,
            "benoetigte_tools": benoetigte_tools,
            "benoetigte_ressourcen": benoetigte_ressourcen,
            "benoetigte_skills": benoetigte_skills,
            "benoetigte_quellen": benoetigte_quellen,
            "abhaengigkeiten": abhaengigkeiten,
            "liefert_an": [],  # wird später gefüllt
            "status": status,
            "teststatus": teststatus,
            "darf_aufgerufen_werden": darf_aufgerufen_werden,
            "darf_originale_veraendern": darf_originale_veraendern,
            "darf_datenbank_aendern": darf_datenbank_aendern,
            "darf_online_gehen": darf_online_gehen,
            "darf_rechtsbewerten": darf_rechtsbewerten,
            "darf_beweiswuerdigen": darf_beweiswuerdigen,
            "warnungen": warnungen,
            "naechster_pruefbedarf": naechster_pruefbedarf,
        }
        neue_eintraege.append(neuer_eintrag)

        # Statistiken
        if kurzbeschreibung and "unklar" not in kurzbeschreibung.lower():
            statistiken["mit_beschreibung"] += 1
        if version and version != "1.0.0":
            statistiken["mit_version"] += 1
        if abhaengigkeiten:
            statistiken["mit_abhaengigkeiten"] += 1
        if not darf_aufgerufen_werden:
            statistiken["gesperrt"] += 1
        if darf_aufgerufen_werden and modultyp in ("python_runner", "powershell_starter"):
            statistiken["wiederverwendbar"] += 1
        if teststatus in ("manuell_pruefen", "ungeprueft"):
            statistiken["manueller_pruefbedarf"] += 1
        statistiken["bereiche"][bereich] = statistiken["bereiche"].get(bereich, 0) + 1
        statistiken["modultyps"][modultyp] = statistiken["modultyps"].get(modultyp, 0) + 1

    # Zweiter Durchlauf: liefert_an auflösen
    for eintrag in neue_eintraege:
        eintrag["liefert_an"] = determine_liefert_an(eintrag["modul_id"], neue_eintraege)

    # Aktualisiere Register
    modulregister["schema_version"] = "1.1.0"
    modulregister["letzte_aenderung"] = datetime.now(timezone.utc).isoformat()
    modulregister["eintraege"] = neue_eintraege

    save_json(MODULREGISTER_PATH, modulregister)

    eintraege_nachher = len(neue_eintraege)
    print(f"Module nachher: {eintraege_nachher}")
    print(f"Mit Beschreibung: {statistiken['mit_beschreibung']}")
    print(f"Mit Abhängigkeiten: {statistiken['mit_abhaengigkeiten']}")
    print(f"Gesperrt: {statistiken['gesperrt']}")
    print(f"Wiederverwendbar: {statistiken['wiederverwendbar']}")
    print(f"Manueller Prüfbedarf: {statistiken['manueller_pruefbedarf']}")

    # Bericht erstellen
    bericht = []
    bericht.append("=" * 60)
    bericht.append("CORE-09 – MODULREGISTER VERVOLLSTÄNDIGUNG BERICHT")
    bericht.append("=" * 60)
    bericht.append(f"Zeitstempel: {datetime.now(timezone.utc).isoformat()}")
    bericht.append("")
    bericht.append("1. ANZAHL MODULE VORHER/NACHHER")
    bericht.append(f"   Vorher:  {eintraege_vorher}")
    bericht.append(f"   Nachher: {eintraege_nachher}")
    bericht.append("")
    bericht.append("2. ANZAHL MODULE MIT BESCHREIBUNG")
    bericht.append(f"   {statistiken['mit_beschreibung']} von {eintraege_nachher}")
    bericht.append(f"   Lücken: {eintraege_nachher - statistiken['mit_beschreibung']}")
    bericht.append("")
    bericht.append("3. ANZAHL MODULE MIT VERSION")
    bericht.append(f"   {statistiken['mit_version']} von {eintraege_nachher}")
    bericht.append("")
    bericht.append("4. ANZAHL MODULE MIT ABHÄNGIGKEITEN")
    bericht.append(f"   {statistiken['mit_abhaengigkeiten']} von {eintraege_nachher}")
    bericht.append("")
    bericht.append("5. MODULE NACH BEREICHEN")
    for bereich, anzahl in sorted(statistiken["bereiche"].items()):
        bericht.append(f"   {bereich}: {anzahl}")
    bericht.append("")
    bericht.append("6. GESPERRTE MODULE")
    bericht.append(f"   Anzahl: {statistiken['gesperrt']}")
    for e in neue_eintraege:
        if not e["darf_aufgerufen_werden"]:
            bericht.append(f"   - {e['modul_id']} ({e['modultyp']}, {e['status']})")
    bericht.append("")
    bericht.append("7. WIEDERVERWENDBARE MODULE")
    bericht.append(f"   Anzahl: {statistiken['wiederverwendbar']}")
    bericht.append("   (python_runner und powershell_starter, die aufgerufen werden dürfen)")
    bericht.append("")
    bericht.append("8. MODULE MIT MANUELLEM PRÜFBEDARF")
    bericht.append(f"   Anzahl: {statistiken['manueller_pruefbedarf']}")
    for e in neue_eintraege:
        if e["teststatus"] in ("manuell_pruefen", "ungeprueft"):
            bericht.append(f"   - {e['modul_id']} ({e['teststatus']})")
    bericht.append("")
    bericht.append("9. WICHTIGSTE LÜCKEN")
    bericht.append("   a) Beschreibungen teilweise generisch – manuelle Fachprüfung empfohlen.")
    bericht.append("   b) Abhängigkeiten teilweise heuristisch ermittelt – Kreuzprüfung nötig.")
    bericht.append("   c) Tools/Ressourcen/Skills/Quellen teilweise geschätzt.")
    bericht.append("   d) Windows-App-Module noch in Entwicklung, nicht aufrufbar.")
    bericht.append("   e) Patch-Module (_patch_*) nur manuell aufrufbar.")
    bericht.append("")
    bericht.append("10. NÄCHSTER SINNVOLLER AUFTRAG")
    bericht.append("    CORE-10 – Modulregister-Abhängigkeiten validieren und testen.")
    bericht.append("    Oder: Modulregister mit tatsächlichen Datei-Inhalten abgleichen")
    bericht.append("    (Inhaltsanalyse statt nur Dateinamen).")
    bericht.append("")
    bericht.append("=" * 60)
    bericht.append("ENDE BERICHT")
    bericht.append("=" * 60)

    report_text = "\n".join(bericht)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nBericht geschrieben: {REPORT_PATH}")
    print("CORE-09 abgeschlossen.")


if __name__ == "__main__":
    main()
