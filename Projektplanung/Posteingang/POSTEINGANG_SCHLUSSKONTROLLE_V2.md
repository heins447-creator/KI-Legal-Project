# Posteingang Schlußkontrolle V2

## Zweck

Die Schlußkontrolle prüft am Ende des Posteingangs, ob ein Eingang für die weitere Bearbeitung organisatorisch tragfähig vorbereitet ist.

Sie prüft mindestens:

- sicher
- bearbeitet
- Sprache erkannt
- grobe Arbeitsübersetzung nach Deutsch möglich
- Anwaltvorlage bereit oder durch Vorzimmer vorbereitbar

## Sprachlogik

Für den schwedischen Arbeitsrechtsfall gilt:

- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- grobe Arbeitsübersetzung: Deutsch

Mehrsprachige Dokumente werden nicht auf eine einzige Sprache verkürzt. Eine Primärsprache wird geführt, weitere erkannte Sprachen werden als Zusatzinformation gespeichert.

## Übersetzung

Der Posteingang fertigt keine rechtliche Übersetzung an.

Er erzeugt Übersetzungsaufträge nach Deutsch, die später über Google, KI oder ein lokales Sprachmodell ausgeführt werden können.

Das genügt für die erste Arbeitsübersetzung zur Anwaltvorlage.

## Grenze

Die Schlußkontrolle bewertet nicht:

- Beweiswert
- Entlastungswert
- rechtliche Erheblichkeit
- Zeugenbezug
- endgültige Aktenzuordnung

Diese Arbeit gehört in die nachgelagerte Agentenbearbeitung oder zur anwaltlichen Bearbeitung.

## Ergebnis

Die Schlußkontrolle erzeugt:

- Berichte unter `Windows_App\Logs\Posteingang_Schlusskontrolle`
- Übersetzungsaufträge unter `Posteingang\96_Uebersetzung_DE`
- Schlußkarten unter `Posteingang\97_Schlusskontrolle`

Die Zentrale kennt danach die Aktion:

`Schlusskontrolle`

Zusätzlich führt `Alles` den Produktionslauf, die Schlußkontrolle, die Arbeitsliste, die Aktenmaterial-Freigabeliste und den Gesamtstatus aus.
