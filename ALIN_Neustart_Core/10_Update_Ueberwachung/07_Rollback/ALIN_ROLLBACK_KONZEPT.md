# ALIN Rollback-Konzept

## Grundsatz

Jedes Update muss ein Rollback ermöglichen.

## Rollback-Verfahren

1. Vor dem Update: Backup der aktuellen Version
2. Update durchführen
3. Test durchführen
4. Bei Fehler: Rollback auf vorherige Version
5. Protokollierung aller Schritte

## Rollback-Kriterien

- Update führt zu Fehlern
- Update verletzt Lizenzbedingungen
- Update ist nicht kompatibel
- Update wurde nicht freigegeben

## Verantwortlichkeit

Rollback darf nur durch Administrator oder automatisch bei kritischen Fehlern erfolgen.
