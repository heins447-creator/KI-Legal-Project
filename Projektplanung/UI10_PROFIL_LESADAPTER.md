# UI10 – Externer Profil-Leseadapter

**Modul-ID:** UI10  
**Version:** 1.0.0  
**Status:** Entwurf – außerhalb Demo-Betriebsstrecke  
**Letzte Änderung:** 2026-05-17  
**Autor:** ALIN Build-System  

---

## 1. Zweck

UI10 liest das **UI09-Zentrale-Profil** und stellt es als **Adapter-JSON** für Module außerhalb des Freeze bereit. Es prüft Konsistenz mit UI08, UI08b und UI08c, ohne die eingefrorene Strecke UI03–UI07b zu berühren.

### Kernprinzip

> **UI10 ist ein reiner Leseadapter.** Er schreibt nicht in UI03–UI07b, ändert keine bestehenden Module, erzeugt nur neue Dateien.

---

## 2. Rote Linie

| Regel | Wert |
|-------|------|
| `produktiv_freigegeben` | `false` |
| `nur_musterdaten` | `true` |
| `echte_daten_erlaubt` | `false` |
| `beruehrt_ui03_ui07b` | `false` |
| `nur_lesend` | `true` |
| `neue_dateien` | `true` |
| Datenbank-Änderung | **Nein** |

---

## 3. Architektur

### 3.1 Eingabe

| Quelle | Pfad | Optional |
|--------|------|----------|
| UI09 Zentrales Profil | `Windows_App/Logs/UI09_ZENTRALES_PROFIL.json` | Nein |
| UI09 Grundschalter | `Windows_App/Logs/UI09_GRUNDSCHALTER.json` | Ja |
| UI08 Posteingang-Status | `Windows_App/Logs/UI08_POSTEINGANG_STATUS.json` | Ja |
| UI08b Fehlerpfad-Status | `Windows_App/Logs/UI08B_FEHLERPFAD_STATUS.json` | Ja |
| UI08c Sanierungsstatus | `Windows_App/Logs/UI08C_SANIERUNGSSTATUS.json` | Ja |
| Sperrregister | `ALIN_Neustart_Core/01_Register/sperrregister.json` | Nein |

### 3.2 Verarbeitung

1. Sperrregister-Prüfung
2. UI09 Profil laden
3. UI09 Grundschalter laden
4. UI08/UI08b/UI08c laden (optional)
5. Konsistenzregeln anwenden
6. Adapter-JSON erstellen
7. HTML-Übersicht + JSON + Bericht + Konsistenz-Log erzeugen

### 3.3 Ausgabe

- `Windows_App/Logs/UI10_PROFIL_ADAPTER.json` – Maschinenlesbarer Adapter
- `Windows_App/Logs/UI10_ADAPTER_UEBERSICHT.html` – Visuelle Übersicht
- `Windows_App/Logs/UI10_PROFIL_LESADAPTER_BERICHT.txt` – Textbericht
- `Windows_App/Logs/UI10_KONSISTENZ_LOG.json` – Konsistenz-Log

---

## 4. Konsistenzregeln (5 Stück)

| ID | Beschreibung | Schwere | Quellen |
|----|--------------|---------|---------|
| KONS_01 | Demo-Modus → keine kritischen gesperrten Fehler in UI08b | WARNUNG | UI09, UI08b |
| KONS_02 | UI09 Sprache muss mit UI08 Sprachprofilen kompatibel sein | MITTEL | UI09, UI08 |
| KONS_03 | Sicherheitsstatus=gesperrt → UI08c meldet gesperrte | KRITISCH | UI09, UI08c |
| KONS_04 | OCR-Ressourcenpaket muss im Ressourcenregister verfügbar sein | HOCH | UI09, Ressourcenregister |
| KONS_05 | Offline-Status erfordert Offline-Cache aktiv | KRITISCH | UI09, UI09-GS |

---

## 5. Bereitgestellte Module (11 Stück)

| Modul | Genutzte Felder | Kompatibilität | Freeze-Status |
|-------|-----------------|--------------|---------------|
| UI08 | sprache_dokument, sicherheitsstatus, betriebsmodus, online_status | lesend | Außerhalb |
| UI08b | betriebsmodus, sicherheitsstatus, Freigaben | lesend | Außerhalb |
| UI08c | betriebsmodus, sicherheitsstatus, Freigaben | lesend | Außerhalb |
| UI03-1b | sprache_dokument, sprache_anwalt, akten_id, betriebsmodus | zukünftig | **Eingefroren** |
| UI03-1c | sprache_dokument, sprache_anwalt, akten_id, betriebsmodus | zukünftig | **Eingefroren** |
| UI03-1d | sprache_dokument, akten_id, betriebsmodus | zukünftig | **Eingefroren** |
| UI03-1e | sprache_anwalt, akten_id, betriebsmodus, mandant_id | zukünftig | **Eingefroren** |
| UI03-1f | akten_id, betriebsmodus, mandant_id | zukünftig | **Eingefroren** |
| UI03-1g | betriebsmodus, online_status, mandant_id | zukünftig | **Eingefroren** |
| UI04b | betriebsmodus, rechtsraum, sachgebiet, mandant_id | zukünftig | **Eingefroren** |
| UI05 | betriebsmodus, online_status, mandant_id, akten_id, freigabe_anwalt | zukünftig | **Eingefroren** |

> **UI03–UI07b bleiben eingefroren.** UI10 markiert sie als "zukünftig" kompatibel, ändert sie aber nicht.

---

## 6. Adapter-JSON-Struktur

```json
{
  "adapter_id": "UI10_PROFIL_ADAPTER",
  "timestamp": "2026-05-17T...",
  "quelle": "UI09",
  "profil_version": "1.0.0",
  "betriebsmodus": "demo",
  "freeze_kompatibilitaet": {
    "beruehrt_ui03_ui07b": false,
    "nur_lesend": true,
    "neue_dateien": true
  },
  "konsistenz": {
    "geprueft": true,
    "fehler": 0,
    "details": []
  },
  "profilfelder": { ... },
  "grundschalter": { ... },
  "bereitgestellt_fuer": [ ... ]
}
```

---

## 7. Lieferpflichten-Checkliste

- [x] Migration (keine DB-Änderung)
- [x] Python-Runner: `Scripts/python_runner/ui10_profil_lesadapter.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui10_profil_lesadapter.py`
- [x] PowerShell-Starter: `Scripts/UI10_PROFIL_LESADAPTER_AUTOLAUF.ps1`
- [x] Konfiguration: `Config/ui10_profil_lesadapter_v1.json`
- [x] Dokumentation: `Projektplanung/UI10_PROFIL_LESADAPTER.md`
- [ ] Testlauf (wird manuell durchgeführt)
- [ ] Bericht unter `Windows_App/Logs`
- [ ] Git-Status vor und nach Änderung
- [ ] Git-Commit bei erfolgreicher Prüfung

---

## 8. Abhängigkeiten

| Modul | Art |
|-------|-----|
| UI09 | Liest zentrales Profil |
| UI08 | Liest Posteingang-Status (optional) |
| UI08b | Liest Fehlerpfad-Status (optional) |
| UI08c | Liest Sanierungsstatus (optional) |
| Sperrregister | Prüft UI10-Sperre |
| Ressourcenregister | Prüft OCR-Paket-Verfügbarkeit (optional) |

---

## 9. Freeze-Kompatibilität

UI10 ist **absichtlich außerhalb des UI07b-Gesamtfreeze** konzipiert:
- Liest UI09 (außerhalb Freeze)
- Liest UI08/UI08b/UI08c (außerhalb Freeze)
- **Liest NICHT direkt UI03–UI07b**
- **Schreibt NICHT in UI03–UI07b**
- Erzeugt nur **neue Dateien** unter `Windows_App/Logs/`
- Adapter-JSON kann zukünftig von UI03–UI07b gelesen werden, wenn Freeze kontrolliert geöffnet wird

---

## 10. Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstellerstellung mit 5 Konsistenzregeln, 11 Modul-Mappings, Freeze-Kompatibilität |
