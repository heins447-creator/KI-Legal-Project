#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI07 – Check-Datei: Betriebsvorbereitung ohne Produktivfreigabe
Prüft: Config, Verzeichnisse, Register, Sperrregister, Healthcheck, Demo-Modus, Ausgabedateien
"""

import json, os, sys

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def t(bez, bed):
    global FEHLER
    if not bed:
        FEHLER += 1
        print(f"  [FAIL] {bez}")
    else:
        print(f"  [OK]   {bez}")

def main():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI07 BETRIEBSVORBEREITUNG – CHECK")
    print("=" * 60)

    # 1. Config
    print("\n[1] Config-Prüfung")
    cfg = load_json("Config/ui07_betriebsvorbereitung_v1.json")
    t("modul_id == UI07", cfg.get("modul_id") == "UI07")
    t("betriebsmodus == vorbereitung", cfg.get("betriebsmodus") == "vorbereitung")
    t("produktiv_freigegeben == False", cfg.get("produktiv_freigegeben") is False)
    t("warnung_roter_rahmen vorhanden", len(cfg.get("warnung_roter_rahmen", "")) > 10)
    t("version_status == vorbereitung", cfg.get("version_status") == "vorbereitung")

    # 2. Verzeichnisse
    print("\n[2] Verzeichnisstruktur")
    verz = cfg.get("verzeichnisse", {})
    t("logs definiert", "logs" in verz)
    t("daten definiert", "daten" in verz)
    t("backup definiert", "backup" in verz)
    t("temp definiert", "temp" in verz)
    t("pruefseiten definiert", "pruefseiten" in verz)

    # 3. Register-Prüfung
    print("\n[3] Register-Prüfung")
    reg = cfg.get("register_pruefung", {})
    t("register_pfad gesetzt", len(reg.get("pfad", "")) > 0)
    erf = reg.get("erforderlich", [])
    t("modulregister erforderlich", "modulregister.json" in erf)
    t("sperrregister erforderlich", "sperrregister.json" in erf)
    t("toolregister erforderlich", "toolregister.json" in erf)
    t("ressourcenregister erforderlich", "ressourcenregister.json" in erf)
    t("skillregister erforderlich", "skillregister.json" in erf)
    t("lizenzregister erforderlich", "lizenzregister.json" in erf)

    # 4. Sperrregister
    print("\n[4] Sperrregister-Prüfung")
    sperr = cfg.get("sperrregister_pruefung", {})
    t("sperrregister aktiv", sperr.get("aktiv") is True)
    t("sperrregister pfad gesetzt", len(sperr.get("pfad", "")) > 0)
    t("kritische_eintraege_blockieren_start", sperr.get("kritische_eintraege_blockieren_start") is True)

    # 5. Healthcheck
    print("\n[5] Healthcheck-Konfiguration")
    hc = cfg.get("healthcheck", {})
    t("healthcheck register definiert", len(hc.get("pruefe_register", [])) > 0)
    t("healthcheck schnittstellen definiert", len(hc.get("pruefe_schnittstellen", [])) > 0)
    t("healthcheck statusmodelle definiert", len(hc.get("pruefe_statusmodelle", [])) > 0)

    # 6. Demo-Modus
    print("\n[6] Demo-Modus")
    demo = cfg.get("demo_modus", {})
    t("nur_musterdaten == True", demo.get("nur_musterdaten") is True)
    t("echte_daten_erlaubt == False", demo.get("echte_daten_erlaubt") is False)
    t("max_dokumente begrenzt", demo.get("max_dokumente", 999) < 10)
    t("wasserzeichen gesetzt", len(demo.get("wasserzeichen", "")) > 0)

    # 7. Backup
    print("\n[7] Backup-Hinweis")
    backup = cfg.get("backup", {})
    t("backup_hinweis_aktiv", backup.get("hinweis_aktiv") is True)
    t("backup_verzeichnis gesetzt", len(backup.get("backup_verzeichnis", "")) > 0)

    # 8. Startseite
    print("\n[8] Startseite")
    start = cfg.get("startseite", {})
    t("startseite titel gesetzt", len(start.get("titel", "")) > 0)
    t("startseite untertitel gesetzt", len(start.get("untertitel", "")) > 0)
    t("anzeige_module definiert", len(start.get("anzeige_module", [])) > 0)

    # 9. Ausgabe
    print("\n[9] Ausgabekonfiguration")
    aus = cfg.get("ausgabe", {})
    t("html_pruefstartseite definiert", "html_pruefstartseite" in aus)
    t("json_status definiert", "json_status" in aus)
    t("bericht definiert", "bericht" in aus)

    # 10. Python-Runner
    print("\n[10] Python-Runner")
    runner_pfad = "Scripts/python_runner/ui07_betriebsvorbereitung.py"
    t("runner existiert", os.path.isfile(runner_pfad))
    if os.path.isfile(runner_pfad):
        with open(runner_pfad, "r", encoding="utf-8") as f:
            rc = f.read()
        t("runner hat hauptlauf", "def hauptlauf():" in rc)
        t("runner hat selbsttest", "def selbsttest():" in rc)
        t("runner prueft verzeichnisse", "pruefe_verzeichnisse" in rc)
        t("runner prueft register", "pruefe_register" in rc)
        t("runner prueft sperrregister", "pruefe_sperrregister" in rc)
        t("runner erzeugt html", "generiere_html" in rc)
        t("runner erzeugt json", "generiere_status_json" in rc)
        t("runner erzeugt bericht", "schreibe_bericht" in rc)
        t("roter rahmen im html", "roter-rahmen" in rc)
        t("warnung im html", "warnung_roter_rahmen" in rc)

    # 11. Grenzen
    print("\n[11] Grenzen")
    grenzen = cfg.get("grenzen", {})
    t("max_dateigroesse definiert", grenzen.get("max_dateigroesse_mb", 0) > 0)
    t("max_dokumente_pro_lauf definiert", grenzen.get("max_dokumente_pro_lauf", 0) > 0)
    t("timeout definiert", grenzen.get("timeout_sekunden", 0) > 0)

    print("\n" + "=" * 60)
    print(f"ERGEBNIS: {'OK' if FEHLER == 0 else 'FEHLER'} ({FEHLER} Fehler, {WARNUNGEN} Warnungen)")
    print("=" * 60)
    return FEHLER == 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
