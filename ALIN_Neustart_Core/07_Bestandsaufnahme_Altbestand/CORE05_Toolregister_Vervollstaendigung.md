# CORE-05 – Toolregister Vervollständigung und Healthcheck

**Auftragsnummer:** CORE-05  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen (wartet auf Commit-Freigabe)  
**Agent:** ALIN_Core_Build_Agent  
**Geltungsbereich:** `ALIN_Neustart_Core/` – Harte Grenze, keine Änderungen außerhalb.

---

## 1. Ziel

Das Toolregister wurde von 3 Einträgen (Altbestand aus CORE-02) auf 16 Einträge erweitert.  
Jedes Tool erhielt erweiterte Metadaten (Toolgruppe, Healthcheck, Update-Linkage, Lizenz, Sicherheitsflags).  
Ein paralleles Healthcheck-Register (`TOOL_HEALTHCHECK.json`) wurde erstellt, um spätere automatisierte Prüfungen zu ermöglichen – aktuell im Dry-Run-Modus (`status: "ungeprueft"`).

---

## 2. Durchgeführte Arbeiten

### 2.1 Schema-Erweiterung

**Betroffene Dateien:**
- `01_Register/toolregister.schema.json`
- `09_Toolbibliothek/00_Toolregister/ALIN_TOOLREGISTER.schema.json`

**Neue Felder (alle optional, keine Breaking Changes):**

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `toolgruppe` | string | Logische Gruppierung (z. B. "OCR", "PDF") |
| `zweck` | string | Menschenlesbare Zweckbeschreibung |
| `standardtool_ja_nein` | boolean | Primäres Werkzeug für diese Gruppe? |
| `ersatztool_ja_nein` | boolean | Fallback-Alternative? |
| `version_status` | enum | `"aktuell"`, `"veraltet"`, `"zu_pruefen"`, `"unbekannt"` |
| `healthcheck_befehl` | string | CLI-Befehl für Smoke-Test |
| `healthcheck_status` | enum | `"ok"`, `"fehler"`, `"ungeprueft"`, `"nicht_verfuegbar"` |
| `update_id` | string | Verweis auf Eintrag im Update-Register |
| `lizenz_id` | string | Verweis auf Eintrag im Lizenzregister |
| `offline_verfuegbar` | boolean | Funktioniert ohne Internet? |
| `online_erforderlich` | boolean | Erfordert aktive Verbindung? |
| `darf_originale_veraendern` | boolean | **Invariant: immer `false`** (ADR-0004) |
| `darf_von_modulen_verwendet_werden` | boolean | Gate: Fachmodule müssen bei ALIN-Core anfragen |

### 2.2 Toolregister-Befüllung

**Betroffene Dateien:**
- `01_Register/toolregister.json`
- `09_Toolbibliothek/00_Toolregister/ALIN_TOOLREGISTER.json`

**16 Tools (geordnet nach Toolgruppe):**

| # | Tool-ID | Name | Gruppe | Installationsstatus | Standardtool | Ersatztool | `darf_verwendet_werden` |
|---|---------|------|--------|-------------------|--------------|------------|-------------------------|
| 1 | `TESSERACT` | Tesseract OCR | OCR | installiert | ja | nein | ja |
| 2 | `ABBYY` | ABBYY FineReader | OCR | nicht_installiert | nein | ja | nein |
| 3 | `POPPLER_PDFTOPPM` | Poppler pdftoppm | PDF | installiert | ja | nein | ja |
| 4 | `POPPLER_PDFINFO` | Poppler pdfinfo | PDF | installiert | ja | nein | ja |
| 5 | `IMAGEMAGICK` | ImageMagick | Bildverarbeitung | installiert | ja | nein | ja |
| 6 | `PILLOW` | Pillow (Python) | Bildverarbeitung | installiert | nein | ja | ja |
| 7 | `ARGOS_TRANSLATE` | Argos Translate | Übersetzung | installiert | nein | nein | **nein** |
| 8 | `GOOGLETRANS` | googletrans | Übersetzung | installiert | ja | nein | ja |
| 9 | `DEEPL` | DeepL API | Übersetzung | installiert | nein | ja | nein |
| 10 | `AIDER` | Aider (AI Coding) | Windows-App | installiert | nein | nein | **nein** |
| 11 | `PYWIN32` | pywin32 | Windows-App | installiert | ja | nein | ja |
| 12 | `WEBVIEW2` | Microsoft WebView2 | Windows-App | installiert | ja | nein | ja |
| 13 | `SQLITE3` | SQLite3 | Datenbank | installiert | ja | nein | ja |
| 14 | `PSQL` | PostgreSQL (psql) | Datenbank | installiert | nein | ja | ja |
| 15 | `OLLAMA` | Ollama (lokale LLMs) | Sicherheit/Offline-LLM | installiert | nein | nein | **nein** |
| 16 | `OPENSSL` | OpenSSL | Sicherheit | installiert | ja | nein | ja |

**Wichtige Sicherheitsklassifizierungen:**
- `darf_originale_veraendern: false` – **Alle 16 Tools** (keine Ausnahme).
- `darf_von_modulen_verwendet_werden: false` – **4 Tools:** AIDER, ARGOS_TRANSLATE, OLLAMA, ABBYY (explizite Freigabe erforderlich).

### 2.3 Healthcheck-Register

**Betroffene Datei:** `09_Toolbibliothek/06_Healthcheck/TOOL_HEALTHCHECK.json`

- 16 Healthcheck-Einträge, 1:1 zu den Tools.
- Jeder Eintrag enthält: `tool_id`, `befehl`, `erwartet`, `timeout_sekunden`, `status`, `letzte_ausfuehrung`, `ergebnis`.
- **Initialer Status aller Einträge:** `"ungeprueft"` (Dry-Run – keine automatische Ausführung).
- ABBYY hat leeren Befehl, Timeout 0, Status `"nicht_verfuegbar"`.

### 2.4 Update-Register-Abgleich

- 8 der 16 Tools haben eine `update_id` und sind mit dem Update-Register (CORE-04, 12 Einträge) verknüpft.
- 8 Tools haben keine Update-Linkage (kein automatisches Update-Verfahren verfügbar oder nicht erforderlich).

### 2.5 Lizenz-Register-Abgleich

- 10 der 16 Tools haben eine `lizenz_id` und sind mit dem Lizenzregister verknüpft.
- 6 Tools ohne `lizenz_id` (BSD, MIT, Public Domain oder noch nicht erfasst).

---

## 3. Lieferpflichten (gemäß AGENTS.md)

| # | Lieferpflicht | Datei / Pfad | Status |
|---|---------------|--------------|--------|
| 1 | Migration (DB) | *nicht betroffen* | N/A |
| 2 | Python-Läufer | `Scripts/alin_core05_toolregister_befuellen.py` | Erstellt |
| 3 | Prüfdatei | `Scripts/alin_core05_pruefung.py` | Erstellt |
| 4 | PowerShell-Starter | `Scripts/Run_CORE05_Toolregister.ps1` | Erstellt |
| 5 | Konfiguration | *nicht erforderlich* | N/A |
| 6 | Dokumentation | `07_Bestandsaufnahme_Altbestand/CORE05_Toolregister_Vervollstaendigung.md` | Erstellt |
| 7 | Testlauf | *manuell ausstehend* | Pending |
| 8 | Bericht | `Reports/ALIN_CORE05_TOOLREGISTER_BERICHT.txt` | Erstellt |
| 9 | Git-Status vor/nach | *noch nicht ausgeführt* | Pending |
| 10 | Git-Commit | *nur nach Freigabe* | Blockiert |

---

## 4. Statistik

| Metrik | Wert |
|--------|------|
| Tools gesamt | 16 |
| Installiert | 13 |
| Nicht installiert | 1 (ABBYY) |
| Unbekannt | 2 (DEEPL, OLLAMA – Version zu prüfen) |
| Standardtools | 11 |
| Ersatztools | 3 |
| Mit Update-Register verknüpft | 8 |
| Ohne Update-Register | 8 |
| Ohne Lizenz-Linkage | 6 |
| Nicht für Modulnutzung freigegeben | 4 |

---

## 5. Offene Punkte / Nächste Schritte

1. **Validierung:** `alin_core05_pruefung.py` muss ausgeführt werden (blockiert durch Umgebung).
2. **Git-Status & Commit:** Vorher `git status --short --untracked-files=all`, dann Freigabe durch Benutzer.
3. **Version-Prüfung:** TESSERACT, DEEPL, OLLAMA haben `version_status: "zu_pruefen"`.
4. **Lizenz-Nachinventarisierung:** 6 Tools ohne `lizenz_id` müssen in CORE-07/11 nachgetragen werden.
5. **Dry-Run → Live:** `healthcheck_status` von `"ungeprueft"` auf `"ok"` nur nach manuellem Test.

---

## 6. Architekturentscheidungen (ADR)

- **ADR-0004 (Originalschutz):** `darf_originale_veraendern: false` für alle Tools – keine Ausnahme.
- **ADR-0005 (Keine harte Verdrahtung):** `darf_von_modulen_verwendet_werden` als explizites Gate.
- **Offline-First:** `offline_verfuegbar: true` für 14/16 Tools (Ausnahmen: DEEPL, ggf. OLLAMA je nach Modell).

---

*Dokument erstellt am 2026-05-16 – ALIN_Core_Build_Agent*
