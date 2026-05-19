#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10f: Platzhalter-Eingabe/Ausgabe in Modulregister verfeinern
Ersetzt generische Platzhalter-Beschreibungen durch modulspezifische.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"
REPORT_PATH = ROOT / "ALIN_Neustart_Core" / "Reports" / "ALIN_CORE10F_PLATZHALTER_BERICHT.txt"

GENERIC_EINGABE = "Konfiguration und Umgebungsvariablen."
GENERIC_AUSGABE = "Prozess-Start, Log-Datei, Exit-Code."

# Modulspezifische Beschreibungen (modul_id -> (eingabe, ausgabe))
SPECIFIC = {
    # OCR / Arbeitsabbildung
    "KM17_AUTOLAUF": (
        "Arbeitsabbildung-Pfad, Seitenbereich, OCR-Parameter.",
        "OCR-Gesamtergebnis, Seitenliste, Konfidenzreport, Log-Datei."
    ),
    "KM17c_EINZELSEITE_KM12b_AUTOLAUF": (
        "Einzelseite-Arbeitsabbildung, Seitennummer, Sprachvermutung.",
        "OCR-Text der Seite, Koordinaten-Mapping, Seitenkonfidenz, Log."
    ),
    "KM18_AUTOLAUF": (
        "OCR-Rohergebnis, erwartete Sprache, Qualitaetsschwellen.",
        "OCR-Diagnosebericht, Qualitaetsbewertung, Korrekturvorschlag, Log."
    ),
    "KM19_OCR_GESAMTKETTE_SYNCHRONISIEREN_AUTOLAUF": (
        "Einzel-OCR-Ergebnisse, Dokument-ID, Synchronisierungsregeln.",
        "Synchronisierte OCR-Kette, konsolidierter Text, Seitenverknuepfung, Log."
    ),
    "KM19_OCRBETREUER_KORREKTUR_AUTOLAUF": (
        "OCR-Ergebnis mit Fehlverdacht, Korrekturvorschlaege, Seitenliste.",
        "Korrigiertes OCR-Ergebnis, Aenderungsprotokoll, Konfidenznachweis, Log."
    ),
    "Run_KM12_Originalabbildung": (
        "Originaldatei-Pfad, Zielverzeichnis, Abbildungsmodus, Groessenlimit.",
        "Arbeitsabbildung-Pfad, SHA256-Hash Original, SHA256-Hash Abbildung, Groesseninfo, Log."
    ),
    "Run_KM12b_Uebergrosse_Arbeitsabbildungen": (
        "Arbeitsabbildung-Pfad, Seitengroessenlimit, Kompressionsmodus, Qualitaetsstufe.",
        "Aufbereitete Arbeitsabbildung, Groessenreduktion, Qualitaetsbewertung, Log."
    ),
    "Run_KM13_OCR_Pipeline": (
        "Arbeitsabbildung-Pfad, erwartete Sprachenliste, OCR-Engine-Auswahl, Konfiguration.",
        "OCR-Text pro Seite, erkannte Sprache, Konfidenzwerte, Qualitaetsreport, Log."
    ),
    "Run_KM13b_Tesseract_Sprachpaket_Abgleich": (
        "Tessdata-Verzeichnis, erforderliche Sprachenliste, Vergleichsmodus.",
        "Sprachpaket-Status, fehlende Pakete, Installationshinweise, Versionsabgleich, Log."
    ),
    "Run_KM14_Maschinenformat_Fundstellenstruktur": (
        "OCR-Text, Seitenkoordinaten, Dokument-ID, Strukturierungsregeln.",
        "Fundstellen-JSON, Textstruktur-Markdown, Koordinaten-Mapping, Log."
    ),
    "Run_KM16_Sprachrouting_Vor_OCR": (
        "Dokumentprobe, verfuegbare Sprachpakete, Routing-Regeln.",
        "Erkannte Hauptsprache, OCR-Reihenfolge, Sprachwechsel-Verdacht, Log."
    ),

    # Uebersetzung
    "KM21_TRANSLATION_ENV_AUTOLAUF": (
        "Quellsprache, Zielsprache, Argos-Modell-Pfad, Uebersetzungsparameter.",
        "Uebersetzungsumgebungs-Status, verfuegbare Modelle, Testuebersetzung, Log."
    ),
    "Run_KM15_Arbeitsuebersetzung_Fundstellenbindung": (
        "Quelltext, Quellsprache, Zielsprache, Terminologie-Profil, Fundstellen-JSON.",
        "Uebersetzungsvorschlag, Fundstellen-Erklaerung, Konfidenz, Log."
    ),

    # Agenten
    "Run_Agent_Dokumentart": (
        "Dokumentdatei-Pfad, erwartete Kategorien, Erkennungsmodus, Konfidenzschwelle.",
        "Erkannte Dokumentart, Konfidenzwert, Alternativvorschlaege, Agent-Log."
    ),
    "Run_Agent_Sachverhaltsbezug": (
        "Dokumenttext, Sachverhalts-Keywords, Rechtsgebiet, Bezugsregeln.",
        "Sachverhaltsbezug-Vorschlag, relevante Passagen, Konfidenz, Agent-Log."
    ),
    "Run_Agentenbearbeitung": (
        "Agentenauftrag, Eingabedaten, Skill-Set, Ausfuehrungsmodus.",
        "Agent-Ergebnis, Zwischenschritte, Skill-Verbrauch, Agent-Log."
    ),
    "Run_Agenten_Kontext_Skill_Register": (
        "Agent-ID, Kontextdaten, Skill-Register-Referenz, Bindungsmodus.",
        "Skill-Bindungsstatus, verfuegbare Skills, Kontext-Hash, Agent-Log."
    ),
    "Run_Agent_Handoff_Test_Harness": (
        "Quell-Agent-ID, Ziel-Agent-ID, Uebergabedaten, Testmodus.",
        "Handoff-Ergebnis, Datenintegritaet, Uebergabeprotokoll, Test-Log."
    ),
    "Run_Agent_Sprache_Uebersetzung": (
        "Quelltext, Quellsprache, Zielsprache, Agent-Parameter, Terminologie.",
        "Agent-Uebersetzung, Konfidenz, Alternativen, Agent-Log."
    ),

    # Posteingang / Vorzimmer
    "Run_Posteingang_Menu": (
        "Benutzerauswahl, Posteingangs-ID, Filterkriterien, Sortierung.",
        "Gewaehlte Aktion, naechster Prozessschritt, Status, Menu-Log."
    ),
    "Run_Posteingang_Pipeline": (
        "Posteingangsdatei, Dokumentart, Prioritaet, Mandanten-ID, Sachgebiet.",
        "Verarbeitetes Dokument, Weichenstellung, OCR-Auftrag, Pipeline-Log."
    ),
    "Run_Posteingang_Schlusskontrolle": (
        "Zu pruefendes Dokument, Pruefliste, Akten-ID, Kontrollmodus.",
        "Kontrollergebnis, Freigabestatus, Auffaelligkeiten, Kontroll-Log."
    ),
    "Run_Posteingang_Zentrale": (
        "Posteingangsverzeichnis, Verarbeitungsregeln, Batch-Modus, Zeitfenster.",
        "Verarbeitete Dokumente, Fehlerliste, Statistik, Zentral-Log."
    ),
    "Run_Vorzimmer_Arbeitsliste": (
        "Benutzer-ID, Filterdatum, Sortierung, Prioritaetsmodus.",
        "Arbeitsliste, Faelligkeiten, Statusuebersicht, Erinnerungen, Arbeitsliste-Log."
    ),
    "Run_Vorzimmer_Entscheidung": (
        "Entscheidungsvorschlag, Dokument-ID, Benutzerrolle, Entscheidungstyp.",
        "Entscheidung, Kommentar, naechster Schritt, Weichenstellung, Entscheidungs-Log."
    ),
    "Run_Vorzimmer_Kommunikationsparameter": (
        "Mandanten-ID, Kontaktliste, Kommunikationskanal, Vorlage.",
        "Kommunikationsvorschlag, Parameter-Set, Adressatenliste, Kommunikations-Log."
    ),

    # Quellen / Rechtsquellen
    "Run_Quellenbetreuer_Fachanwaltsraster": (
        "Rechtsgebiet, Fachanwaltschaft, Rechtsraum, Aktualitaetsdatum.",
        "Fachanwaltsraster-Eintrag, Quellenliste, Verfuegbarkeit, Quellen-Log."
    ),
    "Run_Quellenkandidaten_EU_SE": (
        "Rechtsgebiet, EU-Rechtsraum, SE-Rechtsraum, Suchkriterien.",
        "Quellenkandidaten-Liste, Verfuegbarkeitsstatus, URLs, Quellen-Log."
    ),
    "Run_Source_Adapter_Healthcheck_Framework": (
        "Quellen-ID, Adapter-Typ, Pruefmodus, Timeout, Retry-Regeln.",
        "Verfuegbarkeitsstatus, Antwortzeit, Offline-Fallback-Liste, Healthcheck-Log."
    ),

    # UI / Anwalt / Mandant
    "UI01_ANWALTSANSICHT_AUTOLAUF": (
        "Mandanten-ID, Akten-ID, Dokument-ID, Anwalt-Ansichtsmodus.",
        "Anwaltsansicht-Layout, Dokumentvorschau, Notizfeld, Statusleiste, UI-Log."
    ),
    "UI02c_FREIGABE_DROPDOWNS_NOTIZEN_AUTOLAUF": (
        "Dokument-ID, Freigabestatus, Dropdown-Werte, Notiztext.",
        "Aktualisierter Status, gespeicherte Dropdown-Werte, Notiz, UI-Log."
    ),
    "UI03_0_UEBERGABE_MANDANTENAKTE_AUTOLAUF": (
        "Dokument-ID, Quellmodul, Zielmodul, Uebergabetyp, Prioritaet.",
        "Uebergabestatus, Empfangsbestaetigung, Aktenverknuepfung, UI-Log."
    ),
    "UI03_1_ANWALTS_DREIANSICHT_AUTOLAUF": (
        "Dokument-ID, Dreiansicht-Modus, Zoomstufe, Seitenbereich.",
        "Dreiansicht-Layout, Navigationsleiste, Seitenminiaturen, UI-Log."
    ),
    "UI04_DURCHSTICH_SEKRETARIAT_ANWALT_RUECKLAUF_AUTOLAUF": (
        "Dokument-ID, Sekretariat-Status, Anwalt-Rueckmeldung, Durchstichtyp.",
        "Ruecklaufstatus, Anwalt-Entscheidung, Protokolleintrag, UI-Log."
    ),
    "UI04b_LOGIKPRUEFUNG_ENTSCHEIDUNG_AUTOLAUF": (
        "Entscheidungsdaten, Logikregeln, Pruemuster, Eskalationsstufe.",
        "Logikpruefungsergebnis, Plausibilitaetsbewertung, Warnungen, UI-Log."
    ),
    "ui02_0_bestandsabgleich_tuerschwelle": (
        "Posteingangs-ID, Dokumentart, Schweregrad, Freigabebedingungen.",
        "Freigabeentscheidung, Weichenstellung, Protokolleintrag, Tuer-Schwelle-Log."
    ),
    "ui02_tuerschwelle_bau_starter": (
        "Bausatz-ID, Konfigurationsprofil, Zielverzeichnis, Bauparameter.",
        "Bausatz-Status, Installationsprotokoll, Fehlerliste, Bau-Starter-Log."
    ),

    # Tools / External / Hilfsskripte
    "Invoke_Aider_Local": (
        "Quellcode-Pfad, Aktion (add/edit/drop), Modell-Parameter, Kontextfenster.",
        "Aider-Ausgabe, Aenderungsvorschlag, Diff-Preview, Exit-Code, Aider-Log."
    ),
    "Run_AI_Coding_Agent_Project_Check": (
        "Projektverzeichnis, Pruefmodus, Regelsatz, Ausgabeformat.",
        "Pruefbericht, Fehlerliste, Empfehlungen, Projekt-Check-Log."
    ),
    "Run_AI_Coding_Agent_Repair_Loop": (
        "Fehlerbericht, Modul-ID, Reparaturmodus, Max-Iterationen, Backup-Modus.",
        "Reparaturvorschlag, angewendete Aenderungen, Testergebnis, Repair-Loop-Log."
    ),
    "Run_ALIN_SafeJob": (
        "Job-Definition, Sicherheitsparameter, Ausfuehrungsumgebung, Rollback-Plan.",
        "Job-Status, Ergebnis, Sicherheitsprotokoll, SafeJob-Log."
    ),
    "Run_Aktenmaterial_Freigabeliste": (
        "Akten-ID, Materialtyp, Freigabestatus, Empfaengerliste.",
        "Freigabeliste, Versandstatus, Empfangsbestaetigungen, Freigabe-Log."
    ),
    "Run_Anwaltvorlage": (
        "Vorlagen-ID, Mandanten-Daten, Sachverhalt, Ausgabeformat.",
        "Generierte Vorlage, Platzhalter-Ersetzung, Qualitaetsbewertung, Vorlagen-Log."
    ),
    "Run_Dokumentsprachprofil": (
        "Dokumentdatei, erwartete Sprachen, Profilierungsmodus, Granularitaet.",
        "Sprachprofil, Sprachanteile, Konfidenzwerte, Profil-Log."
    ),
    "Run_KM10_Schnittstellen_Lueckenabgleich": (
        "Schnittstellenregister, Modulregister, Abgleichsmodus, Toleranzregeln.",
        "Lueckenbericht, fehlende Schnittstellen, Empfehlungen, Abgleich-Log."
    ),
    "Run_KM20_Konsolidierung": (
        "Quelldaten-Pfade, Konsolidierungsregeln, Zielformat, Deduplizierungsmodus.",
        "Konsolidierte Daten, Duplikate-Report, Datenqualitaet, Konsolidierungs-Log."
    ),
    "Run_KM20b_Bereinigung": (
        "Zu bereinigende Daten, Bereinigungsregeln, Backup-Modus, Testmodus.",
        "Bereinigte Daten, Entfernte Eintraege, Protokoll, Bereinigungs-Log."
    ),
    "Update_External_Tools_Library": (
        "Tool-Liste, Update-Modus, Versionspruefung, Download-Quellen.",
        "Update-Status, neue Versionen, Fehlerliste, Hash-Verifizierung, Update-Log."
    ),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def determine_specific(modul_id):
    """Bestimmt modulspezifische eingabe/ausgabe."""
    if modul_id in SPECIFIC:
        return SPECIFIC[modul_id]

    # Pattern-basierte Fallbacks
    name_lower = modul_id.lower()

    if "ocr" in name_lower or "km13" in name_lower or "km17" in name_lower or "km18" in name_lower or "km19" in name_lower:
        return (
            "Arbeitsabbildung-Pfad, OCR-Parameter, erwartete Sprache.",
            "OCR-Ergebnis, Konfidenzwert, erkannte Sprache, Log."
        )
    if "uebersetz" in name_lower or "translation" in name_lower or "km15" in name_lower or "km21" in name_lower:
        return (
            "Quelltext, Quellsprache, Zielsprache, Terminologie.",
            "Uebersetzungsvorschlag, Fundstellen-Bindung, Konfidenz, Log."
        )
    if "posteingang" in name_lower or "vorzimmer" in name_lower:
        return (
            "Posteingangsdatei, Mandanten-ID, Sachgebiet, Prioritaet.",
            "Verarbeitetes Dokument, Weichenstellung, Status, Log."
        )
    if "quellen" in name_lower or "source" in name_lower:
        return (
            "Rechtsgebiet, Rechtsraum, Quellen-ID, Pruefmodus.",
            "Quellenstatus, Verfuegbarkeit, Fundstellen, Log."
        )
    if "ui" in name_lower or "anwalt" in name_lower or "durchstich" in name_lower or "logik" in name_lower or "tuerschwelle" in name_lower:
        return (
            "Benutzereingabe, Dokument-ID, Aktion, Parameter.",
            "UI-Status, Aktualisierte Ansicht, Ergebnis, Log."
        )
    if "agent" in name_lower or "handoff" in name_lower:
        return (
            "Agent-ID, Auftragstyp, Eingabedaten, Skill-Set.",
            "Agent-Ergebnis, Routing-Vorschlag, Skill-Verbrauch, Agent-Log."
        )
    if "aider" in name_lower or "repair" in name_lower or "check" in name_lower or "update" in name_lower or "konsolid" in name_lower or "bereinig" in name_lower or "safejob" in name_lower:
        return (
            "Konfiguration, Arbeitsverzeichnis, Parameter, Modus.",
            "Ergebnis, Status, Protokoll, Exit-Code."
        )

    # Ultimate fallback - sollte bei den 48 nicht vorkommen
    return (GENERIC_EINGABE, GENERIC_AUSGABE)


def main():
    print("=" * 70)
    print("CORE-10f PLATZHALTER VERFEINERN")
    print("=" * 70)

    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    eintraege = modulregister.get("eintraege", [])

    updated = 0
    unchanged = 0
    report_lines = [
        "=" * 70,
        "CORE-10f PLATZHALTER-VERFEINERUNGS-BERICHT",
        "=" * 70,
        f"Erstellt: 2026-05-16",
        "",
        "1. UEBERSICHT",
        "-" * 40,
    ]

    for m in eintraege:
        mid = m.get("modul_id", "")
        current_eingabe = m.get("eingabe", "")
        current_ausgabe = m.get("ausgabe", "")

        if current_eingabe == GENERIC_EINGABE and current_ausgabe == GENERIC_AUSGABE:
            new_eingabe, new_ausgabe = determine_specific(mid)
            if new_eingabe != GENERIC_EINGABE or new_ausgabe != GENERIC_AUSGABE:
                m["eingabe"] = new_eingabe
                m["ausgabe"] = new_ausgabe
                updated += 1
                report_lines.append(f"  {mid}")
                report_lines.append(f"    ALT: {current_eingabe} / {current_ausgabe}")
                report_lines.append(f"    NEU: {new_eingabe} / {new_ausgabe}")
                report_lines.append("")
            else:
                unchanged += 1
        else:
            unchanged += 1

    report_lines.extend([
        "",
        "2. ZUSAMMENFASSUNG",
        "-" * 40,
        f"  Verfeinerte Eintraege: {updated}",
        f"  Unveraenderte Eintraege: {unchanged}",
        f"  Gesamt-Eintraege: {len(eintraege)}",
        "",
        "3. ERGEBNIS",
        "-" * 40,
        f"  Generische Platzhalter uebrig: {sum(1 for m in eintraege if m.get('eingabe') == GENERIC_EINGABE and m.get('ausgabe') == GENERIC_AUSGABE)}",
        "",
        "=" * 70,
        "ENDE BERICHT",
        "=" * 70,
    ])

    # Save updated register
    save_json(REGISTER_DIR / "modulregister.json", modulregister)

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    print(f"\nBericht geschrieben nach: {REPORT_PATH}")
    print(f"Modulregister aktualisiert: {REGISTER_DIR / 'modulregister.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
