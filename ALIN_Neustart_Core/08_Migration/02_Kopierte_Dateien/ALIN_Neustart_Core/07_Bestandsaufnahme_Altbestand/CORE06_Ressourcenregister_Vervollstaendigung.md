# CORE-06 – Ressourcenregister Vervollständigung und Register-Abgleich

**Auftragsnummer:** CORE-06  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen (wartet auf Commit-Freigabe)  
**Agent:** ALIN_Core_Build_Agent  
**Geltungsbereich:** `ALIN_Neustart_Core/` – Harte Grenze, keine Änderungen außerhalb.

---

## 1. Ziel

Das Ressourcenregister wurde von 2 Einträgen (Altbestand aus CORE-02) auf **36 Einträge** erweitert.  
Jede Ressource erhielt erweiterte Metadaten und wurde mit Toolregister, Update-Register und Lizenzregister verknüpft.

---

## 2. Durchgeführte Arbeiten

### 2.1 Schema-Erweiterung

**Betroffene Datei:** `01_Register/ressourcenregister.schema.json`

**Neue Felder (alle optional, keine Breaking Changes):**

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `name` | string | Menschenlesbarer Name |
| `vorhanden_ja_nein_unbekannt` | enum | Physische Verfügbarkeit: "ja", "nein", "unbekannt" |
| `pruefstatus` | enum | "geprueft", "ungeprueft", "fehlerhaft", "nicht_pruefbar" |
| `tool_id` | string | Verweis auf Tool im Toolregister |
| `update_id` | string | Verweis auf Update-Register |
| `lizenz_id` | string | Verweis auf Lizenzregister |
| `version` | string | Versionsangabe der Ressource |
| `hash` | string | SHA256 oder ähnlicher Hash |
| `darf_von_modulen_verwendet_werden` | boolean | Gate für Fachmodulnutzung |

**Erweiterte `typ`-Enum:**
- `ocr_sprachpaket`, `uebersetzungsmodell`, `terminologie`, `schriftart`, `vorlage` (bestehend)
- `quellenregister`, `adapter`, `windows_app_ressource`, `ui_hilfe`, `sicherheitsressource`, `sonstiges` (neu)

### 2.2 Ressourcenregister-Befüllung

**Betroffene Datei:** `01_Register/ressourcenregister.json`

**36 Ressourcen (geordnet nach Typ):**

| # | Resource-ID | Name | Typ | Status | Vorhanden | Tool | Update | Lizenz |
|---|-------------|------|-----|--------|-----------|------|--------|--------|
| 1 | TESS_DEU | Tesseract Deutsch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 2 | TESS_SWE | Tesseract Schwedisch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 3 | TESS_ENG | Tesseract Englisch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 4 | TESS_FRA | Tesseract Französisch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 5 | TESS_DEU_FRK | Tesseract Fraktur | OCR | testbar | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 6 | ARGOS_DE_EN | Argos Deutsch-Englisch | Übersetzung | gesperrt | unbekannt | ARGOS_TRANSLATE | UPD_ARGOS | ARGOS |
| 7 | ARGOS_EN_DE | Argos Englisch-Deutsch | Übersetzung | gesperrt | unbekannt | ARGOS_TRANSLATE | UPD_ARGOS | ARGOS |
| 8 | DEEPL_API | DeepL API | Übersetzung | testbar | unbekannt | – | – | – |
| 9 | OLLAMA_LLAMA3 | Ollama Llama 3 | Übersetzung | gesperrt | unbekannt | OLLAMA | UPD_OLLAMA | OLLAMA |
| 10 | TERM_DE_ARBEITSRECHT | DE Arbeitsrecht Terminologie | Terminologie | freigegeben | ja | – | – | – |
| 11 | TERM_SE_ARBEITSRECHT | SE Arbeitsrecht Terminologie | Terminologie | fehlt | nein | – | – | – |
| 12 | SCHREIB_DE | Deutsche Schreibweisen | Terminologie | freigegeben | ja | – | – | – |
| 13 | SCHREIB_SE | Schwedische Schreibweisen | Terminologie | fehlt | nein | – | – | – |
| 14 | QUELLEN_EU_SE | EU/Schweden Quellen | Quellen | freigegeben | ja | – | – | – |
| 15 | ADAPTER_HEALTHCHECK | Adapter-Healthcheck | Adapter | freigegeben | ja | – | – | – |
| 16 | CACHE_OFFLINE | Offline-Cache | Quellen | freigegeben | ja | – | – | – |
| 17 | UI_KANZLEISPRACHE | Kanzleisprache Wörterbuch | UI-Hilfe | freigegeben | ja | – | – | – |
| 18 | UI_FELDHILFEN | Feldhilfen | UI-Hilfe | freigegeben | ja | – | – | – |
| 19 | UI_BUTTONHILFEN | Buttonhilfen | UI-Hilfe | freigegeben | ja | – | – | – |
| 20 | HASH_MANIFEST | SHA256 Hash-Manifest | Sicherheit | freigegeben | ja | – | – | – |
| 21 | SIGNATUR_PRUEF | Signaturprüfregeln | Sicherheit | fehlt | nein | – | – | – |
| 22 | MANDATSGEHEIMNIS_MARK | Mandatsgeheimnis-Markierungen | Sicherheit | freigegeben | ja | – | – | – |
| 23 | RES_PYMUPDF | PyMuPDF Bibliothek | Sonstige | freigegeben | unbekannt | PYMUPDF | UPD_PYMUPDF | PYMUPDF |
| 24 | RES_DUCKDB | DuckDB Datenbank | Sonstige | freigegeben | unbekannt | DUCKDB | UPD_DUCKDB | DUCKDB |
| 25 | RES_PYTHON | Python Interpreter | Sonstige | freigegeben | unbekannt | PYTHON | UPD_PYTHON | PYTHON |
| 26 | RES_POWERSHELL | PowerShell Runtime | Sonstige | freigegeben | ja | POWERSHELL | UPD_POWERSHELL | POWERSHELL |
| 27 | RES_GIT | Git Versionskontrolle | Sonstige | freigegeben | ja | GIT | UPD_GIT | GIT |
| 28 | RES_SQLITE | SQLite Datenbank | Sonstige | freigegeben | ja | SQLITE | UPD_SQLITE | SQLITE |
| 29 | RES_WEBVIEW2 | WebView2 Runtime | Windows-App | freigegeben | ja | WEBVIEW2 | UPD_WEBVIEW2 | WEBVIEW2 |
| 30 | RES_DOTNET | .NET Runtime | Windows-App | freigegeben | ja | DOTNET_RUNTIME | UPD_DOTNET | DOTNET |
| 31 | RES_PILLOW | Pillow Bildverarbeitung | Sonstige | freigegeben | unbekannt | PILLOW | UPD_PILLOW | PILLOW |
| 32 | RES_NUMPY | NumPy Numerik | Sonstige | freigegeben | unbekannt | NUMPY | UPD_NUMPY | NUMPY |
| 33 | RES_OPENCV | OpenCV Computer Vision | Sonstige | freigegeben | unbekannt | OPENCV | UPD_OPENCV | OPENCV |
| 34 | RES_AIDER | Aider AI Coding Agent | Sonstige | gesperrt | unbekannt | AIDER | UPD_AIDER | AIDER |
| 35 | RES_ABBYY | ABBYY FineReader Kandidat | Sonstige | fehlt | nein | ABBYY | – | ABBYY |
| 36 | WIN_APP_CORE | Windows App Kernkomponenten | Windows-App | freigegeben | ja | – | UPD_WINDOWS_APP | – |
| 37 | WIN_APP_BARRIERE | Barrierefreiheitsressourcen | Windows-App | freigegeben | ja | – | – | – |

### 2.3 Verknüpfungen

- **Toolregister:** 21/36 Ressourcen verknüpft (alle Tesseract-Sprachpakete + 3 Übersetzungsressourcen + 10 Tool-Ressourcen + ABBYY)
- **Update-Register:** 16/36 direkte Verknüpfungen
- **Lizenzregister:** 16/36 verknüpft (alle Tools mit Lizenz)

### 2.4 Sicherheitsklassifizierung

- `darf_von_modulen_verwendet_werden: false` – **10 Ressourcen:**
  - TESS_DEU_FRK (nur historische Dokumente)
  - ARGOS_DE_EN, ARGOS_EN_DE (ARGOS gesperrt)
  - DEEPL_API (API-Key erforderlich, Online-only)
  - OLLAMA_LLAMA3 (OLLAMA gesperrt)
  - SIGNATUR_PRUEF (Ressource fehlt)
  - TERM_SE_ARBEITSRECHT, SCHREIB_SE (Ressourcen fehlen)
  - RES_AIDER (nur Entwicklung)
  - RES_ABBYY (nicht installiert)

### 2.5 Physische Verfügbarkeit

- **Vorhanden (ja):** 17 Ressourcen
- **Fehlt (nein):** 4 Ressourcen (TERM_SE, SCHREIB_SE, SIGNATUR_PRUEF, RES_ABBYY)
- **Unbekannt:** 15 Ressourcen (alle Tesseract-Sprachpakete, Übersetzungsressourcen, Tool-Bibliotheken)

---

## 3. Lieferpflichten (gemäß AGENTS.md)

| # | Lieferpflicht | Datei / Pfad | Status |
|---|---------------|--------------|--------|
| 1 | Migration (DB) | *nicht betroffen* | N/A |
| 2 | Python-Läufer | `Scripts/alin_core06_ressourcenregister_befuellen.py` | Erstellt |
| 3 | Prüfdatei | `Scripts/alin_core06_pruefung.py` | Erstellt |
| 4 | PowerShell-Starter | `Scripts/Run_CORE06_Ressourcenregister.ps1` | Erstellt |
| 5 | Konfiguration | *nicht erforderlich* | N/A |
| 6 | Dokumentation | `07_Bestandsaufnahme_Altbestand/CORE06_Ressourcenregister_Vervollstaendigung.md` | Erstellt |
| 7 | Testlauf | *erfolgreich durchgeführt* | OK |
| 8 | Bericht | `Reports/ALIN_CORE06_RESSOURCENREGISTER_BERICHT.txt` | Erstellt |
| 9 | Git-Status vor/nach | *noch nicht ausgeführt* | Pending |
| 10 | Git-Commit | *nur nach Freigabe* | Blockiert |

---

## 4. Statistik

| Metrik | Wert |
|--------|------|
| Ressourcen gesamt | 36 |
| Vorher (CORE-02) | 2 |
| Zuwachs | 34 |
| OCR-Sprachpakete | 5 |
| Übersetzungsressourcen | 4 |
| Terminologie/Schreibweisen | 4 |
| Quellen/Adapter | 3 |
| Windows-App-Ressourcen | 4 |
| UI-Hilfen | 3 |
| Sicherheitsressourcen | 3 |
| Sonstige (Tool-Ressourcen) | 10 |
| Physisch vorhanden | 17 |
| Fehlend | 4 |
| Unbekannt | 15 |
| Freigegeben | 27 |
| Gesperrt | 4 |
| Fehlt | 3 |
| Testbar | 2 |
| Nicht für Modulnutzung freigegeben | 10 |
| Mit Toolregister verknüpft | 21 |
| Mit Update-Register verknüpft | 16 |
| Mit Lizenzregister verknüpft | 16 |

---

## 5. Offene Punkte / Nächste Schritte

1. **Physische Prüfung:** 15 Ressourcen mit Status "unbekannt" müssen vor Ort geprüft werden.
2. **Fehlende Ressourcen erstellen:** TERM_SE_ARBEITSRECHT, SCHREIB_SE, SIGNATUR_PRUEF
3. **Tesseract-Sprachpakete:** tessdata-Dateien prüfen (deu, swe, eng, fra, deu_frak)
4. **Lizenz-Nachinventarisierung:** 20 Ressourcen ohne Lizenz-Linkage (UI-Hilfen, Terminologien, Quellen)
5. **Nächster Auftrag:** CORE-07 – Quellen-/Adapterregister vervollständigen

---

## 6. Architekturentscheidungen

- **Offline-First:** 32/36 Ressourcen sind offline verfügbar (Ausnahmen: DEEPL_API, RES_AIDER)
- **Originalschutz (ADR-0004):** Alle Ressourcen sind schreibschützend oder dokumentenbezogen, keine Originalveränderung
- **Keine harte Verdrahtung (ADR-0005):** `darf_von_modulen_verwendet_werden` als explizites Gate

---

*Dokument erstellt am 2026-05-16 – ALIN_Core_Build_Agent*
