# Sprachkontext Personen, Fall und Kommunikation V1

## Zweck

Die Software muß Sprache nicht nur als Liste von 24 Sprachen führen.

Erforderlich sind getrennte Ebenen:

1. Softwareebene
2. Personalebene
3. Fallebene
4. Beteiligtenebene
5. Kommunikationsebene

## Softwareebene

Alle 24 EU-Amtssprachen sind im System verfügbar.

Das bedeutet nicht, daß jeder Anwalt jeden Auftrag in jeder Sprache annimmt. Die Sprache ist verfügbar, aber die konkrete Nutzung wird durch Profile gesteuert.

## Personalebene

Für Anwalt und Sekretariat wird gespeichert:

- interne Arbeitssprache
- Sprachen, in denen Aufträge angenommen werden
- Sprachen, in denen aktiv kommuniziert werden kann
- Sprachen, in denen Dokumente geprüft werden können
- Zielsprachregel für Übersetzungen

Beispiel V1:

- Anwalt arbeitet intern deutsch
- Anwalt kann deutsch, englisch und schwedisch als Auftragssprachen freigeben
- Sekretariat arbeitet intern deutsch
- Sekretariat kann für Posteingang und Vorzimmer eigene Kommunikationssprachen haben

## Fallebene

Ein Fall führt eigene Sprachwerte.

Zu speichern sind insbesondere:

- Staat
- Landessprache
- Prozeßsprache
- interne Arbeitssprache
- Sprache eingehender Dokumente
- Zielsprache interner Dokumentenbearbeitung
- Standardsprache Mandant
- Standardsprache gegnerischer Anwalt
- Standardsprache Gegenseite
- Standardsprache Gericht

## Beteiligtenebene

Jeder Beteiligte kann eine eigene Sprachlage haben.

Beispiele:

- Mandant spricht Englisch
- Gericht arbeitet in der Prozeßsprache Schwedisch
- gegnerischer Anwalt kommuniziert Englisch
- Gegenseite spricht Schwedisch
- interne Bearbeitung erfolgt Deutsch

Diese Werte dürfen nicht vermischt werden.

## Kommunikationsebene

Die tatsächliche Schreibsprache wird je Empfängerrolle bestimmt.

Beispiele:

- Schreiben an Gericht: Schwedisch
- Schreiben an Mandant: Deutsch oder Englisch, je nach Mandantenprofil
- Schreiben an gegnerischen Anwalt: Englisch oder Schwedisch
- interne Notiz: Deutsch

## Mandant erst nach Annahme

Mandantenbezogene Spracheinstellungen werden erst verbindlich, wenn der Mandant angenommen wurde.

Vorher darf nur ein Vorprofil geführt werden.

Dieses Vorprofil dient der Eingangsprüfung, Rückfrage und Angebotsentscheidung. Es ersetzt keine Mandatsannahme.

## Vorlage Schweden Arbeitsrecht

V1 legt eine Vorlage an:

- Staat: Schweden
- Landessprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- Gerichtskommunikation: Schwedisch
- gegnerischer Anwalt: Englisch als Kommunikationssprache möglich
- Gegenseite: Schwedisch
- Mandant: vorläufig Deutsch, später mandantenbezogen änderbar

## Leitregel

Dokumentensprache, Kommunikationssprache, tatsächliche Sprache einer Person und Prozeßsprache sind getrennte Werte.

Nur so kann die Software später zutreffend entscheiden, ob übersetzt, vorgelegt, zurückgefragt oder in einer bestimmten Sprache geschrieben werden muß.
