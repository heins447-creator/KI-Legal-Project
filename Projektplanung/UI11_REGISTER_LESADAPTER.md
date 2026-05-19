# UI11 – Register-Leseadapter

**Modul-ID:** UI11  
**Version:** 1.0.0  
**Status:** Entwurf – außerhalb Demo-Betriebsstrecke  
**Letzte Änderung:** 2026-05-17  
**Autor:** ALIN Build-System  

---

## 1. Zweck

UI11 liest alle **8 zentralen Register** aus `ALIN_Neustart_Core/01_Register/` und stellt sie als zentraler Adapter-JSON für Module außerhalb des Freeze bereit. Er ergänzt UI10 (Profil-Leseadapter) um eine zentrale Leseschicht für Verfügbarkeit, Sperren, Ressourcen, Skills und Quellenstatus.

### Abgedeckte Register

| Register | Datei | Inhalt |
|----------|-------|--------|
| Sperrregister | `sperrregister.json` | Gesperrte Module, Freigabebedingungen |
| Ressourcenregister | `ressourcenregister.json` | Verfügbare Ressourcen, Sprachpakete |
| Skillregister | `skillregister.json` | Agenten-Skills, Fähigkeiten |
| Toolregister | `toolregister.json` | Externe Tools, Versionen |
| Quellen-/Adapterregister | `quellen_adapter_register.json` | EU-Quellen, Adapter |
| Lizenzregister | `lizenzregister.json` | Lizenzen, Compliance |
| Update-Register | `update_register.json` | Update-Status, Versionen |
| Modulregister | `modulregister.json` | Alle Module, Abhängigkeiten |

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

| Quelle | Pfad |
|--------|------|
| Sperrregister | `ALIN_Neustart_Core/01_Register/sperrregister.json` |
| Ressourcenregister | `ALIN_Neustart_Core/01_Register/ressourcenregister.json` |
| Skillregister | `ALIN_Neustart_Core/01_Register/skillregister.json` |
| Toolregister | `ALIN_Neustart_Core/01_Register/toolregister.json` |
| Quellen-/Adapterregister | `ALIN_Neustart_Core/01_Register/quellen_adapter_register.json` |
| Lizenzregister | `ALIN_Neustart_Core/01_Register/lizenzregister.json` |
| Update-Register | `ALIN_Neustart_Core/01_Register/update_register.json` |
| Modulregister | `ALIN_Neustart_Core/01_Register/modulregister.json` |

### 3.2 Verarbeitung

1. Sperrregister-Prüfung für UI11
2. Alle 8 Register laden
3. Pro Register: Anzahl Einträge, Warnungen, Gesperrte zählen
4. Konsistenzregeln anwenden
5. Adapter-JSON erstellen
6. HTML-Übersicht + JSON + Bericht + Konsistenz-Log erzeugen

### 3.3 Ausgabe

- `Windows_App/Logs/UI11_REGISTER_ADAPTER.json` – Maschinenlesbarer Adapter
- `Windows_App/Logs/UI11_REGISTER_UEBERSICHT.html` – Visuelle Register-Übersicht
- `Windows_App/Logs/UI11_REGISTER_LESADAPTER_BERICHT.txt` – Textbericht
- `Windows_App/Logs/UI11_KONSISTENZ_LOG.json` – Konsistenz-Log

---

## 4. Konsistenzregeln (5 Stück)

| ID | Beschreibung | Schwere | Quellen |
|----|--------------|---------|---------|
| REG_KONS_01 | Gesperrte Module müssen im Modulregister existieren | KRITISCH | Sperrregister, Modulregister |
| REG_KONS_02 | Jedes Tool muss eine Lizenz haben | HOCH | Toolregister, Lizenzregister |
| REG_KONS_03 | Modul-Ressourcen müssen im Ressourcenregister existieren | MITTEL | Modulregister, Ressourcenregister |
| REG_KONS_04 | Update-Einträge nicht älter als 90 Tage | WARNUNG | Update-Register |
| REG_KONS_05 | Mindestens ein EU-Quelleneintrag | MITTEL | Quellen-/Adapterregister |

---

## 5. Adapter-JSON-Struktur

```json
{
  "adapter_id": "UI11_REGISTER_ADAPTER",
  "timestamp": "2026-05-17T...",
  "quelle": "ALIN_Neustart_Core/01_Register",
  "register_anzahl": 8,
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
  "register_zusammenfassung": {
    "sperrregister": { "eintraege": 2, "warnungen": 0, "gesperrt": 2, "status": "ok" },
    "ressourcenregister": { "eintraege": 40, ... },
    ...
  },
  "register_daten": {
    "sperrregister": { "schema_version": "1.0", "register_id": "...", "eintraege_anzahl": 2 },
    ...
  }
}
```

---

## 6. Lieferpflichten-Checkliste

- [x] Migration (keine DB-Änderung)
- [x] Python-Runner: `Scripts/python_runner/ui11_register_lesadapter.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui11_register_lesadapter.py`
- [x] PowerShell-Starter: `Scripts/UI11_REGISTER_LESADAPTER_AUTOLAUF.ps1`
- [x] Konfiguration: `Config/ui11_register_lesadapter_v1.json`
- [x] Dokumentation: `Projektplanung/UI11_REGISTER_LESADAPTER.md`
- [ ] Testlauf (wird manuell durchgeführt)
- [ ] Bericht unter `Windows_App/Logs`
- [ ] Git-Status vor und nach Änderung
- [ ] Git-Commit bei erfolgreicher Prüfung

---

## 7. Abhängigkeiten

| Modul | Art |
|-------|-----|
| UI09 | Liest zentrales Profil (optional, zukünftig kombinierbar) |
| UI10 | Liest Profil-Adapter (optional, zukünftig kombinierbar) |
| Sperrregister | Prüft UI11-Sperre |
| Alle 8 Register | Liest Register-Daten |

---

## 8. Freeze-Kompatibilität

UI11 ist **absichtlich außerhalb des UI07b-Gesamtfreeze** konzipiert:
- Liest nur aus `ALIN_Neustart_Core/01_Register/`
- **Liest NICHT direkt UI03–UI07b**
- **Schreibt NICHT in UI03–UI07b**
- Erzeugt nur **neue Dateien** unter `Windows_App/Logs/`

---

## 9. Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstellerstellung mit 8 Registern, 5 Konsistenzregeln, Freeze-Kompatibilität |
