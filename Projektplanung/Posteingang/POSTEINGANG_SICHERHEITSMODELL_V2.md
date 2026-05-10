# Posteingang Sicherheitsmodell V2

## Zweck

V2 ergänzt die vorhandene Posteingangsstruktur um ein Sicherheitsgatter.

Der Posteingang bleibt ein vorgelagerter Sicherheits-, Prüf- und Entscheidungsbereich. Keine fremde Datei wird unmittelbar in den normalen Dokumentenbestand übernommen.

## Prüfungen in V2

V2 führt folgende Prüfungen aus:

- SHA-256-Hash
- Dateigröße
- Dateiendung
- Dateikopf
- Erkennung aktiver oder ausführbarer Dateien
- Erkennung doppelter gefährlicher Endungen
- Windows-Defender-Prüfung über PowerShell
- Authenticode-Abfrage über Windows
- Erkennung von Signaturhinweisen in E-Mail, PDF, XML und Signaturcontainern
- Erzeugung einer Sicherheitskarte
- Erzeugung eines Sicherheitsberichtes

## Signierte Postsendungen

Signierte Postsendungen werden in V2 nicht automatisch als sicher behandelt.

Signiert bedeutet nicht automatisch vertrauenswürdig.

Bei S/MIME, PDF-Signaturen, P7M/P7S, ASiC, XML-Signaturen und vergleichbaren Signaturformen wird zunächst nur erkannt, daß eine Signaturprüfung erforderlich ist. Diese Eingänge werden in `Posteingang/07_Signaturpruefung` überführt.

## Grenzen von V2

V2 ist noch keine vollständige beA-, S/MIME-, PAdES-, XAdES- oder qualifizierte Signaturprüfung.

V2 schafft die sichere Schleuse. Die vollständige fachliche Signaturvalidierung folgt in V3.

## Entscheidungslinie

- Ausführbare oder aktive Dateien bleiben gesperrt.
- Unklare Dateien bleiben in Quarantäne.
- Signaturhinweise führen zur Signaturprüfung.
- Nur technisch unauffällige Dateien gehen an das Vorzimmer.
- Das Vorzimmer entscheidet über Weitergabe, Rückfrage, Ersatzanforderung oder Zurückweisung.
