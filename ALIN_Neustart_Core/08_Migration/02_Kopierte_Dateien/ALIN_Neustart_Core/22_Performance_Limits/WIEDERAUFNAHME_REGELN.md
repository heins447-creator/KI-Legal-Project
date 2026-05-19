# ALIN Wiederaufnahme-Regeln

## Grundsatz

Abgebrochene Prozesse können wiederaufgenommen werden.

## Regeln

1. Status wird auf `abbruch` gesetzt.
2. Protokollierung: Abbruchgrund, Zeitstempel.
3. Wiederaufnahme möglich, wenn:
   - Fehler behoben
   - Ressourcen verfügbar
   - Keine Sperre

## Wiederaufnahme

1. Benutzer oder System startet Wiederaufnahme.
2. Prüfung: Ist Wiederaufnahme möglich?
3. Prozess wird fortgesetzt.
4. Protokollierung.
