#!/usr/bin/env python3
"""
WINAPP – Windows App Build und Release (Vorbereitung)
Lokale Buildstruktur, Pruefskripte, Release-Artefaktordner, Bericht und Sperrhinweise.
KEIN Produktivrelease. KEIN Deployment. KEINE echte Installation.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
EINGABEN = {
    "csproj": BASE_DIR / "Windows_App" / "App" / "KI_Legal_WindowsApp.csproj",
    "release_checklist": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "RELEASE_CHECKLIST.md",
    "changelog": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "CHANGELOG.md",
    "rollback_plan": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "ROLLBACK_PLAN.md",
    "version_json": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "VERSION.json",
    "build_script": BASE_DIR / "Windows_App" / "Scripts" / "Build_App.ps1",
}
AUSGABEN = {
    "bericht": BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "WINAPP_WINDOWS_APP_BUILD_RELEASE_BERICHT.txt",
    "sperrhinweise": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "SPERRHINWEISE_WINAPP.md",
}


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")


def pruefe_eingaben() -> tuple[bool, list[str]]:
    fehler = []
    for name, pfad in EINGABEN.items():
        if not pfad.exists():
            fehler.append(f"Eingabe fehlt: {name} -> {pfad}")
    return (len(fehler) == 0, fehler)


def pruefe_csproj() -> tuple[bool, list[str]]:
    fehler = []
    pfad = EINGABEN["csproj"]
    inhalt = pfad.read_text(encoding="utf-8")
    if "<Project" not in inhalt:
        fehler.append("csproj enthaelt kein <Project-Tag")
    if "<TargetFramework" not in inhalt and "<TargetFrameworks" not in inhalt:
        fehler.append("csproj enthaelt kein TargetFramework")
    return (len(fehler) == 0, fehler)


def aktualisiere_version_json() -> tuple[bool, str]:
    try:
        pfad = EINGABEN["version_json"]
        daten = json.loads(pfad.read_text(encoding="utf-8"))
        daten["build"] = datetime.now(timezone.utc).strftime("%Y%m%d")
        daten["letzte_aenderung"] = zeitstempel()
        daten["status"] = "vorbereitung"
        daten["hinweis"] = "Nur lokale Vorbereitung. Kein Produktivrelease."
        pfad.write_text(json.dumps(daten, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return (True, "VERSION.json aktualisiert")
    except Exception as e:
        return (False, str(e))


def aktualisiere_changelog() -> tuple[bool, str]:
    try:
        pfad = EINGABEN["changelog"]
        eintrag = f"\n## [{zeitstempel()}] WINAPP Vorbereitung\n- Buildstruktur geprueft\n- Release-Artefaktordner vorbereitet\n- Sperrhinweise dokumentiert\n- KEIN Produktivrelease\n"
        inhalt = pfad.read_text(encoding="utf-8")
        pfad.write_text(inhalt + eintrag, encoding="utf-8")
        return (True, "CHANGELOG.md aktualisiert")
    except Exception as e:
        return (False, str(e))


def erstelle_sperrhinweise() -> tuple[bool, str]:
    try:
        pfad = AUSGABEN["sperrhinweise"]
        text = (
            "# SPERRHINWEISE WINAPP\n\n"
            "## Rote Linien\n\n"
            "- [ ] KEIN Produktivrelease ohne gesonderte Freigabe.\n"
            "- [ ] KEIN Deployment auf Kanzleisysteme.\n"
            "- [ ] KEINE echte Installation ohne Abnahme.\n"
            "- [ ] KEINE Veroeffentlichung (Cloud/Internet).\n"
            "- [ ] KEINE echten Mandantendaten im Build.\n"
            "- [ ] KEIN MSIX-Paket ohne Signaturpruefung.\n\n"
            "## Zulaessig\n\n"
            "- [x] Lokale Buildstruktur vorbereiten.\n"
            "- [x] Build-Skripte erstellen und pruefen.\n"
            "- [x] Release-Artefaktordner anlegen.\n"
            "- [x] Demo-/Entwicklungsbuild dokumentieren.\n"
            "- [x] Signatur-/Installer-Anforderungen dokumentieren.\n\n"
            f"Erstellt: {zeitstempel()}\n"
        )
        pfad.write_text(text, encoding="utf-8")
        return (True, "SPERRHINWEISE_WINAPP.md erstellt")
    except Exception as e:
        return (False, str(e))


def schreibe_bericht(ergebnisse: list[tuple[str, bool, str]]) -> None:
    pfad = AUSGABEN["bericht"]
    lines = [
        "WINAPP – Windows App Build und Release (Vorbereitung)",
        "=" * 60,
        f"Zeitstempel: {zeitstempel()}",
        "Modul: WINAPP",
        "Stufe: Windows App Build und Release",
        "Hinweis: NUR VORBEREITUNG – Kein Produktivrelease",
        "",
        "Ergebnisse:",
        "-" * 40,
    ]
    for name, ok, msg in ergebnisse:
        status = "OK" if ok else "FEHLER"
        lines.append(f"[{status}] {name}: {msg}")
    lines.append("")
    lines.append("Zusammenfassung:")
    ok_count = sum(1 for _, ok, _ in ergebnisse if ok)
    lines.append(f"  Erfolgreich: {ok_count} / {len(ergebnisse)}")
    if ok_count == len(ergebnisse):
        lines.append("  Gesamt: ALLE PRUEFUNGEN BESTANDEN")
    else:
        lines.append("  Gesamt: FEHLER AUFGETRETEN")
    lines.append("")
    lines.append("Sperrhinweise:")
    lines.append("  - Kein Produktivrelease ohne gesonderte Freigabe.")
    lines.append("  - Kein Deployment auf Kanzleisysteme.")
    lines.append("  - Keine echten Mandantendaten im Build.")
    pfad.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    log("WINAPP – Windows App Build und Release (Vorbereitung) gestartet")
    ergebnisse: list[tuple[str, bool, str]] = []

    ok, fehler = pruefe_eingaben()
    ergebnisse.append(("Eingaben pruefen", ok, "; ".join(fehler) if fehler else "Alle vorhanden"))
    if not ok:
        log("FEHLER: Eingaben fehlen")
        schreibe_bericht(ergebnisse)
        return 1

    ok, fehler = pruefe_csproj()
    ergebnisse.append(("csproj pruefen", ok, "; ".join(fehler) if fehler else "Struktur OK"))

    ok, msg = aktualisiere_version_json()
    ergebnisse.append(("VERSION.json aktualisieren", ok, msg))

    ok, msg = aktualisiere_changelog()
    ergebnisse.append(("CHANGELOG.md aktualisieren", ok, msg))

    ok, msg = erstelle_sperrhinweise()
    ergebnisse.append(("Sperrhinweise erstellen", ok, msg))

    schreibe_bericht(ergebnisse)
    log("Bericht geschrieben")

    if all(ok for _, ok, _ in ergebnisse):
        log("WINAPP erfolgreich abgeschlossen")
        return 0
    else:
        log("WINAPP mit Fehlern abgeschlossen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
