# ALIN Timeout-Regeln

## Grundsatz

Jeder Prozess hat ein Timeout.

## Regeln

1. Timeout wird vor Prozessstart festgelegt.
2. Bei Timeout: Prozess abbrechen, Status auf `abbruch` setzen.
3. Protokollierung: Zeitstempel, Dauer, Grund.
4. Benachrichtigung: Administrator bei wiederholten Timeouts.

## Standard-Timeouts

| Prozess | Timeout |
|---------|---------|
| OCR | 300 s |
| Übersetzung | 120 s |
| Datenbank | 30 s |
| Healthcheck | 60 s |
