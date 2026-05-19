# CORE-10 – Modulabhaengigkeiten, Schnittstellen und Registerkonsistenz pruefen
## Auftrag

Nach Abschluss von CORE-09 (Modulregister vervollstaendigt) ist der naechste logische
Schritt eine Konsistenzpruefung ueber alle 163 Module sowie die dazugehoerigen
Register und Schnittstellen-Schemas.

## Ziel

Identifikation von Luecken, Widerspruechen und Risiken bevor weitere Bausteine
(Posteingang, OCR, UI, Tuerenschwelle) auf das Modulregister aufbauen.

## Pruefpunkte (12)

| Nr | Pruefpunkt | Beschreibung |
|----|------------|--------------|
| 01 | Modul-ID-Eindeutigkeit | Keine doppelten `modul_id` im Register |
| 02 | Fehlende Abhaengigkeiten | Jeder Eintrag in `abhaengigkeiten` muss auf existierende `modul_id` zeigen |
| 03 | Widerspruechliche Modulnamen | Gleicher `modulname` darf nicht auf unterschiedliche ID/Pfad verweisen |
| 04 | Module ohne Eingabe/Ausgabe/Teststatus | Heuristische Platzhalter-Erkennung |
| 05 | Aufrufrechte ohne Ressourcen | `darf_aufgerufen_werden=true` aber leere Tools/Skills/Ressourcen |
| 06 | Datenbank-aendernde Module | `darf_datenbank_aendern=true` – Review-Liste |
| 07 | Online-faehige Module | `darf_online_gehen=true` – Review-Liste |
| 08 | Unklare Schnittstellen | Generische/Platzhalter-Eingabe oder -Ausgabe |
| 09 | Uebergaben ohne Schema | `liefert_an` ohne passendes Schnittstellen-Schema |
| 10 | Querregister-Verknuepfungen | Tools, Ressourcen, Skills, Quellen muessen in ihren Registern existieren |
| 11 | Bidirektionale Abhaengigkeiten | A -> B in `abhaengigkeiten` erfordert B -> A in `liefert_an` |
| 12 | AGENTS.md-Konformitaet | `darf_rechtsbewerten=false`, `darf_beweiswuerdigen=false` fuer alle |

## Liefergegenstaende

1. `Scripts/alin_core10_konsistenz_pruefung.py` – Python-Pruefskript
2. `Scripts/Run_CORE10_Konsistenz.ps1` – PowerShell-Starter
3. `Reports/ALIN_CORE10_KONSISTENZ_BERICHT.txt` – Zusammenfassung
4. `Reports/ALIN_CORE10_PRUEFBERICHT.txt` – Detail-Findings
5. `Projektplanung/.../CORE10_... .md` – Dokumentation (diese Datei)

## Abgrenzung

- **Nur lesend**: Keine Aenderungen an Registern, DB oder Quellcode.
- **Kein Commit** ohne separate Freigabe.
- **Keine Internetverbindung** erforderlich.

## Naechster Schritt

Findings aus CORE-10 in die naechsten Auftraege (z. B. UI-Integration,
Posteingang-Pipeline) einfliessen lassen.
