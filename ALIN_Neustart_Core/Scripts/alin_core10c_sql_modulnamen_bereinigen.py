#!/usr/bin/env python3
"""
CORE-10c – SQL-Modulnamen bereinigen
====================================
Auftrag:  20 Module im modulregister.json haben SQL-Code als modulname.
          Diese werden auf den Dateinamen (ohne Pfad/Endung) korrigiert.
Harte Grenzen (AGENTS.md):
  - Nur ALIN_Neustart_Core aendern
  - Keine Ressourcen ergaenzen
  - Keine Schnittstellen bauen
  - Keine Abhaengigkeiten reparieren
  - Keine Altbestandsdateien aendern
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REGISTER_PFAD = Path("ALIN_Neustart_Core/01_Register/modulregister.json")
BERICHT_PFAD = Path("ALIN_Neustart_Core/Reports/ALIN_CORE10C_SQL_MODULNAMEN_BERICHT.txt")

# Mapping: modul_id -> korrekter modulname (aus dem Dateinamen abgeleitet)
KORREKTUREN = {
    "001_db_schema_audit": "001_db_schema_audit",
    "002_apply_posteingang_schema": "002_apply_posteingang_schema",
    "003_verify_posteingang_schema": "003_verify_posteingang_schema",
    "012_posteingang_sprachkontext_gate_v2": "012_posteingang_sprachkontext_gate_v2",
    "013_kontrolle_posteingang_nach_bereinigung": "013_kontrolle_posteingang_nach_bereinigung",
    "013_posteingang_db_altlasten_cleanup": "013_posteingang_db_altlasten_cleanup",
    "014_posteingang_clean_verify": "014_posteingang_clean_verify",
    "020_posteingang_gesamtstatus_v1": "020_posteingang_gesamtstatus_v1",
    "021_posteingang_db_dateien_auswahl_testlauf_v1": "021_posteingang_db_dateien_auswahl_testlauf_v1",
    "025_schweden_arbeitsrecht_sprachkontext_korrektur_v1": "025_schweden_arbeitsrecht_sprachkontext_korrektur_v1",
    "032_check_dokumentsprachprofil_v1": "032_check_dokumentsprachprofil_v1",
    "033_posteingang_schlusskontrolle_v2": "033_posteingang_schlusskontrolle_v2",
    "034_posteingang_endabnahme_v2": "034_posteingang_endabnahme_v2",
    "036_check_vorzimmer_kommunikationsparameter_v1": "036_check_vorzimmer_kommunikationsparameter_v1",
    "037_posteingang_endabnahme_v3": "037_posteingang_endabnahme_v3",
    "039_check_anwaltvorlage_grundmodul_v1": "039_check_anwaltvorlage_grundmodul_v1",
    "041_check_agentenbearbeitung_grundmodul_v1": "041_check_agentenbearbeitung_grundmodul_v1",
    "043_check_agent_dokumentart_erkennen_v1": "043_check_agent_dokumentart_erkennen_v1",
    "045_check_agent_sprache_uebersetzung_v1": "045_check_agent_sprache_uebersetzung_v1",
    "047_check_agent_sachverhaltsbezug_v1": "047_check_agent_sachverhaltsbezug_v1",
}

def main():
    print("CORE-10c – SQL-Modulnamen bereinigen")
    print("=" * 60)

    if not REGISTER_PFAD.exists():
        print(f"FEHLER: {REGISTER_PFAD} nicht gefunden")
        return 1

    with open(REGISTER_PFAD, "r", encoding="utf-8") as f:
        data = json.load(f)

    aenderungen = []
    for entry in data["eintraege"]:
        modul_id = entry.get("modul_id", "")
        if modul_id in KORREKTUREN:
            alter_name = entry["modulname"]
            neuer_name = KORREKTUREN[modul_id]
            if alter_name != neuer_name:
                entry["modulname"] = neuer_name
                aenderungen.append({
                    "modul_id": modul_id,
                    "alt": alter_name,
                    "neu": neuer_name,
                })

    if not aenderungen:
        print("Keine Aenderungen erforderlich – alle Modulnamen sind korrekt.")
        return 0

    # Register zurueckschreiben
    with open(REGISTER_PFAD, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Bericht erstellen
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bericht = []
    bericht.append("=" * 60)
    bericht.append("CORE-10c SQL-MODULNAMEN BEREINIGUNG")
    bericht.append(f"Erstellt: {timestamp}")
    bericht.append("=" * 60)
    bericht.append("")
    bericht.append(f"Anzahl korrigierter Module: {len(aenderungen)}")
    bericht.append("")
    for a in aenderungen:
        bericht.append(f"  {a['modul_id']}")
        bericht.append(f"    ALT: {a['alt']}")
        bericht.append(f"    NEU: {a['neu']}")
        bericht.append("")
    bericht.append("=" * 60)
    bericht.append("ENDE BERICHT")
    bericht.append("=" * 60)

    bericht_text = "\n".join(bericht)
    BERICHT_PFAD.parent.mkdir(parents=True, exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write(bericht_text)

    print(f"\n{len(aenderungen)} Modulnamen korrigiert:")
    for a in aenderungen:
        print(f"  {a['modul_id']}: '{a['alt']}' -> '{a['neu']}'")
    print(f"\nRegister gespeichert: {REGISTER_PFAD}")
    print(f"Bericht geschrieben: {BERICHT_PFAD}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
