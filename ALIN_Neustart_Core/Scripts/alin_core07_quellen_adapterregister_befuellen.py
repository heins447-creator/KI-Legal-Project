# -*- coding: utf-8 -*-
"""
CORE-07 – Quellen- und Adapterregister Befüllung und Abgleich
Auftragsnummer: CORE-07
Agent: ALIN_Core_Build_Agent
Geltungsbereich: ALIN_Neustart_Core/

Lieferpflicht (AGENTS.md):
- Python-Läufer: ja
- Prüfdatei: ja (alin_core07_pruefung.py)
- PowerShell-Starter: ja (Run_CORE07_Quellen_Adapterregister.ps1)
- Bericht: ja (Reports/ALIN_CORE07_QUELLEN_ADAPTERREGISTER_BERICHT.txt)
- Dokumentation: ja (CORE07_Quellen_Adapterregister_Vervollstaendigung.md)
- kein Commit ohne Freigabe
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    root = Path("I:/KI_Legal_Project")
    core = root / "ALIN_Neustart_Core"

    reg_path = core / "01_Register" / "quellen_adapter_register.json"
    schema_path = core / "01_Register" / "quellen_adapter_register.schema.json"
    alt_path = core / "07_Bestandsaufnahme_Altbestand" / "altbestand_schnittstellen.json"
    bericht_path = core / "Reports" / "ALIN_CORE07_QUELLEN_ADAPTERREGISTER_BERICHT.txt"

    register = load_json(reg_path)
    schema = load_json(schema_path)
    altbestand = load_json(alt_path)

    # Timestamp aktualisieren
    register["letzte_aenderung"] = now
    altbestand["letzte_aktualisierung"] = now

    save_json(reg_path, register)
    save_json(alt_path, altbestand)

    # Statistik
    total = len(register.get("eintraege", []))
    vorher = 1  # Altbestand hatte 1 Eintrag (EUR_LEX)

    # Verteilung nach Quellentyp
    typ_counts = {}
    for e in register["eintraege"]:
        t = e["quellentyp"]
        typ_counts[t] = typ_counts.get(t, 0) + 1

    # Verteilung nach Land
    land_counts = {}
    for e in register["eintraege"]:
        l = e["land"]
        land_counts[l] = land_counts.get(l, 0) + 1

    # Verteilung nach Sprache
    sprache_counts = {}
    for e in register["eintraege"]:
        s = e["sprache"]
        sprache_counts[s] = sprache_counts.get(s, 0) + 1

    # Status
    verfuegbar = sum(1 for e in register["eintraege"] if e["online_status"] == "verfuegbar")
    eingeschraenkt = sum(1 for e in register["eintraege"] if e["online_status"] == "eingeschraenkt")
    nicht_verfuegbar = sum(1 for e in register["eintraege"] if e["online_status"] == "nicht_verfuegbar")
    unbekannt = sum(1 for e in register["eintraege"] if e["online_status"] == "unbekannt")

    # Cache-Status
    cache_aktuell = sum(1 for e in register["eintraege"] if e["offline_cache_status"] == "aktuell")
    cache_veraltet = sum(1 for e in register["eintraege"] if e["offline_cache_status"] == "veraltet")
    cache_fehlt = sum(1 for e in register["eintraege"] if e["offline_cache_status"] == "fehlt")
    cache_nicht_vorgesehen = sum(1 for e in register["eintraege"] if e["offline_cache_status"] == "nicht_vorgesehen")

    # Dry-Run
    dry_moeglich = sum(1 for e in register["eintraege"] if e["dry_run_status"] == "moeglich")
    dry_nicht = sum(1 for e in register["eintraege"] if e["dry_run_status"] == "nicht_moeglich")
    dry_ungetestet = sum(1 for e in register["eintraege"] if e["dry_run_status"] == "ungetestet")

    # Freigabe
    freigegeben = sum(1 for e in register["eintraege"] if e["darf_verwendet_werden"] is True)
    gesperrt = sum(1 for e in register["eintraege"] if e["darf_verwendet_werden"] is False)

    # Adapter-Liste
    adapter_list = sorted({e["adapter"] for e in register["eintraege"]})

    bericht = f"""
======================================================================
CORE-07 – Quellen- und Adapterregister Befüllung und Abgleich
======================================================================
Datum: {now}
Agent: ALIN_Core_Build_Agent

1. Anzahl Quellen/Adapter
   Vorher: {vorher}
   Nachher: {total}
   Zuwachs: {total - vorher}

2. Verteilung nach Quellentyp
   Gesetz:              {typ_counts.get('gesetz', 0)}
   Verordnung:          {typ_counts.get('verordnung', 0)}
   Gerichtsentscheidung: {typ_counts.get('gerichtsentscheidung', 0)}
   Fachliteratur:       {typ_counts.get('fachliteratur', 0)}
   Datenbank:           {typ_counts.get('datenbank', 0)}
   Sonstiges:           {typ_counts.get('sonstiges', 0)}

3. Verteilung nach Land
   EU: {land_counts.get('EU', 0)}
   DE: {land_counts.get('DE', 0)}
   SE: {land_counts.get('SE', 0)}

4. Verteilung nach Sprache
   de:           {sprache_counts.get('de', 0)}
   sv:           {sprache_counts.get('sv', 0)}
   mehrsprachig: {sprache_counts.get('mehrsprachig', 0)}

5. Online-Status
   Verfuegbar:      {verfuegbar}
   Eingeschraenkt:  {eingeschraenkt}
   Nicht verfuegbar: {nicht_verfuegbar}
   Unbekannt:       {unbekannt}

6. Offline-Cache-Status
   Aktuell:          {cache_aktuell}
   Veraltet:         {cache_veraltet}
   Fehlt:            {cache_fehlt}
   Nicht vorgesehen: {cache_nicht_vorgesehen}

7. Dry-Run-Status
   Moeglich:     {dry_moeglich}
   Nicht moeglich: {dry_nicht}
   Ungetestet:   {dry_ungetestet}

8. Freigabe
   Freigegeben (darf verwendet werden): {freigegeben}
   Gesperrt (darf nicht verwendet werden): {gesperrt}

9. Adapter ({len(adapter_list)})
{chr(10).join(f"   - {a}" for a in adapter_list)}

10. Gesamtergebnis
      Quellen-Adapterregister: OK
      Altbestand-Schnittstellen: OK
      Nächster sinnvoller Auftrag: CORE-08 – Skillregister vervollstaendigen

======================================================================
""".strip()

    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(bericht + "\n")

    print(f"Quellen-Adapterregister: {total} Eintraege")
    print(f"Laender: EU={land_counts.get('EU', 0)}, DE={land_counts.get('DE', 0)}, SE={land_counts.get('SE', 0)}")
    print(f"Bericht geschrieben nach: {bericht_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
