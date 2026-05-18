# ALIN Secrets-Policy

## Grundsatz

Keine Zugangsdaten in Code, Logs oder Config.

## Regeln

1. Keine API-Schlüssel in Git.
2. Keine Passwörter in JSON-Dateien.
3. Keine Zugangsdaten in Logs.
4. Geheimnisse nur über geschützten lokalen Speicher.
5. Bei Verdacht auf Leak: Sofort ändern und protokollieren.

## Speicher

- Windows Credential Manager
- Oder geschützte lokale Datei (verschlüsselt)

## Verboten

- Hardcodierte Passwörter
- API-Keys in Quellcode
- Secrets in Umgebungsvariablen (außer lokale Entwicklung)
