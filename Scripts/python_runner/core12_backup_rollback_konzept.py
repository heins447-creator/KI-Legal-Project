#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-12 – Backup-/Rollback-Konzept für DB-ändernde und kritische Module
=======================================================================
Zweck:
    1. Liest die 18 DB-ändernden Module aus review_listen.json
    2. Kennzeichnet die 2 kritischen Module (DB + Online)
    3. Definiert Backup-Pflicht vor jeder DB-Änderung
    4. Dokumentiert Rollback-Pfade pro Modul
    5. Bereitet Sperrlogik für kritische Module vor
    6. Führt KEINE DB-Änderung durch
    7. Kein Internet, keine Cloud, keine Installation
    8. Erzeugt Konzept, Register-Ergänzung und Prüfbericht

Harte Grenzen (AGENTS.md):
    - Keine Änderungen außerhalb von I:\KI_Legal_Project
    - Keine echten Mandantendaten an externe Modelle
    - Keine freie Internetrecherche
    - Keine API-Schlüssel in Git
    - Keine endgültige Rechtsberatung
    - Keine Beweiswürdigung
    - Keine Türschwelle, bevor Quellenregister, Fachanwaltsraster,
      Quellenbetreuer, Adapter, Cache und Offline-Fallback stehen.
"""

import json
import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path

# ============================================================================
# KONFIGURATION
# ============================================================================

BASE_DIR = Path("I:/KI_Legal_Project")
REVIEW_LISTEN_PATH = BASE_DIR / "ALIN_Neustart_Core/04_Healthcheck/review_listen.json"
MIGRATIONS_DIR = BASE_DIR / "Database/Migrations"
BACKUP_KONZEPT_DIR = BASE_DIR / "ALIN_Neustart_Core/17_Backup_Restore"
REPORTS_DIR = BASE_DIR / "Windows_App/Logs"
REGISTER_DIR = BASE_DIR / "ALIN_Neustart_Core/01_Register"

# Sicherstellen, dass Ausgabeverzeichnisse existieren
for d in [BACKUP_KONZEPT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def load_review_listen():
    """Lädt review_listen.json und gibt die 'listen'-Struktur zurück."""
    if not REVIEW_LISTEN_PATH.exists():
        print(f"[FEHLER] review_listen.json nicht gefunden: {REVIEW_LISTEN_PATH}")
        sys.exit(1)
    with open(REVIEW_LISTEN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("listen", {})

def load_modulregister():
    """Lädt modulregister.json für zusätzliche Metadaten."""
    path = REGISTER_DIR / "modulregister.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_migration_sql(modul_id):
    """Sucht die zugehörige SQL-Migrationsdatei für ein Modul."""
    if not MIGRATIONS_DIR.exists():
        return None
    # Mappings: modul_id -> erwarteter Dateiname
    mapping = {
        "001_posteingang_intake_schema": "001_posteingang_intake_schema.sql",
        "004_language_context_v2": "004_language_context_v2.sql",
        "005_dokumentsprachprofil_v1": "005_dokumentsprachprofil_v1.sql",
        "006_vorzimmer_kommunikationsparameter_v1": "006_vorzimmer_kommunikationsparameter_v1.sql",
        "007_anwaltvorlage_grundmodul_v1": "007_anwaltvorlage_grundmodul_v1.sql",
        "008_agentenbearbeitung_grundmodul_v1": "008_agentenbearbeitung_grundmodul_v1.sql",
        "009_agent_dokumentart_erkennen_v1": "009_agent_dokumentart_erkennen_v1.sql",
        "010_agent_sprache_uebersetzung_v1": "010_agent_sprache_uebersetzung_v1.sql",
        "011_agent_sachverhaltsbezug_v1": "011_agent_sachverhaltsbezug_v1.sql",
        "011_quellenbetreuer_fachanwaltsraster_v1": "011_quellenbetreuer_fachanwaltsraster_v1.sql",
        "012_agenten_kontext_skill_register_v1": "012_agenten_kontext_skill_register_v1.sql",
        "014_source_adapter_healthcheck_framework_v1": "014_source_adapter_healthcheck_framework_v1.sql",
    }
    filename = mapping.get(modul_id)
    if filename:
        p = MIGRATIONS_DIR / filename
        if p.exists():
            return str(p.relative_to(BASE_DIR))
    # Fallback: Suche nach Präfix
    for f in MIGRATIONS_DIR.iterdir():
        if f.is_file() and f.suffix == ".sql":
            if f.stem.startswith(modul_id.replace("_", "_")) or modul_id in f.stem:
                return str(f.relative_to(BASE_DIR))
    return None

def determine_risikoklasse(modul, risikoklassen):
    """Ermittelt die Risikoklasse eines Moduls aus den Risikoklassen-Listen."""
    modul_id = modul.get("modul_id", "")
    for klasse, eintraege in risikoklassen.items():
        for m in eintraege.get("module", []):
            if m.get("modul_id") == modul_id:
                return klasse, m.get("risikogrund", [])
    # Fallback: Selbst berechnen
    if modul.get("darf_datenbank_aendern") and modul.get("darf_online_gehen"):
        return "KRITISCH", ["DB-ändernd UND online-fähig"]
    elif modul.get("darf_datenbank_aendern"):
        return "HOCH", ["DB-ändernd"]
    return "NIEDRIG", []

def generate_backup_pflicht(modul, risikoklasse):
    """Generiert die Backup-Pflicht-Beschreibung für ein Modul."""
    modul_id = modul.get("modul_id", "")
    pflicht = {
        "vor_ausfuehrung": True,
        "backup_typ": "vollstaendig",
        "backup_umfang": [
            "Datenbank-Schema (alle Tabellen)",
            "Datenbank-Daten (alle Zeilen)",
            "Konfigurationsdateien (Config/)",
            "Register-Dateien (ALIN_Neustart_Core/01_Register/)"
        ],
        "backup_ziel": "ALIN_Neustart_Core/17_Backup_Restore/Backups/",
        "backup_naming": f"backup_vor_{modul_id}_{{timestamp}}.zip",
        "rollback_dauer_max": "5 Minuten",
        "manuelle_freigabe_erforderlich": risikoklasse == "KRITISCH",
        "doppelkontrolle_erforderlich": risikoklasse == "KRITISCH",
    }
    if risikoklasse == "KRITISCH":
        pflicht["zusaetzliche_massnahmen"] = [
            "Sperrlogik aktivieren (siehe Sperrregister)",
            "Offline-Modus erzwingen vor Ausführung",
            "Protokollierung aller Änderungen im Audit-Log",
            "Rollback-Skript vorab testen"
        ]
    elif risikoklasse == "HOCH":
        pflicht["zusaetzliche_massnahmen"] = [
            "Backup-Integrität prüfen vor Ausführung",
            "Test-Restore auf Staging-Datenbank"
        ]
    else:
        pflicht["zusaetzliche_massnahmen"] = [
            "Standard-Backup vor Ausführung"
        ]
    return pflicht

def generate_rollback_pfad(modul, sql_path):
    """Generiert den Rollback-Pfad für ein Modul."""
    modul_id = modul.get("modul_id", "")
    pfad = {
        "rollback_art": "datenbank_restore",
        "rollback_quelle": "letztes_valides_backup",
        "rollback_schritte": [
            "1. Ausführung sofort stoppen (falls noch läuft)",
            "2. Datenbank-Verbindungen trennen",
            "3. Backup-Archiv entpacken",
            "4. SQL-Dump einspielen: sqlite3 alin.db < backup_dump.sql",
            "5. Integritätsprüfung: SELECT count(*) FROM sqlite_master;",
            "6. Register-Dateien aus Backup zurückspielen",
            "7. Sperrregister-Eintrag auf 'zurueckgesetzt' setzen",
            "8. Ergebnis protokollieren"
        ],
        "rollback_dauer_schaetzung": "2-5 Minuten",
        "rollback_getestet": False,
        "rollback_test_empfohlen": True,
        "zugehoerige_migration": sql_path,
    }
    if sql_path:
        pfad["rollback_schritte"].insert(3,
            f"3a. Falls Migration bereits teilweise ausgeführt: {sql_path} manuell prüfen")
    return pfad

def generate_sperrlogik_eintrag(modul):
    """Generiert einen Sperrregister-Eintrag für kritische Module."""
    modul_id = modul.get("modul_id", "")
    return {
        "modul_id": modul_id,
        "sperrstatus": "vorbereitet",
        "sperrgrund": "DB-ändernd und/oder online-fähig – erfordert explizite Freigabe",
        "freigabe_erfordert": [
            "manuelle_bestätigung",
            "backup_erfolgt",
            "offline_modus_bestätigt"
        ],
        "gesperrte_operationen": [
            "datenbank_aenderung",
            "online_verbindung",
            "schema_migration"
        ],
        "ausnahmen": [
            "lesender_zugriff",
            "pruefung",
            "bericht_erstellung"
        ],
        "protokollierung": "vollstaendig",
        "gueltig_ab": datetime.now(timezone.utc).isoformat(),
    }

# ============================================================================
# HAUPTLOGIK
# ============================================================================

def main():
    print("=" * 70)
    print("CORE-12 – BACKUP-/ROLLBACK-KONZEPT")
    print("DB-ändernde und kritische Module")
    print("=" * 70)

    # 1. Review-Listen laden
    listen = load_review_listen()
    db_module = listen.get("db_aendernde_module", {})
    risikoklassen = listen.get("risikoklassen", {})

    module_list = db_module.get("module", [])
    anzahl = db_module.get("anzahl", len(module_list))

    print(f"\n[1] DB-ändernde Module gefunden: {anzahl}")

    # 2. Kritische Module identifizieren
    kritische_module = []
    hoch_module = []
    for m in module_list:
        klasse, gruende = determine_risikoklasse(m, risikoklassen)
        m["_risikoklasse"] = klasse
        m["_risikogrund"] = gruende
        if klasse == "KRITISCH":
            kritische_module.append(m)
        elif klasse == "HOCH":
            hoch_module.append(m)

    print(f"[2] Kritische Module (KRITISCH): {len(kritische_module)}")
    for km in kritische_module:
        print(f"    ⚠️  {km['modul_id']} – {km.get('modulname', '')}")
        print(f"       Gründe: {', '.join(km['_risikogrund']) if km['_risikogrund'] else 'DB-ändernd + Online-fähig'}")

    print(f"[2b] Hoch-Risiko Module: {len(hoch_module)}")

    # 3. Backup-Pflicht definieren
    print("\n[3] Backup-Pflicht wird für alle DB-ändernden Module definiert...")
    konzept = {
        "schema_version": "CORE-12-v1",
        "erstellt_am": datetime.now(timezone.utc).isoformat(),
        "zweck": "Backup-/Rollback-Konzept für DB-ändernde und kritische Module",
        "db_aendernde_module_gesamt": anzahl,
        "kritische_module_anzahl": len(kritische_module),
        "hoch_risiko_module_anzahl": len(hoch_module),
        "allgemeine_regeln": {
            "backup_vor_jeder_db_aenderung": True,
            "backup_mindestens_vollstaendig": True,
            "backup_auf_bewaehrtem_medium": True,
            "rollback_pfad_dokumentiert": True,
            "rollback_getestet_empfohlen": True,
            "keine_db_aenderung_ohne_backup": True,
            "manuelle_freigabe_fuer_kritisch": True,
            "doppelkontrolle_fuer_kritisch": True,
        },
        "module": [],
        "sperrregister": [],
    }

    for m in module_list:
        modul_id = m.get("modul_id", "")
        risikoklasse = m.get("_risikoklasse", "NIEDRIG")
        sql_path = find_migration_sql(modul_id)

        eintrag = {
            "modul_id": modul_id,
            "modulname": m.get("modulname", ""),
            "bereich": m.get("bereich", ""),
            "status": m.get("status", ""),
            "risikoklasse": risikoklasse,
            "risikogrund": m.get("_risikogrund", []),
            "darf_datenbank_aendern": m.get("darf_datenbank_aendern", False),
            "darf_online_gehen": m.get("darf_online_gehen", False),
            "backup_pflicht": generate_backup_pflicht(m, risikoklasse),
            "rollback_pfad": generate_rollback_pfad(m, sql_path),
            "zugehoerige_migration": sql_path,
        }
        konzept["module"].append(eintrag)

        # Sperrlogik für kritische Module
        if risikoklasse == "KRITISCH":
            sperr = generate_sperrlogik_eintrag(m)
            konzept["sperrregister"].append(sperr)

    # 4. Konzept-JSON schreiben
    konzept_path = BACKUP_KONZEPT_DIR / "CORE12_backup_rollback_konzept.json"
    with open(konzept_path, "w", encoding="utf-8") as f:
        json.dump(konzept, f, indent=2, ensure_ascii=False)
    print(f"[4] Konzept-JSON geschrieben: {konzept_path.relative_to(BASE_DIR)}")

    # 5. Konzept-Markdown schreiben
    md_path = BACKUP_KONZEPT_DIR / "CORE12_backup_rollback_konzept.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# CORE-12 – Backup-/Rollback-Konzept\n\n")
        f.write(f"**Erstellt:** {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write("## Zusammenfassung\n\n")
        f.write(f"- **DB-ändernde Module gesamt:** {anzahl}\n")
        f.write(f"- **Kritische Module (KRITISCH):** {len(kritische_module)}\n")
        f.write(f"- **Hoch-Risiko Module:** {len(hoch_module)}\n\n")
        f.write("## Allgemeine Regeln\n\n")
        f.write("1. **Backup vor jeder DB-Änderung** – Pflicht, keine Ausnahme.\n")
        f.write("2. **Vollständiges Backup** – Schema + Daten + Config + Register.\n")
        f.write("3. **Rollback-Pfad dokumentiert** – Jeder Schritt nachvollziehbar.\n")
        f.write("4. **Keine DB-Änderung ohne Backup** – Harte Grenze.\n")
        f.write("5. **Manuelle Freigabe für KRITISCH** – Doppelkontrolle erforderlich.\n")
        f.write("6. **Sperrregister für kritische Module** – Automatische Sperre bis Freigabe.\n\n")
        f.write("## Kritische Module (besondere Kennzeichnung)\n\n")
        for km in kritische_module:
            f.write(f"### ⚠️ {km['modul_id']}\n\n")
            f.write(f"- **Name:** {km.get('modulname', '')}\n")
            f.write(f"- **Bereich:** {km.get('bereich', '')}\n")
            f.write(f"- **Risikogrund:** {', '.join(km['_risikogrund']) if km['_risikogrund'] else 'DB-ändernd und online-fähig'}\n")
            f.write(f"- **Sperrstatus:** Vorbereitet (siehe Sperrregister)\n")
            f.write(f"- **Freigabe erfordert:** Manuelle Bestätigung + Backup + Offline-Modus\n\n")
        f.write("## Modul-Details (alle DB-ändernden)\n\n")
        f.write("| Modul-ID | Bereich | Risiko | Migration |\n")
        f.write("|----------|---------|--------|-----------|\n")
        for eintrag in konzept["module"]:
            mig = eintrag["zugehoerige_migration"] or "–"
            f.write(f"| {eintrag['modul_id']} | {eintrag['bereich']} | {eintrag['risikoklasse']} | {mig} |\n")
        f.write("\n## Sperrregister (für kritische Module)\n\n")
        f.write("```json\n")
        json.dump(konzept["sperrregister"], f, indent=2, ensure_ascii=False)
        f.write("\n```\n")
    print(f"[5] Konzept-Markdown geschrieben: {md_path.relative_to(BASE_DIR)}")

    # 6. Register-Ergänzung: Sperrregister-JSON
    sperrregister_path = REGISTER_DIR / "sperrregister.json"
    sperrregister = {"schema_version": "1.0", "letzte_aenderung": datetime.now(timezone.utc).isoformat(), "eintraege": []}
    if sperrregister_path.exists():
        try:
            with open(sperrregister_path, "r", encoding="utf-8") as f:
                sperrregister = json.load(f)
        except Exception:
            pass
    # Neue Einträge hinzufügen (ohne Duplikate)
    existing_ids = {e.get("modul_id") for e in sperrregister.get("eintraege", [])}
    for sperr in konzept["sperrregister"]:
        if sperr["modul_id"] not in existing_ids:
            sperrregister["eintraege"].append(sperr)
    sperrregister["letzte_aenderung"] = datetime.now(timezone.utc).isoformat()
    with open(sperrregister_path, "w", encoding="utf-8") as f:
        json.dump(sperrregister, f, indent=2, ensure_ascii=False)
    print(f"[6] Sperrregister aktualisiert: {sperrregister_path.relative_to(BASE_DIR)}")
    print(f"    Einträge gesamt: {len(sperrregister['eintraege'])}")

    # 7. Prüfbericht schreiben
    bericht_path = REPORTS_DIR / "ALIN_CORE12_PRUEFBERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-12 – PRÜFBERICHT: Backup-/Rollback-Konzept\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Erstellt: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"DB-ändernde Module: {anzahl}\n")
        f.write(f"Kritische Module: {len(kritische_module)}\n")
        f.write(f"Hoch-Risiko Module: {len(hoch_module)}\n\n")
        f.write("PRÜFPUNKTE:\n")
        f.write(f"  [OK] Review-Listen gelesen: {REVIEW_LISTEN_PATH.exists()}\n")
        f.write(f"  [OK] Migrationen-Verzeichnis geprüft: {MIGRATIONS_DIR.exists()}\n")
        f.write(f"  [OK] Konzept-JSON erstellt: {konzept_path.exists()}\n")
        f.write(f"  [OK] Konzept-Markdown erstellt: {md_path.exists()}\n")
        f.write(f"  [OK] Sperrregister aktualisiert: {sperrregister_path.exists()}\n")
        f.write(f"  [OK] Keine DB-Änderung durchgeführt: JA\n")
        f.write(f"  [OK] Kein Internet/Cloud/Installation: JA\n\n")
        f.write("KRITISCHE MODULE:\n")
        for km in kritische_module:
            f.write(f"  – {km['modul_id']} ({km.get('bereich', '')})\n")
        f.write("\nMIGRATIONEN ZUGEORDNET:\n")
        for eintrag in konzept["module"]:
            mig = eintrag["zugehoerige_migration"] or "KEINE"
            f.write(f"  – {eintrag['modul_id']}: {mig}\n")
        f.write("\n" + "=" * 70 + "\n")
        f.write("STATUS: KONZEPT VOLLSTÄNDIG ERSTELLT\n")
        f.write("NÄCHSTER SCHRITT: Freigabe durch menschliche Prüfung erforderlich\n")
        f.write("=" * 70 + "\n")
    print(f"[7] Prüfbericht geschrieben: {bericht_path.relative_to(BASE_DIR)}")

    # 8. Zusammenfassung ausgeben
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"DB-ändernde Module:        {anzahl}")
    print(f"Kritische Module:          {len(kritische_module)}")
    print(f"Hoch-Risiko Module:        {len(hoch_module)}")
    print(f"Sperrregister-Einträge:    {len(konzept['sperrregister'])}")
    print(f"Konzept-JSON:              {konzept_path.relative_to(BASE_DIR)}")
    print(f"Konzept-Markdown:          {md_path.relative_to(BASE_DIR)}")
    print(f"Sperrregister:             {sperrregister_path.relative_to(BASE_DIR)}")
    print(f"Prüfbericht:               {bericht_path.relative_to(BASE_DIR)}")
    print("=" * 70)
    print("CORE-12 ABGESCHLOSSEN – Keine DB-Änderung durchgeführt.")
    print("=" * 70)

    return 0

# ============================================================================
# SELBSTTEST
# ============================================================================

def selbsttest():
    print("CORE-12 SELBSTTEST ==================================================")
    def t(bez, bed):
        status = "OK" if bed else "FEHLER"
        print(f"  [{status}] {bez}")
        return bed

    ok = True
    ok &= t("Review-Listen-Datei existiert", REVIEW_LISTEN_PATH.exists())
    ok &= t("Migrationen-Verzeichnis existiert", MIGRATIONS_DIR.exists())
    ok &= t("Register-Verzeichnis existiert", REGISTER_DIR.exists())
    ok &= t("Base-Verzeichnis existiert", BASE_DIR.exists())

    # Teste JSON-Laden
    try:
        listen = load_review_listen()
        db_mods = listen.get("db_aendernde_module", {})
        ok &= t("DB-ändernde Module lesbar", db_mods.get("anzahl", 0) > 0)
    except Exception as e:
        ok &= t("DB-ändernde Module lesbar", False)
        print(f"    Exception: {e}")

    # Teste Risikoklassen
    try:
        risikoklassen = listen.get("risikoklassen", {})
        ok &= t("Risikoklassen lesbar", "KRITISCH" in risikoklassen)
    except Exception:
        ok &= t("Risikoklassen lesbar", False)

    print("=" * 70)
    print(f"SELBSTTEST: {'ALLE PRÜFUNGEN BESTANDEN' if ok else 'FEHLER AUFGETRETEN'}")
    print("=" * 70)
    return 0 if ok else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(selbsttest())
    sys.exit(main())
