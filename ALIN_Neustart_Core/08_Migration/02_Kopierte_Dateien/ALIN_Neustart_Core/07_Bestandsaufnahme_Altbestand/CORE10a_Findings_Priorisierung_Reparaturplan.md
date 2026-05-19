# CORE-10a – Findings priorisieren und Reparaturauftraege ableiten

## Metadaten

| Feld | Wert |
|------|------|
| Auftrag | CORE-10a |
| Vorlage | CORE-10 |
| Erstellt | 2026-05-16 |
| Status | Abgeschlossen (nur Analyse, keine Reparatur) |
| Gesamtfindings | 551 |

## Ziel

Die 551 Findings aus CORE-10 werden nach P0-P3 priorisiert. Fuer jede Gruppe wird abgeleitet:

- Was ist das Problem?
- Welche Dateien sind betroffen?
- Wie viele Findings?
- Welches Risiko?
- Was darf geaendert werden?
- Was darf NICHT geaendert werden?
- Welcher Folgeauftrag ergibt sich?
- Ist Anwaltspruefung erforderlich?

## P0 – KRITISCH (310 Findings)

### P02: Fehlende Abhaengigkeiten (1 Finding)

| Feld | Wert |
|------|------|
| Problem | Modul `check_ui01_anwaltsansicht_v1` referenziert nicht-existentes Modul `ui01_anwaltsansicht` |
| Betroffene Dateien | `modulregister.json` (Eintrag `check_ui01_anwaltsansicht_v1`) |
| Anzahl | 1 Finding |
| Risiko | HOCH – Laufzeitfehler, Modul kann nicht ausgefuehrt werden |
| Erlaubte Aenderungen | `modulregister.json`: `abhaengigkeiten` korrigieren ODER `ui01_anwaltsansicht` nachinventarisieren |
| Verbotene Aenderungen | Keine Aenderung an Quellcode der referenzierten (nicht existenten) Module |
| Folgeauftrag | **CORE-10a-P02**: Abhaengigkeit korrigieren – entweder `ui01_anwaltsansicht` nachinventarisieren oder Referenz entfernen |
| Anwaltspruefung | Nein |

### P03: Widerspruechliche Modulnamen (123 Findings, 20 Module)

| Feld | Wert |
|------|------|
| Problem | 20 Module haben SQL-Code als `modulname` (z.B. `SELECT table_name`, `SELECT COUNT(*)`). Die CORE-09-Heuristik `determine_modulname()` hat SQL-Fragmente aus dem Quellcode statt des Dateinamens extrahiert. |
| Betroffene Dateien | `modulregister.json` (20 Eintraege), `alin_core09_modulregister_befuellen.py` (Heuristik) |
| Anzahl | 123 Findings (Paarvergleiche), 20 Module |
| Risiko | HOCH – Registerabfragen nach Modulnamen liefern falsche Ergebnisse. Konsistenzpruefungen werden unbrauchbar. |
| Erlaubte Aenderungen | `modulregister.json`: `modulname` korrigieren auf Basis des Dateinamens (ohne Pfad/Endung). `alin_core09_modulregister_befuellen.py`: Heuristik korrigieren. |
| Verbotene Aenderungen | Keine Aenderung an den Python-Quelldateien der 20 Module selbst (nur Register-Metadaten) |
| Folgeauftrag | **CORE-10a-P03**: Heuristik in CORE-09 korrigieren (`determine_modulname`) und 20 Modulnamen im Register bereinigen |
| Anwaltspruefung | Nein |

**Betroffene Module:**

- `002_apply_posteingang_schema` → modulname=`SELECT table_name`
- `003_verify_posteingang_schema` → modulname=`SELECT table_name`
- `012_posteingang_sprachkontext_gate_v2` → modulname=`SELECT table_name`
- `013_kontrolle_posteingang_nach_bereinigung` → modulname=`SELECT table_name`
- `013_posteingang_db_altlasten_cleanup` → modulname=`SELECT COUNT(*)`
- `014_posteingang_clean_verify` → modulname=`SELECT COUNT(*)`
- `020_posteingang_gesamtstatus_v1` → modulname=`SELECT table_name`
- `021_posteingang_db_dateien_auswahl_testlauf_v1` → modulname=`SELECT table_name`
- `025_schweden_arbeitsrecht_sprachkontext_korrektur_v1` → modulname=`SELECT COUNT(*)`
- `032_check_dokumentsprachprofil_v1` → modulname=`SELECT table_name`
- `033_posteingang_schlusskontrolle_v2` → modulname=`SELECT table_name`
- `034_posteingang_endabnahme_v2` → modulname=`SELECT table_name`
- `036_check_vorzimmer_kommunikationsparameter_v1` → modulname=`SELECT table_name`
- `037_posteingang_endabnahme_v3` → modulname=`SELECT table_name`
- `039_check_anwaltvorlage_grundmodul_v1` → modulname=`SELECT table_name`
- `041_check_agentenbearbeitung_grundmodul_v1` → modulname=`SELECT table_name`
- `043_check_agent_dokumentart_erkennen_v1` → modulname=`SELECT table_name`
- `045_check_agent_sprache_uebersetzung_v1` → modulname=`SELECT table_name`
- `047_check_agent_sachverhaltsbezug_v1` → modulname=`SELECT table_name`

### P10: Querregister-Verknuepfungen (186 Findings, 35 Module, 8 Ressourcen)

| Feld | Wert |
|------|------|
| Problem | 186 Verweise auf Ressourcen, die im `ressourcenregister.json` nicht existieren. TESS_SPA, TESS_NLD, TESS_POL (Tesseract-Sprachpakete) und ARGOS_DE_* (Argos-Translate-Sprachpaare) fehlen. |
| Betroffene Dateien | `modulregister.json` (35 Module mit ungueltigen Ressourcen), `ressourcenregister.json` (fehlende Eintraege) |
| Anzahl | 186 Findings, 35 Module, 8 fehlende Ressourcen |
| Risiko | MITTEL-HOCH – Module koennen nicht ausgefuehrt werden, wenn Ressourcen fehlen. Offline-Betrieb auf Gerichtslaptop beeintraechtigt. |
| Erlaubte Aenderungen | `ressourcenregister.json`: Fehlende Ressourcen nachinventarisieren ODER `modulregister.json`: Verweise entfernen, wenn Ressourcen nicht mehr benoetigt |
| Verbotene Aenderungen | Keine Installation tatsaechlicher Tesseract/Argos-Pakete (nur Register-Eintragung) |
| Folgeauftrag | **CORE-10a-P10**: Ressourcenregister vervollstaendigen (TESS_* und ARGOS_DE_*) oder Modulregister bereinigen |
| Anwaltspruefung | Nein |

**Fehlende Ressourcen:**

- `TESS_SPA` – Tesseract Spanisch
- `TESS_NLD` – Tesseract Niederlaendisch
- `TESS_POL` – Tesseract Polnisch
- `ARGOS_DE_SV` – Argos Deutsch-Schwedisch
- `ARGOS_DE_ES` – Argos Deutsch-Spanisch
- `ARGOS_DE_NL` – Argos Deutsch-Niederlaendisch
- `ARGOS_DE_PL` – Argos Deutsch-Polnisch
- `ARGOS_DE_FR` – Argos Deutsch-Franzoesisch

## P1 – HOCH (16 Findings)

### P09: Schema-Luecken (16 Findings, 16 Module)

| Feld | Wert |
|------|------|
| Problem | 16 Module liefern Daten an andere Module, aber ihr Bereich passt zu keinem der 8 definierten Schnittstellen-Schemas. Neue Uebergaben (vorzimmer, agent, quellen, sprache, ui) sind nicht abgedeckt. |
| Betroffene Dateien | `03_Schnittstellen/` (fehlende Schemas), `modulregister.json` (16 Module) |
| Anzahl | 16 Findings, 16 Module |
| Risiko | MITTEL – Keine Schema-Validierung moeglich. Datenformat-Inkonsistenzen zwischen Modulen wahrscheinlich. |
| Erlaubte Aenderungen | Neue Schnittstellen-Schemas erstellen (`03_Schnittstellen/`) oder Bereichszuordnung korrigieren |
| Verbotene Aenderungen | Keine Aenderung an Modul-Quellcode ohne begleitende Schema-Aenderung |
| Folgeauftrag | **CORE-10a-P09**: Schnittstellen-Schemas fuer Bereiche `vorzimmer`, `agent`, `quellen`, `sprache`, `ui` erstellen |
| Anwaltspruefung | Nein |

**Betroffene Module nach Bereich:**

- **vorzimmer**: `017_vorzimmer_arbeitsliste_v1`, `018_vorzimmer_entscheidung_v1`, `035_vorzimmer_kommunikationsparameter_v1`
- **agent**: `040_agentenbearbeitung_grundmodul_v1`, `042_agent_dokumentart_erkennen_v1`, `044_agent_sprache_uebersetzung_v1`, `046_agent_sachverhaltsbezug_v1`, `048_agenten_kontext_skill_register_v1`, `055_agent_handoff_test_harness_v1`
- **quellen**: `051_quellenkandidaten_eu_se_v1`, `053_source_adapter_healthcheck_framework_v1`, `km20_quellen_fundstellen_konsolidierung`
- **sprache**: `km15_arbeitsuebersetzung_fundstellenbindung`, `km21_translation_env_prepare`
- **ui**: `ui02_tuerschwelle_bau`, `ui03_0_uebergabe_mandantenakte`, `ui04b_logikpruefung_entscheidung`

## P2 – MITTEL (96 Findings)

### P04/P08: Platzhalter-Eingaben/Ausgaben (96 Findings, 48 Module)

| Feld | Wert |
|------|------|
| Problem | 48 PowerShell-Starter haben identische Platzhalter-Beschreibungen fuer Eingabe/Ausgabe (`Konfiguration und Umgebungsvariablen` / `Prozess-Start, Log-Datei, Exit-Code`). Keine spezifische Schnittstellenbeschreibung. |
| Betroffene Dateien | `modulregister.json` (48 PowerShell-Starter) |
| Anzahl | 96 Findings (48 x Eingabe + 48 x Ausgabe) |
| Risiko | NIEDRIG-MITTEL – Eingabe/Ausgabe nicht dokumentiert. Wartung und Fehlersuche erschwert. |
| Erlaubte Aenderungen | `modulregister.json`: `eingabe`/`ausgabe` auf spezifische Parameter erweitern |
| Verbotene Aenderungen | Keine Aenderung an PowerShell-Skripten selbst (nur Register-Metadaten) |
| Folgeauftrag | **CORE-10a-P04**: PowerShell-Starter-Eingaben/Ausgaben im Register verfeinern |
| Anwaltspruefung | Nein |

**Betroffene Module (alle PowerShell-Starter in `Scripts/`):**

`Invoke_Aider_Local`, `KM17_AUTOLAUF`, `KM17c_EINZELSEITE_KM12b_AUTOLAUF`, `KM18_AUTOLAUF`, `KM19_OCR_GESAMTKETTE_SYNCHRONISIEREN_AUTOLAUF`, `KM19_OCRBETREUER_KORREKTUR_AUTOLAUF`, `KM21_TRANSLATION_ENV_AUTOLAUF`, `Run_Agent_Dokumentart`, `Run_Agent_Handoff_Test_Harness`, `Run_Agent_Sachverhaltsbezug`, `Run_Agent_Sprache_Uebersetzung`, `Run_Agenten_Kontext_Skill_Register`, `Run_Agentenbearbeitung`, `Run_AI_Coding_Agent_Project_Check`, `Run_AI_Coding_Agent_Repair_Loop`, `Run_Aktenmaterial_Freigabeliste`, `Run_ALIN_SafeJob`, `Run_Anwaltvorlage`, `Run_Dokumentsprachprofil`, `Run_KM10_Schnittstellen_Lueckenabgleich`, `Run_KM12_Originalabbildung`, `Run_KM12b_Uebergrosse_Arbeitsabbildungen`, `Run_KM13_OCR_Pipeline`, `Run_KM13b_Tesseract_Sprachpaket_Abgleich`, `Run_KM14_Maschinenformat_Fundstellenstruktur`, `Run_KM15_Arbeitsuebersetzung_Fundstellenbindung`, `Run_KM16_Sprachrouting_Vor_OCR`, `Run_KM20_Konsolidierung`, `Run_KM20b_Bereinigung`, `Run_Posteingang_Menu`, `Run_Posteingang_Pipeline`, `Run_Posteingang_Schlusskontrolle`, `Run_Posteingang_Zentrale`, `Run_Quellenbetreuer_Fachanwaltsraster`, `Run_Quellenkandidaten_EU_SE`, `Run_Source_Adapter_Healthcheck_Framework`, `Run_Vorzimmer_Arbeitsliste`, `Run_Vorzimmer_Entscheidung`, `Run_Vorzimmer_Kommunikationsparameter`, `UI01_ANWALTSANSICHT_AUTOLAUF`, `ui02_0_bestandsabgleich_tuerschwelle`, `ui02_tuerschwelle_bau_starter`, `UI02c_FREIGABE_DROPDOWNS_NOTIZEN_AUTOLAUF`, `UI03_0_UEBERGABE_MANDANTENAKTE_AUTOLAUF`, `UI03_1_ANWALTS_DREIANSICHT_AUTOLAUF`, `UI04_DURCHSTICH_SEKRETARIAT_ANWALT_RUECKLAUF_AUTOLAUF`, `UI04b_LOGIKPRUEFUNG_ENTSCHEIDUNG_AUTOLAUF`, `Update_External_Tools_Library`

## P3 – NIEDRIG (31 Findings)

### P06: Datenbank-aendernde Module (18 Findings)

| Feld | Wert |
|------|------|
| Problem | 18 Module haben `darf_datenbank_aendern=true`. Darunter 7 `python_runner` und 11 `datenbank_migration`. |
| Betroffene Dateien | `modulregister.json` (18 Eintraege) |
| Anzahl | 18 Findings |
| Risiko | NIEDRIG – Informationell. Kein Fehler, aber wichtig fuer Backup/Restore-Planung. |
| Erlaubte Aenderungen | Keine (nur Dokumentation) |
| Verbotene Aenderungen | Keine Aenderung der Berechtigungen ohne Architektur-Review |
| Folgeauftrag | Dokumentation aktualisieren: Liste DB-aendernder Module in Backup-Konzept uebernehmen |
| Anwaltspruefung | Nein |

### P07: Online-faehige Module (13 Findings)

| Feld | Wert |
|------|------|
| Problem | 13 Module haben `darf_online_gehen=true`. Darunter 5 PowerShell-Starter und 8 Python-Module. |
| Betroffene Dateien | `modulregister.json` (13 Eintraege) |
| Anzahl | 13 Findings |
| Risiko | NIEDRIG – Informationell. Wichtig fuer Offline-Gerichtslaptop-Konfiguration. |
| Erlaubte Aenderungen | Keine (nur Dokumentation) |
| Verbotene Aenderungen | Keine Aenderung der Online-Berechtigungen ohne Datenschutz-Review |
| Folgeauftrag | Dokumentation aktualisieren: Liste online-faehiger Module in Offline-Konzept uebernehmen |
| Anwaltspruefung | Nein |

## Reparatur-Reihenfolge (vorgeschlagen)

1. **P03** – Modulnamen bereinigen (20 Module, 123 Findings)
   - Grund: Heisst alle anderen Pruefungen auf (Widersprueche verschwinden)

2. **P02** – Fehlende Abhaengigkeit korrigieren (1 Finding)
   - Grund: Laufzeitfehler verhindern

3. **P10** – Ressourcenregister vervollstaendigen (186 Findings)
   - Grund: Offline-Betrieb sicherstellen

4. **P09** – Schnittstellen-Schemas erstellen (16 Findings)
   - Grund: Datenkonsistenz zwischen Modulen

5. **P04/P08** – Platzhalter verfeinern (96 Findings)
   - Grund: Wartbarkeit verbessern

6. **P06/P07** – Dokumentation aktualisieren (31 Findings)
   - Grund: Informationell, kein Eingriff erforderlich

## Anwaltspruefung

**Keine der 551 Findings erfordert eine Anwaltspruefung.**

Alle Findings betreffen technische Registerkonsistenz, Metadaten-Qualitaet und Schnittstellenabdeckung. Keine Rechtsberatung, keine Beweiswuerdigung, keine Mandantendaten betroffen.

## Harte Grenzen (AGENTS.md)

- Keine Aenderungen ausserhalb von `I:\KI_Legal_Project`
- Keine echten Mandantendaten an externe Modelle
- Keine API-Schluessel in Git
- Keine endgueltige Rechtsberatung
- Keine Beweiswuerdigung
- Keine Tuerschwelle, bevor Quellenregister, Fachanwaltsraster, Quellenbetreuer, Adapter, Cache und Offline-Fallback stehen.

## Liefergegenstaende CORE-10a

| # | Datei | Pfad |
|---|-------|------|
| 1 | Python-Analyseskript | `ALIN_Neustart_Core/Scripts/python_runner/alin_core10a_findings_priorisierung.py` |
| 2 | Pruefdatei | `ALIN_Neustart_Core/Scripts/python_runner/check_alin_core10a_findings_priorisierung.py` |
| 3 | PowerShell-Starter | `ALIN_Neustart_Core/Scripts/Run_CORE10a_Priorisierung.ps1` |
| 4 | Dokumentation | `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE10a_Findings_Priorisierung_Reparaturplan.md` |
| 5 | Bericht (Text) | `Windows_App/Logs/ALIN_CORE10A_FINDINGS_PRIORISIERUNG_BERICHT.txt` |
| 6 | Bericht (JSON) | `Windows_App/Logs/ALIN_CORE10A_PRIORISIERUNG.json` |
