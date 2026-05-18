# ALIN Tool-Nachladekonzept

## Grundsatz

Module dürfen keine Tools selbst suchen, laden oder installieren. Module fragen ALIN-Core nach dem freigegebenen Tool.

## Nachlade-Routine

1. Prüfung: Ist das Tool im Toolregister?
2. Prüfung: Ist der Lizenzstatus freigegeben?
3. Prüfung: Ist das Tool installiert?
4. Falls nicht: Hinweis an Administrator, keine automatische Installation.

## Offline-Betrieb

- Alle benötigten Tools müssen vorab installiert sein.
- Keine Nachladung im Offline-Modus.
