# CORE-04 – Update-Register initial befüllen

**Datum:** 2026-05-16  
**Auftrag:** Update-Register mit initialen Einträgen befüllen (P0-1 aus CORE-03)  
**Scope:** ALIN_Neustart_Core/01_Register/update_register.json und ALIN_Neustart_Core/10_Update_Ueberwachung/00_Update_Register/ALIN_UPDATE_REGISTER.json

---

## 1. Ziel

Das Update-Register war vollständig leer (0 Einträge). Ohne Update-Register können Tools, Sprachpakete, Quellen, Adapter und Modelle nicht überwacht werden.  
**Ziel:** Mindestens alle bekannten Komponenten mit Update-Einträgen versehen, damit ein Healthcheck möglich ist.

---

## 2. Schema

**Datei:** `ALIN_Neustart_Core/01_Register/update_register.schema.json`

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| update_id | string | Eindeutige Update-ID (z. B. UPD_TESSERACT) |
| komponente_id | string | Verweis auf Lizenzregister |
| aktuelle_version | string | Aktuell installierte Version |
| verfuegbare_version | string | Neueste verfügbare Version |
| quelle | string | Download-Quelle |
| lizenz | string | Lizenzkennung |
| hash | string | SHA256-Hash (leer bei unbekannt) |
| pruefstatus | enum | geprüft/testbar/ungeprüft/gesperrt/zurückgesetzt |
| automatische_pruefung | boolean | Ob automatisch geprüft werden darf |
| automatische_ersetzung | boolean | Ob automatisch ersetzt werden darf |
| rollback_moeglich | boolean | Ob Rollback möglich ist |
| freigabeprotokoll | array | Liste der Freigabeeinträge |
| warnungen | array | Aktive Warnungen |

---

## 3. Befüllte Einträge (12 Stück)

| # | Update-ID | Komponente | Quelle | Lizenz | Rollback |
|---|-----------|------------|--------|--------|----------|
| 1 | UPD_TESSERACT | Tesseract OCR | GitHub Releases | Apache-2.0 | Nein |
| 2 | UPD_PYTHON | Python Interpreter | python.org | PSF-2.0 | Nein |
| 3 | UPD_AIDER | Aider (AI Agent) | GitHub Releases | Apache-2.0 | Nein |
| 4 | UPD_GIT | Git | git-scm.com | GPL-2.0 | Nein |
| 5 | UPD_DOTNET | .NET Runtime | Microsoft | MIT | Nein |
| 6 | UPD_WEBVIEW2 | WebView2 Runtime | Microsoft | MS-Lizenz | Nein |
| 7 | UPD_POWERSHELL | PowerShell | GitHub | MIT | Nein |
| 8 | UPD_SQLITE | SQLite | sqlite.org | Public-Domain | Nein |
| 9 | UPD_TESS_DEU | Tesseract DEU | tessdata | Apache-2.0 | Nein |
| 10 | UPD_TESS_SWE | Tesseract SWE | tessdata | Apache-2.0 | Nein |
| 11 | UPD_WINDOWS_APP | Windows-App (eigen) | Intern | Proprietär | **Ja** |
| 12 | UPD_ALIN_CORE | ALIN Core (Gesamtsystem) | Git | Proprietär | **Ja** |

---

## 4. Qualitätsmerkmale

- **Alle Versionen = "unbekannt":** Manuelle Prüfung erforderlich (kein automatischer Abruf)
- **Alle Prüfstatus = "ungeprueft":** Noch kein Healthcheck durchgeführt
- **Automatische Prüfung/Ersetzung = false:** Dry-Run-Standard (keine automatischen Änderungen)
- **Rollback nur für Eigenentwicklungen:** Windows-App und ALIN-Core
- **Warnungen vorhanden:** Jeder Eintrag hat kontextspezifische Warnungen

---

## 5. Erstellte Artefakte

| Artefakt | Pfad |
|----------|------|
| Python-Läufer | `ALIN_Neustart_Core/Scripts/alin_core04_update_register_befuellen.py` |
| Prüfdatei | `ALIN_Neustart_Core/Scripts/alin_core04_pruefung.py` |
| PowerShell-Starter | `ALIN_Neustart_Core/Scripts/Run_CORE04_Update_Register.ps1` |
| Update-Register (01) | `ALIN_Neustart_Core/01_Register/update_register.json` |
| Update-Register (10) | `ALIN_Neustart_Core/10_Update_Ueberwachung/00_Update_Register/ALIN_UPDATE_REGISTER.json` |
| Bericht | `ALIN_Neustart_Core/Reports/ALIN_CORE04_UPDATE_REGISTER_BERICHT.txt` |
| Dokumentation | `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE04_Update_Register_Befuellung.md` |

---

## 6. Validierung

- Schema-Validierung: OK
- Pflichtfelder: Alle 13 Felder pro Eintrag vorhanden
- Prüfstatus-Werte: Alle gültig
- Boolean-Felder: Alle korrekt typisiert
- Listen-Felder: Alle als Arrays vorhanden

**Ergebnis:** 0 Fehler, 0 Warnungen

---

## 7. Nächste Schritte

1. **CORE-05:** Toolregister vervollständigen (P0-2)
2. **CORE-06:** Ressourcenregister vervollständigen (P0-3)
3. **Versionsermittlung:** Aktuelle Versionen der 12 Komponenten manuell oder per Script ermitteln
4. **Healthcheck:** Ersten Update-Healthcheck durchführen

---

*Dokumentation erstellt im Rahmen von CORE-04.*  
*Liegt unter: ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE04_Update_Register_Befuellung.md*
