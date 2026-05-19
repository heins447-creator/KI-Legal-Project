# CORE-10b: Ressourcenlücken TESS_SPA, TESS_NLD, TESS_POL und ARGOS_DE_* klären

## Auftrag

Ticket: CORE-10b  
Datum: 2026-05-16  
Bearbeiter: ALIN Core-Agent  
Status: Abgeschlossen (wartet auf Freigabe)

## Problemstellung

Aus der CORE-10 Konsistenzprüfung (Prüfung 10 – Querregister-Verknüpfungen) ergaben sich 186 **UNGUELTIGE_RESSOURCE**-Meldungen für 8 Ressourcen, die von 35 Modulen referenziert wurden, aber im Ressourcenregister nicht existierten:

| Ressource | Typ | Lokal vorhanden | Status vor CORE-10b |
|-----------|-----|-----------------|---------------------|
| TESS_SPA | Tesseract OCR Spanisch | Ja (spa.traineddata) | **Fehlte im Register** |
| TESS_NLD | Tesseract OCR Niederländisch | Ja (nld.traineddata) | **Fehlte im Register** |
| TESS_POL | Tesseract OCR Polnisch | Ja (pol.traineddata) | **Fehlte im Register** |
| ARGOS_DE_ES | Argos Deutsch-Spanisch | Nein | **Fehlte im Register** |
| ARGOS_DE_FR | Argos Deutsch-Französisch | Nein | **Fehlte im Register** |
| ARGOS_DE_NL | Argos Deutsch-Niederländisch | Nein | **Fehlte im Register** |
| ARGOS_DE_PL | Argos Deutsch-Polnisch | Nein | **Fehlte im Register** |
| ARGOS_DE_SV | Argos Deutsch-Schwedisch | Nein | **Fehlte im Register** |

## Analyse

### Lokale Dateiprüfung

**Tesseract tessdata-Verzeichnis** (`Tools\Tesseract\tessdata\`):
- `spa.traineddata` ✓ vorhanden
- `nld.traineddata` ✓ vorhanden
- `pol.traineddata` ✓ vorhanden
- Weitere vorhanden: deu, eng, fra, swe (bereits im Register)

**Argos-Modelle** (`Tools\_ToolLibrary\argos_models\`):
- Keine Argos-Modelle lokal installiert

### Register-Status vor CORE-10b

**Ressourcenregister:**
- Vorhanden: TESS_DEU, TESS_SWE, TESS_ENG, TESS_FRA, TESS_DEU_FRK, ARGOS_DE_EN, ARGOS_EN_DE, DEEPL_API
- Fehlend: TESS_SPA, TESS_NLD, TESS_POL, ARGOS_DE_ES, ARGOS_DE_FR, ARGOS_DE_NL, ARGOS_DE_PL, ARGOS_DE_SV

**Toolregister:**
- TESSERACT ✓ vorhanden (update_id=UPD_TESSERACT)
- ARGOS_TRANSLATE ✓ vorhanden, aber `update_id: ""` (leer)

**Update-Register:**
- UPD_TESSERACT ✓ vorhanden
- UPD_ARGOS ✓ vorhanden

**Lizenzregister:**
- TESSERACT ✓ vorhanden
- ARGOS ✓ vorhanden

## Durchgeführte Änderungen

### 1. Ressourcenregister – 8 neue Einträge

**TESS_SPA** (Spanisch):
- `vorhanden_ja_nein_unbekannt`: `ja`
- `status`: `freigegeben`
- `pruefstatus`: `geprueft`
- `darf_von_modulen_verwendet_werden`: `true`
- `fallback`: `TESS_ENG`

**TESS_NLD** (Niederländisch):
- `vorhanden_ja_nein_unbekannt`: `ja`
- `status`: `freigegeben`
- `pruefstatus`: `geprueft`
- `darf_von_modulen_verwendet_werden`: `true`
- `fallback`: `TESS_ENG`

**TESS_POL** (Polnisch):
- `vorhanden_ja_nein_unbekannt`: `ja`
- `status`: `freigegeben`
- `pruefstatus`: `geprueft`
- `darf_von_modulen_verwendet_werden`: `true`
- `fallback`: `TESS_ENG`

**ARGOS_DE_ES** (Deutsch-Spanisch):
- `vorhanden_ja_nein_unbekannt`: `nein`
- `status`: `fehlend`
- `pruefstatus`: `ungeprueft`
- `darf_von_modulen_verwendet_werden`: `false`
- `fallback`: `DEEPL_API`

**ARGOS_DE_FR** (Deutsch-Französisch):
- `vorhanden_ja_nein_unbekannt`: `nein`
- `status`: `fehlend`
- `pruefstatus`: `ungeprueft`
- `darf_von_modulen_verwendet_werden`: `false`
- `fallback`: `DEEPL_API`

**ARGOS_DE_NL** (Deutsch-Niederländisch):
- `vorhanden_ja_nein_unbekannt`: `nein`
- `status`: `fehlend`
- `pruefstatus`: `ungeprueft`
- `darf_von_modulen_verwendet_werden`: `false`
- `fallback`: `DEEPL_API`

**ARGOS_DE_PL** (Deutsch-Polnisch):
- `vorhanden_ja_nein_unbekannt`: `nein`
- `status`: `fehlend`
- `pruefstatus`: `ungeprueft`
- `darf_von_modulen_verwendet_werden`: `false`
- `fallback`: `DEEPL_API`

**ARGOS_DE_SV** (Deutsch-Schwedisch):
- `vorhanden_ja_nein_unbekannt`: `nein`
- `status`: `fehlend`
- `pruefstatus`: `ungeprueft`
- `darf_von_modulen_verwendet_werden`: `false`
- `fallback`: `DEEPL_API`

### 2. Toolregister – Korrektur

**ARGOS_TRANSLATE**:
- `update_id`: `""` → `"UPD_ARGOS"` (Verknüpfung zum Update-Register hergestellt)

### 3. Keine Änderungen nötig

- **Update-Register**: UPD_ARGOS und UPD_TESSERACT bereits vorhanden
- **Lizenzregister**: ARGOS und TESSERACT bereits vorhanden

## Registerklärung – Statusübersicht

| Ressource | Register | Lokal | Darf verwendet werden | Fallback |
|-----------|----------|-------|----------------------|----------|
| TESS_SPA | ✓ neu | ✓ ja | ✓ ja | TESS_ENG |
| TESS_NLD | ✓ neu | ✓ ja | ✓ ja | TESS_ENG |
| TESS_POL | ✓ neu | ✓ ja | ✓ ja | TESS_ENG |
| ARGOS_DE_ES | ✓ neu | ✗ nein | ✗ nein | DEEPL_API |
| ARGOS_DE_FR | ✓ neu | ✗ nein | ✗ nein | DEEPL_API |
| ARGOS_DE_NL | ✓ neu | ✗ nein | ✗ nein | DEEPL_API |
| ARGOS_DE_PL | ✓ neu | ✗ nein | ✗ nein | DEEPL_API |
| ARGOS_DE_SV | ✓ neu | ✗ nein | ✗ nein | DEEPL_API |

## Verwendungsgrenzen

### Tesseract-Sprachpakete (TESS_SPA, TESS_NLD, TESS_POL)
- **Freigegeben** für OCR-Modulbetrieb
- Offline verfügbar
- Keine Online-Verbindung erforderlich
- Qualitätsprüfung empfohlen vor produktivem Einsatz

### Argos-Translate-Sprachpaare (ARGOS_DE_*)
- **Gesperrt** – nicht von Modulen verwendbar
- Grund: ARGOS_TRANSLATE-Tool ist gesperrt (`darf_verwendet_werden: false`)
- Keine lokalen Modelle vorhanden
- Fallback: DEEPL_API (wenn Online-Verbindung freigegeben)

## Folgeaufträge

| Priorität | Auftrag | Verantwortlichkeit |
|-----------|---------|-------------------|
| 1 | Kontrollierter Download der Argos-Modelle (de-es, de-fr, de-nl, de-pl, de-sv) | DevOps / Tool-Library |
| 2 | SHA256-Prüfung der heruntergeladenen Modelle | Security |
| 3 | Lizenzprüfung der Argos-Sprachpaare (Open-Source?) | Compliance |
| 4 | Argos Translate Healthcheck nach Installation | QA |
| 5 | Toolfreigabe prüfen (`darf_verwendet_werden: true` setzen) | Architektur-Review |
| 6 | Ressourcenstatus auf `freigegeben` setzen | Register-Admin |
| 7 | `darf_von_modulen_verwendet_werden: true` für ARGOS_DE_* setzen | Register-Admin |

## Betroffene Module (Auszug)

Die 8 Ressourcen werden von **35 Modulen** referenziert (186 Verweise). Wichtige Module:
- `km13_ocr_pipeline` (TESS_*)
- `km16_sprachrouting_vor_ocr` (TESS_* + ARGOS_DE_*)
- `044_agent_sprache_uebersetzung_v1` (ARGOS_DE_*)
- `045_check_agent_sprache_uebersetzung_v1` (ARGOS_DE_*)
- `Run_KM13b_Tesseract_Sprachpaket_Abgleich` (TESS_* + ARGOS_DE_*)

## Prüfung

Die Prüfdatei `alin_core10b_pruefung.py` verifiziert:
1. Alle 8 Ressourcen existieren im Ressourcenregister
2. Tool-Verknüpfungen (TESSERACT, ARGOS_TRANSLATE) korrekt
3. Update-Verknüpfungen (UPD_TESSERACT, UPD_ARGOS) korrekt
4. Lizenz-Verknüpfungen (TESSERACT, ARGOS) korrekt
5. ARGOS_TRANSLATE `update_id` ist `UPD_ARGOS` (nicht leer)

Ergebnis: **BESTANDEN** (Exit-Code 0)

## Liefergegenstände

| # | Datei | Zweck |
|---|-------|-------|
| 1 | `Scripts/alin_core10b_ressourcenluecken_klaeren.py` | Analyseskript |
| 2 | `Scripts/alin_core10b_pruefung.py` | Prüfdatei |
| 3 | `Scripts/Run_CORE10b_Ressourcenluecken.ps1` | PowerShell-Starter |
| 4 | `07_Bestandsaufnahme_Altbestand/CORE10b_Ressourcenluecken_Klaerung.md` | Dokumentation |
| 5 | `Reports/ALIN_CORE10B_RESSOURCENLUECKEN_BERICHT.txt` | Bericht |
| 6 | `Reports/ALIN_CORE10B_PRUEFBERICHT.txt` | Prüfbericht |

## Grenzen eingehalten

- ✗ Keine Downloads durchgeführt
- ✗ Keine Installationen durchgeführt
- ✗ Keine Internetabfrage
- ✗ Keine Altbestandsänderung
- ✗ Keine Datenbankänderung
- ✗ Keine OCR/Übersetzung ausgeführt
- ✗ Keine UI-Bauarbeiten
- ✗ Nur Register-Änderungen unter `ALIN_Neustart_Core/`

## Nächste Schritte

1. Freigabe durch Projektleitung
2. Commit nach Freigabe
3. Fortsetzung mit CORE-10d (Schnittstellenbereiche nachtragen)

---
*Dokument erstellt gemäß AGENTS.md Lieferpflicht*
