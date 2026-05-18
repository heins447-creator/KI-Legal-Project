# CORE-10g – Reviewlisten dokumentieren

## Zweck

Lesende Analyse aller Module im [`modulregister.json`](ALIN_Neustart_Core/01_Register/modulregister.json) zur Erstellung von Reviewlisten für Backup/Restore, Offline-Betrieb und Sicherheitsüberprüfung. Keine Registeränderung, keine Modulausführung, keine Datenbankänderung, keine Online-/Cloud-Nutzung.

## Durchgeführte Analysen

| Kategorie | Anzahl | Beschreibung |
|---|---|---|
| DB-ändernde Module | 18 | `darf_datenbank_aendern=true` – relevant für Backup/Restore |
| Online-fähige Module | 14 | `darf_online_gehen=true` – relevant für Offline-Gerichtslaptop |
| Installations-/Update-Module | 5 | Keyword-Erkennung (install, update, patch, setup) |
| Rechtsbewertende Module | 0 | `darf_rechtsbewerten=true` |
| Beweiswürdigende Module | 0 | `darf_beweiswuerdigen=true` |
| Original-ändernde Module | 2 | `darf_originale_veraendern=true` |
| Produktiv freigegebene Module | 0 | `produktivfreigabe=true` |

## Risikoklassen-Verteilung

| Risikoklasse | Anzahl | Beschreibung |
|---|---|---|
| KRITISCH | 2 | Mehrere Hochrisiko-Berechtigungen aktiviert |
| HOCH | 14 | Mindestens eine Hochrisiko-Berechtigung aktiviert |
| MITTEL | 16 | Produktiv oder kombinierte Berechtigungen |
| NIEDRIG | 131 | Keine kritischen Berechtigungen |

## Kritische Module

1. **011_quellenbetreuer_fachanwaltsraster_v1** [anwalt]
   - `darf_datenbank_aendern=true`, `darf_online_gehen=true`
2. **014_source_adapter_healthcheck_framework_v1** [quellen]
   - `darf_datenbank_aendern=true`, `darf_online_gehen=true`

## Empfohlene Maßnahmen

- Backup-Konzept: 18 DB-ändernde Module erfordern vor dem Einsatz Datensicherung.
- Offline-Konfiguration: 14 online-fähige Module müssen auf dem Gerichtslaptop explizit deaktiviert oder quarantäniert werden.
- Originalschutz: 2 original-ändernde Module (`_patch_css`, `_patch_html`) erfordern besondere Aufmerksamkeit.
- Kritische Module: 2 Module mit kombiniertem DB- + Online-Zugriff sind für das Mandatsgeheimnis relevant.

## Dateien

- [`ALIN_Neustart_Core/04_Healthcheck/review_listen.json`](ALIN_Neustart_Core/04_Healthcheck/review_listen.json) – maschinenlesbare Reviewlisten
- [`ALIN_Neustart_Core/Scripts/alin_core10g_reviewlisten_dokumentieren.py`](ALIN_Neustart_Core/Scripts/alin_core10g_reviewlisten_dokumentieren.py)
- [`ALIN_Neustart_Core/Scripts/alin_core10g_pruefung.py`](ALIN_Neustart_Core/Scripts/alin_core10g_pruefung.py)
- [`ALIN_Neustart_Core/Scripts/Run_CORE10g_Reviewlisten.ps1`](ALIN_Neustart_Core/Scripts/Run_CORE10g_Reviewlisten.ps1)
- [`ALIN_Neustart_Core/Reports/ALIN_CORE10G_REVIEWLISTEN_BERICHT.txt`](ALIN_Neustart_Core/Reports/ALIN_CORE10G_REVIEWLISTEN_BERICHT.txt)
- [`ALIN_Neustart_Core/Reports/ALIN_CORE10G_PRUEFBERICHT.txt`](ALIN_Neustart_Core/Reports/ALIN_CORE10G_PRUEFBERICHT.txt)
- Diese Datei

## Grenzen

- Nur Register-Metadaten analysiert, kein Quellcode-Review.
- Risikoklassen basieren auf Heuristik (Berechtigungskombinationen).
- Keine Echtzeit-Überwachung, nur statische Klassifizierung.
