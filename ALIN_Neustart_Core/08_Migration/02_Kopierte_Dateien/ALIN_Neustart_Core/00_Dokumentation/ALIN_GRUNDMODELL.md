# ALIN Grundmodell

## Zweck

ALIN-Core ist das zentrale Grundmodell der ALIN-Software. Es ist kein Fachmodul, keine UI und keine OCR. Es ist die professionelle Infrastruktur, auf der alle vorhandenen und künftigen Module aufsetzen.

## Was ALIN-Core leistet

1. **Identitäten** – Eindeutige IDs für Vorgänge, Dokumente, Seiten, Akten, Mandanten.
2. **Statusmodell** – Einheitliche Zustände für Eingang, Dokument, Akte, Weiche, Anwalt, Rücklauf.
3. **Register** – Zentrale Verzeichnisse für Module, Ressourcen, Skills, Quellen/Adapter, Tools, Lizenzen, Updates.
4. **Resolver** – Bestimmt aus Akte, Dokument und Eingang: Sprache, Land, Rechtsraum, Rechtsgebiet, benötigte Ressourcen, zulässiger nächster Schritt.
5. **Schnittstellenverträge** – Jedes Übergabeobjekt hat ein Schema mit Pflichtfeldern.
6. **Healthcheck** – Systemstart-Prüfung aller Bestandteile.
7. **Audit-/Protokollschicht** – Jede Entscheidung ist nachvollziehbar.
8. **Rollen-/Rechteschicht** – Sekretariat, Anwalt, Administrator, System, Agent.
9. **Test-/Abnahmeschicht** – Definition of Done für jedes Modul.
10. **Windows-App-Grundlage** – Vorbereitung für WinUI 3 / Windows App SDK.
11. **Toolbibliothek** – Zentrale Verwaltung aller externen Tools.
12. **Lizenzregister** – Jede Komponente hat Lizenzstatus, SPDX-ID, Hash, Freigabe.
13. **Update-Überwachung** – Prüfung, aber keine automatische unkontrollierte Ersetzung.
14. **Kanzlei-Sprachgebrauch** – UI verwendet Kanzleibegriffe, technische Begriffe bleiben intern.

## Was ALIN-Core nicht ist

- Kein Briefkasten (Posteingang existiert bereits).
- Keine OCR (KM12–KM21 existieren bereits).
- Keine Anwaltsvorlage (UI01–UI04 existieren bereits).
- Keine Türschwelle (wird später angebunden).
- Keine Quellenverwaltung (Quellenbetreuer existiert bereits).
- Keine Datenbankänderung (bestehende DB bleibt).

## Grundsatz: Keine harte Verdrahtung

Kein Fachmodul darf künftig Sprachpakete, Quellen, Adapter, Schreibweisen, Länderregeln, Tools, KI-Modelle oder Skills hart verdrahten.

Einzelmodule fragen ALIN-Core:

- Welche Sprache hat das Dokument?
- Welches Land / welcher Rechtsraum gilt?
- Welches Rechtsgebiet gilt?
- Welche OCR-Ressource ist freigegeben?
- Welche Übersetzungsressource ist freigegeben?
- Welche Quelle ist zulässig?
- Welcher Adapter ist verfügbar?
- Welcher Skill ist geprüft?
- Welches Tool ist Standard?
- Welcher Offline-Fallback gilt?
- Welche Warnungen bestehen?
- Welcher nächste Prozessschritt ist zulässig?

## Verzeichnisstruktur

```
ALIN_Neustart_Core/
├── 00_Dokumentation
├── 01_Register
├── 02_Statusmodell
├── 03_Schnittstellen
├── 04_Healthcheck
├── 05_Resolver
├── 06_Audit_Protokoll
├── 07_Bestandsaufnahme_Altbestand
├── 08_Windows_App_Grundlage
├── 09_Toolbibliothek
├── 10_Update_Ueberwachung
├── 11_Lizenzen_Compliance
├── 12_Dokumentation_Hilfe_Infofelder
├── 13_Anforderungen_Abnahme
├── 14_Architekturentscheidungen
├── 15_Teststrategie
├── 16_Build_Release
├── 17_Backup_Restore
├── 18_Rechte_Rollen
├── 19_Secrets_Sicherheit
├── 20_Datenschutz_Mandatsgeheimnis
├── 21_Support_Diagnose
├── 22_Performance_Limits
├── 23_Import_Export
├── 24_Konfigurationsprofile
├── Scripts
└── Reports
```

## Altbestand

Der vorhandene Altbestand unter `I:\KI_Legal_Project` bleibt unverändert. Er wird später nur lesend inventarisiert und sauber an das neue Grundmodell angebunden.

## Nächste Aufträge

Siehe [`ALIN_NAECHSTE_AUFTRAEGE.md`](ALIN_NAECHSTE_AUFTRAEGE.md).
