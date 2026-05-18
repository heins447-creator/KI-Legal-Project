# CORE-10e: Fehlende Abhängigkeit ui01_anwaltsansicht klären

## Auftrag

Ticket: CORE-10e  
Datum: 2026-05-16  
Bearbeiter: ALIN Core-Agent  
Status: Abgeschlossen (wartet auf Freigabe)

## Problemstellung

Im Rahmen der CORE-10 Konsistenzprüfung (P02 – fehlende Abhängigkeiten) wurde festgestellt, dass das Modul `check_ui01_anwaltsansicht_v1` eine Abhängigkeit auf `ui01_anwaltsansicht` deklariert, das Modul jedoch nicht im Modulregister existiert.

## Analyse

### Schritt 1: Suche im Modulregister

Suche nach `ui01_anwaltsansicht` im Modulregister ergab 4 Treffer:

| Zeile | Modul-ID | Typ | Bemerkung |
|-------|----------|-----|-----------|
| 4364 | `check_ui01_anwaltsansicht_v1` | pruefdatei | Deklariert Abhängigkeit auf `ui01_anwaltsansicht` |
| 4381 | — | — | Abhängigkeitseintrag: `"ui01_anwaltsansicht"` |
| 5410 | `ui01_anwaltsansicht_v1` | python_runner | Das eigentliche Modul existiert |

### Schritt 2: Root-Cause-Analyse

Das Modul `ui01_anwaltsansicht_v1` existiert im Register (Zeile 5410, Typ: `python_runner`).  
Die Abhängigkeit in `check_ui01_anwaltsansicht_v1` verweist jedoch auf `ui01_anwaltsansicht` **ohne** `_v1`-Suffix.

**Ursache:** Inkonsistente Namensgebung – fehlende Versionsnummer im Abhängigkeitsverweis.

### Schritt 3: Entscheidung

Da das Zielmodul eindeutig identifizierbar ist (`ui01_anwaltsansicht_v1`) und es sich um eine offensichtliche Namensinkonsistenz handelt, wird der Abhängigkeitsverweis korrigiert.

**Keine weiteren Änderungen** erforderlich (Altbestand, UI-Code, Ressourcen, Schnittstellen bleiben unberührt).

## Durchgeführte Änderung

### Datei: `ALIN_Neustart_Core/01_Register/modulregister.json`

**Zeile 4381** – Abhängigkeitsarray von `check_ui01_anwaltsansicht_v1`:

```diff
- "abhaengigkeiten": ["ui01_anwaltsansicht"],
+ "abhaengigkeiten": ["ui01_anwaltsansicht_v1"],
```

## Prüfung

Die Prüfdatei `alin_core10e_pruefung.py` verifiziert:
1. Alle Abhängigkeiten von `check_ui01_anwaltsansicht_v1` existieren als Modul-ID im Register.
2. Kein Verweis auf nicht-existente Module mehr vorhanden.

Ergebnis: **BESTANDEN** (Exit-Code 0)

## Liefergegenstände

| # | Datei | Zweck |
|---|-------|-------|
| 1 | `Scripts/alin_core10e_ui01_abhaengigkeit_klaeren.py` | Analyseskript |
| 2 | `Scripts/alin_core10e_pruefung.py` | Prüfdatei |
| 3 | `Scripts/Run_CORE10e_UI01_Abhaengigkeit.ps1` | PowerShell-Starter |
| 4 | `07_Bestandsaufnahme_Altbestand/CORE10e_UI01_Abhaengigkeit_Klaerung.md` | Dokumentation |
| 5 | `Reports/ALIN_CORE10E_UI01_ABHAENGIGKEIT_BERICHT.txt` | Bericht |

## Auswirkungen

- **P02-Finding:** Behoben (1 von N)
- **Risiko:** Keines – reine Korrektur eines Verweises
- **Breaking Change:** Nein
- **Datenbank:** Nicht betroffen
- **Altbestand:** Nicht betroffen

## Nächste Schritte

1. Freigabe durch Projektleitung
2. Commit nach Freigabe
3. Fortsetzung mit CORE-10b (Ressourcenlücken)

---
*Dokument erstellt gemäß AGENTS.md Lieferpflicht*
