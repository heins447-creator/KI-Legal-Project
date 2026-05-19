# API-Key-Verbot in Git

## Grundsatz

API-Keys dürfen niemals in Git committet werden.

## Maßnahmen

1. `.gitignore` enthält alle Config-Dateien mit Secrets.
2. Pre-Commit-Hooks prüfen auf API-Keys.
3. Code-Review: Keine Secrets im Code.

## Bei Verstoß

1. Key sofort widerrufen.
2. Neuen Key generieren.
3. Protokollieren.
