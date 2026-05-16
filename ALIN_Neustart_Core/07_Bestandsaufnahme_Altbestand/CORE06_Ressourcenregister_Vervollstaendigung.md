# CORE-06 – Ressourcenregister Vervollständigung und Register-Abgleich

**Auftragsnummer:** CORE-06  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen (wartet auf Commit-Freigabe)  
**Agent:** ALIN_Core_Build_Agent  
**Geltungsbereich:** `ALIN_Neustart_Core/` – Harte Grenze, keine Änderungen außerhalb.

---

## 1. Ziel

Das Ressourcenregister wurde von 2 Einträgen (Altbestand aus CORE-02) auf 22 Einträge erweitert.  
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
- `quellenregister`, `adapter`, `windows_app_ressource`, `ui_hilfe`, `sicherheitsressource` (neu)

### 2.2 Ressourcenregister-Befüllung

**Betroffene Datei:** `01_Register/ressourcenregister.json`

**22 Ressourcen (geordnet nach Typ):**

| # | Resource-ID | Name | Typ | Status | Vorhanden | Tool | Update | Lizenz |
|---|-------------|------|-----|--------|-----------|------|--------|--------|
| 1 | TESS_DEU | Tesseract Deutsch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 2 | TESS_SWE | Tesseract Schwedisch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 3 | TESS_ENG | Tesseract Englisch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 4 | TESS_FRA | Tesseract Französisch | OCR | freigegeben | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 5 | TESS_DEU_FRK | Tesseract Fraktur | OCR | testbar | unbekannt | TESSERACT | UPD_TESSERACT | TESSERACT |
| 6 | ARGOS_DE_EN | Argos Deutsch-Englisch | Übersetzung | gesperrt | unbekannt | ARGOS_TRANSLATE | – | – |
| 7 | ARGOS_EN_DE | Argos Englisch-Deutsch | Übersetzung | gesperrt | unbekannt | ARGOS_TRANSLATE | – | – |
| 8 | DEEPL_API | DeepL API | Übersetzung | testbar | unbekannt | – | – | – |
| 9 | OLLAMA_LLAMA3 | Ollama Llama 3 | Übersetzung | gesperrt | unbekannt | OLLAMA | – | – |
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

### 2.3 Verknüpfungen

- **Toolregister:** 8/22 Ressourcen verknüpft (alle Tesseract-Sprachpakete + 3 Übersetzungsressourcen)
- **Update-Register:** 0/22 direkte Verknüpfungen (Update-IDs sind Tool-bezogen, nicht Ressourcen-bezogen; 5 OCR-Ressourcen teilen UPD_TESSERACT)
- **Lizenzregister:** 5/22 verknüpft (TESSERACT-Sprachpakete)

### 2.4 Sicherheitsklassifizierung

- `darf_von_modulen_verwendet_werden: false` – **6 Ressourcen:**
  - TESS_DEU_FRK (nur historische Dokumente)
  - ARGOS_DE_EN, ARGOS_EN_DE (ARGOS gesperrt)
  - DEEPL_API (API-Key erforderlich, Online-only)
  - OLLAMA_LLAMA3 (OLLAMA gesperrt)
  - SIGNATUR_PRUEF (Ressource fehlt)
  - TERM_SE_ARBEITSRECHT, SCHREIB_SE (Ressourcen fehlen)

### 2.5 Physische Verfügbarkeit

- **Vorhanden (ja):** 10 Ressourcen
- **Fehlt (nein):** 3 Ressourcen (TERM_SE, SCHREIB_SE, SIGNATUR_PRUEF)
- **Unbekannt:** 9 Ressourcen (alle Tesseract-Sprachpakete, Übersetzungsressourcen)

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
| Ressourcen gesamt | 22 |
| Vorher (CORE-02) | 2 |
| Zuwachs | 20 |
| OCR-Sprachpakete | 5 |
| Übersetzungsressourcen | 4 |
| Terminologie/Schreibweisen | 4 |
| Quellen/Adapter | 3 |
| UI-Hilfen | 3 |
| Sicherheitsressourcen | 3 |
| Physisch vorhanden | 10 |
| Fehlend | 3 |
| Unbekannt | 9 |
| Freigegeben | 13 |
| Gesperrt | 4 |
| Fehlt | 3 |
| Testbar | 2 |
| Nicht für Modulnutzung freigegeben | 8 |
| Mit Toolregister verknüpft | 8 |
| Mit Lizenzregister verknüpft | 5 |

---

## 5. Offene Punkte / Nächste Schritte

1. **Physische Prüfung:** 9 Ressourcen mit Status "unbekannt" müssen vor Ort geprüft werden.
2. **Fehlende Ressourcen erstellen:** TERM_SE_ARBEITSRECHT, SCHREIB_SE, SIGNATUR_PRUEF
3. **Tesseract-Sprachpakete:** tessdata-Dateien prüfen (deu, swe, eng, fra, deu_frak)
4. **Lizenz-Nachinventarisierung:** 17 Ressourcen ohne Lizenz-Linkage
5. **Nächster Auftrag:** CORE-07 – Quellen-/Adapterregister vervollständigen

---

## 6. Architekturentscheidungen

- **Offline-First:** 19/22 Ressourcen sind offline verfügbar (Ausnahmen: DEEPL_API)
- **Originalschutz (ADR-0004):** Alle Ressourcen sind schreibschützend oder dokumentenbezogen, keine Originalveränderung
- **Keine harte Verdrahtung (ADR-0005):** `darf_von_modulen_verwendet_werden` als explizites Gate

---

*Dokument erstellt am 2026-05-16 – ALIN_Core_Build_Agent*
