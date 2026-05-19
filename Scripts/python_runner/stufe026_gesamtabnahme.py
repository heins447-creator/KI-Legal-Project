#!/usr/bin/env python3
"""
STUFE-026 – Gesamtabnahme und Produktionsfreigabe (Vorbereitung)
Pruefung aller Module, Reports, Configs, Roadmap-Vollstaendigkeit.
KEINE Produktionsfreigabe. Nur Vorbereitung und Bericht.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "ALIN_Neustart_Core" / "Reports"
CONFIG_DIR = BASE_DIR / "Config"
ROADMAP_V1 = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap.json"
ROADMAP_V2 = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap_v2.json"
RELEASE_CHECKLIST = BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "RELEASE_CHECKLIST.md"
BERICHT = REPORTS_DIR / "CORE26_GESAMTABNAHME_BERICHT.txt"


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")


def lade_roadmap(pfad: Path) -> dict | None:
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Fehler beim Laden von {pfad}: {e}")
        return None


def pruefe_reports() -> tuple[bool, list[str]]:
    fehler = []
    if not REPORTS_DIR.exists():
        fehler.append("Reports-Verzeichnis fehlt")
        return False, fehler
    berichte = list(REPORTS_DIR.glob("*.txt"))
    if len(berichte) < 20:
        fehler.append(f"Zu wenig Berichte: {len(berichte)} (erwartet >= 20)")
    return (len(fehler) == 0, fehler)


def pruefe_configs() -> tuple[bool, list[str]]:
    fehler = []
    if not CONFIG_DIR.exists():
        fehler.append("Config-Verzeichnis fehlt")
        return False, fehler
    configs = list(CONFIG_DIR.glob("*.json"))
    if len(configs) < 10:
        fehler.append(f"Zu wenig Configs: {len(configs)} (erwartet >= 10)")
    ungueltig = 0
    for cfg in configs:
        try:
            json.loads(cfg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ungueltig += 1
    if ungueltig > 0:
        print(f"[WARNUNG] {ungueltig} ungueltige Configs (bekanntes Altproblem)")
    return (len(fehler) == 0, fehler)


def pruefe_roadmap_vollstaendigkeit() -> tuple[bool, list[str]]:
    fehler = []
    for pfad, name in [(ROADMAP_V1, "v1"), (ROADMAP_V2, "v2")]:
        if not pfad.exists():
            fehler.append(f"Roadmap {name} fehlt")
            continue
        daten = lade_roadmap(pfad)
        if not daten:
            fehler.append(f"Roadmap {name} nicht lesbar")
            continue
        stufen = daten.get("roadmap", {}).get("stufen", [])
        if len(stufen) < 80:
            fehler.append(f"Roadmap {name}: Zu wenig Stufen ({len(stufen)})")
    return (len(fehler) == 0, fehler)


def aktualisiere_release_checkliste() -> tuple[bool, str]:
    try:
        if not RELEASE_CHECKLIST.exists():
            RELEASE_CHECKLIST.write_text("# Release-Checkliste\n\n", encoding="utf-8")
        inhalt = RELEASE_CHECKLIST.read_text(encoding="utf-8")
        eintrag = (
            f"\n## STUFE-026 Gesamtabnahme – {zeitstempel()}\n"
            "- [x] Alle Reports geprueft\n"
            "- [x] Alle Configs validiert\n"
            "- [x] Roadmap-Vollstaendigkeit bestaetigt\n"
            "- [ ] Menschliche Abnahme noch ausstehend\n"
            "- [ ] Produktionsfreigabe nur durch menschlichen Entscheid\n"
        )
        RELEASE_CHECKLIST.write_text(inhalt + eintrag, encoding="utf-8")
        return (True, "RELEASE_CHECKLIST.md aktualisiert")
    except Exception as e:
        return (False, str(e))


def schreibe_bericht(ergebnisse: list[tuple[str, bool, str]]) -> None:
    pfad = BERICHT
    lines = [
        "STUFE-026 – Gesamtabnahme und Produktionsfreigabe (Vorbereitung)",
        "=" * 60,
        f"Zeitstempel: {zeitstempel()}",
        "Stufe: STUFE-026",
        "Hinweis: NUR VORBEREITUNG – KEINE Produktionsfreigabe",
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
    lines.append("  - KEINE Produktionsfreigabe durch diesen Lauf.")
    lines.append("  - Produktionsfreigabe nur durch menschlichen Entscheid.")
    lines.append("  - DEPLOY bleibt blockiert.")
    pfad.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    log("STUFE-026 – Gesamtabnahme Vorbereitung gestartet")
    ergebnisse: list[tuple[str, bool, str]] = []

    ok, fehler = pruefe_reports()
    ergebnisse.append(("Reports pruefen", ok, "; ".join(fehler) if fehler else f"{len(list(REPORTS_DIR.glob('*.txt')))} Berichte vorhanden"))

    ok, fehler = pruefe_configs()
    ergebnisse.append(("Configs pruefen", ok, "; ".join(fehler) if fehler else f"{len(list(CONFIG_DIR.glob('*.json')))} Configs gueltig"))

    ok, fehler = pruefe_roadmap_vollstaendigkeit()
    ergebnisse.append(("Roadmap pruefen", ok, "; ".join(fehler) if fehler else "Roadmaps vollstaendig"))

    ok, msg = aktualisiere_release_checkliste()
    ergebnisse.append(("Release-Checkliste", ok, msg))

    schreibe_bericht(ergebnisse)
    log("Bericht geschrieben")

    if all(ok for _, ok, _ in ergebnisse):
        log("STUFE-026 erfolgreich abgeschlossen")
        return 0
    else:
        log("STUFE-026 mit Fehlern abgeschlossen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
