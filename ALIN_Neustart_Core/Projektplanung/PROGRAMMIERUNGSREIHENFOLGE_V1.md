# PROGRAMMIERUNGSREIHENFOLGE_V1

Erstellt: 2026-05-19 04:51:07

## Zweck

Dieses Dokument legt die verbindliche Reihenfolge fuer die weitere Programmierung fest. Es uebersetzt den Arbeitsauftrag vom 19.05.2026 in eine pruefbare Reihenfolge, ohne selbst eine fachliche oder sicherheitsrelevante Entscheidung zu ersetzen.

## Grundsatz

Die Phasen aus dem Arbeitsauftrag bleiben fuehrend. Die im Projekt zusaetzlich genannte Sperrfolge vor der Mandatsannahme wird als harte Zwischenreihenfolge vor der Tuerschwelle gefuehrt.

## Naechster umzusetzender Programmierbaustein

Phase 0, AP 0.1: pyproject.toml mit uv, Lockfile und Offline-Wheelhouse-Konzept.

## Harte Sperren

- Keine Aenderungen ausserhalb von I:\KI_Legal_Project\ALIN_Neustart_Core.
- Keine echte Mandantendaten, keine Cloud, keine Fremd-API-Aufrufe.
- Keine freie Internetrecherche und keine automatische Internetverbindung.
- Keine Datenbankaenderung ohne Migration.
- Keine Tuerschwelle, bevor Quellenregister, Fachanwaltsraster, Quellenbetreuer, Adapter, Cache und Offline-Fallback stehen.
- Keine Auslieferung ohne Testlauf, Bericht und Git-Status.

## Reihenfolge

### 0. PROGRAMMIERUNGSREIHENFOLGE_V1

- Titel: Verbindliche Programmierungsreihenfolge festlegen
- Phase: Vorbereitung
- Ziel: Den neuen Arbeitsauftrag in eine pruefbare Ausfuehrungsreihenfolge ueberfuehren.
- Danach: Phase 0 starten, beginnend mit AP 0.1.

### 1. PHASE_0_FUNDAMENT

- Titel: Phase 0: Fundament
- Phase: 0
- Ziel: Reproduzierbare Umgebung, technische Sperren, versionierte Datenbank.
- Arbeitspakete: 0.1 pyproject.toml mit uv, Lockfile, Offline-Wheelhouse, 0.2 DuckDB-Schema mit versionierten Migrationen und Migrations-Runner, 0.3 pytest-Aufsetzung und tests/-Struktur, 0.4 strukturiertes JSON-Logging, 0.5 rote Linien als technische Blocker, 0.6 Dispatcher alin.py mit dry-run/execute, 0.7 Internet-Sperre mit Update-Ausnahme
- Blockiert: Alle produktiven Pipeline-Bausteine; Jede Tuerschwellen-Funktion; Jede echte Datenbankfunktion ohne Migration
- Danach: PHASE_1_WERKZEUGKASTEN_BOOTSTRAPPER

### 2. PHASE_1_WERKZEUGKASTEN_BOOTSTRAPPER

- Titel: Phase 1: Werkzeugkasten und Bootstrapper
- Phase: 1
- Ziel: Offline-Installationspaket, Lizenzcheck, Healthcheck und MSIX-Skelett.
- Arbeitspakete: 1.1, 1.2, 1.3, 1.4, 1.5
- Blockiert: Phase 2 Eingang und Sicherheit
- Danach: PHASE_2_EINGANG_SICHERHEIT

### 3. PHASE_2_EINGANG_SICHERHEIT

- Titel: Phase 2: Eingang und Sicherheit
- Phase: 2
- Ziel: Posteingang, Schutzsoftware, Dateityp-, PDF-, Office-, Container- und Quarantaenepruefung.
- Arbeitspakete: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
- Blockiert: Sichtungsschicht mit Triage-Agent
- Danach: PHASE_3_SICHTUNG_TRIAGE

### 4. PHASE_3_SICHTUNG_TRIAGE

- Titel: Phase 3: Sichtungsschicht mit Triage-Agent
- Phase: 3
- Ziel: Sichtung vor der Mandatsannahme mit Schnell-OCR, lokaler KI und anwaltlicher Entscheidung.
- Arbeitspakete: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
- Blockiert: Aktenbearbeitung nach Annahme
- Danach: PHASE_4_AKTENBEARBEITUNG

### 5. QUELLENBETREUER_FACHANWALTSRASTER_V1

- Titel: Quellenbetreuer und Fachanwaltsraster
- Phase: Sperrfolge vor Tuerschwelle
- Ziel: Quellenbetreuung und fachliche Rasterung pruefbar machen, bevor die Mandatsannahme produktiv wird.
- Blockiert: MANDATSANNAHME_TUERSCHWELLE_V1
- Danach: AGENTEN_KONTEXT_SKILL_REGISTER_V1

### 6. AGENTEN_KONTEXT_SKILL_REGISTER_V1

- Titel: Agenten-Kontext und Skill-Register
- Phase: Sperrfolge vor Tuerschwelle
- Ziel: Agenten duerfen nur mit registriertem Kontext, Skill-Grenzen und Pruefpflichten arbeiten.
- Blockiert: MANDATSANNAHME_TUERSCHWELLE_V1
- Danach: AGENTEN_KOMMUNIKATION_UND_PRUEFAUFTRAEGE_V1

### 7. AGENTEN_KOMMUNIKATION_UND_PRUEFAUFTRAEGE_V1

- Titel: Agentenkommunikation und Pruefauftraege
- Phase: Sperrfolge vor Tuerschwelle
- Ziel: Pruefauftraege zwischen Agenten nachvollziehbar und auditierbar machen.
- Blockiert: MANDATSANNAHME_TUERSCHWELLE_V1
- Danach: RECHTSKONTEXT_SPRACHPAKET_CACHE_V1

### 8. RECHTSKONTEXT_SPRACHPAKET_CACHE_V1

- Titel: Rechtskontext-Sprachpaket-Cache
- Phase: Sperrfolge vor Tuerschwelle
- Ziel: Relevante Sprach- und Rechtskontextpakete lokal, nachvollziehbar und offline verfuegbar halten.
- Blockiert: MANDATSANNAHME_TUERSCHWELLE_V1
- Danach: ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1

### 9. ANYTHINGLLM_OFFLINE_HANDAKTE_ZENTRALE_V1

- Titel: AnythingLLM Offline-Handakte-Zentrale
- Phase: Sperrfolge vor Tuerschwelle
- Ziel: Lokale Recherche in der Handakte ohne Cloud, Telemetrie oder Fremd-API absichern.
- Blockiert: MANDATSANNAHME_TUERSCHWELLE_V1
- Danach: MANDATSANNAHME_TUERSCHWELLE_V1

### 10. MANDATSANNAHME_TUERSCHWELLE_V1

- Titel: Mandatsannahme-Tuerschwelle
- Phase: Sperrfolge vor Tuerschwelle
- Ziel: Harte Grenze zwischen Sichtung und Aktenbearbeitung technisch erzwingen.
- Blockiert: Phase 4 darf keine Triage-Ergebnisse still uebernehmen.
- Danach: PHASE_4_AKTENBEARBEITUNG

### 11. PHASE_4_AKTENBEARBEITUNG

- Titel: Phase 4: Aktenbearbeitung
- Phase: 4
- Ziel: Doppel-OCR, CAT-Uebersetzung, Quellen- und Auditnachweise nach Mandatsannahme.
- Arbeitspakete: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9
- Blockiert: EU-Quellen-Adapter und Pflege-Maske
- Danach: PHASE_5_EU_QUELLEN_ADAPTER

### 12. PHASE_5_EU_QUELLEN_ADAPTER

- Titel: Phase 5: EU-Quellen-Adapter und Pflege-Maske
- Phase: 5
- Ziel: Modulare Quellenadapter, Selbsttests, Pflege-Maske und sichere Schluesselablage.
- Arbeitspakete: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
- Blockiert: Laptop-Anwendung
- Danach: PHASE_6_LAPTOP_ANWENDUNG

### 13. PHASE_6_LAPTOP_ANWENDUNG

- Titel: Phase 6: Laptop-Anwendung
- Phase: 6
- Ziel: Verschluesselte Aktenpakete, Lesegeraet, Notizen, lokales RAG und Rueckspiel.
- Arbeitspakete: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
- Blockiert: Reife Bedienoberflaeche
- Danach: PHASE_7_UI_BARRIEREFREIHEIT

### 14. PHASE_7_UI_BARRIEREFREIHEIT

- Titel: Phase 7: Bedienoberflaeche und Barrierefreiheit
- Phase: 7
- Ziel: Reife Windows-Anwendung mit Tastaturbedienung, Kontrast, Skalierung und Sprachen.
- Arbeitspakete: 7.1, 7.2, 7.3, 7.4, 7.5
- Blockiert: Update, Backup, Lizenz
- Danach: PHASE_8_UPDATE_BACKUP_LIZENZ

### 15. PHASE_8_UPDATE_BACKUP_LIZENZ

- Titel: Phase 8: Update, Backup, Lizenz
- Phase: 8
- Ziel: Rollback-faehige Updates, Backup/Restore, Lizenzschluessel-Architektur und Kundendokumentation.
- Arbeitspakete: 8.1, 8.2, 8.3, 8.4, 8.5
- Danach: Abnahme durch Anwalt, keine KI-Selbstfreigabe.

## Umgang mit offenen Punkten

Nicht von der KI entschieden werden: LLM-Standardmodell, Adapter-Reihenfolge jenseits der bereits freigegebenen Sperrfolge, Software-Lizenz, beA-Aufnahme in Version 1, PyMuPDF-Lizenzvariante und Abschluss einer Phase. Bei Beruehrung wird eine Frage in `00_Dokumentation/OFFENE_FRAGEN_AN_ANWALT.md` eingetragen.
