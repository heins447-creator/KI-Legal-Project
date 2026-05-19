# ALIN Tests

Dieses Verzeichnis enthaelt die pytest-kompatiblen Tests fuer ALIN.

Regeln:

- Nur synthetische Testdaten.
- Keine echten Mandantendaten.
- Keine Internetverbindungen.
- Keine Fremd-API-Aufrufe.
- Datenbanktests verwenden temporaere Datenbanken.

`pytest` ist in AP 0.3 konfiguriert, aber in der geprueften lokalen Laufzeit noch nicht installiert. Die Installation erfolgt spaeter nur kontrolliert aus dem Offline-Wheelhouse.
