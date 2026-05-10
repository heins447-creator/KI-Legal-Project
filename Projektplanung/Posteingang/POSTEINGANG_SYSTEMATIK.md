# Posteingang – Systematik Vorzimmer bis Anwaltsvorlage

Stand: 2026-05-10

## Grundsatz

Der Posteingang ist die einzige zulässige Eintrittsstelle für alle von außen kommenden Nachrichten, Dateien und Dokumente.

Er ist nicht nur Dateiimport, sondern die technische und organisatorische Eingangsschleuse der Kanzlei.

Alles, was von außen kommt, wird erfaßt. Nichts wird ungeprüft in eine Akte, in eine KI-Auswertung oder in die anwaltliche Bearbeitung weitergereicht.

## Eingangsarten

Zum Posteingang gehören insbesondere:

- E-Mail
- beA-Eingang
- Upload
- Datenträger
- Papierpost mit Scan
- Mandantenunterlagen
- Gerichtsschreiben
- Behördenschreiben
- gegnerische Schriftsätze
- Arbeitsvertrag
- Kündigung
- Anlagen
- fremdsprachige Dokumente
- umfangreiche Aktenpakete

## Grundablauf

1. Eingang von außen
2. Eingang registrieren
3. Eingangs-ID vergeben
4. Original sichern
5. Arbeitskopie erzeugen
6. technische Prüfung
7. Sicherheitsstatus festlegen
8. Absenderstatus feststellen
9. Sprache und Dokumentart nur bei technischer Freigabe vorprüfen
10. Handlungsvorschlag für Sekretariat erzeugen
11. organisatorische Entscheidung der Sekretärin
12. Rückfrage, technische Prüfung, Sperrung oder Vorlage an Anwalt
13. anwaltliche Mandatsentscheidung

Ein problematischer Eingang wird nicht verworfen. Er wird gesichert, gesperrt, protokolliert und weitergeführt.

## Technische Prüfung

Vor jeder inhaltlichen Bearbeitung sind zwingend durchzuführen:

- Original unverändert speichern
- Hashwert bilden
- Dateityp prüfen
- Dateiendung mit tatsächlichem Dateityp abgleichen
- Schadsoftwareprüfung anstoßen
- gefährliche Dateitypen sperren
- Signaturstatus prüfen oder übernehmen
- Verschlüsselungsstatus prüfen
- Lesbarkeit feststellen
- Arbeitskopie erzeugen
- Prüfergebnis protokollieren

Gesperrte oder besonders zu prüfende Dateitypen:

- .exe
- .msi
- .bat
- .cmd
- .ps1
- .vbs
- .js
- .scr
- Makrodateien
- verschlüsselte Archive
- unbekannte Dateitypen

## Trennung zwischen Eingang und Dateiinhalt

Der Eingang wird unabhängig vom Dateiinhalt erfaßt.

Der digitale Umschlag enthält sichere Metadaten:

- Eingangsdatum
- Eingangskanal
- Absenderangaben
- Betreff
- Dateiname
- Dateigröße
- Hashwert
- Signaturstatus
- Sicherheitsstatus
- Vorgangs-ID
- Fristverdacht
- Bearbeitungsstatus

Auch wenn der Inhalt nicht geöffnet werden darf, bleibt der Eingang organisatorisch bearbeitbar.

## Sicherheitsstufen

S0 = unbedenklich  
S1 = geringer Hinweis  
S2 = eingeschränkt verarbeitbar  
S3 = technische Rückfrage erforderlich  
S4 = gesperrt, nicht öffnen  
S5 = kritischer Sicherheitsfall  

S0 bedeutet: Datei zulässig, schadstofffrei, lesbar, Absender plausibel. Weiter zur Vorprüfung.

S1 bedeutet: geringer Hinweis, aber kein schweres Risiko. Weiterverarbeitung mit Vermerk.

S2 bedeutet: Inhalt lesbar, aber Echtheit oder Signatur nicht vollständig gesichert. Verarbeitung mit Warnvermerk.

S3 bedeutet: Datei nicht lesbar, verschlüsselt oder Prüfstatus unklar. Rückfrage oder technische Prüfung erforderlich.

S4 bedeutet: Schadsoftwareverdacht, gesperrter Dateityp, Makro- oder Skriptrisiko. Nicht öffnen, nicht auswerten, nicht an KI geben.

S5 bedeutet: kritischer Sicherheitsfall, etwa widersprüchlicher Absender, mutmaßlicher Angriff oder verdächtige Datei in angeblichem Behörden- oder Gerichtseingang. Isolieren und technische Stelle oder Kanzleileitung informieren.

## Absenderstatus

A0 = sicher erkannt  
A1 = plausibel erkannt  
A2 = unklar  
A3 = widersprüchlich  
A4 = verdächtig  

Bei unklarem, widersprüchlichem oder verdächtigem Absender darf nicht blind über denselben Kanal vertraut werden. Rückfragen erfolgen über bekannte sichere Kontaktdaten oder sichere Übertragungswege.

## Rolle der Sekretärin

Die Sekretärin ist die organisatorische Entscheidungsstelle im Vorzimmer.

Sie entscheidet den nächsten organisatorischen Bearbeitungsschritt.

Sie darf und muß entscheiden:

- Absender anschreiben
- Neuübersendung anfordern
- sicheren Übertragungsweg verlangen
- technische Prüfung veranlassen
- Eingang vorläufig zuordnen
- Vorgang mit Sperrvermerk dem Anwalt vorlegen
- Fristverdacht markieren
- Rückfrage telefonisch oder schriftlich vorbereiten
- Vorlage an Anwalt freigeben

Sie entscheidet nicht:

- Mandat annehmen oder ablehnen
- Dokument ist rechtlich beweiskräftig
- Signatur ist rechtlich ausreichend
- Frist läuft sicher oder sicher nicht
- Beweismittel ist verwertbar oder unverwertbar

## Rolle der KI

Die KI arbeitet erst nach technischer Freigabe.

Sie darf unterstützen bei:

- Sprache erkennen
- Dokumentart vorschlagen
- Absender und Beteiligte aus sicherem Text erkennen
- Kurzansicht erzeugen
- mögliche Fristbegriffe markieren
- Dokumente gruppieren
- Rückfragevorschlag formulieren
- Vorlage an Anwalt vorbereiten

Sie darf nicht:

- Schadsoftware beurteilen
- Zertifikate abschließend bewerten
- Signaturstatus überstimmen
- gesperrte Dateien lesen
- unsichere Anhänge öffnen
- technische Sperren umgehen

Die technische Prüfroutine steht über der KI.

## Kurzansicht statt Vollübersetzung

Im Posteingang wird keine vollständige belastbare Übersetzung des gesamten Datenbestands erstellt.

Bei fremdsprachigen Dokumenten erzeugt die Software nur eine nicht zitierfähige Eingangskurzansicht.

Die Kurzansicht enthält:

- Sprache
- vermutete Dokumentart
- Kurzinhalt
- erkennbare Namen
- erkennbare Daten
- mögliche Fristen
- kritische Begriffe
- Hinweis auf späteren Übersetzungsbedarf

Diese Kurzansicht dient nur der Orientierung für Sekretariat und Anwalt.

## Vorlage an den Anwalt

Der Anwalt erhält keine ungeordnete Dateiablage, sondern eine Vorzimmer-Vorlage.

Diese enthält:

- vorläufige Vorgangs-ID
- Eingangsdatum
- Eingangskanal
- Absenderstatus
- erkannte oder vermutete Beteiligte
- Dokumentenübersicht
- technischer Sicherheitsstatus
- Signaturstatus
- Sprachstatus
- Kurzansicht fremdsprachiger Dokumente
- Fristverdacht
- problematische Dateien
- empfohlene nächste Schritte
- bereits veranlaßte Rückfragen

## Anwaltsentscheidung

Der Anwalt entscheidet:

- Mandat annehmen
- Mandat ablehnen
- weitere Unterlagen anfordern
- nur Erstberatung
- Interessenkollision prüfen
- Frist sofort prüfen
- technische Prüfung abwarten
- umfangreiche weitere Akten nachimportieren lassen

Erst nach anwaltlicher Annahme darf aus dem Eingang eine Mandatsakte entstehen.

## Zentrale Regel

Die Software prüft technisch.

Die KI ordnet nur nach technischer Freigabe vor.

Die Sekretärin entscheidet den organisatorischen nächsten Schritt.

Der Anwalt entscheidet rechtlich und mandatsbezogen.

Problematische Eingänge werden nicht verworfen. Sie werden gesichert, gesperrt, protokolliert, organisatorisch zugeordnet und entweder zur Neuübersendung, technischen Prüfung oder anwaltlichen Entscheidung weitergeführt.