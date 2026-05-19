# Phase 1, AP 1.2 — Werkzeuge offline herunterladen und SHA-256 pruefen

**Datum:** 2026-05-19  
**Status:** Infrastruktur bereit — Download ausstehend  
**Konfiguration:** `Config/phase1_ap02_offline_download_v1.json`  
**Manifest:** `09_Toolbibliothek/04_Hashes/SHA256_MANIFEST.csv`

---

## Ziel

Die 6 in AP 1.1 als `installationsstatus: ausstehend` markierten Tools werden als Offline-Pakete heruntergeladen und in `09_Toolbibliothek/02_Installer_Offline` abgelegt. Fuer jede Datei wird SHA-256 berechnet und im Manifest gespeichert.

## Tools (6)

| Tool-ID | Typ | Paket / Datei | Lizenz |
|---------|-----|----------------|--------|
| PADDLEOCR | Python Wheel | paddleocr | Apache-2.0 |
| PYHANKO | Python Wheel | pyhanko | MIT |
| MSOFFCRYPTO | Python Wheel | msoffcrypto-tool | MIT |
| CLAMAV | Installer | ClamAV-1.3.1.win.x64.msi | GPL-2.0 |
| OLLAMA | Installer | OllamaSetup.exe | MIT |
| ARGOS_TRANSLATE | Python Wheel | argostranslate | MIT |

## Ausfuehren

```powershell
# Alle 6 Tools herunterladen
.\Scripts\Run_PHASE1_AP02_Offline_Download.ps1

# Nur ein bestimmtes Tool
.\Scripts\Run_PHASE1_AP02_Offline_Download.ps1 -Tool PYHANKO

# Dry-Run (kein tatsaechlicher Download)
.\Scripts\Run_PHASE1_AP02_Offline_Download.ps1 -DryRun
```

## Verzeichnisstruktur nach Download

```
09_Toolbibliothek/
  02_Installer_Offline/
    PADDLEOCR/     paddleocr-*.whl
    PYHANKO/       pyhanko-*.whl
    MSOFFCRYPTO/   msoffcrypto_tool-*.whl
    CLAMAV/        ClamAV-1.3.1.win.x64.msi
    OLLAMA/        OllamaSetup.exe
    ARGOS_TRANSLATE/ argostranslate-*.whl
  04_Hashes/
    SHA256_MANIFEST.csv
```

## Hinweise

- **PADDLEOCR**: Das Hauptpaket `paddleocr` hat grosse Abhaengigkeiten (paddlepaddle ~1 GB). Der Runner laedt nur das Hauptrad ohne Abhaengigkeiten (`--no-deps`). Abhaengigkeiten werden in AP 1.3 (Bootstrapper) gesondert behandelt.
- **CLAMAV / OLLAMA**: Installer werden per HTTP direkt von den offiziellen Seiten geladen. Groesse ca. 30 MB (ClamAV) und 100 MB (Ollama).
- **ARGOS_TRANSLATE**: Sprachmodelle (`.argosmodel`-Dateien) sind nicht im Python-Paket enthalten und werden in AP 1.3 konfiguriert (Frage G5 analoge Entscheidung fuer Uebersetzungssprachen).

## Naechster Schritt

**AP 1.3** — Bootstrapper: alle 16 Tools pruefen, fehlende installieren.
