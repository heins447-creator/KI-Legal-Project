# Posteingang – technischer Umsetzungsplan

Stand: 2026-05-10

## Ziel

Die Systematik des Posteingangs wird technisch so umgesetzt, daß jeder externe Eingang zuerst gesichert, geprüft, bewertet und organisatorisch zugeordnet wird, bevor er an den Anwalt oder in eine Akte gelangt.

## Erste technische Ausbaustufe

### 001 Posteingangsmodell und Statuswerte

Die Software erhält ein Modell für Eingang, Eingangsdatei, technische Prüfung, Absenderstatus und Vorzimmerentscheidung.

### 002 Eingangs-ID

Jeder Eingang erhält eine eindeutige ID.

Beispiel:

EING-2026-000001

### 003 Original und Arbeitskopie

Jede Datei wird getrennt gespeichert:

- Original unverändert
- Arbeitskopie für Verarbeitung

### 004 Hashwert

Für jede Datei wird ein Hashwert gebildet.

### 005 Sicherheitsstatus

Jede Datei erhält einen Sicherheitsstatus:

- ungeprüft
- unauffällig
- Hinweis
- eingeschränkt verarbeitbar
- Rückfrage erforderlich
- gesperrt
- kritischer Sicherheitsfall

### 006 Absenderstatus

Jeder Eingang erhält einen Absenderstatus:

- sicher erkannt
- plausibel erkannt
- unklar
- widersprüchlich
- verdächtig

### 007 Vorzimmer-Entscheidung

Die Software zeigt eine Handlungsempfehlung:

- weiter zur Vorprüfung
- Absender anschreiben
- Neuübersendung anfordern
- technische Prüfung veranlassen
- Anwalt mit Sperrvermerk informieren
- Fristverdacht markieren

### 008 KI nur nach Freigabe

Die KI darf nur Dateien verarbeiten, deren technischer Status dies erlaubt.

### 009 Anwaltsvorlage

Aus geprüften Metadaten, Kurzansichten und Vorzimmerentscheidung entsteht eine Vorlage an den Anwalt.

## Erste Programmieraufträge

1. Posteingangsmodell als Klassen und Statuswerte vorbereiten
2. Eingangs-ID erzeugen
3. Original- und Arbeitskopiepfade festlegen
4. Hashwertberechnung ergänzen
5. Sicherheitsstatusmodell ergänzen
6. Absenderstatusmodell ergänzen
7. Vorzimmer-Entscheidungstypen ergänzen
8. erste Posteingangsmaske vorbereiten

## Noch nicht in Ausbaustufe 1

- echte beA-Integration
- vollständige Signaturvalidierung
- vollständige Virenscanner-Integration
- Vollübersetzung
- Massennachimport
- juristische Beweismittelbewertung