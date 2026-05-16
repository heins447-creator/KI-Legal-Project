# CORE-10d: Schnittstellenbereiche nachtragen

## Auftrag

Ticket: CORE-10d  
Datum: 2026-05-16  
Bearbeiter: ALIN Core-Agent  
Status: Abgeschlossen (wartet auf Freigabe)

## Ziel

Die Schnittstellenbereiche im ALIN_Neustart_Core sauber nachgetragen, geordnet und prüfbar gemacht. Es geht ausschließlich um Registerpflege – keine neue Funktion, keine Cloud/API-Nutzung, keine Installation.

## Neue Datei

### schnittstellenregister.json

Neues zentrales Register unter `ALIN_Neustart_Core/01_Register/schnittstellenregister.json` mit 14 Schnittstellen:

| # | ID | Name | Bereich | Status | Cloud-Status |
|---|----|------|---------|--------|-------------|
| 1 | SI_CORE_REGISTRY | Core-Register-Schnittstelle | register | aktiv | keiner |
| 2 | SI_UI_EINGANG_TUERSCHWELLE | UI-Eingang-Türschwelle | ui | aktiv | keiner |
| 3 | SI_UI_MANDANTENAKTE | UI-Mandantenakte | ui | vorbereitet | keiner |
| 4 | SI_DOKUMENT_ORIGINAL | Dokument-Originalsicherung | schnittstellen | aktiv | keiner |
| 5 | SI_OCR_PIPELINE | OCR-Pipeline | ocr | aktiv | keiner |
| 6 | SI_FUNDSTELLEN_TEXTSTRUKTUR | Fundstellen-Textstruktur | schnittstellen | vorbereitet | keiner |
| 7 | SI_UEBERSETZUNG_TERMINOLOGIE | Übersetzung-Terminologie | sprache | gesperrt | gesperrt |
| 8 | SI_QUELLEN_ADAPTER | Quellen-Adapter | quellen | aktiv | manuell_freigabepflichtig |
| 9 | SI_RESSOURCEN_HEALTHCHECK | Ressourcen-Healthcheck | register | aktiv | keiner |
| 10 | SI_AGENTEN_AUFTRAG | Agenten-Auftrag | agent | vorbereitet | keiner |
| 11 | SI_AKTENPROFIL_GRUNDSCHALTER | Aktenprofil-Grundschalter | register | aktiv | keiner |
| 12 | SI_EXPORT_IMPORT | Export-Import | schnittstellen | vorbereitet | keiner |
| 13 | SI_BACKUP_INTEGRITAET | Backup-Integrität | register | aktiv | keiner |
| 14 | SI_GESPERRTE_EXTERN | Gesperrte externe Schnittstellen | schnittstellen | gesperrt | gesperrt |

## Durchgeführte Arbeit

### 1. Schnittstellenregister erstellt

Jede Schnittstelle enthält:
- `schnittstelle_id`, `name`, `bereich`, `beschreibung`
- `status` (aktiv/vorbereitet/gesperrt)
- `eingaben`, `ausgaben`
- `beteiligte_module`, `beteiligte_register`
- `benoetigte_ressourcen`, `benoetigte_tools`
- `quellen_oder_adapter`
- `offline_faehig`, `cloud_bezug`, `cloud_status`
- `db_aenderung`, `originalaenderung`, `produktivfreigabe`
- `risikohinweis`, `pruefstatus`, `letzter_abgleich`

### 2. Cloud-/API-Schnittstellen

| Schnittstelle | Cloud-Bezug | Status |
|---------------|-------------|--------|
| SI_GESPERRTE_EXTERN | direkt | GESPERRT |
| SI_UEBERSETZUNG_TERMINOLOGIE | indirekt | GESPERRT |
| SI_QUELLEN_ADAPTER | indirekt | manuell_freigabepflichtig |

**DEEPL_API** ist explizit als gesperrt markiert. Keine automatische Nutzung.

### 3. Modul-Zuordnung

Jede Schnittstelle verweist auf konkrete Module aus dem Modulregister:
- SI_OCR_PIPELINE: km13_ocr_pipeline, km16_sprachrouting_vor_ocr, km17_sprachrouting_ocr_integration, km18_ocr_ergebnisdiagnose, km19_ocr_gesamtkette_synchronisieren, km19_ocrbetreuer_korrektur
- SI_AGENTEN_AUFTRAG: 040_agentenbearbeitung_grundmodul_v1, 042_agent_dokumentart_erkennen_v1, 044_agent_sprache_uebersetzung_v1, 046_agent_sachverhaltsbezug_v1
- SI_UI_EINGANG_TUERSCHWELLE: ui02_tuerschwelle_bau, ui02c_freigabe_dropdowns_notizen, ui04b_logikpruefung_entscheidung
- etc.

### 4. Verwendungsgrenzen

- **Aktiv** (5 Schnittstellen): Register, OCR, Quellen-Adapter, Healthcheck, Backup – freigegeben
- **Vorbereitet** (4 Schnittstellen): UI-Mandantenakte, Fundstellen, Agenten, Export – noch nicht freigegeben
- **Gesperrt** (2 Schnittstellen): Übersetzung (Argos fehlt), Externe Cloud/API

## Prüfung

Die Prüfdatei `alin_core10d_pruefung.py` verifiziert:
1. schnittstellenregister.json vorhanden ✓
2. JSON gültig ✓
3. Jede Schnittstelle hat ID ✓
4. Jede Schnittstelle hat Bereich ✓
5. Jede Schnittstelle hat Status ✓
6. Jede Schnittstelle hat Eingaben/Ausgaben ✓
7. Cloud-Schnittstellen nicht automatisch aktiv ✓
8. DEEPL_API nicht automatisch freigegeben ✓
9. Ressourcen existieren oder sind als fehlend/gesperrt markiert ✓
10. Tools existieren oder sind als fehlend/gesperrt markiert ✓
11. Module existieren oder sind als offen markiert ✓

Ergebnis: **BESTANDEN** (Exit-Code 0)

## Liefergegenstände

| # | Datei | Zweck |
|---|-------|-------|
| 1 | `Scripts/alin_core10d_schnittstellenbereiche_nachtragen.py` | Analyseskript |
| 2 | `Scripts/alin_core10d_pruefung.py` | Prüfdatei |
| 3 | `Scripts/Run_CORE10d_Schnittstellenbereiche.ps1` | PowerShell-Starter |
| 4 | `01_Register/schnittstellenregister.json` | Schnittstellenregister |
| 5 | `07_Bestandsaufnahme_Altbestand/CORE10d_Schnittstellenbereiche.md` | Dokumentation |
| 6 | `Reports/ALIN_CORE10D_SCHNITTSTELLENBEREICHE_BERICHT.txt` | Bericht |
| 7 | `Reports/ALIN_CORE10D_PRUEFBERICHT.txt` | Prüfbericht |

## Grenzen eingehalten

- ✗ Keine Änderung am Altbestand außerhalb ALIN_Neustart_Core
- ✗ Keine Originaldateien verändert
- ✗ Keine Datenbankänderung
- ✗ Keine Installation
- ✗ Kein Internet
- ✗ Keine Cloud/API-Nutzung
- ✗ Keine Argos-Downloads
- ✗ Keine OCR
- ✗ Keine Übersetzung
- ✗ Keine Rechtsbewertung
- ✗ Keine Beweiswürdigung
- ✗ Keine Produktivfreigabe
- ✗ Nur Registerpflege

## Nächste Schritte

1. Freigabe durch Projektleitung
2. Commit nach Freigabe
3. Fortsetzung mit P04/P08 (Platzhalter verfeinern) oder P06/P07 (Reviewlisten dokumentieren)

---
*Dokument erstellt gemäß AGENTS.md Lieferpflicht*
