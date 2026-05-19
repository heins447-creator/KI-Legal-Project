# ALIN Log-Sanitizing-Regeln

## Grundsatz

Logs dürfen keine vertraulichen Daten enthalten.

## Regeln

1. Keine Passwörter in Logs.
2. Keine API-Keys in Logs.
3. Keine Mandantendaten in Logs (außer ID).
4. Keine Dokumenteninhalte in Logs.
5. Persönliche Daten anonymisieren.

## Erlaubt in Logs

- IDs (Akten-ID, Mandanten-ID, Vorgangs-ID)
- Status
- Fehlermeldungen (ohne Daten)
- Zeitstempel
