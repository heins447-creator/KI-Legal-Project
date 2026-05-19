# CORE-09 – Modulregister vervollständigen

## Auftrag
Das Modulregister im Neustart-Core fachlich und technisch vervollständigen. Die vorhandenen 163 Module sollen mit Beschreibung, Version, Eingabe, Ausgabe, Abhängigkeiten, Status und Verwendungsgrenzen ergänzt werden.

## Durchführung
1. Schema auf Version 1.1.0 erweitert um:
   - modultyp, bereich, kurzbeschreibung
   - version_status, eingabe, ausgabe
   - benoetigte_tools, benoetigte_ressourcen, benoetigte_skills, benoetigte_quellen
   - abhaengigkeiten, liefert_an
   - teststatus
   - darf_originale_veraendern, darf_datenbank_aendern, darf_online_gehen
   - darf_rechtsbewerten, darf_beweiswuerdigen
   - naechster_pruefbedarf

2. Python-Befüllskript `alin_core09_modulregister_befuellen.py` erstellt.
   - Liest vorhandenes Modulregister und Altbestand
   - Bestimmt modultyp aus Dateiendung und Namen
   - Bestimmt bereich aus Modul-ID, Namen und Pfad
   - Generiert kurzbeschreibung aus bekannten Mapping oder heuristisch
   - Bestimmt eingabe/ausgabe aus modultyp und bereich
   - Ordnet tools, ressourcen, skills, quellen zu
   - Ermittelt abhaengigkeiten heuristisch (Prüfdateien -> Zielmodul, PowerShell -> Python-Runner, KM-Kette)
   - Berechnet liefert_an bidirektional
   - Setzt Verwendungsgrenzen konservativ
   - Markiert unklare Angaben entsprechend

3. Python-Prüfskript `alin_core09_pruefung.py` erstellt.
   - Prüft Schema-Version, Pflichtfelder, Eindeutigkeit
   - Prüft Enum-Werte, Boolean-Typen, Array-Typen
   - Prüft Konsistenz: gesperrt => darf_aufgerufen_werden = false
   - Prüft AGENTS.md-Konformität: darf_rechtsbewerten = false, darf_beweiswuerdigen = false
   - Prüft bidirektionale Abhängigkeiten
   - Prüft Pfad-Existenz (nur Warnung)

4. PowerShell-Starter `Run_CORE09_Modulregister.ps1` erstellt.

## Ergebnis
- `ALIN_Neustart_Core/01_Register/modulregister.schema.json` (1.1.0)
- `ALIN_Neustart_Core/01_Register/modulregister.json` (vervollständigt)
- `ALIN_Neustart_Core/Scripts/alin_core09_modulregister_befuellen.py`
- `ALIN_Neustart_Core/Scripts/alin_core09_pruefung.py`
- `ALIN_Neustart_Core/Scripts/Run_CORE09_Modulregister.ps1`
- `ALIN_Neustart_Core/Reports/ALIN_CORE09_MODULREGISTER_BERICHT.txt`
- `ALIN_Neustart_Core/Reports/ALIN_CORE09_PRUEFBERICHT.txt`
- `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_modulkarte.json` (unverändert, nur lesend)

## Grenzen
- Keine Internetabfrage.
- Keine Downloads.
- Keine Installation.
- Keine Altbestandsänderung.
- Keine Datenbankänderung.
- Kein Commit ohne Freigabe.

## Nächster sinnvoller Auftrag
CORE-10 – Modulregister-Abhängigkeiten validieren und testen.
Oder: Inhaltsanalyse der Modul-Dateien für präzisere Beschreibungen.
