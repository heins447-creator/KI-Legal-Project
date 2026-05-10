# Posteingang DB-Dateien Auswahl Testlauf V1

## Zweck

Dieses Modul nimmt vorhandene Dateien aus der Dokumententabelle der Kanzlei-Datenbank und legt geeignete Kopien wieder in den Roh-Eingang.

Es verändert die Ursprungsdateien nicht.

## Quelle

Quelle ist die Tabelle `documents` in:

`Database\Legal_Brain.duckdb`

## Ziel

Geeignete Kopien werden abgelegt in:

`Posteingang\00_Roh_Eingang`

Danach läuft der normale Posteingang:

1. Sicherheitsgate
2. Sprachkontext-Gate
3. Pipeline-Protokoll
4. Vorzimmer-Arbeitsliste
5. Gesamtstatus

## Auswahlregel

Nicht verwendet werden:

- Dateien aus dem Posteingang selbst
- AnythingLLM-Ablage
- ausführbare Dateien
- Skripte
- gepackte Archive
- leere Dateien
- sehr große Dateien

Bevorzugt werden:

- Textdateien
- PDF
- DOCX
- EML
- Dateien mit erkennbarem Hinweis auf Deutsch, Schwedisch oder Englisch

## Leitregel

Die Datenbank dient hier nur als Fundstelle.

Der Test erfolgt ausschließlich über Kopien im Roh-Eingang.
