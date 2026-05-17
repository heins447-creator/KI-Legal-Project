# UI08c – Fehlerpfad-Sanierungsplan Posteingang

**Modul-ID:** UI08c  
**Version:** 1.0.0  
**Status:** Entwurf – außerhalb Demo-Betriebsstrecke  
**Letzte Änderung:** 2026-05-17  
**Autor:** ALIN Build-System  

---

## 1. Zweck

UI08c wertet die Ergebnisse von **UI08b** strukturiert aus und erstellt einen **Sanierungsplan**. Ziel ist nicht die sofortige Sanierung, sondern die **Klärung von Verantwortlichkeiten, Sanierbarkeit und Freigabebedarf**.

### Kernfragen

| Frage | Beantwortung durch UI08c |
|-------|--------------------------|
| Was ist kritisch? | Schweregrad-Zählung pro Fehlerpfad |
| Was blockiert den Eingang? | `bleibt_gesperrt = true` |
| Was ist nur Warnung? | Schweregrad MITTEL |
| Wer muss reagieren? | 5 Verantwortlichkeiten: Posteingang, Vorzimmer, Anwalt, Agent, Schlusskontrolle |
| Was ist automatisch zulässig? | `automatisch = true` mit definierte Aktion |
| Was braucht manuelle Freigabe? | `automatisch = false` mit manueller Aktion |
| Was bleibt gesperrt? | `bleibt_gesperrt = true` |

---

## 2. Rote Linie

| Regel | Wert |
|-------|------|
| `produktiv_freigegeben` | `false` |
| `nur_musterdaten` | `true` |
| `echte_daten_erlaubt` | `false` |
| Änderungen an UI03–UI07b | **Verboten** (Freeze) |
| Datenbank-Änderung | **Nein** (nur lesend) |

---

## 3. Verantwortlichkeiten (5 Stellen)

| ID | Name | Zuständig für | Autom. sanierbar | Manuell erforderlich |
|----|------|---------------|------------------|----------------------|
| POSTEINGANG | Posteingang / Intake | FEHLER_01–04 | 01, 02 | 03, 04 |
| VORZIMMER | Vorzimmer / Sekretariat | FEHLER_05–06 | 05 | 06 |
| ANWALT | Anwalt | FEHLER_07 | – | 07 |
| AGENT | Agentenstrecke | FEHLER_08 | 08 | – |
| SCHLUSSKONTROLLE | Schlusskontrolle | FEHLER_09 | – | 09 |

---

## 4. Sanierungsregeln (9 Stück)

| Fehler | Name | Schwere | Autom. | Aktion | Gesperrt | Escalation |
|--------|------|---------|--------|--------|----------|------------|
| FEHLER_01 | Fehlende Sprache | KRITISCH | Ja | Tesseract-Neustart, OCR-Fallback | Nein | Vorzimmer |
| FEHLER_02 | Unsichere Sprache | HOCH | Ja | Warteschlange + Bestätigung | Nein | Vorzimmer |
| FEHLER_03 | Fehlender Aktenbezug | KRITISCH | Nein | Sekretariat ordnet zu | Ja | Anwalt |
| FEHLER_04 | Gesperrter Eingang | KRITISCH | Nein | Sicherheitsprüfung | Ja | Anwalt |
| FEHLER_05 | Fehlende Sicherheitsfreigabe | HOCH | Ja | Erneuter Scan | Nein | Vorzimmer |
| FEHLER_06 | Unklare Vorzimmerentscheidung | MITTEL | Nein | Weiche setzen | Nein | Anwalt |
| FEHLER_07 | Fehlende Anwaltfreigabe | HOCH | Nein | Anwalt prüft | Ja | Anwalt |
| FEHLER_08 | Blockierte Agentenbearbeitung | MITTEL | Ja | Task resetten | Nein | Vorzimmer |
| FEHLER_09 | Unvollständige Schlusskontrolle | KRITISCH | Nein | Manuell nachkontrollieren | Ja | Anwalt |

---

## 5. Architektur

### 5.1 Eingabe
- UI08b JSON-Status: `Windows_App/Logs/UI08B_FEHLERPFAD_STATUS.json`
- UI08b Textbericht: `Windows_App/Logs/UI08B_FEHLERPFAD_PRUEFUNG_POSTEINGANG_BERICHT.txt`
- Config: `Config/ui08c_fehlerpfad_sanierungsplan_posteingang_v1.json`
- Sperrregister

### 5.2 Verarbeitung
1. Sperrregister-Prüfung
2. UI08b-Ergebnis laden (falls vorhanden, sonst Config-Defaults)
3. Pro Verantwortlichkeit Fehlerpfade zuordnen
4. Sanierungsregeln anwenden (automatisch/manuell/gesperrt)
5. Zusammenfassung aggregieren
6. HTML/JSON/CSV/Bericht erzeugen

### 5.3 Ausgabe
- `Windows_App/Logs/UI08C_SANIERUNGSPLAN.html` – Visueller Plan
- `Windows_App/Logs/UI08C_SANIERUNGSSTATUS.json` – Maschinenlesbar
- `Windows_App/Logs/UI08C_SANIERUNGSPLAN_BERICHT.txt` – Textbericht
- `Windows_App/Logs/UI08C_MASSNAHMEN.csv` – CSV für Import/Weiterverarbeitung

---

## 6. Lieferpflichten-Checkliste

- [x] Migration (keine DB-Änderung)
- [x] Python-Runner: `Scripts/python_runner/ui08c_fehlerpfad_sanierungsplan_posteingang.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui08c_fehlerpfad_sanierungsplan_posteingang.py`
- [x] PowerShell-Starter: `Scripts/UI08C_FEHLERPFAD_SANIERUNGSPLAN_POSTEINGANG_AUTOLAUF.ps1`
- [x] Konfiguration: `Config/ui08c_fehlerpfad_sanierungsplan_posteingang_v1.json`
- [x] Dokumentation: `Projektplanung/UI08C_FEHLERPFAD_SANIERUNGSPLAN_POSTEINGANG.md`
- [ ] Testlauf (wird manuell durchgeführt)
- [ ] Bericht unter `Windows_App/Logs`
- [ ] Git-Status vor und nach Änderung
- [ ] Git-Commit bei erfolgreicher Prüfung

---

## 7. Abhängigkeiten

| Modul | Art |
|-------|-----|
| UI08b | Liest Fehlerpfad-Ergebnisse |
| UI08 | Liest Posteingang-Struktur |
| Sperrregister | Prüft UI08c-Sperre |

---

## 8. Freeze-Kompatibilität

UI08c ist **außerhalb des UI07b-Gesamtfreeze**. Es liest nur aus der eingefrorenen Strecke und aus UI08b, schreibt nicht dorthin.

---

## 9. Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstellerstellung mit 5 Verantwortlichkeiten und 9 Sanierungsregeln |
