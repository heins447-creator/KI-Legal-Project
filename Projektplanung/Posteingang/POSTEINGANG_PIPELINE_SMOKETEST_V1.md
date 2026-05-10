# Posteingang Pipeline Smoketest V1

## Zweck

Der Smoketest prüft, ob die Posteingang-Pipeline nicht nur leer durchläuft, sondern mit kontrollierten Testeingängen korrekt arbeitet.

## Geprüfte Fälle

Der Test legt vier künstliche Dateien in den Roh-Eingang:

1. schwedische Textdatei
2. deutsche Textdatei
3. aktive PowerShell-Datei
4. E-Mail mit Signaturhinweis

## Erwartung

Die aktive Datei muß in Quarantäne gehen.

Die signierte E-Mail muß in die Signaturprüfung gehen.

Die unauffälligen Textdateien müssen durch Sicherheitsprüfung und Sprachkontextprüfung laufen.

Zu den verarbeiteten Dateien müssen Sicherheitsberichte, Sprachberichte und Vorzimmer-Sprachkarten entstehen.

## Bereinigung

Alle durch den Test erzeugten Posteingangsdateien werden danach nach `Posteingang/99_Archiv_Altlasten` verschoben.

Der aktive Posteingang muß nach dem Test wieder leer sein.
