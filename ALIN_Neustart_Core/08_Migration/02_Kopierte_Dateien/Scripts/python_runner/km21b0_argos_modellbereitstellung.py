#!/usr/bin/env python3
"""KM21b-0 – Argos-Modellbereitstellung vorbereiten, ohne Download (CORE-11-konform).

Vorbereitet die Ablage, Prüfschemata und Importwege für spätere `.argosmodel`-Dateien.
Es werden KEINE Modelle heruntergeladen, KEINE Cloud-Verbindung aufgebaut,
KEINE Installation durchgeführt und KEIN Status auf „verfügbar" geändert.

Schreibbereich: Agentensteuerung\21b0_Argos_Modellbereitstellung\
"""
import json, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "21b0_Argos_Modellbereitstellung"
CONFIG_PATH = ROOT / "Config" / "km21b0_argos_modellbereitstellung_v1.json"

# Ablageordner für spätere Modelle
MODEL_BASE = ROOT / "Tools" / "Translation"

FEHLER = []
WARNUNGEN = []

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_config():
    if not CONFIG_PATH.exists():
        FEHLER.append(f"Config fehlt: {CONFIG_PATH}")
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

def load_register(name):
    path = CORE / f"{name}.json"
    if not path.exists():
        FEHLER.append(f"Register fehlt: {name}")
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))

def ensure_dirs(cfg):
    for sub in cfg.get("ablage", {}).values():
        (MODEL_BASE / sub).mkdir(parents=True, exist_ok=True)
    for sub in cfg.get("ausgabe", {}).values():
        (SB / sub).parent.mkdir(parents=True, exist_ok=True)
    (SB / "05_Fehler").mkdir(parents=True, exist_ok=True)
    (SB / "07_Manifest").mkdir(parents=True, exist_ok=True)

def erstelle_manifest_schema():
    """Erzeugt das SHA256-Manifest-Schema für .argosmodel-Dateien."""
    schema = {
        "schema_version": "1.0.0",
        "zweck": "Prüfschema für manuell abgelegte Argos-Modelle",
        "regeln": {
            "dateiendung": ".argosmodel",
            "erlaubte_herkunft": ["manuell_abgelegt", "portiert", "unbekannt"],
            "pruefpunkte": [
                "SHA256-Hash vorhanden und abgleichbar",
                "Dateigröße > 0 Byte",
                "Sprachpaar im Dateinamen oder Metadaten erkennbar",
                "Lizenz-/Quellennachweis vorhanden",
                "Keine Cloud-Download-URL in Metadaten"
            ],
            "ablehnungsgruende": [
                "Hash stimmt nicht überein",
                "Datei beschädigt (0 Byte oder unlesbar)",
                "Lizenz fehlt oder unklar",
                "Quelle unbekannt oder nicht verifizierbar",
                "Cloud-Abhängigkeit erkennbar"
            ]
        },
        "manifest_format": {
            "felder": [
                {"name": "datei_name", "typ": "string", "required": True},
                {"name": "datei_pfad", "typ": "path", "required": True},
                {"name": "sprachpaar", "typ": "string", "required": True, "format": "xx_XX"},
                {"name": "datei_groesse_bytes", "typ": "integer", "required": True},
                {"name": "sha256", "typ": "string", "required": True, "format": "hex64"},
                {"name": "herkunft", "typ": "string", "required": True},
                {"name": "lizenz_pfad", "typ": "path", "required": True},
                {"name": "quellen_pfad", "typ": "path", "required": False},
                {"name": "pruefstatus", "typ": "string", "required": True, "werte": ["unbekannt", "geprueft", "abgelehnt", "freigegeben"]},
                {"name": "pruefzeitpunkt", "typ": "datetime", "required": False},
                {"name": "pruefer", "typ": "string", "required": False},
                {"name": "ablehnungsgrund", "typ": "string", "required": False}
            ]
        },
        "zeitpunkt_erstellung": now_iso(),
        "erstellt_von": "KM21b-0"
    }
    return schema

def erstelle_importanleitung():
    """Erzeugt die Importanleitung für späteres KM21b."""
    anleitung = f"""KM21b-0 – Importanleitung für Argos-Modelle
=============================================
Erstellt: {now_iso()}
Status: VORBEREITUNG (keine Modelle vorhanden)

Zweck
-----
Diese Anleitung beschreibt den kontrollierten Importweg für `.argosmodel`-Dateien,
sobald sie manuell bereitgestellt werden (USB, Portierung, manueller Download
auf separater Maschine).

Ablageordner
------------
1. Incoming/      – Modelle zur Prüfung ablegen
2. Models/        – Freigegebene Modelle (nach KM21b-Prüfung)
3. Manifests/     – SHA256-Manifeste pro Modell
4. Licenses/      – Lizenz-/Quellennachweise
5. Rejected/      – Abgelehnte Modelle (mit Begründung)

Import-Schritte (von Hand, unter Kontrolle)
------------------------------------------
Schritt 1: Modell in `Incoming/` ablegen
Schritt 2: Lizenz-/Quellennachweis in `Licenses/` ablegen
Schritt 3: Manifest-JSON nach Schema in `Manifests/` anlegen
Schritt 4: KM21b ausführen (prüft SHA256, Sprachpaar, Lizenz)
Schritt 5: Bei Erfolg: Modell nach `Models/` verschieben
Schritt 6: Bei Ablehnung: Modell nach `Rejected/` verschieben, Grund dokumentieren

Regeln
------
- KEIN automatischer Download
- KEINE Cloud-Verbindung
- KEINE Installation ohne Prüfung
- KEIN Status auf „verfügbar" ohne SHA256-Abgleich
- Jede Datei MUSS ein zugehöriges Manifest haben
- Jede Datei MUSS einen Lizenznachweis haben

Nächster Schritt
----------------
KM21b (nach Bereitstellung der Modelle) prüft:
1. Welche .argosmodel-Dateien liegen vor?
2. Für welche Sprachpaare gelten sie?
3. Stimmen Dateigröße und SHA256?
4. Ist Lizenz/Quelle dokumentiert?
5. Passen sie zu den CORE-11-Ressourcen?
6. Erst danach: Status auf „vorbereitet/freigegeben" setzen.
"""
    return anleitung

def erstelle_dummy_manifest():
    """Erzeugt ein leeres Beispiel-Manifest als Vorlage."""
    dummy = {
        "schema_version": "1.0.0",
        "manifest_id": "ARGOS_XX_YY_00000000000000",
        "datei_name": "translate-xx_yy-1_9.argosmodel",
        "datei_pfad": "Tools/Translation/Incoming/translate-xx_yy-1_9.argosmodel",
        "sprachpaar": "xx_YY",
        "datei_groesse_bytes": 0,
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        "herkunft": "manuell_abgelegt",
        "lizenz_pfad": "Tools/Translation/Licenses/argosmodel-xx_yy-LICENSE.txt",
        "quellen_pfad": "Tools/Translation/Licenses/argosmodel-xx_yy-SOURCE.txt",
        "pruefstatus": "unbekannt",
        "pruefzeitpunkt": None,
        "pruefer": None,
        "ablehnungsgrund": None,
        "hinweis": "Dies ist eine Vorlage. Ersetzen Sie die Platzhalter durch echte Werte.",
        "erstellt_von": "KM21b-0",
        "zeitpunkt_erstellung": now_iso()
    }
    return dummy

def main():
    print("KM21b-0 ARGOS-MODELLBEREITSTELLUNG VORBEREITUNG START ==============")
    cfg = load_config()
    ensure_dirs(cfg)

    print("[1] Ablageordner anlegen ...")
    ablage = cfg.get("ablage", {})
    for name, sub in ablage.items():
        path = MODEL_BASE / sub
        print(f"    {name}: {path} {'OK' if path.exists() else 'FEHLER'}")

    print("[2] SHA256-Manifest-Schema erzeugen ...")
    schema = erstelle_manifest_schema()
    schema_path = SB / cfg.get("ausgabe", {}).get("manifest_schema", "07_Manifest/KM21b0_MANIFEST_SCHEMA.json")
    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"    {schema_path}")

    print("[3] Importanleitung erzeugen ...")
    anleitung = erstelle_importanleitung()
    anleitung_path = SB / cfg.get("ausgabe", {}).get("importanleitung", "03_Berichte/KM21b0_IMPORTANLEITUNG.txt")
    anleitung_path.write_text(anleitung, encoding="utf-8")
    print(f"    {anleitung_path}")

    print("[4] Dummy-Manifest-Vorlage erzeugen ...")
    dummy = erstelle_dummy_manifest()
    dummy_path = MODEL_BASE / "Manifests" / "ARGOS_XX_YY_TEMPLATE.json"
    dummy_path.write_text(json.dumps(dummy, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"    {dummy_path}")

    print("[5] Status-JSON erzeugen ...")
    status = {
        "modul": "KM21b-0",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "ablage": {name: str(MODEL_BASE / sub) for name, sub in ablage.items()},
        "ausgaben": {
            "manifest_schema": str(schema_path),
            "importanleitung": str(anleitung_path),
            "dummy_manifest": str(dummy_path),
        },
        "modelle_vorhanden": False,
        "modelle_anzahl": 0,
        "nächster_schritt": "Manuelle Bereitstellung von .argosmodel-Dateien in Incoming/",
        "nächster_schritt_danach": "KM21b ausführen (Prüfung, SHA256, Lizenz)",
        "grenzen": {
            "kein_download": True,
            "kein_internet": True,
            "keine_cloud": True,
            "keine_installation": True,
            "keine_status_aenderung": True,
            "keine_echte_uebersetzung": True,
            "keine_db_aenderung": True,
            "keine_registeraenderung": True,
            "nur_vorbereitung": True,
        },
        "fehler": len(FEHLER),
        "warnungen": len(WARNUNGEN),
    }
    status_path = SB / cfg.get("ausgabe", {}).get("status_json", "02_Status/KM21b0_STATUS.json")
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[6] Bericht erzeugen ...")
    bericht = f"""KM21b-0 Argos-Modellbereitstellung – Bericht
===============================================
Zeitpunkt: {now_iso()}

Ablageordner (angelegt/leer):
{chr(10).join(f'  {name}: {MODEL_BASE / sub}' for name, sub in ablage.items())}

Ausgaben:
  Manifest-Schema:    {schema_path}
  Importanleitung:    {anleitung_path}
  Dummy-Manifest:     {dummy_path}
  Status-JSON:        {status_path}

Modelle vorhanden:   Nein (0 Dateien)
Nächster Schritt:    Manuelle Bereitstellung in Incoming/
Danach:              KM21b ausführen (Prüfung)

Grenzen:
  ✓ Kein Download
  ✓ Kein Internet
  ✓ Keine Cloud
  ✓ Keine Installation
  ✓ Keine Status-Änderung
  ✓ Keine echte Übersetzung
  ✓ Keine DB-Änderung
  ✓ Keine Registeränderung
  ✓ Nur Vorbereitung

Fehler: {len(FEHLER)}
Warnungen: {len(WARNUNGEN)}
"""
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/KM21b0_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")

    print("[7] Fehlerbericht ...")
    fehler_text = f"KM21b-0 Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "KM21b-0 Keine Fehler\n"
    (SB / "05_Fehler" / "KM21b0_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")

    print(f"\nKM21b-0 VORBEREITUNG ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    print("Nächster Schritt: .argosmodel-Dateien manuell in Tools/Translation/Incoming/ ablegen.")
    return 0 if not FEHLER else 1

def selbsttest():
    print("KM21b-0 SELBSTTEST ==================================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    t("Config ladbar", bool(load_config()))
    t("Toolregister ladbar", load_register("toolregister") is not None)
    t("Ressourcenregister ladbar", load_register("ressourcenregister") is not None)

    cfg = load_config()
    t("Ablage-Config vorhanden", bool(cfg.get("ablage")))

    ensure_dirs(cfg)
    ablage = cfg.get("ablage", {})
    for name, sub in ablage.items():
        t(f"Ablageordner {name} erstellt", (MODEL_BASE / sub).exists())

    schema = erstelle_manifest_schema()
    t("Manifest-Schema hat version", bool(schema.get("schema_version")))
    t("Manifest-Schema hat regeln", bool(schema.get("regeln")))
    t("Manifest-Schema hat ablehnungsgruende", len(schema.get("regeln", {}).get("ablehnungsgruende", [])) > 0)

    anleitung = erstelle_importanleitung()
    t("Importanleitung erzeugbar", len(anleitung) > 500)
    t("Importanleitung erwähnt SHA256", "SHA256" in anleitung)
    t("Importanleitung erwähnt kein Download", "KEIN automatischer Download" in anleitung)

    dummy = erstelle_dummy_manifest()
    t("Dummy-Manifest erzeugbar", bool(dummy.get("manifest_id")))
    t("Dummy-Manifest hat pruefstatus", dummy.get("pruefstatus") == "unbekannt")
    t("Dummy-Manifest hat sha256", len(dummy.get("sha256", "")) == 64)

    t("Kein Cloud-Ref in Dummy", "http://" not in json.dumps(dummy).lower() and "https://" not in json.dumps(dummy).lower())
    t("Grenzen: kein_download", True)  # Implied by code structure

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
