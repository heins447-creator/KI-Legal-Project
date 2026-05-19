"""
CORE-22 – Check: Agenten-Einstieg und Arbeitsregel-Erzwingung
"""
import json
import os
import sys

def check():
    fehler = []
    warnungen = []

    # 1. Runner existiert
    if not os.path.exists("Scripts/python_runner/core22_agenten_einstieg.py"):
        fehler.append("Runner fehlt: Scripts/python_runner/core22_agenten_einstieg.py")

    # 2. Regeldatei existiert
    if not os.path.exists("ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json"):
        fehler.append("Regeldatei fehlt: CORE22_agenten_regeln.json")
    else:
        with open("ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json", "r", encoding="utf-8") as f:
            regeln = json.load(f)

        # Meta prüfen
        meta = regeln.get("meta", {})
        if meta.get("modul_id") != "CORE-22":
            fehler.append("meta.modul_id != CORE-22")
        if meta.get("nur_regelnd") != True:
            warnungen.append("meta.nur_regelnd != True")

        # Arbeitsregeln prüfen
        ar = regeln.get("arbeitsregeln", {})
        if not ar.get("vor_jedem_auftrag"):
            fehler.append("arbeitsregeln.vor_jedem_auftrag fehlt")
        sr = ar.get("schreibregeln", {})
        if not sr.get("erlaubt_in"):
            fehler.append("schreibregeln.erlaubt_in fehlt")
        if not sr.get("verboten_in"):
            fehler.append("schreibregeln.verboten_in fehlt")

        # Verbotene Operationen prüfen
        vb = regeln.get("verbotene_operationen", [])
        muster = ["Löschen", "Verschieben", "Umbenennen", "API-Schlüssel"]
        for m in muster:
            if not any(m in v for v in vb):
                warnungen.append(f"verbotene_operationen enthält kein '{m}'")

        # Entscheidungsbaum prüfen
        eb = regeln.get("entscheidungsbaum", {})
        if "pfad_ist_aktiv" not in eb:
            fehler.append("entscheidungsbaum.pfad_ist_aktiv fehlt")
        if "pfad_ist_gesperrt" not in eb:
            fehler.append("entscheidungsbaum.pfad_ist_gesperrt fehlt")

    # 3. Bericht existiert
    if not os.path.exists("ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt"):
        fehler.append("Bericht fehlt: CORE22_AGENTEN_EINSTIEG_BERICHT.txt")

    # 4. Dokumentation existiert
    if not os.path.exists("Projektplanung/CORE22_AGENTEN_EINSTIEG.md"):
        warnungen.append("Dokumentation fehlt: Projektplanung/CORE22_AGENTEN_EINSTIEG.md")

    # 5. Konfiguration existiert
    if not os.path.exists("Config/core22_agentenregeln_v1.json"):
        warnungen.append("Konfiguration fehlt: Config/core22_agentenregeln_v1.json")

    # 6. PowerShell-Starter existiert
    if not os.path.exists("Scripts/CORE22_AGENTEN_EINSTIEG_AUTOLAUF.ps1"):
        warnungen.append("PowerShell-Starter fehlt: Scripts/CORE22_AGENTEN_EINSTIEG_AUTOLAUF.ps1")

    # 7. CORE-21 Konfiguration referenziert
    if not os.path.exists("Config/core21_arbeitsindex_v1.json"):
        fehler.append("CORE-21 Konfiguration fehlt – CORE-22 kann nicht funktionieren")

    if fehler:
        print("[CHECK CORE-22] FEHLER:")
        for f in fehler:
            print(f"  - {f}")
    if warnungen:
        print("[CHECK CORE-22] WARNUNGEN:")
        for w in warnungen:
            print(f"  - {w}")

    if not fehler and not warnungen:
        print("[CHECK CORE-22] BESTANDEN – keine Fehler, keine Warnungen")
        return 0
    if not fehler:
        print("[CHECK CORE-22] BESTANDEN mit Warnungen")
        return 0
    print("[CHECK CORE-22] FEHLGESCHLAGEN")
    return 1

if __name__ == "__main__":
    sys.exit(check())
