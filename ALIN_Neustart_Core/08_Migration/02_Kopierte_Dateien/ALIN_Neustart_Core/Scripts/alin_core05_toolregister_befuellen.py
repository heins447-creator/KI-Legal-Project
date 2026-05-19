# -*- coding: utf-8 -*-
"""
CORE-05 – Toolregister vervollstaendigen und mit Update-Register abgleichen

Befuellt beide Toolregister (01_Register/ und 09_Toolbibliothek/00_Toolregister/)
mit erweiterten Eintraegen und verknuepft mit Update-Register.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

CORE = Path("I:/KI_Legal_Project/ALIN_Neustart_Core")
REGISTER_DIR = CORE / "01_Register"
TOOLREG_DIR = CORE / "09_Toolbibliothek/00_Toolregister"
REPORTS_DIR = CORE / "Reports"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    print("=" * 70)
    print("CORE-05 – Toolregister vervollstaendigen")
    print("=" * 70)

    # Toolregister laden
    toolreg = load_json(REGISTER_DIR / "toolregister.json")
    eintraege = toolreg.get("eintraege", [])

    print(f"Vorhandene Eintraege: {len(eintraege)}")

    # Update-Register laden fuer Abgleich
    update_reg = load_json(REGISTER_DIR / "update_register.json")
    update_ids = {e["komponente_id"]: e["update_id"] for e in update_reg.get("eintraege", [])}

    # Verknuepfung pruefen und ergaenzen
    verknuepft = 0
    for e in eintraege:
        tool_id = e.get("tool_id", "")
        if tool_id in update_ids and not e.get("update_id"):
            e["update_id"] = update_ids[tool_id]
            verknuepft += 1

    print(f"Update-Verknuepfungen ergaenzt: {verknuepft}")

    # Zeitstempel aktualisieren
    toolreg["letzte_aenderung"] = now_iso()

    # Beide Pfade schreiben
    path_01 = REGISTER_DIR / "toolregister.json"
    path_09 = TOOLREG_DIR / "ALIN_TOOLREGISTER.json"

    save_json(path_01, toolreg)
    save_json(path_09, toolreg)

    print(f"Geschrieben nach: {path_01}")
    print(f"Geschrieben nach: {path_09}")

    # Bericht
    bericht = []
    bericht.append("=" * 70)
    bericht.append("CORE-05 TOOLREGISTER BERICHT")
    bericht.append("=" * 70)
    bericht.append(f"Zeitstempel: {now_iso()}")
    bericht.append(f"Gesamtanzahl Tools: {len(eintraege)}")
    bericht.append("")

    installiert = [e for e in eintraege if e.get("installationsstatus") == "installiert"]
    nicht_installiert = [e for e in eintraege if e.get("installationsstatus") == "nicht_installiert"]
    unbekannt = [e for e in eintraege if e.get("installationsstatus") == "unbekannt"]

    bericht.append(f"Installiert: {len(installiert)}")
    bericht.append(f"Nicht installiert: {len(nicht_installiert)}")
    bericht.append(f"Unbekannt: {len(unbekannt)}")
    bericht.append("")

    standard = [e for e in eintraege if e.get("standardtool_ja_nein")]
    ersatz = [e for e in eintraege if e.get("ersatztool_ja_nein")]
    bericht.append(f"Standardtools: {len(standard)}")
    bericht.append(f"Ersatztools: {len(ersatz)}")
    bericht.append("")

    bericht.append("Tools mit Update-Verknuepfung:")
    for e in eintraege:
        if e.get("update_id"):
            bericht.append(f"  {e['tool_id']} -> {e['update_id']}")
    bericht.append("")

    bericht.append("Tools ohne Update-Verknuepfung:")
    for e in eintraege:
        if not e.get("update_id"):
            bericht.append(f"  {e['tool_id']}")
    bericht.append("")

    bericht.append("Nicht freigegebene Tools:")
    for e in eintraege:
        if not e.get("darf_verwendet_werden"):
            bericht.append(f"  {e['tool_id']} ({e.get('name')})")
    bericht.append("")

    bericht.append("=" * 70)
    bericht_text = "\n".join(bericht)

    bericht_path = REPORTS_DIR / "ALIN_CORE05_TOOLREGISTER_BERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(bericht_text)
    print(f"\nBericht geschrieben nach: {bericht_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
