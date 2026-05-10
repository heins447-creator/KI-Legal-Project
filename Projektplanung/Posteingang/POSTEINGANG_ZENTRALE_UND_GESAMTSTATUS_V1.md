# Posteingang Zentrale und Gesamtstatus V1

## Zweck

Dieser Schritt legt einen festen Einstieg für den Posteingang an.

Bisher bestehen mehrere Einzelskripte. Die Zentrale bündelt die Bedienung, ohne die Fachlogik zu vermischen.

## Zentrale

Der Einstieg liegt unter:

`Scripts\Run_Posteingang_Zentrale.ps1`

## Aufrufe

Gesamtstatus:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Gesamtstatus`

Betriebsstatus:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Status`

Produktionslauf:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Produktionslauf`

Vorzimmer-Arbeitsliste:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Arbeitsliste`

Vorzimmer-Entscheidung:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Entscheidung`

## Gesamtstatus

Der Gesamtstatus prüft:

- Pflichtskripte
- Pflichtordner
- offene Arbeitsdateien
- Nachweisdateien
- Datenbank-Grundzustand
- Sprachkontext-V2-Tabellen
- Git-Status

## Leitregel

Der Posteingang wird künftig über die Zentrale bedient.

Neue Dateien gehören ausschließlich in:

`Posteingang\00_Roh_Eingang`

Danach wird der Produktionslauf über die Zentrale gestartet.
