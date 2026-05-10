# Posteingang Bedienstart V1

## Zweck

Dieser Schritt legt einen festen Bedienstart für den Posteingang an.

Künftig muß nicht mehr nach einzelnen Skripten gesucht werden.

## Startdateien

Projektwurzel:

`START_POSTEINGANG.cmd`

Menü-Starter:

`Scripts\Run_Posteingang_Menu.ps1`

Zentrale:

`Scripts\Run_Posteingang_Zentrale.ps1`

## Menü

Das Menü bietet:

1. Gesamtstatus
2. Produktionslauf
3. Vorzimmer-Arbeitsliste
4. Vorzimmer-Entscheidung
5. Betriebsstatus
0. Beenden

## Arbeitsregel

Neue fremde Dateien gehören ausschließlich nach:

`Posteingang\00_Roh_Eingang`

Danach wird im Menü der Produktionslauf gestartet.

## Keine Nachausführung von finally-Blöcken

Einzelne `finally`-Blöcke werden nicht mehr nachträglich in die Konsole eingefügt.

Die Starter führen selbständig zum Einstiegspunkt zurück.
