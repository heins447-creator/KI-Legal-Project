# Phase 1, AP 1.1 — Endgültige Werkzeugliste mit Lizenzcheck

**Datum:** 2026-05-19  
**Status:** Abgeschlossen  
**Konfiguration:** `Config/phase1_ap01_toollist_v1.json`  
**Register:** `01_Register/toolregister.json`

---

## Ergebnis

16 Produktions-Tools identifiziert, lizenzgeprüft und im Toolregister dokumentiert.

### Endgültige Tool-Liste (16 Tools)

| # | Tool-ID | Name | Lizenz | Ampel | Status |
|---|---------|------|--------|-------|--------|
| 1 | PYTHON | Python 3.12 | PSF-2.0 | 🟢 | installiert |
| 2 | POWERSHELL | PowerShell 5.1+ | MIT | 🟢 | installiert |
| 3 | DOTNET_RUNTIME | .NET Runtime 8 | MIT | 🟢 | installiert |
| 4 | WEBVIEW2 | WebView2 Runtime | MS-Redistributable | 🟢 | installiert |
| 5 | DUCKDB | DuckDB 1.5.2 | MIT | 🟢 | installiert |
| 6 | TESSERACT | Tesseract OCR 5.4 | Apache-2.0 | 🟢 | installiert |
| 7 | PADDLEOCR | PaddleOCR 2.7 | Apache-2.0 | 🟢 | ausstehend (AP 1.2) |
| 8 | PYMUPDF | PyMuPDF (fitz) 1.24 | AGPL-3.0 | 🟡 | installiert |
| 9 | PYHANKO | pyHanko 0.21 | MIT | 🟢 | ausstehend (AP 1.2) |
| 10 | MSOFFCRYPTO | msoffcrypto-tool 5.4 | MIT | 🟢 | ausstehend (AP 1.2) |
| 11 | CLAMAV | ClamAV 1.3 | GPL-2.0 | 🟡 | ausstehend (AP 1.2) |
| 12 | PILLOW | Pillow 10 | HPND | 🟢 | installiert |
| 13 | NUMPY | NumPy 2 | BSD-3-Clause | 🟢 | installiert |
| 14 | OPENCV | OpenCV 4 | Apache-2.0 | 🟢 | installiert |
| 15 | OLLAMA | Ollama 0.3 | MIT | 🟢 | ausstehend (AP 1.2) |
| 16 | ARGOS_TRANSLATE | Argos Translate | MIT | 🟢 | nicht installiert (AP 1.2) |

### Entfernte Tools

| Tool-ID | Grund |
|---------|-------|
| ABBYY | Proprietäre Lizenz — per Arbeitsauftrag B7 gestrichen |
| AIDER | Nur Entwicklungswerkzeug, nicht Produktionssoftware |
| GIT | Nur Entwicklungswerkzeug, nicht Produktionssoftware |
| SQLITE | DuckDB ist Hauptdatenbank; SQLite ist Python-Stdlib, kein separates Tool |

---

## Offene Lizenzfragen

### 🟡 PyMuPDF (AGPL-3.0) — Frage G4
AGPL-3.0 kann bei Verkauf der Software Lizenzkonflikte auslösen. Muss vor erstem Verkauf durch Anwalt entschieden werden: freie AGPL-Variante behalten oder kommerzielle Lizenz kaufen.  
**Auswirkung jetzt:** Kein Blocker für Entwicklung. Tool darf verwendet werden.

### 🟡 ClamAV (GPL-2.0)
GPL-2.0 erlaubt kommerzielle Weitergabe, verlangt aber Beilage des Lizenztexts und Quellcode-Angebot. Beides ist standardmäßig erfüllt.  
**Auswirkung jetzt:** Kein Blocker.

### 🟡 LLM-Modell — Frage G5
Welches Modell wird in der Erstauslieferung mitgeliefert? Mistral, Phi-3 und Llama 3.1 8B sind unproblematisch lizenziert. Entscheidung steht noch aus.  
**Auswirkung jetzt:** Kein Blocker für AP 1.2 — Ollama wird ohne Standardmodell vorbereitet.

---

## Nächster Schritt

**AP 1.2** — Werkzeuge offline herunterladen, in `09_Toolbibliothek/02_Installer_Offline` ablegen, SHA-256 prüfen.

Betrifft: PADDLEOCR, PYHANKO, MSOFFCRYPTO, CLAMAV, OLLAMA, ARGOS_TRANSLATE (die noch nicht installierten Tools).
