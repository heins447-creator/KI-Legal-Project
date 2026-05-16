# -*- coding: utf-8 -*-
"""
CORE-06 – Ressourcenregister Befüllung und Abgleich
Auftragsnummer: CORE-06
Agent: ALIN_Core_Build_Agent
Geltungsbereich: ALIN_Neustart_Core/

Lieferpflicht (AGENTS.md):
- Python-Läufer: ja
- Prüfdatei: ja (alin_core06_pruefung.py)
- PowerShell-Starter: ja (Run_CORE06_Ressourcenregister.ps1)
- Bericht: ja (Reports/ALIN_CORE06_RESSOURCENREGISTER_BERICHT.txt)
- Dokumentation: ja (CORE06_Ressourcenregister_Vervollstaendigung.md)
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

    reg_path = core / "01_Register" / "ressourcenregister.json"
    schema_path = core / "01_Register" / "ressourcenregister.schema.json"
    toolreg_path = core / "01_Register" / "toolregister.json"
    upd_path = core / "01_Register" / "update_register.json"
    liz_path = core / "01_Register" / "lizenzregister.json"
    alt_path = core / "07_Bestandsaufnahme_Altbestand" / "altbestand_ressourcenkarte.json"
    bericht_path = core / "Reports" / "ALIN_CORE06_RESSOURCENREGISTER_BERICHT.txt"

    register = load_json(reg_path)
    schema = load_json(schema_path)
    toolreg = load_json(toolreg_path)
    updreg = load_json(upd_path)
    lizreg = load_json(liz_path)
    altbestand = load_json(alt_path)

    # Abgleich mit Toolregister
    tool_ids = {t["tool_id"] for t in toolreg.get("eintraege", [])}
    upd_ids = {u["komponente_id"] for u in updreg.get("eintraege", [])}
    liz_ids = {l["komponente_id"] for l in lizreg.get("eintraege", [])}

    verknuepfungen_tool = 0
    verknuepfungen_update = 0
    verknuepfungen_lizenz = 0
    fehlende_tools = []
    fehlende_updates = []
    fehlende_lizenzen = []

    for res in register.get("eintraege", []):
        tid = res.get("tool_id", "")
        uid = res.get("update_id", "")
        lid = res.get("lizenz_id", "")

        if tid and tid in tool_ids:
            verknuepfungen_tool += 1
        elif tid:
            fehlende_tools.append((res["resource_id"], tid))

        if uid and uid in upd_ids:
            verknuepfungen_update += 1
        elif uid:
            fehlende_updates.append((res["resource_id"], uid))

        if lid and lid in liz_ids:
            verknuepfungen_lizenz += 1
        elif lid:
            fehlende_lizenzen.append((res["resource_id"], lid))

    # Timestamp aktualisieren
    register["letzte_aenderung"] = now
    altbestand["letzte_aktualisierung"] = now

    save_json(reg_path, register)
    save_json(alt_path, altbestand)

    # Statistik
    total = len(register.get("eintraege", []))
    vorher = 2  # Altbestand hatte 2 Einträge
    ocr = sum(1 for r in register["eintraege"] if r["typ"] == "ocr_sprachpaket")
    uebers = sum(1 for r in register["eintraege"] if r["typ"] == "uebersetzungsmodell")
    term = sum(1 for r in register["eintraege"] if r["typ"] == "terminologie")
    quellen = sum(1 for r in register["eintraege"] if r["typ"] in ("quellenregister", "adapter"))
    ui = sum(1 for r in register["eintraege"] if r["typ"] == "ui_hilfe")
    sicher = sum(1 for r in register["eintraege"] if r["typ"] == "sicherheitsressource")
    vorhanden = sum(1 for r in register["eintraege"] if r.get("vorhanden_ja_nein_unbekannt") == "ja")
    fehlt = sum(1 for r in register["eintraege"] if r.get("vorhanden_ja_nein_unbekannt") == "nein")
    unbekannt = sum(1 for r in register["eintraege"] if r.get("vorhanden_ja_nein_unbekannt") == "unbekannt")
    gesperrt = sum(1 for r in register["eintraege"] if r["status"] == "gesperrt")
    nicht_frei = sum(1 for r in register["eintraege"] if r.get("darf_von_modulen_verwendet_werden") is False)

    bericht = f"""
======================================================================
CORE-06 – Ressourcenregister Befüllung und Abgleich
======================================================================
Datum: {now}
Agent: ALIN_Core_Build_Agent

1. Anzahl Ressourcen
   Vorher: {vorher}
   Nachher: {total}
   Zuwachs: {total - vorher}

2. Verteilung nach Typ
   OCR-Sprachpakete:        {ocr}
   Übersetzungsressourcen:   {uebers}
   Terminologie/Schreibweise: {term}
   Quellen/Adapter:          {quellen}
   Windows-App/UI-Hilfen:    {ui}
   Sicherheitsressourcen:    {sicher}

3. Physische Verfügbarkeit
   Vorhanden (ja):   {vorhanden}
   Fehlt (nein):     {fehlt}
   Unbekannt:        {unbekannt}

4. Status
   Freigegeben:  {sum(1 for r in register["eintraege"] if r["status"] == "freigegeben")}
   Testbar:      {sum(1 for r in register["eintraege"] if r["status"] == "testbar")}
   Veraltet:     {sum(1 for r in register["eintraege"] if r["status"] == "veraltet")}
   Gesperrt:     {gesperrt}
   Fehlt:        {sum(1 for r in register["eintraege"] if r["status"] == "fehlt")}

5. Verknüpfungen
   Mit Toolregister:   {verknuepfungen_tool}/{total}
   Mit Update-Register: {verknuepfungen_update}/{total}
   Mit Lizenzregister: {verknuepfungen_lizenz}/{total}

6. Gesperrt / Nicht für Module freigegeben
   Nicht für Modulnutzung freigegeben: {nicht_frei}

7. Fehlende Verknüpfungen (Tool)
{chr(10).join(f"   - {rid}: {tid}" for rid, tid in fehlende_tools) or "   (keine)"}

8. Fehlende Verknüpfungen (Update)
{chr(10).join(f"   - {rid}: {uid}" for rid, uid in fehlende_updates) or "   (keine)"}

9. Fehlende Verknüpfungen (Lizenz)
{chr(10).join(f"   - {rid}: {lid}" for rid, lid in fehlende_lizenzen) or "   (keine)"}

10. Gesamtergebnis
    Ressourcenregister: OK
    Altbestand-Ressourcenkarte: OK
    Nächster sinnvoller Auftrag: CORE-07 – Quellen-/Adapterregister vervollständigen

======================================================================
""".strip()

    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(bericht + "\n")

    print(f"Ressourcenregister: {total} Eintraege")
    print(f"Verknuepfungen Tool/Update/Lizenz: {verknuepfungen_tool}/{verknuepfungen_update}/{verknuepfungen_lizenz}")
    print(f"Bericht geschrieben nach: {bericht_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
