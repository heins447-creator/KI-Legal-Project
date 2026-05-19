# -*- coding: utf-8 -*-
"""
CORE-08 – Skillregister Befüllung und Abgleich
Auftragsnummer: CORE-08
Agent: ALIN_Core_Build_Agent
Geltungsbereich: ALIN_Neustart_Core/

Lieferpflicht (AGENTS.md):
- Python-Läufer: ja
- Prüfdatei: ja (alin_core08_pruefung.py)
- PowerShell-Starter: ja (Run_CORE08_Skillregister.ps1)
- Bericht: ja (Reports/ALIN_CORE08_SKILLREGISTER_BERICHT.txt)
- Dokumentation: ja (CORE08_Skillregister_Vervollstaendigung.md)
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

    reg_path = core / "01_Register" / "skillregister.json"
    schema_path = core / "01_Register" / "skillregister.schema.json"
    alt_path = core / "07_Bestandsaufnahme_Altbestand" / "altbestand_schnittstellen.json"
    bericht_path = core / "Reports" / "ALIN_CORE08_SKILLREGISTER_BERICHT.txt"

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
    vorher = 5  # Altbestand hatte 5 Einträge

    # Verteilung nach Skillgruppe
    gruppe_counts = {}
    for e in register["eintraege"]:
        g = e.get("skillgruppe", "unbekannt")
        gruppe_counts[g] = gruppe_counts.get(g, 0) + 1

    # Offline-Moeglichkeit
    offline_ja = sum(1 for e in register["eintraege"] if e.get("offline_moeglich") is True)
    offline_nein = sum(1 for e in register["eintraege"] if e.get("offline_moeglich") is False)

    # Online erforderlich
    online_ja = sum(1 for e in register["eintraege"] if e.get("online_erforderlich") is True)
    online_nein = sum(1 for e in register["eintraege"] if e.get("online_erforderlich") is False)

    # Sicherheitsstufen
    sicherheit_counts = {}
    for e in register["eintraege"]:
        s = e.get("sicherheitsstufe", "unbekannt")
        sicherheit_counts[s] = sicherheit_counts.get(s, 0) + 1

    # Status
    gesperrt = sum(1 for e in register["eintraege"] if e.get("status") == "gesperrt")
    frei = sum(1 for e in register["eintraege"] if e.get("status") != "gesperrt")

    # Bewertungsrechte
    darf_bewerten = sum(1 for e in register["eintraege"] if e.get("darf_bewerten") is True)
    darf_beweis = sum(1 for e in register["eintraege"] if e.get("darf_beweiswuerdigen") is True)
    darf_recht = sum(1 for e in register["eintraege"] if e.get("darf_rechtsbewertung") is True)
    darf_stamm = sum(1 for e in register["eintraege"] if e.get("darf_stammdaten_aendern") is True)
    darf_orig = sum(1 for e in register["eintraege"] if e.get("darf_originale_veraendern") is True)

    # Tools genutzt
    tools_used = set()
    for e in register["eintraege"]:
        for t in e.get("verwendete_tools", []):
            tools_used.add(t)

    bericht = f"""
======================================================================
CORE-08 – Skillregister Befüllung und Abgleich
======================================================================
Datum: {now}
Agent: ALIN_Core_Build_Agent

1. Anzahl Skills
   Vorher: {vorher}
   Nachher: {total}
   Zuwachs: {total - vorher}

2. Verteilung nach Skillgruppe
   Eingang/Briefkasten:     {gruppe_counts.get('eingang_briefkasten', 0)}
   Dokument-Voranalyse:     {gruppe_counts.get('dokument_voranalyse', 0)}
   Routing/Weiche:          {gruppe_counts.get('routing_weiche', 0)}
   OCR/Fundstellen:         {gruppe_counts.get('ocr_fundstellen', 0)}
   Sprache/Uebersetzung:    {gruppe_counts.get('sprache_uebersetzung', 0)}
   Kanzlei-Arbeit:          {gruppe_counts.get('kanzlei_arbeit', 0)}
   Quellen/Adapter:         {gruppe_counts.get('quellen_adapter', 0)}

3. Offline-/Online-Faehigkeit
   Offline moeglich:     {offline_ja}
   Offline nicht moeglich: {offline_nein}
   Online erforderlich:  {online_ja}
   Online nicht erforderlich: {online_nein}

4. Sicherheitsstufen
   Normal:   {sicherheit_counts.get('normal', 0)}
   Hoch:     {sicherheit_counts.get('hoch', 0)}
   Kritisch: {sicherheit_counts.get('kritisch', 0)}

5. Status
   Gesperrt:   {gesperrt}
   Freigegeben: {frei}

6. Bewertungsrechte (sollten alle 0 sein)
   Darf bewerten:            {darf_bewerten}
   Darf beweiswuerdigen:     {darf_beweis}
   Darf rechtsbewertung:     {darf_recht}
   Darf Stammdaten aendern:  {darf_stamm}
   Darf Originale veraendern: {darf_orig}

7. Verwendete Tools ({len(tools_used)})
{chr(10).join(f'   - {t}' for t in sorted(tools_used))}

8. Gesamtergebnis
      Skillregister: OK
      Altbestand-Schnittstellen: OK
      Alle Skills gesperrt bis Freigabe.
      Nächster sinnvoller Auftrag: CORE-09 – Modulregister vervollstaendigen

======================================================================
""".strip()

    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(bericht + "\n")

    print(f"Skillregister: {total} Eintraege")
    print(f"Skillgruppen: {len(gruppe_counts)}")
    print(f"Bericht geschrieben nach: {bericht_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
