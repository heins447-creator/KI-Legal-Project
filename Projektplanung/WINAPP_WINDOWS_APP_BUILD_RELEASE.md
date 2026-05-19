# WINAPP – Windows App Build und Release (Vorbereitung)

## Ziel

Lokale Buildstruktur, Pruefskripte, Release-Artefaktordner, Bericht und Sperrhinweise fuer die Windows-App vorbereiten.

**WICHTIG:** Diese Stufe ist ausschliesslich Vorbereitung. Es findet kein Produktivrelease statt.

## Sicherheitsgrenzen (Rote Linien)

- **KEIN** Produktivrelease ohne gesonderte Freigabe.
- **KEIN** Deployment auf Kanzleisysteme.
- **KEINE** echte Installation ohne Abnahme.
- **KEINE** Veroeffentlichung (Cloud/Internet).
- **KEINE** echten Mandantendaten im Build.
- **KEIN** MSIX-Paket ohne Signaturpruefung.

## Zulaessig

- Lokale Buildstruktur vorbereiten.
- Build-Skripte erstellen und pruefen.
- Release-Artefaktordner anlegen.
- Demo-/Entwicklungsbuild dokumentieren.
- Signatur-/Installer-Anforderungen dokumentieren.
- Changelog und Version aktualisieren.

## Eingaben

| Datei | Beschreibung |
|-------|-------------|
| `Windows_App/App/KI_Legal_WindowsApp.csproj` | Projektdatei der Windows-App |
| `ALIN_Neustart_Core/16_Build_Release/RELEASE_CHECKLIST.md` | Release-Checkliste |
| `ALIN_Neustart_Core/16_Build_Release/CHANGELOG.md` | Changelog |
| `ALIN_Neustart_Core/16_Build_Release/ROLLBACK_PLAN.md` | Rollback-Plan |
| `ALIN_Neustart_Core/16_Build_Release/VERSION.json` | Versionsinformationen |
| `Windows_App/Scripts/Build_App.ps1` | Build-Skript |

## Ausgaben

| Datei | Beschreibung |
|-------|-------------|
| `ALIN_Neustart_Core/16_Build_Release/VERSION.json` | Aktualisierte Version (Status: vorbereitung) |
| `ALIN_Neustart_Core/16_Build_Release/CHANGELOG.md` | Aktualisierter Changelog |
| `ALIN_Neustart_Core/16_Build_Release/SPERRHINWEISE_WINAPP.md` | Sperrhinweise |
| `ALIN_Neustart_Core/Reports/WINAPP_WINDOWS_APP_BUILD_RELEASE_BERICHT.txt` | Bericht |

## Testkriterien

1. Alle Eingaben existieren.
2. `csproj`-Struktur ist gueltig.
3. `VERSION.json` wurde aktualisiert (Status: `vorbereitung`).
4. `CHANGELOG.md` enthaelt neuen Eintrag.
5. Sperrhinweise sind dokumentiert.

## Abhaengigkeiten

- `STUFE-012` (abgeschlossen)
- `UI14` (abgeschlossen)

## Technische Module

- `Scripts/python_runner/winapp_windows_app_build_release.py` – Runner
- `Scripts/python_runner/check_winapp_windows_app_build_release.py` – Check
- `Scripts/WINAPP_WINDOWS_APP_BUILD_RELEASE_AUTOLAUF.ps1` – PowerShell-Starter
- `Config/winapp_windows_app_build_release_v1.json` – Konfiguration

## Hinweis

Diese Stufe dient der Vorbereitung. Das tatsaechliche Kompilieren und Release der Windows-App erfordert eine gesonderte Freigabe und ist hier ausgeschlossen.
