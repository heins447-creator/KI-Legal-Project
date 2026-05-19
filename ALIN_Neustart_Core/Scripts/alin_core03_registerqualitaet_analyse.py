# -*- coding: utf-8 -*-
"""
CORE-03 – Registerqualität prüfen, Lücken klassifizieren und Nachinventarisierung planen
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("I:/KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core"
REGISTER_DIR = CORE / "01_Register"
ALTBESTAND_DIR = CORE / "07_Bestandsaufnahme_Altbestand"
REPORTS_DIR = CORE / "Reports"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_modulregister(data: dict) -> dict:
    eintraege = data.get("eintraege", [])
    stats = {
        "anzahl": len(eintraege),
        "nach_status": Counter(e.get("status", "unbekannt") for e in eintraege),
        "nach_kategorie": Counter(),
        "module_ohne_beschreibung": [],
        "module_ohne_version": [],
        "module_ohne_abhaengigkeiten": [],
        "ps1_module": [],
        "py_module": [],
        "sql_module": [],
        "cs_module": [],
    }
    for e in eintraege:
        pfad = e.get("pfad", "")
        modul_id = e.get("modul_id", "unbekannt")
        if ".ps1" in pfad:
            stats["nach_kategorie"]["PowerShell_Skript"] += 1
            stats["ps1_module"].append(modul_id)
        elif ".py" in pfad:
            stats["nach_kategorie"]["Python_Skript"] += 1
            stats["py_module"].append(modul_id)
        elif ".sql" in pfad:
            stats["nach_kategorie"]["SQL_Migration"] += 1
            stats["sql_module"].append(modul_id)
        elif ".cs" in pfad:
            stats["nach_kategorie"]["CSharp_Quellcode"] += 1
            stats["cs_module"].append(modul_id)
        else:
            stats["nach_kategorie"]["Sonstige"] += 1
        
        if not e.get("zweck") or e.get("zweck") == "Keine Beschreibung verfuegbar":
            stats["module_ohne_beschreibung"].append(modul_id)
        if not e.get("version") or e.get("version") == "unbekannt":
            stats["module_ohne_version"].append(modul_id)
        abhaengig = e.get("abhaengig_von", [])
        if not abhaengig or abhaengig == ["unbekannt"]:
            stats["module_ohne_abhaengigkeiten"].append(modul_id)
    return stats


def analyze_register(data: dict, name: str) -> dict:
    eintraege = data.get("eintraege", [])
    stats = {
        "anzahl": len(eintraege),
        "nach_status": Counter(),
        "felder": defaultdict(set),
    }
    for e in eintraege:
        for key in e:
            stats["felder"][key].add(e.get(key))
        if "status" in e:
            stats["nach_status"][e["status"]] += 1
        elif "freigabestatus" in e:
            stats["nach_status"][e["freigabestatus"]] += 1
        elif "installationsstatus" in e:
            stats["nach_status"][e["installationsstatus"]] += 1
        elif "teststatus" in e:
            stats["nach_status"][e["teststatus"]] += 1
        elif "online_status" in e:
            stats["nach_status"][e["online_status"]] += 1
    return stats


def analyze_altbestand_luecken(data: dict) -> dict:
    luecken = data.get("luecken", [])
    stats = {
        "anzahl": len(luecken),
        "nach_kategorie": Counter(l.get("kategorie", "unbekannt") for l in luecken),
        "nach_schwere": Counter(l.get("schwere", "unbekannt") for l in luecken),
        "nach_prioritaet": Counter(l.get("prioritaet", "unbekannt") for l in luecken),
        "dringend": [l for l in luecken if l.get("prioritaet") == "dringend"],
        "hoch": [l for l in luecken if l.get("prioritaet") == "hoch"],
    }
    return stats


def main():
    bericht = []
    sep = "=" * 70
    
    bericht.append("ALIN CORE-03 REGISTERQUALITAETSANALYSE")
    bericht.append(sep)
    bericht.append("")
    
    # Modulregister
    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    mod_stats = analyze_modulregister(modulregister)
    bericht.append("1. MODULREGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl Module: {mod_stats['anzahl']}")
    bericht.append(f"Kategorien:")
    for kat, anz in sorted(mod_stats['nach_kategorie'].items(), key=lambda x: -x[1]):
        bericht.append(f"  {kat}: {anz}")
    bericht.append(f"Status:")
    for st, anz in sorted(mod_stats['nach_status'].items(), key=lambda x: -x[1]):
        bericht.append(f"  {st}: {anz}")
    bericht.append(f"Module ohne Beschreibung: {len(mod_stats['module_ohne_beschreibung'])}")
    bericht.append(f"Module ohne Version: {len(mod_stats['module_ohne_version'])}")
    bericht.append(f"Module ohne Abhaengigkeiten: {len(mod_stats['module_ohne_abhaengigkeiten'])}")
    bericht.append("")
    
    # Ressourcenregister
    res = load_json(REGISTER_DIR / "ressourcenregister.json")
    res_stats = analyze_register(res, "ressourcenregister")
    bericht.append("2. RESSOURCENREGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl: {res_stats['anzahl']}")
    bericht.append(f"Status: {dict(res_stats['nach_status'])}")
    bericht.append("")
    
    # Toolregister
    tool = load_json(REGISTER_DIR / "toolregister.json")
    tool_stats = analyze_register(tool, "toolregister")
    bericht.append("3. TOOLREGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl: {tool_stats['anzahl']}")
    bericht.append(f"Status: {dict(tool_stats['nach_status'])}")
    bericht.append("")
    
    # Skillregister
    skill = load_json(REGISTER_DIR / "skillregister.json")
    skill_stats = analyze_register(skill, "skillregister")
    bericht.append("4. SKILLREGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl: {skill_stats['anzahl']}")
    bericht.append(f"Status: {dict(skill_stats['nach_status'])}")
    bericht.append("")
    
    # Quellen-Adapter-Register
    quellen = load_json(REGISTER_DIR / "quellen_adapter_register.json")
    quellen_stats = analyze_register(quellen, "quellen_adapter_register")
    bericht.append("5. QUELLEN-/ADAPTER-REGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl: {quellen_stats['anzahl']}")
    bericht.append(f"Status: {dict(quellen_stats['nach_status'])}")
    bericht.append("")
    
    # Lizenzregister
    lizenz = load_json(REGISTER_DIR / "lizenzregister.json")
    lizenz_stats = analyze_register(lizenz, "lizenzregister")
    bericht.append("6. LIZENZREGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl: {lizenz_stats['anzahl']}")
    bericht.append(f"Status: {dict(lizenz_stats['nach_status'])}")
    bericht.append("")
    
    # Update-Register
    update = load_json(REGISTER_DIR / "update_register.json")
    update_stats = analyze_register(update, "update_register")
    bericht.append("7. UPDATE-REGISTER")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl: {update_stats['anzahl']}")
    bericht.append("")
    
    # Lückenanalyse
    luecken_data = load_json(ALTBESTAND_DIR / "altbestand_luecken.json")
    luecken_stats = analyze_altbestand_luecken(luecken_data)
    bericht.append("8. LUECKENANALYSE")
    bericht.append("-" * 40)
    bericht.append(f"Gesamtanzahl Luecken: {luecken_stats['anzahl']}")
    bericht.append(f"Nach Kategorie:")
    for kat, anz in sorted(luecken_stats['nach_kategorie'].items(), key=lambda x: -x[1]):
        bericht.append(f"  {kat}: {anz}")
    bericht.append(f"Nach Schwere:")
    for schw, anz in sorted(luecken_stats['nach_schwere'].items(), key=lambda x: -x[1]):
        bericht.append(f"  {schw}: {anz}")
    bericht.append(f"Nach Prioritaet:")
    for prio, anz in sorted(luecken_stats['nach_prioritaet'].items(), key=lambda x: -x[1]):
        bericht.append(f"  {prio}: {anz}")
    bericht.append("")
    
    # Bewertung
    bericht.append("9. BEWERTUNG UND EMPFEHLUNGEN")
    bericht.append("-" * 40)
    
    # Modulregister Bewertung
    ps1_anz = len(mod_stats['ps1_module'])
    py_anz = len(mod_stats['py_module'])
    sql_anz = len(mod_stats['sql_module'])
    cs_anz = len(mod_stats['cs_module'])
    
    bericht.append("a) Modulregister:")
    bericht.append(f"   - {ps1_anz} PowerShell-Module, {py_anz} Python-Module, {sql_anz} SQL-Migrationen, {cs_anz} C#-Dateien")
    bericht.append(f"   - {len(mod_stats['module_ohne_beschreibung'])} Module ohne sinnvolle Beschreibung")
    bericht.append(f"   - {len(mod_stats['module_ohne_version'])} Module ohne Version")
    bericht.append("   EMPFEHLUNG: Beschreibungen aus SYNOPSIS/DESCRIPTION/DOCSTRING nachtragen")
    bericht.append("")
    
    bericht.append("b) Ressourcenregister (nur 2 Eintraege):")
    bericht.append("   - Nur 'Python_Interpreter' und 'Tesseract_OCR' erfasst")
    bericht.append("   FEHLEND: PowerShell-Engine, Windows-App-Runtime, .NET-Runtime,")
    bericht.append("            Datenbank-Engine, Git-Client, Webbrowser-Engine")
    bericht.append("   URSACHE: Extraktionslogik prueft nur auf EXE-Dateien in Scripts/")
    bericht.append("")
    
    bericht.append("c) Toolregister (nur 3 Eintraege):")
    bericht.append("   - Nur 'Tesseract_OCR', 'Python_Interpreter', 'Git' erfasst")
    bericht.append("   FEHLEND: Alle externen Tools aus ALIN_Neustart_Core/09_Toolbibliothek")
    bericht.append("   URSACHE: Kein Scan von 09_Toolbibliothek/ durchgefuehrt")
    bericht.append("")
    
    bericht.append("d) Skillregister (5 Eintraege):")
    bericht.append("   - Skills wurden aus speziellen Python-Runners extrahiert")
    bericht.append("   - 'Spracherkennung', 'OCR_Betreuung', 'Agenten_Skill_Management'")
    bericht.append("   BEWERTUNG: Korrekt, aber unvollstaendig (nur explizit markierte Skills)")
    bericht.append("")
    
    bericht.append("e) Quellen-Adapter-Register (1 Eintrag):")
    bericht.append("   - Nur 'EU_Offizielle_Quellen' erfasst")
    bericht.append("   FEHLEND: Alle Quellen aus Projektplanung/Quellen/ und Database/Migrations/")
    bericht.append("   URSACHE: Nur aus 051_quellenkandidaten_eu_se_v1.py extrahiert")
    bericht.append("")
    
    bericht.append("f) Update-Register (0 Eintraege):")
    bericht.append("   - Keine Updates erfasst")
    bericht.append("   FEHLEND: Alle Tool-Updates, Sprachpaket-Updates, Schema-Migrationen")
    bericht.append("   URSACHE: Keine Extraktionslogik fuer Update-Register implementiert")
    bericht.append("")
    
    # Nachinventarisierungsaufträge
    bericht.append("10. NACHINVENTARISIERUNGSAUFTRAEGE (nach Prioritaet)")
    bericht.append("-" * 40)
    bericht.append("P0-DRINGEND:")
    bericht.append("  [ ] CORE-03a: Update-Register befuellen (Tool-Updates, Sprachpakete, Schema-Migrationen)")
    bericht.append("  [ ] CORE-03b: Toolregister vervollstaendigen (Scan 09_Toolbibliothek/)")
    bericht.append("  [ ] CORE-03c: Ressourcenregister vervollstaendigen (System-Runtimes, Engines)")
    bericht.append("")
    bericht.append("P1-HOCH:")
    bericht.append("  [ ] CORE-03d: Quellen-Adapter-Register vervollstaendigen (alle Quellen-Adapter)")
    bericht.append("  [ ] CORE-03e: Modul-Beschreibungen nachtragen (SYNOPSIS/DESCRIPTION auslesen)")
    bericht.append("  [ ] CORE-03f: Modul-Versionen pruefen und nachtragen")
    bericht.append("")
    bericht.append("P2-MITTEL:")
    bericht.append("  [ ] CORE-03g: Modul-Abhaengigkeiten vervollstaendigen (Import/Require-Analyse)")
    bericht.append("  [ ] CORE-03h: Skillregister vervollstaendigen (implizite Skills identifizieren)")
    bericht.append("  [ ] CORE-03i: Lizenzregister vervollstaendigen (Third-Party-Lizenzen)")
    bericht.append("")
    bericht.append("P3-NIEDRIG:")
    bericht.append("  [ ] CORE-03j: Altbestand-Modulkarte mit Windows_App-Modulen ergaenzen")
    bericht.append("  [ ] CORE-03k: Schnittstellen-Dokumentation vervollstaendigen")
    bericht.append("")
    
    bericht.append(sep)
    bericht.append("ENDE CORE-03 ANALYSE")
    
    text = "\n".join(bericht)
    print(text)
    
    bericht_path = REPORTS_DIR / "ALIN_CORE03_REGISTERQUALITAET_BERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nBericht geschrieben nach: {bericht_path}")


if __name__ == "__main__":
    main()
