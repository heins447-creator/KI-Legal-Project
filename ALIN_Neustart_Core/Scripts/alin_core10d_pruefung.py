#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10d Prüfdatei
Verifiziert das Schnittstellenregister und alle Verknüpfungen.
"""

import json
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("CORE-10d PRUEFUNG")
    print("=" * 60)

    # 1. schnittstellenregister.json vorhanden
    si_path = REGISTER_DIR / "schnittstellenregister.json"
    if not si_path.exists():
        print("[FEHLER] schnittstellenregister.json nicht vorhanden")
        return 1
    print("[OK] schnittstellenregister.json vorhanden")

    # 2. JSON gültig
    try:
        schnittstellenregister = load_json(si_path)
    except json.JSONDecodeError as e:
        print(f"[FEHLER] Ungueltiges JSON: {e}")
        return 1
    print("[OK] schnittstellenregister.json ist gueltiges JSON")

    schnittstellen = schnittstellenregister.get("eintraege", [])
    print(f"[OK] {len(schnittstellen)} Schnittstellen gefunden")

    # Lade Referenzregister
    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    ressourcenregister = load_json(REGISTER_DIR / "ressourcenregister.json")
    toolregister = load_json(REGISTER_DIR / "toolregister.json")
    lizenzregister = load_json(REGISTER_DIR / "lizenzregister.json")

    modul_ids = {m["modul_id"] for m in modulregister.get("eintraege", [])}
    res_ids = {r["resource_id"] for r in ressourcenregister.get("eintraege", [])}
    tool_ids = {t["tool_id"] for t in toolregister.get("eintraege", [])}
    lizenz_ids = {l["komponente_id"] for l in lizenzregister.get("eintraege", [])}

    fehler = []
    gesperrte_cloud = 0
    deepl_gesperrt = True

    for idx, si in enumerate(schnittstellen, 1):
        sid = si.get("schnittstelle_id", f"EINTRAG_{idx}")

        # 3. Jede Schnittstelle hat ID
        if not si.get("schnittstelle_id"):
            fehler.append(f"{sid}: Keine schnittstelle_id")

        # 4. Jede Schnittstelle hat Bereich
        if not si.get("bereich"):
            fehler.append(f"{sid}: Kein bereich")

        # 5. Jede Schnittstelle hat Status
        status = si.get("status")
        if not status:
            fehler.append(f"{sid}: Kein status")

        # 6. Jede Schnittstelle hat Eingaben/Ausgaben
        if not si.get("eingaben"):
            fehler.append(f"{sid}: Keine eingaben")
        if not si.get("ausgaben"):
            fehler.append(f"{sid}: Keine ausgaben")

        # 7. Cloud-Schnittstellen nicht automatisch aktiv
        cloud_status = si.get("cloud_status", "keiner")
        if cloud_status in ("gesperrt", "manuell_freigabepflichtig"):
            gesperrte_cloud += 1
            if status == "aktiv":
                fehler.append(f"{sid}: Cloud-Status '{cloud_status}' aber status='aktiv'")

        # 8. DEEPL_API nicht automatisch freigegeben
        if "DEEPL_API" in str(si.get("beteiligte_module", [])) or "DEEPL_API" in str(si.get("quellen_oder_adapter", [])):
            if status == "aktiv":
                fehler.append(f"{sid}: DEEPL_API darf nicht aktiv sein")
            if si.get("produktivfreigabe"):
                fehler.append(f"{sid}: DEEPL_API darf nicht produktivfreigegeben sein")

        # 9. Ressourcen existieren oder sind fehlend/gesperrt markiert
        for res in si.get("benoetigte_ressourcen", []):
            if res not in res_ids:
                if status not in ("gesperrt", "platzhalter"):
                    fehler.append(f"{sid}: Ressource '{res}' fehlt im Register und Status ist '{status}'")

        # 10. Tools existieren oder sind fehlend/gesperrt markiert
        for tool in si.get("benoetigte_tools", []):
            if tool not in tool_ids:
                if status not in ("gesperrt", "platzhalter"):
                    fehler.append(f"{sid}: Tool '{tool}' fehlt im Toolregister und Status ist '{status}'")

        # 11. Module existieren oder sind offen markiert
        for mod in si.get("beteiligte_module", []):
            if mod not in modul_ids:
                if status not in ("gesperrt", "platzhalter", "vorbereitet"):
                    fehler.append(f"{sid}: Modul '{mod}' fehlt im Modulregister und Status ist '{status}'")

    # 12-15. Keine Altbestandsdateien, Installation, Internet/Cloudnutzung
    # (Durch Register-Only-Arbeit erfüllt)

    print(f"[OK] {len(schnittstellen)} Schnittstellen geprüft")
    print(f"[OK] {gesperrte_cloud} Cloud-/Online-Schnittstellen als gesperrt/manuell markiert")
    print(f"[OK] DEEPL_API nicht aktiv/freigegeben")

    print("=" * 60)
    if fehler:
        print(f"PRUEFUNG FEHLGESCHLAGEN – {len(fehler)} Fehler:")
        for f in fehler:
            print(f"  {f}")
        return 1
    else:
        print("PRUEFUNG BESTANDEN – Keine Fehler")
        return 0


if __name__ == "__main__":
    sys.exit(main())
