# Posteingang Pipeline V1

## Zweck

Diese Pipeline verbindet die bisher getrennten Posteingangsschritte zu einem geordneten Ablauf.

Der Posteingang bleibt ein vorgelagerter Sicherheits-, Prüf- und Entscheidungsbereich. Keine fremde Datei wird unmittelbar in den normalen Dokumentenbestand übernommen.

## Ablauf

1. Neue Dateien liegen in `Posteingang/00_Roh_Eingang`.
2. Das Sicherheitsgate prüft Hashwert, Dateityp, aktive Dateiendungen, Signaturhinweise, Windows-Defender-Anstoß und Authenticode-Hinweise.
3. Gesperrte oder unklare Dateien bleiben in Quarantäne oder Signaturprüfung.
4. Nur technisch freigegebene Dateien gelangen in die Sprachkontextprüfung.
5. Die Sprachkontextprüfung vergleicht erwartete Dokumentensprache, erkannte Sprache, interne Arbeitssprache, Prozeßsprache und Kommunikationssprache.
6. Das Ergebnis wird für das Vorzimmer protokolliert.
7. Erst danach kann entschieden werden, ob die Sache an Anwaltvorlage, Rückfrage, Abweisung oder spätere Aktenzuordnung geht.

## Grundsatz

Signiert bedeutet nicht automatisch sicher.

Technisch unauffällig bedeutet nicht automatisch fachlich verwertbar.

Sprachlich passend bedeutet nicht automatisch aktenreif.

Die Vorzimmerentscheidung bleibt als eigener Schritt sichtbar.
