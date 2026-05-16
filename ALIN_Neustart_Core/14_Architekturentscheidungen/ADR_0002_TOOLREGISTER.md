# ADR 0002: Toolregister

## Kontext

Module dürfen keine Tools hart verdrahten.

## Entscheidung

Zentrales Toolregister in ALIN-Core.

## Begründung

- Einheitliche Verwaltung aller Tools.
- Lizenzprüfung vor Nutzung.
- Healthcheck für alle Tools.
- Keine harte Verdrahtung in Fachmodulen.

## Konsequenzen

- Jedes Tool muss im Register eingetragen sein.
- Module fragen ALIN-Core nach dem Tool.
