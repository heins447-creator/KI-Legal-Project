#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10g: Reviewlisten dokumentieren
Identifiziert DB-ändernde, online-fähige und Installations-/Update-Module,
vergibt Risikoklassen und schreibt Reviewlisten als JSON und Bericht.
NUR lesend – keine Registeränderung, keine Modulausführung, keine DB-Änderung.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"
HEALTHCHECK_DIR = ROOT / "ALIN_Neustart_Core" / "04_Healthcheck"
REPORT_PATH = ROOT / "ALIN_Neustart_Core" / "Reports" / "ALIN_CORE10G_REVIEWLISTEN_BERICHT.txt"
REVIEW_JSON_PATH = HEALTHCHECK_DIR / "review_listen.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def determine_risk_class(m):
    """Vergeben einer Risikoklasse basierend auf Modul-Eigenschaften."""
    scores = []
    reasons = []

    # DB-Änderung
    if m.get("darf_datenbank_aendern", False):
        scores.append(2)
        reasons.append("darf_datenbank_aendern=true")

    # Online-Fähigkeit
    if m.get("darf_online_gehen", False):
        scores.append(3)
        reasons.append("darf_online_gehen=true")

    # Originaländerung
    if m.get("darf_originale_veraendern", False):
        scores.append(3)
        reasons.append("darf_originale_veraendern=true")

    # Rechtsbewertung (hohes Risiko)
    if m.get("darf_rechtsbewerten", False):
        scores.append(4)
        reasons.append("darf_rechtsbewerten=true")

    # Beweiswürdigung (sehr hohes Risiko)
    if m.get("darf_beweiswuerdigen", False):
        scores.append(5)
        reasons.append("darf_beweiswuerdigen=true")

    # Produktivfreigabe
    if m.get("produktivfreigabe", False):
        scores.append(1)
        reasons.append("produktivfreigabe=true")

    # Status gesperrt (Risiko-Reduktion)
    if m.get("status") == "gesperrt":
        scores.append(-2)
        reasons.append("status=gesperrt")

    # Status vorbereitet (Risiko-Reduktion)
    if m.get("status") == "vorbereitet":
        scores.append(-1)
        reasons.append("status=vorbereitet")

    total = sum(scores)

    if total >= 5:
        return "KRITISCH", reasons
    elif total >= 3:
        return "HOCH", reasons
    elif total >= 1:
        return "MITTEL", reasons
    else:
        return "NIEDRIG", reasons


def has_installation_update_reference(m):
    """Prüft ob Modul Installations-/Download-/Update-Bezug hat."""
    mid = m.get("modul_id", "").lower()
    name = m.get("modulname", "").lower()
    beschreibung = m.get("kurzbeschreibung", "").lower()
    combined = f"{mid} {name} {beschreibung}"

    keywords = [
        "install", "download", "update", "nachlad", "upgrade", "patch",
        "setup", "deploy", "verteil", "external_tools", "toolbibliothek",
        "installer", "hash", "versionspruef", "versionsvergleich"
    ]

    for kw in keywords:
        if kw in combined:
            return True, kw
    return False, None


def main():
    print("=" * 70)
    print("CORE-10g REVIEWLISTEN DOKUMENTIEREN")
    print("=" * 70)

    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    eintraege = modulregister.get("eintraege", [])

    # Listen
    db_aendernd = []
    online_faehig = []
    install_update = []
    rechtsbewertend = []
    beweiswuerdigend = []
    original_aendernd = []
    produktiv_freigegeben = []

    risk_classes = {"KRITISCH": [], "HOCH": [], "MITTEL": [], "NIEDRIG": []}

    for m in eintraege:
        mid = m.get("modul_id", "")
        record = {
            "modul_id": mid,
            "modulname": m.get("modulname", ""),
            "bereich": m.get("bereich", ""),
            "status": m.get("status", ""),
            "darf_datenbank_aendern": m.get("darf_datenbank_aendern", False),
            "darf_online_gehen": m.get("darf_online_gehen", False),
            "darf_originale_veraendern": m.get("darf_originale_veraendern", False),
            "darf_rechtsbewerten": m.get("darf_rechtsbewerten", False),
            "darf_beweiswuerdigen": m.get("darf_beweiswuerdigen", False),
            "produktivfreigabe": m.get("produktivfreigabe", False),
        }

        # DB-ändernd
        if record["darf_datenbank_aendern"]:
            db_aendernd.append(record)

        # Online-fähig
        if record["darf_online_gehen"]:
            online_faehig.append(record)

        # Installations-/Update-Bezug
        has_inst, kw = has_installation_update_reference(m)
        if has_inst:
            r = dict(record)
            r["erkennungs_keyword"] = kw
            install_update.append(r)

        # Rechtsbewertend
        if record["darf_rechtsbewerten"]:
            rechtsbewertend.append(record)

        # Beweiswürdigend
        if record["darf_beweiswuerdigen"]:
            beweiswuerdigend.append(record)

        # Original-ändernd
        if record["darf_originale_veraendern"]:
            original_aendernd.append(record)

        # Produktiv freigegeben
        if record["produktivfreigabe"]:
            produktiv_freigegeben.append(record)

        # Risikoklasse
        risk, reasons = determine_risk_class(m)
        r = dict(record)
        r["risikoklasse"] = risk
        r["risikogrund"] = reasons
        risk_classes[risk].append(r)

    # Review-Listen JSON
    review_listen = {
        "schema_version": "1.0.0",
        "erstellt": datetime.now(timezone.utc).isoformat(),
        "beschreibung": "CORE-10g Reviewlisten – Klassifizierung aller Module nach Risiko und Berechtigungen",
        "listen": {
            "db_aendernde_module": {
                "anzahl": len(db_aendernd),
                "beschreibung": "Module die die Datenbank aendern duerfen",
                "module": db_aendernd
            },
            "online_faehige_module": {
                "anzahl": len(online_faehig),
                "beschreibung": "Module die online gehen duerfen (Cloud/API/Internet)",
                "module": online_faehig
            },
            "installations_update_module": {
                "anzahl": len(install_update),
                "beschreibung": "Module mit Installations-, Download- oder Update-Bezug",
                "module": install_update
            },
            "rechtsbewertende_module": {
                "anzahl": len(rechtsbewertend),
                "beschreibung": "Module die Rechtsbewertungen durchfuehren duerfen",
                "module": rechtsbewertend
            },
            "beweiswuerdigende_module": {
                "anzahl": len(beweiswuerdigend),
                "beschreibung": "Module die Beweiswuerdigungen durchfuehren duerfen",
                "module": beweiswuerdigend
            },
            "original_aendernde_module": {
                "anzahl": len(original_aendernd),
                "beschreibung": "Module die Originaldateien aendern duerfen",
                "module": original_aendernd
            },
            "produktiv_freigegebene_module": {
                "anzahl": len(produktiv_freigegeben),
                "beschreibung": "Module mit Produktivfreigabe",
                "module": produktiv_freigegeben
            },
            "risikoklassen": {
                "KRITISCH": {
                    "anzahl": len(risk_classes["KRITISCH"]),
                    "beschreibung": "Kritische Module – mehrere Hochrisiko-Berechtigungen aktiviert",
                    "module": risk_classes["KRITISCH"]
                },
                "HOCH": {
                    "anzahl": len(risk_classes["HOCH"]),
                    "beschreibung": "Hohes Risiko – mindestens eine Hochrisiko-Berechtigung aktiviert",
                    "module": risk_classes["HOCH"]
                },
                "MITTEL": {
                    "anzahl": len(risk_classes["MITTEL"]),
                    "beschreibung": "Mittleres Risiko – produktiv oder kombinierte Berechtigungen",
                    "module": risk_classes["MITTEL"]
                },
                "NIEDRIG": {
                    "anzahl": len(risk_classes["NIEDRIG"]),
                    "beschreibung": "Niedriges Risiko – keine kritischen Berechtigungen",
                    "module": risk_classes["NIEDRIG"]
                }
            }
        }
    }

    save_json(REVIEW_JSON_PATH, review_listen)

    # Bericht
    report_lines = [
        "=" * 70,
        "CORE-10g REVIEWLISTEN BERICHT",
        "=" * 70,
        f"Erstellt: {datetime.now(timezone.utc).isoformat()}",
        f"Gesamt-Module im Register: {len(eintraege)}",
        "",
        "1. DB-ÄNDERNDE MODULE",
        "-" * 40,
        f"  Anzahl: {len(db_aendernd)}",
    ]
    for m in db_aendernd:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")

    report_lines.extend([
        "",
        "2. ONLINE-FÄHIGE MODULE",
        "-" * 40,
        f"  Anzahl: {len(online_faehig)}",
    ])
    for m in online_faehig:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")

    report_lines.extend([
        "",
        "3. INSTALLATIONS-/UPDATE-BEZOGENE MODULE",
        "-" * 40,
        f"  Anzahl: {len(install_update)}",
    ])
    for m in install_update:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] keyword={m['erkennungs_keyword']}")

    report_lines.extend([
        "",
        "4. RECHTSBEWERTENDE MODULE",
        "-" * 40,
        f"  Anzahl: {len(rechtsbewertend)}",
    ])
    for m in rechtsbewertend:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")

    report_lines.extend([
        "",
        "5. BEWEISWÜRDIGENDE MODULE",
        "-" * 40,
        f"  Anzahl: {len(beweiswuerdigend)}",
    ])
    for m in beweiswuerdigend:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")

    report_lines.extend([
        "",
        "6. ORIGINAL-ÄNDERNDE MODULE",
        "-" * 40,
        f"  Anzahl: {len(original_aendernd)}",
    ])
    for m in original_aendernd:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")

    report_lines.extend([
        "",
        "7. PRODUKTIV FREIGEGEBENE MODULE",
        "-" * 40,
        f"  Anzahl: {len(produktiv_freigegeben)}",
    ])
    for m in produktiv_freigegeben:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")

    report_lines.extend([
        "",
        "8. RISIKOKLASSEN-VERTEILUNG",
        "-" * 40,
        f"  KRITISCH:  {len(risk_classes['KRITISCH'])} Module",
        f"  HOCH:      {len(risk_classes['HOCH'])} Module",
        f"  MITTEL:    {len(risk_classes['MITTEL'])} Module",
        f"  NIEDRIG:   {len(risk_classes['NIEDRIG'])} Module",
        "",
        "9. KRITISCHE MODULE (Detail)",
        "-" * 40,
    ])
    for m in risk_classes["KRITISCH"]:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")
        report_lines.append(f"      Risikogrund: {', '.join(m['risikogrund'])}")

    report_lines.extend([
        "",
        "10. HOCHRISIKO-MODULE (Detail)",
        "-" * 40,
    ])
    for m in risk_classes["HOCH"]:
        report_lines.append(f"    - {m['modul_id']} [{m['bereich']}] status={m['status']}")
        report_lines.append(f"      Risikogrund: {', '.join(m['risikogrund'])}")

    report_lines.extend([
        "",
        "=" * 70,
        "ENDE BERICHT",
        "=" * 70,
    ])

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    print(f"\nReviewlisten-JSON geschrieben nach: {REVIEW_JSON_PATH}")
    print(f"Bericht geschrieben nach: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
