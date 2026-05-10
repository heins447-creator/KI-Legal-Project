# Posteingang Bedienstart V2

## Zweck

Der Bedienstart wurde an die neue Posteingangslogik angepaßt.

Das Menü enthält jetzt auch:

- Schlußkontrolle
- Alles ausführen

## Schlußkontrolle

Die Schlußkontrolle prüft, ob je Eingang die Mindestpunkte vorliegen:

- sicher
- bearbeitet
- Sprache erkannt
- grobe Arbeitsübersetzung nach Deutsch möglich
- Anwaltvorlage bereit oder durch Vorzimmer vorbereitbar

## Bedienung

Start über:

`I:\KI_Legal_Project\START_POSTEINGANG.cmd`

Oder direkt über:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Menu.ps1`

## Zentrale Aktionen

Die Zentrale kann direkt aufgerufen werden:

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Gesamtstatus`

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Produktionslauf`

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Schlusskontrolle`

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Arbeitsliste`

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Entscheidung`

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Aktenmaterial`

`I:\KI_Legal_Project\Scripts\Run_Posteingang_Zentrale.ps1 -Aktion Alles`

## Grenze

Der Posteingang bleibt technische und organisatorische Eingangsbearbeitung.

Inhaltliche Beweiswürdigung, Entlastungsbewertung, rechtliche Einordnung und endgültige Aktenzuordnung erfolgen nachgelagert.
