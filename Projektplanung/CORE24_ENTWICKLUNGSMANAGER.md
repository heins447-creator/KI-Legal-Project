# CORE-24: Autonomer Entwicklungsmanager / Auftragsqueue / Selbstreparatur

**Modul-ID:** CORE-24  
**Version:** 1.0.0  
**Erstellt:** 2026-05-18  
**Status:** In Entwicklung  
**Ziel:** Ein selbstlaufender Entwicklungsprozess, der autonom Aufträge ausführt, Fehler repariert und bei Erfolg committet.

---

## 1. Übersicht

CORE-24 ist der erste vollständig autonome Entwicklungsmanager im ALIN_Neustart_Core. Er:

1. Liest das Dashboard ([`CORE23_dashboard.json`](ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json))
2. Prüft den Arbeitsindex ([`Config/core21_arbeitsindex_v1.json`](Config/core21_arbeitsindex_v1.json))
3. Bestimmt selbst den nächsten zulässigen Auftrag
4. Führt eine Auftragsqueue ([`CORE24_auftragsqueue.json`](ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json))
5. Führt für jeden Auftrag aus: `py_compile` → Runner → Check
6. Bei Fehler: Fehlerbericht auswerten → Reparaturauftrag erzeugen → erneut testen
7. Bei Erfolg: `git add` + `git commit`
8. Leitet den nächsten Auftrag aus der Queue ab
9. Hält nur bei harter Sperre an (z.B. Check 3x fehlgeschlagen, unbekannter Fehler, Pfad gesperrt)

---

## 2. Dateien

| Datei | Pfad | Zweck |
|-------|------|-------|
| Haupt-Runner | [`Scripts/python_runner/core24_entwicklungsmanager.py`](Scripts/python_runner/core24_entwicklungsmanager.py) | Queue-Logik, Selbstreparatur, Git-Commit |
| Prüfdatei | [`Scripts/python_runner/check_core24_entwicklungsmanager.py`](Scripts/python_runner/check_core24_entwicklungsmanager.py) | Prüft alle Voraussetzungen |
| PowerShell-Starter | [`Scripts/CORE24_ENTWICKLUNGSMANAGER_AUTOLAUF.ps1`](Scripts/CORE24_ENTWICKLUNGSMANAGER_AUTOLAUF.ps1) | Startet den gesamten Prozess |
| Konfiguration | [`Config/core24_entwicklungsmanager_v1.json`](Config/core24_entwicklungsmanager_v1.json) | Queue-Regeln, Reparatur-Limit, erlaubte Auftragstypen |
| Dokumentation | [`Projektplanung/CORE24_ENTWICKLUNGSMANAGER.md`](Projektplanung/CORE24_ENTWICKLUNGSMANAGER.md) | Diese Datei |
| Queue | [`ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json`](ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json) | Aktive Auftragsqueue |
| Reparatur-Log | [`ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_reparatur_log.json`](ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_reparatur_log.json) | Fehler- und Reparaturhistorie |
| Bericht | [`ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt`](ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt) | Laufzeitbericht |

---

## 3. Datenquellen

- [`ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json`](ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json)
- [`Config/core21_arbeitsindex_v1.json`](Config/core21_arbeitsindex_v1.json)
- [`Config/core22_agentenregeln_v1.json`](Config/core22_agentenregeln_v1.json)
- [`ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json`](ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json)
- [`ALIN_Neustart_Core/08_Migration/09_Manifest/AGENTENFREIGABE_KLARSTELLUNG.txt`](ALIN_Neustart_Core/08_Migration/09_Manifest/AGENTENFREIGABE_KLARSTELLUNG.txt)

---

## 4. Ablauf

### 4.1 Start (PowerShell-Starter)

1. Voraussetzungen prüfen (Python, Config)
2. Verzeichnisse sicherstellen
3. `py_compile` für Runner und Check
4. Check ausführen
5. Git-Status vorher speichern
6. Runner ausführen (autonomer Entwicklungsmanager)
7. Git-Status nachher speichern
8. Bei Erfolg: `git add` + `git commit`

### 4.2 Autonomer Entwicklungsmanager (Python-Runner)

1. **Initialisierung**
   - Bericht initialisieren
   - Konfiguration laden
   - Dashboard laden
   - Arbeitsindex laden
   - Queue laden

2. **Auftragsableitung**
   - Wenn Queue leer: Ableite ersten Auftrag aus Dashboard
   - Suche Module mit Status "fehlerhaft" oder "vorhanden"
   - Erzeuge Prüfungsauftrag für das nächste offene Modul

3. **Hauptschleife**
   - Finde nächsten ausstehenden Auftrag
   - Prüfe Auftragstyp (verboten → harte Sperre)
   - Prüfe Zielpfad (`bereich_status()`)
   - `py_compile` → Runner → Check
   - Bei Erfolg: `git add` + `git commit`
   - Bei Fehler: Reparaturauftrag erzeugen, erneut versuchen
   - Max. 3 Reparaturversuche pro Auftrag

4. **Abschluss**
   - Bericht schreiben
   - Queue speichern
   - Reparatur-Log speichern

---

## 5. Harte Sperre

Der Entwicklungsmanager hält an bei:

- Check 3x fehlgeschlagen für selben Auftrag
- Unbekannter Fehlertyp (nicht in erlaubten Fehlerkategorien)
- Zielpfad hat `bereich_status == 'gesperrt'`
- `py_compile` fehlschlägt nach 3 Reparaturversuchen
- Runner fehlschlägt nach 3 Reparaturversuchen
- Git-Commit fehlschlägt nach 3 Versuchen
- Auftragstyp in `verbotene_auftragstypen`

Bei harter Sperre:
- Auftrag wird als `hart_gesperrt` markiert
- Bericht wird geschrieben
- Reparatur-Log wird aktualisiert
- Prozess endet mit Exit-Code 1

---

## 6. Erlaubte und Verbotene Auftragstypen

### Erlaubt
- `python_runner`
- `alin_core_script`
- `pruefung`
- `manifest_schreiben`
- `bericht_schreiben`
- `git_status`
- `git_commit`

### Verboten
- `delete`
- `move`
- `rename`
- `pip_install`
- `pip_uninstall`
- `internet_zugriff`
- `datenbank_aenderung`
- `produktivfreigabe`
- `deployment`

---

## 7. Git-Regeln

- **Erlaubte Befehle:** `git status`, `git diff`, `git add`, `git commit`, `git log`
- **Commit-Nachricht:** Prefix `CORE-24`
- **Commit nur bei Erfolg:** Ja
- **Nur auftragsbezogene Dateien:** Ja

---

## 8. Konfiguration

Die Konfiguration [`Config/core24_entwicklungsmanager_v1.json`](Config/core24_entwicklungsmanager_v1.json) enthält:

- `queue_regeln`: Pfade, Max-Reparaturversuche, Pause
- `erlaubte_auftragstypen`: Liste erlaubter Typen
- `verbotene_auftragstypen`: Liste verbotener Typen
- `harte_sperre_bedingungen`: Liste der Sperrbedingungen
- `erlaubte_fehlerkategorien`: Fehler, die reparierbar sind
- `git_regeln`: Git-spezifische Einstellungen
- `python_toolchain`: Python-Interpreter, Runner-Verzeichnis

---

## 9. Lieferpflichten (AGENTS.md)

Jeder Baustein liefert:

1. ✅ Migration (falls Datenbank betroffen) – hier nicht betroffen
2. ✅ Python-Läufer unter `Scripts/python_runner/`
3. ✅ Prüfdatei unter `Scripts/python_runner/`
4. ✅ PowerShell-Starter unter `Scripts/`
5. ✅ Konfiguration unter `Config/`
6. ✅ Dokumentation unter `Projektplanung/`
7. ✅ Testlauf
8. ✅ Bericht unter `ALIN_Neustart_Core/Reports/`
9. ✅ Git-Status vor und nach Änderung
10. ✅ Git-Commit nur bei erfolgreichem Build und erfolgreicher Prüfung

---

## 10. Testlauf

### Voraussetzungen
- Python 3.12 unter `I:\KI_Legal_Project\Tools\Python312\python.exe`
- Git installiert und im PATH
- Alle Datenquellen vorhanden

### Schritte
1. PowerShell öffnen
2. `cd I:\KI_Legal_Project`
3. `.\Scripts\CORE24_ENTWICKLUNGSMANAGER_AUTOLAUF.ps1`

### Erwartetes Ergebnis
- py_compile erfolgreich
- Check erfolgreich (0 Fehler)
- Runner startet und verarbeitet Aufträge
- Git-Status vorher/nachher gespeichert
- Bei Erfolg: Git-Commit
- Bericht unter `ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt`

---

## 11. Abhängigkeiten

- CORE-21 (Arbeitsindex)
- CORE-22 (Agentenregeln)
- CORE-23 (Projekt-Dashboard)

---

## 12. Autor

Erstellt durch: Roo (KI-Coding-Agent)  
Datum: 2026-05-18  
Projekt: ALIN_Neustart_Core
