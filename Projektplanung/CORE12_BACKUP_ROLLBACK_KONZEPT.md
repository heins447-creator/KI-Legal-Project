# CORE-12 – Backup-/Rollback-Konzept für DB-ändernde und kritische Module

## Metadaten

| Feld | Wert |
|------|------|
| **Modul-ID** | `core12_backup_rollback_konzept` |
| **Schema-Version** | `CORE-12-v1` |
| **Status** | Konzept vollständig erstellt |
| **Zweck** | Backup-Pflicht, Rollback-Pfade und Sperrlogik für alle DB-ändernden Module |
| **Sperrregister-Status** | Verbindliches Register (versioniert, siehe CORE-12a) |

## Zusammenfassung

Dieses Modul erstellt ein **Backup-/Rollback-Konzept** für alle 18 DB-ändernden Module des Projekts. Es identifiziert 2 kritische Module (DB-ändernd **und** online-fähig), definiert Backup-Pflichten, dokumentiert Rollback-Pfade und bereitet eine Sperrlogik vor.

**Wichtig:** Dieses Modul führt **keine DB-Änderung** durch. Es ist rein konzeptionell und erzeugt Dokumentation sowie Register-Ergänzungen.

## Liefergegenstände

| # | Datei | Zweck |
|---|-------|-------|
| 1 | `Scripts/python_runner/core12_backup_rollback_konzept.py` | Python-Runner – liest Review-Listen, erzeugt Konzept |
| 2 | `Scripts/python_runner/check_core12_backup_rollback_konzept.py` | Prüfdatei – 15+ Checks |
| 3 | `Scripts/CORE12_BACKUP_ROLLBACK_KONZEPT_AUTOLAUF.ps1` | PowerShell-Starter |
| 4 | `Config/core12_backup_rollback_konzept_v1.json` | Konfiguration (gitignored) |
| 5 | `Projektplanung/CORE12_BACKUP_ROLLBACK_KONZEPT.md` | Diese Dokumentation |
| 6 | `ALIN_Neustart_Core/17_Backup_Restore/CORE12_backup_rollback_konzept.json` | Erzeugtes Konzept-JSON |
| 7 | `ALIN_Neustart_Core/17_Backup_Restore/CORE12_backup_rollback_konzept.md` | Erzeugtes Konzept-Markdown |
| 8 | `ALIN_Neustart_Core/01_Register/sperrregister.json` | Ergänztes Sperrregister |
| 9 | `Windows_App/Logs/ALIN_CORE12_PRUEFBERICHT.txt` | Prüfbericht |

## DB-ändernde Module (18 Stück)

Die folgenden Module haben `darf_datenbank_aendern = true`:

| # | Modul-ID | Bereich | Migration |
|---|----------|---------|-----------|
| 1 | `001_db_schema_audit` | register | – |
| 2 | `002_apply_posteingang_schema` | posteingang | – |
| 3 | `003_verify_posteingang_schema` | posteingang | – |
| 4 | `013_posteingang_db_altlasten_cleanup` | posteingang | – |
| 5 | `021_posteingang_db_dateien_auswahl_testlauf_v1` | posteingang | – |
| 6 | `022_posteingang_db_testlauf_auswertung_v1` | posteingang | – |
| 7 | `001_posteingang_intake_schema` | posteingang | `001_posteingang_intake_schema.sql` |
| 8 | `004_language_context_v2` | register | `004_language_context_v2.sql` |
| 9 | `005_dokumentsprachprofil_v1` | sprache | `005_dokumentsprachprofil_v1.sql` |
| 10 | `006_vorzimmer_kommunikationsparameter_v1` | vorzimmer | `006_vorzimmer_kommunikationsparameter_v1.sql` |
| 11 | `007_anwaltvorlage_grundmodul_v1` | anwalt | `007_anwaltvorlage_grundmodul_v1.sql` |
| 12 | `008_agentenbearbeitung_grundmodul_v1` | agent | `008_agentenbearbeitung_grundmodul_v1.sql` |
| 13 | `009_agent_dokumentart_erkennen_v1` | agent | `009_agent_dokumentart_erkennen_v1.sql` |
| 14 | `010_agent_sprache_uebersetzung_v1` | agent | `010_agent_sprache_uebersetzung_v1.sql` |
| 15 | `011_agent_sachverhaltsbezug_v1` | agent | `011_agent_sachverhaltsbezug_v1.sql` |
| 16 | `011_quellenbetreuer_fachanwaltsraster_v1` | anwalt | `011_quellenbetreuer_fachanwaltsraster_v1.sql` |
| 17 | `012_agenten_kontext_skill_register_v1` | agent | `012_agenten_kontext_skill_register_v1.sql` |
| 18 | `014_source_adapter_healthcheck_framework_v1` | quellen | `014_source_adapter_healthcheck_framework_v1.sql` |

## Kritische Module (2 Stück)

Diese Module sind **KRITISCH**, weil sie sowohl DB-ändernd **als auch** online-fähig sind:

### ⚠️ `011_quellenbetreuer_fachanwaltsraster_v1`
- **Bereich:** anwalt
- **Risiko:** DB-ändernd + Online-fähig
- **Sperrstatus:** Vorbereitet
- **Freigabe erfordert:** Manuelle Bestätigung + Backup + Offline-Modus

### ⚠️ `014_source_adapter_healthcheck_framework_v1`
- **Bereich:** quellen
- **Risiko:** DB-ändernd + Online-fähig
- **Sperrstatus:** Vorbereitet
- **Freigabe erfordert:** Manuelle Bestätigung + Backup + Offline-Modus

## Backup-Pflicht

### Allgemeine Regeln (gilt für alle 18 Module)

1. **Backup vor jeder DB-Änderung** – Pflicht, keine Ausnahme.
2. **Vollständiges Backup** – Schema + Daten + Config + Register.
3. **Rollback-Pfad dokumentiert** – Jeder Schritt nachvollziehbar.
4. **Keine DB-Änderung ohne Backup** – Harte Grenze.

### Zusätzliche Maßnahmen für KRITISCHE Module

- **Manuelle Freigabe** erforderlich
- **Doppelkontrolle** erforderlich
- **Sperrlogik aktivieren** (siehe Sperrregister)
- **Offline-Modus erzwingen** vor Ausführung
- **Protokollierung** aller Änderungen im Audit-Log
- **Rollback-Skript vorab testen**

### Zusätzliche Maßnahmen für HOCH-Risiko Module

- Backup-Integrität prüfen vor Ausführung
- Test-Restore auf Staging-Datenbank

## Rollback-Pfad

### Standard-Rollback (alle DB-ändernden Module)

1. Ausführung sofort stoppen (falls noch läuft)
2. Datenbank-Verbindungen trennen
3. Backup-Archiv entpacken
4. SQL-Dump einspielen: `sqlite3 alin.db < backup_dump.sql`
5. Integritätsprüfung: `SELECT count(*) FROM sqlite_master;`
6. Register-Dateien aus Backup zurückspielen
7. Sperrregister-Eintrag auf 'zurueckgesetzt' setzen
8. Ergebnis protokollieren

**Geschätzte Dauer:** 2–5 Minuten

## Sperrregister (verbindliches Register)

Das Sperrregister (`ALIN_Neustart_Core/01_Register/sperrregister.json`) ist ein **verbindliches Register** und wird versioniert (nicht gitignored).

Es enthält für jedes kritische Modul:

- `modul_id` – Eindeutige Identifikation
- `sperrstatus` – Aktuell: `vorbereitet`
- `sperrgrund` – Begründung für die Sperre
- `freigabe_erfordert` – Liste der Freigabe-Bedingungen
- `gesperrte_operationen` – Was blockiert wird
- `ausnahmen` – Was erlaubt bleibt (z. B. lesender Zugriff)
- `protokollierung` – Vollständige Protokollierung

**Hinweis:** Das Sperrregister wird manuell gepflegt (kein Laufzeit-Artefakt). Änderungen erfordern Git-Commit.

## Harte Grenzen

- **Keine DB-Änderung** durch dieses Modul
- **Kein Internet**, keine Cloud, keine Installation
- **Nur konzeptionelle** Arbeit – Dokumentation und Register-Ergänzung
- **Keine echten Mandantendaten** verarbeitet

## Abhängigkeiten

- `ALIN_Neustart_Core/04_Healthcheck/review_listen.json` (Eingabe)
- `Database/Migrations/` (Referenz für SQL-Dateien)
- `ALIN_Neustart_Core/01_Register/modulregister.json` (optional, für Metadaten)

## Nächste Schritte

1. **Menschliche Prüfung** des Konzepts durch Projektleitung
2. **Freigabe** der Sperrlogik für kritische Module
3. **Test-Restore** auf Staging-Datenbank durchführen
4. **Integration** des Backup-/Rollback-Konzepts in die Windows-App
5. **UI04b** oder weitere Module erstellen (nach Freigabe)

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| v1 | 2026-05-16 | Erstellerstellung des Konzepts |
| v1.1 | 2026-05-16 | CORE-12a: Sperrregister als verbindliches Register geklärt und versioniert |
