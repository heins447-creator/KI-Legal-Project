"""
CORE-28: Rechte und Rollen
Validiert Rollenmodell, Berechtigungs-Schema und Freigaberegeln.
"""
import json
import os
import sys
from datetime import datetime, timezone

CONFIG_PATH = "Config/core28_rechte_rollen_v1.json"
BERICHT_PFAD = "ALIN_Neustart_Core/Reports/CORE28_RECHTE_ROLLEN_BERICHT.txt"
QUELLEN = {
    "rollenmodell": "ALIN_Neustart_Core/02_Module_Aktiv/CORE28_Rechte_Rollen/ROLLENMODELL.md",
    "freigaberegeln": "ALIN_Neustart_Core/02_Module_Aktiv/CORE28_Rechte_Rollen/FREIGABEREGELN.md",
    "berechtigungen": "ALIN_Neustart_Core/02_Module_Aktiv/CORE28_Rechte_Rollen/BERECHTIGUNGEN.schema.json",
}


def lade_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def pruefe_datei_existenz(pfade):
    ergebnisse = {}
    for name, pfad in pfade.items():
        ergebnisse[name] = os.path.exists(pfad)
    return ergebnisse


def pruefe_rollenmodell(pfad, config):
    fehler = []
    with open(pfad, "r", encoding="utf-8") as f:
        inhalt = f.read()

    pflicht = config["validierung"]["rollenmodell_pflichtfelder"]
    for feld in pflicht:
        if feld not in inhalt:
            fehler.append(f"ROLLENMODELL.md fehlt: {feld}")

    # Prüfe erlaubte Rollen
    erlaubte_rollen = config["validierung"]["erlaubte_rollen"]
    for rolle in erlaubte_rollen:
        if rolle not in inhalt:
            fehler.append(f"Rolle fehlt im Rollenmodell: {rolle}")

    return fehler


def pruefe_freigaberegeln(pfad, config):
    fehler = []
    with open(pfad, "r", encoding="utf-8") as f:
        inhalt = f.read()

    pflicht = config["validierung"]["freigaberegeln_pflichtabschnitte"]
    for abschnitt in pflicht:
        if abschnitt not in inhalt:
            fehler.append(f"FREIGABEREGELN.md fehlt Abschnitt: {abschnitt}")

    return fehler


def pruefe_berechtigungen_schema(pfad, config):
    fehler = []
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        return [f"BERECHTIGUNGEN.schema.json ist kein gültiges JSON: {e}"]

    required = config["validierung"]["berechtigungen_schema_required"]
    props = schema.get("properties", {})
    for feld in required:
        if feld not in props:
            fehler.append(f"Schema fehlt Property: {feld}")

    # Prüfe Rollen-Enum
    rolle_prop = props.get("rolle", {})
    enum_rollen = rolle_prop.get("enum", [])
    erlaubte = config["validierung"]["erlaubte_rollen"]
    for rolle in erlaubte:
        if rolle not in enum_rollen:
            fehler.append(f"Schema-Enum fehlt Rolle: {rolle}")

    return fehler


def schreibe_bericht(ergebnisse, fehler_pro_datei):
    zeit = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    lines = [
        "============================================",
        "CORE-28 BERICHT: Rechte und Rollen",
        "============================================",
        f"Zeitstempel: {zeit}",
        "",
        "1. DATEI-EXISTENZ",
        "-----------------",
    ]
    for name, existiert in ergebnisse.items():
        status = "OK" if existiert else "FEHLT"
        lines.append(f"  {name}: {status}")

    lines.append("")
    lines.append("2. VALIDIERUNG")
    lines.append("--------------")

    total_fehler = 0
    for name, fehler in fehler_pro_datei.items():
        lines.append(f"\n  {name}:")
        if fehler:
            for f in fehler:
                lines.append(f"    FEHLER: {f}")
                total_fehler += 1
        else:
            lines.append("    OK")

    lines.append("")
    lines.append("3. ZUSAMMENFASSUNG")
    lines.append("------------------")
    lines.append(f"  Gesamtfehler: {total_fehler}")
    lines.append(f"  Status: {'ERFOLG' if total_fehler == 0 else 'FEHLER'}")
    lines.append("")
    lines.append("============================================")
    lines.append("ENDE CORE-28 BERICHT")
    lines.append("============================================")

    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return total_fehler == 0


def main():
    config = lade_config()
    ergebnisse = pruefe_datei_existenz(QUELLEN)

    fehler_pro_datei = {}
    if ergebnisse["rollenmodell"]:
        fehler_pro_datei["rollenmodell"] = pruefe_rollenmodell(QUELLEN["rollenmodell"], config)
    else:
        fehler_pro_datei["rollenmodell"] = ["Datei nicht gefunden"]

    if ergebnisse["freigaberegeln"]:
        fehler_pro_datei["freigaberegeln"] = pruefe_freigaberegeln(QUELLEN["freigaberegeln"], config)
    else:
        fehler_pro_datei["freigaberegeln"] = ["Datei nicht gefunden"]

    if ergebnisse["berechtigungen"]:
        fehler_pro_datei["berechtigungen"] = pruefe_berechtigungen_schema(QUELLEN["berechtigungen"], config)
    else:
        fehler_pro_datei["berechtigungen"] = ["Datei nicht gefunden"]

    erfolg = schreibe_bericht(ergebnisse, fehler_pro_datei)
    if erfolg:
        print("CORE-28: ERFOLG – alle Validierungen bestanden.")
        return 0
    else:
        print("CORE-28: FEHLER – Validierungsfehler gefunden.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
