# -*- coding: utf-8 -*-
"""
CORE-21 Check-Datei
Prüft den Arbeitsindex, den Bericht und die Konfiguration.
"""

import json
import sys
from pathlib import Path

PROJEKT_ROOT = Path("I:/KI_Legal_Project")

ARBEITSINDEX_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_arbeitsindex.json"
BERICHT_PFAD = PROJEKT_ROOT / "ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt"
KONFIG_PFAD = PROJEKT_ROOT / "Config/core21_arbeitsindex_v1.json"

FEHLER = []
WARNUNG = []


def pruefe_datei_existiert(pfad: Path, name: str):
    if not pfad.exists():
        FEHLER.append(f"{name} fehlt: {pfad}")
        return False
    return True


def pruefe_json_valide(pfad: Path, name: str):
    if not pfad.exists():
        FEHLER.append(f"{name} fehlt: {pfad}")
        return None
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        FEHLER.append(f"{name} nicht valides JSON: {e}")
        return None


def pruefe_arbeitsindex(data: dict):
    if not isinstance(data, dict):
        FEHLER.append("Arbeitsindex ist kein dict")
        return

    # meta
    meta = data.get("meta")
    if not isinstance(meta, dict):
        FEHLER.append("meta fehlt oder ist kein dict")
        return

    if meta.get("modul_id") != "CORE-21":
        FEHLER.append(f"meta.modul_id erwartet 'CORE-21', ist '{meta.get('modul_id')}'")

    if not meta.get("version"):
        FEHLER.append("meta.version fehlt")

    if not meta.get("zeitstempel"):
        FEHLER.append("meta.zeitstempel fehlt")

    # zusammenfassung
    zus = data.get("zusammenfassung")
    if not isinstance(zus, dict):
        FEHLER.append("zusammenfassung fehlt")
    else:
        if zus.get("arbeitsbestand_anzahl") != 311:
            FEHLER.append(f"arbeitsbestand_anzahl muss 311 sein, ist {zus.get('arbeitsbestand_anzahl')}")
        if zus.get("referenzbestand_anzahl") != 311:
            FEHLER.append(f"referenzbestand_anzahl muss 311 sein, ist {zus.get('referenzbestand_anzahl')}")
        if zus.get("gesperrt_gesamt", 0) <= 0:
            WARNUNG.append("gesperrt_gesamt ist 0 oder fehlt")
        if zus.get("massgebliche_skripte", 0) <= 0:
            WARNUNG.append("massgebliche_skripte ist 0 oder fehlt")
        if zus.get("alte_bereiche", 0) <= 0:
            FEHLER.append("alte_bereiche fehlt oder ist 0")
        if zus.get("neue_bereiche", 0) <= 0:
            FEHLER.append("neue_bereiche fehlt oder ist 0")

    # empfohlener_start
    start = data.get("empfohlener_start")
    if not isinstance(start, dict):
        FEHLER.append("empfohlener_start fehlt")
    else:
        if not start.get("datei"):
            FEHLER.append("empfohlener_start.datei fehlt")
        if not start.get("alternativen") or not isinstance(start["alternativen"], list):
            FEHLER.append("empfohlener_start.alternativen fehlt oder ist keine Liste")

    # arbeitsbestand
    if not isinstance(data.get("arbeitsbestand"), list):
        FEHLER.append("arbeitsbestand fehlt oder ist keine Liste")
    elif len(data["arbeitsbestand"]) != 311:
        FEHLER.append(f"arbeitsbestand muss 311 Einträge haben, hat {len(data['arbeitsbestand'])}")

    # referenzbestand
    if not isinstance(data.get("referenzbestand"), list):
        FEHLER.append("referenzbestand fehlt oder ist keine Liste")
    elif len(data["referenzbestand"]) != 311:
        FEHLER.append(f"referenzbestand muss 311 Einträge haben, hat {len(data['referenzbestand'])}")

    # gesperrte_pfade
    gp = data.get("gesperrte_pfade")
    if not isinstance(gp, dict):
        FEHLER.append("gesperrte_pfade fehlt oder ist kein dict")
    else:
        erwartet = {"gesperrt", "manuell", "archiv", "dublette", "testrest", "laufzeit"}
        fehlende = erwartet - set(gp.keys())
        if fehlende:
            FEHLER.append(f"gesperrte_pfade fehlen Schlüssel: {fehlende}")

    # massgebliche_skripte
    if not isinstance(data.get("massgebliche_skripte"), list):
        FEHLER.append("massgebliche_skripte fehlt oder ist keine Liste")
    elif len(data["massgebliche_skripte"]) == 0:
        FEHLER.append("massgebliche_skripte ist leer")

    # alte_arbeitsbereiche
    if not isinstance(data.get("alte_arbeitsbereiche"), list) or len(data.get("alte_arbeitsbereiche", [])) == 0:
        FEHLER.append("alte_arbeitsbereiche fehlt oder ist leer")

    # neue_arbeitsbereiche
    if not isinstance(data.get("neue_arbeitsbereiche"), list) or len(data.get("neue_arbeitsbereiche", [])) == 0:
        FEHLER.append("neue_arbeitsbereiche fehlt oder ist leer")


def pruefe_konfig(data: dict):
    if not isinstance(data, dict):
        FEHLER.append("Konfiguration ist kein dict")
        return

    if data.get("modul_id") != "CORE-21":
        FEHLER.append(f"Konfig modul_id erwartet 'CORE-21', ist '{data.get('modul_id')}'")

    am = data.get("arbeitsmodus")
    if not isinstance(am, dict):
        FEHLER.append("Konfig arbeitsmodus fehlt")
    else:
        if not am.get("empfohlener_start"):
            FEHLER.append("Konfig arbeitsmodus.empfohlener_start fehlt")
        alts = am.get("erste_lese_dateien")
        if not isinstance(alts, list) or len(alts) == 0:
            FEHLER.append("Konfig arbeitsmodus.erste_lese_dateien fehlt oder ist leer")

    bereiche = data.get("bereiche")
    if not isinstance(bereiche, dict):
        FEHLER.append("Konfig bereiche fehlt")
    else:
        for k in ("aktiv", "referenz", "gesperrt"):
            if not isinstance(bereiche.get(k), list):
                FEHLER.append(f"Konfig bereiche.{k} fehlt oder ist keine Liste")

    pr = data.get("pruefregeln")
    if not isinstance(pr, dict):
        FEHLER.append("Konfig pruefregeln fehlt")
    else:
        if pr.get("manifest_anzahl") != 311:
            FEHLER.append(f"Konfig pruefregeln.manifest_anzahl muss 311 sein")


def pruefe_bericht():
    if not BERICHT_PFAD.exists():
        FEHLER.append(f"Bericht fehlt: {BERICHT_PFAD}")
        return
    try:
        with open(BERICHT_PFAD, "r", encoding="utf-8") as f:
            inhalt = f.read()
    except Exception as e:
        FEHLER.append(f"Bericht nicht lesbar: {e}")
        return

    if "CORE-21 ARBEITSINDEX-BERICHT" not in inhalt:
        FEHLER.append("Bericht enthält nicht den erwarteten Titel")
    if "ENDE CORE-21 ARBEITSINDEX-BERICHT" not in inhalt:
        FEHLER.append("Bericht enthält nicht das erwartete Ende")
    if "BESTANDEN" not in inhalt:
        WARNUNG.append("Bericht zeigt nicht BESTANDEN (wird erst nach erfolgreichem Lauf gesetzt)")


def main():
    print("[CHECK CORE-21] Prüfung wird gestartet ...")

    ai = pruefe_json_valide(ARBEITSINDEX_PFAD, "Arbeitsindex")
    if ai is not None:
        pruefe_arbeitsindex(ai)
        print("  -> Arbeitsindex JSON valide")
    else:
        print("  -> Arbeitsindex JSON FEHLER")

    konfig = pruefe_json_valide(KONFIG_PFAD, "Konfiguration")
    if konfig is not None:
        pruefe_konfig(konfig)
        print("  -> Konfiguration JSON valide")
    else:
        print("  -> Konfiguration JSON FEHLER")

    pruefe_bericht()
    if BERICHT_PFAD.exists():
        print("  -> Bericht vorhanden")
    else:
        print("  -> Bericht FEHLER (noch nicht erstellt)")

    print("")
    if WARNUNG:
        print("WARNUNGEN:")
        for w in WARNUNG:
            print(f"  [WARN] {w}")

    if FEHLER:
        print("FEHLER:")
        for f in FEHLER:
            print(f"  [FEHL] {f}")
        print(f"\n[CHECK CORE-21] NICHT BESTANDEN – {len(FEHLER)} Fehler, {len(WARNUNG)} Warnungen")
        sys.exit(1)
    else:
        if WARNUNG:
            print(f"\n[CHECK CORE-21] BESTANDEN mit {len(WARNUNG)} Warnung(en)")
        else:
            print("\n[CHECK CORE-21] BESTANDEN - keine Fehler, keine Warnungen")
        sys.exit(0)


if __name__ == "__main__":
    main()
