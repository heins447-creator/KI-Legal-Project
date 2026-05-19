# UI08b – Fehlerpfadprüfung / Plausibilitätsprüfung Posteingang

**Modul-ID:** UI08b  
**Version:** 1.0.0  
**Status:** Entwurf – außerhalb Demo-Betriebsstrecke  
**Letzte Änderung:** 2026-05-17  
**Autor:** ALIN Build-System  

---

## 1. Zweck

UI08b prüft die bestehende Posteingang-Infrastruktur (UI08) auf **9 definierte Fehlerpfade**. Ziel ist nicht der Umbau, sondern die **Sichtbarmachung von Fehlerlagen**:

- Fehlende oder unsichere Sprache
- Fehlender Aktenbezug
- Gesperrter Eingang ohne Freigabe
- Fehlende Sicherheitsfreigabe
- Unklare Vorzimmerentscheidung
- Fehlende Anwaltfreigabe
- Blockierte Agentenbearbeitung
- Unvollständige Schlusskontrolle

---

## 2. Rote Linie

| Regel | Wert |
|-------|------|
| `produktiv_freigegeben` | `false` |
| `nur_musterdaten` | `true` |
| `echte_daten_erlaubt` | `false` |
| Änderungen an UI03-UI07b | **Verboten** (Freeze) |

---

## 3. Fehlerpfade (9 Stück)

| ID | Name | Schwere | Prüfmechanismus |
|----|------|---------|-----------------|
| FEHLER_01 | Fehlende Sprache | KRITISCH | DB: `dokumente.sprache IS NULL` |
| FEHLER_02 | Unsichere Sprache | HOCH | DB: `dokumente.sprache = 'unbekannt'` |
| FEHLER_03 | Fehlender Aktenbezug | KRITISCH | DB: `dokumente.akten_id IS NULL` |
| FEHLER_04 | Gesperrter Eingang | KRITISCH | JSON: `eingang_status.gesperrt = true` |
| FEHLER_05 | Fehlende Sicherheitsfreigabe | HOCH | JSON: `sicherheitsstatus.freigegeben = false` |
| FEHLER_06 | Unklare Vorzimmerentscheidung | MITTEL | JSON: `vorzimmer.entscheidung IN ('zurueckgehalten','unklar')` |
| FEHLER_07 | Fehlende Anwaltfreigabe | HOCH | JSON: `anwalt.freigabe = false` |
| FEHLER_08 | Blockierte Agentenbearbeitung | MITTEL | JSON: `agent.status IN ('blockiert','fehler')` |
| FEHLER_09 | Unvollständige Schlusskontrolle | KRITISCH | Datei: `schlusskontrolle.json` fehlt |

---

## 4. Architektur

### 4.1 Eingabe
- DuckDB `Database/Legal_Brain.duckdb` (Tabellen: `dokumente`, `posteingang`, `sprachprofile`)
- JSON-Karten unter `ALIN_Neustart_Core/02_Statusmodell/`
- Sperrregister `ALIN_Neustart_Core/01_Register/sperrregister.json`

### 4.2 Verarbeitung
1. Sperrregister-Prüfung
2. Für jeden Fehlerpfad:
   - DB-Prüfung (SQL WHERE)
   - JSON-Prüfung (Feldwert-Matching)
   - Datei-Prüfung (Existenz)
3. Aggregation nach Schweregrad
4. HTML-Übersicht mit Ampelfarben

### 4.3 Ausgabe
- `Windows_App/Logs/UI08B_FEHLERPFAD_UEBERSICHT.html` – Visuelle Fehlerübersicht
- `Windows_App/Logs/UI08B_FEHLERPFAD_STATUS.json` – Maschinenlesbarer Status
- `Windows_App/Logs/UI08B_FEHLERPFAD_PRUEFUNG_POSTEINGANG_BERICHT.txt` – Textbericht

---

## 5. Lieferpflichten-Checkliste

- [x] Migration (keine DB-Änderung, nur Lesen)
- [x] Python-Runner: `Scripts/python_runner/ui08b_fehlerpfad_pruefung_posteingang.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui08b_fehlerpfad_pruefung_posteingang.py`
- [x] PowerShell-Starter: `Scripts/UI08B_FEHLERPFAD_PRUEFUNG_POSTEINGANG_AUTOLAUF.ps1`
- [x] Konfiguration: `Config/ui08b_fehlerpfad_pruefung_posteingang_v1.json`
- [x] Dokumentation: `Projektplanung/UI08B_FEHLERPFAD_PRUEFUNG_POSTEINGANG.md`
- [ ] Testlauf (wird manuell durchgeführt)
- [ ] Bericht unter `Windows_App/Logs`
- [ ] Git-Status vor und nach Änderung
- [ ] Git-Commit bei erfolgreicher Prüfung

---

## 6. Abhängigkeiten

| Modul | Art |
|-------|-----|
| UI08 | Liest Posteingang-Struktur |
| UI03-1g | Liest Gesamtstatus |
| UI04b | Liest Logikprüfung-Status |
| UI05 | Liest Arbeitszentrale-Status |
| Sperrregister | Prüft UI08b-Sperre |

---

## 7. Freeze-Kompatibilität

UI08b ist **außerhalb des UI07b-Gesamtfreeze**. Es liest nur aus der eingefrorenen Strecke, schreibt nicht dorthin.

---

## 8. Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstellerstellung mit 9 Fehlerpfaden |
