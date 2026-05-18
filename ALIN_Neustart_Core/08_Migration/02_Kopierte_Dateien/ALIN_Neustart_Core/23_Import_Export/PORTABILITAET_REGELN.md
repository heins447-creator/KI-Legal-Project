# ALIN Portabilitätsregeln

## Grundsatz

Daten und Konfigurationen müssen portierbar sein.

## Regeln

1. Alle Pfade sind relativ.
2. Konfigurationen sind JSON-Dateien.
3. Datenbank ist portable Datei (DuckDB).
4. Keine absoluten Pfade in Config.
5. Keine Registry-Einträge.

## Migration

1. Export aus alter Umgebung.
2. Import in neue Umgebung.
3. Pfade anpassen.
4. Healthcheck durchführen.
