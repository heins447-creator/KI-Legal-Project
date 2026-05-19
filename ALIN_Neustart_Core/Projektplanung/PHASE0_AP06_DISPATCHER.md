# Phase 0, AP 0.6: Dispatcher `alin.py`

## Ziel

`alin.py` ist die lokale Kommandozentrale fuer sichere Pruef- und Wartungslaeufe.

## Modi

- Standard: `--dry-run`
- Echte Ausfuehrung: `--execute`

## Kommandos

- `health`: lokaler Status als JSON
- `redline-check`: prueft eine Aktion gegen `.alin/redlines.json`
- `migrate`: ruft den DuckDB-Migrationsrunner auf
- `safety-setting`: Platzhalter fuer sicherheitsrelevante Einstellungen, nur mit Admin-Passwort

## Admin-Passwort

Es wird kein Klartextpasswort gespeichert. Fuer sicherheitsrelevante Befehle muss die Umgebung den SHA-256-Hash in `ALIN_ADMIN_PASSWORD_SHA256` enthalten.

## Beispiele

```powershell
python alin.py health
python alin.py --dry-run migrate
python alin.py --execute safety-setting --admin-password "***"
```
