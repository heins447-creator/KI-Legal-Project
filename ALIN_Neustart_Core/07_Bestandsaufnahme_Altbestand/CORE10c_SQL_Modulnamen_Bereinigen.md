# CORE-10c – SQL-Modulnamen bereinigen

## Metadaten

| Feld | Wert |
|------|------|
| Auftrag | CORE-10c |
| Vorlage | CORE-10a P03 |
| Erstellt | 2026-05-16 |
| Status | Abgeschlossen |

## Ziel

20 Module im `modulregister.json` hatten SQL-Code als `modulname` (z.B. `SELECT table_name`, `SELECT COUNT(*)`). Diese wurden auf den korrekten Dateinamen korrigiert.

## Durchgeführte Änderungen

### Geänderte Datei

- `ALIN_Neustart_Core/01_Register/modulregister.json` – 20 Modulnamen korrigiert

### Korrigierte Module

| modul_id | Alter modulname | Neuer modulname |
|----------|-----------------|-----------------|
| 001_db_schema_audit | SELECT table_schema, table_name, table_type | 001_db_schema_audit |
| 002_apply_posteingang_schema | SELECT table_name | 002_apply_posteingang_schema |
| 003_verify_posteingang_schema | SELECT table_name | 003_verify_posteingang_schema |
| 012_posteingang_sprachkontext_gate_v2 | SELECT table_name | 012_posteingang_sprachkontext_gate_v2 |
| 013_kontrolle_posteingang_nach_bereinigung | SELECT table_name | 013_kontrolle_posteingang_nach_bereinigung |
| 013_posteingang_db_altlasten_cleanup | SELECT COUNT(*) | 013_posteingang_db_altlasten_cleanup |
| 014_posteingang_clean_verify | SELECT COUNT(*) | 014_posteingang_clean_verify |
| 020_posteingang_gesamtstatus_v1 | SELECT table_name | 020_posteingang_gesamtstatus_v1 |
| 021_posteingang_db_dateien_auswahl_testlauf_v1 | SELECT table_name | 021_posteingang_db_dateien_auswahl_testlauf_v1 |
| 025_schweden_arbeitsrecht_sprachkontext_korrektur_v1 | SELECT COUNT(*) | 025_schweden_arbeitsrecht_sprachkontext_korrektur_v1 |
| 032_check_dokumentsprachprofil_v1 | SELECT table_name | 032_check_dokumentsprachprofil_v1 |
| 033_posteingang_schlusskontrolle_v2 | SELECT table_name | 033_posteingang_schlusskontrolle_v2 |
| 034_posteingang_endabnahme_v2 | SELECT table_name | 034_posteingang_endabnahme_v2 |
| 036_check_vorzimmer_kommunikationsparameter_v1 | SELECT table_name | 036_check_vorzimmer_kommunikationsparameter_v1 |
| 037_posteingang_endabnahme_v3 | SELECT table_name | 037_posteingang_endabnahme_v3 |
| 039_check_anwaltvorlage_grundmodul_v1 | SELECT table_name | 039_check_anwaltvorlage_grundmodul_v1 |
| 041_check_agentenbearbeitung_grundmodul_v1 | SELECT table_name | 041_check_agentenbearbeitung_grundmodul_v1 |
| 043_check_agent_dokumentart_erkennen_v1 | SELECT table_name | 043_check_agent_dokumentart_erkennen_v1 |
| 045_check_agent_sprache_uebersetzung_v1 | SELECT table_name | 045_check_agent_sprache_uebersetzung_v1 |
| 047_check_agent_sachverhaltsbezug_v1 | SELECT table_name | 047_check_agent_sachverhaltsbezug_v1 |

## Grenzen

- Nur `ALIN_Neustart_Core` geändert
- Keine Ressourcen ergänzt
- Keine Schnittstellen gebaut
- Keine Abhängigkeiten repariert
- Keine Altbestandsdateien geändert

## Liefergegenstände

| # | Datei | Pfad |
|---|-------|------|
| 1 | Python-Skript | `ALIN_Neustart_Core/Scripts/alin_core10c_sql_modulnamen_bereinigen.py` |
| 2 | Prüfdatei | `ALIN_Neustart_Core/Scripts/check_alin_core10c_sql_modulnamen.py` |
| 3 | PowerShell-Starter | `ALIN_Neustart_Core/Scripts/Run_CORE10c_SQL_Modulnamen.ps1` |
| 4 | Bericht | `ALIN_Neustart_Core/Reports/ALIN_CORE10C_SQL_MODULNAMEN_BERICHT.txt` |
| 5 | Geändertes Register | `ALIN_Neustart_Core/01_Register/modulregister.json` |
