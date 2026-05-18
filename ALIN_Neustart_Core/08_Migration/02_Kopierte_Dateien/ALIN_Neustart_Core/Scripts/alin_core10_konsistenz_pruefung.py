#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10 – Modulabhaengigkeiten, Schnittstellen und Registerkonsistenz pruefen.

Prueft:
  1. Eindeutigkeit der Modul-IDs
  2. Fehlende Abhaengigkeiten (Ziel-Modul existiert nicht)
  3. Widerspruechliche Modulnamen (gleicher Name, andere ID/Pfad)
  4. Module ohne Eingabe / Ausgabe / Teststatus
  5. Module mit Aufrufrechten aber ohne Ressourcen/Tools/Skills
  6. Datenbank-aendernde Module
  7. Online-faehige Module
  8. Unklare Schnittstellen (Platzhalter-Eingabe/Ausgabe)
  9. Uebergaben ohne Schema-Abdeckung (Handoffs vs. Schemas)
 10. Querregister-Verknuepfungen (Tools, Ressourcen, Skills, Quellen)
 11. Bidirektionale Abhaengigkeiten
 12. AGENTS.md-Konformitaet (Rechtsbewertung/Beweiswuerdigung verboten)

Liefert:
  - ALIN_CORE10_KONSISTENZ_BERICHT.txt  (Zusammenfassung)
  - ALIN_CORE10_PRUEFBERICHT.txt        (Detail-Findings)

Hinweis: Keine Aenderungen an Registern – nur Lesezugriff.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
REGISTER_DIR = BASE_DIR / "01_Register"
SCHNITTSTELLEN_DIR = BASE_DIR / "03_Schnittstellen"
REPORTS_DIR = BASE_DIR / "Reports"

DATEIEN = {
    "modul": REGISTER_DIR / "modulregister.json",
    "tool": REGISTER_DIR / "toolregister.json",
    "ressource": REGISTER_DIR / "ressourcenregister.json",
    "skill": REGISTER_DIR / "skillregister.json",
    "quelle": REGISTER_DIR / "quellen_adapter_register.json",
}

SCHNITTSTELLEN_SCHEMAS = [
    "uebergabe_posteingang_sekretariat.schema.json",
    "uebergabe_sekretariat_weiche.schema.json",
    "uebergabe_weiche_anwalt.schema.json",
    "uebergabe_weiche_ocr.schema.json",
    "uebergabe_ocr_an_anwalt.schema.json",
    "uebergabe_ocr_an_akte.schema.json",
    "ruecklauf_anwalt_sekretariat.schema.json",
]

PLATZHALTER_EINGABE = {
    "unbekannt", "nicht definiert", "nicht spezifiziert", "schaetzung",
    "konfiguration und umgebungsvariablen", "umgebungsvariablen",
}
PLATZHALTER_AUSGABE = {
    "unbekannt", "nicht definiert", "nicht spezifiziert", "schaetzung",
    "prozess-start, log-datei, exit-code", "prozess-start",
}

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def lade_json(pfad: Path):
    if not pfad.exists():
        print(f"[FEHLER] Datei nicht gefunden: {pfad}")
        sys.exit(1)
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(txt: str) -> str:
    return txt.lower().strip().rstrip(".")


def ist_platzhalter(txt: str, platzhalter_set: set) -> bool:
    t = normalize(txt)
    return t in platzhalter_set or t == "" or "platzhalter" in t or "schaetzung" in t


# ---------------------------------------------------------------------------
# Prueffunktionen
# ---------------------------------------------------------------------------
def pruefung_01_modul_id_eindeutigkeit(module):
    findings = []
    ids = {}
    for m in module:
        mid = m["modul_id"]
        ids.setdefault(mid, []).append(m["modulname"])
    for mid, names in ids.items():
        if len(names) > 1:
            findings.append(f"DUPLIKAT modul_id='{mid}' – verwendet von: {', '.join(names)}")
    return findings


def pruefung_02_fehlende_abhaengigkeiten(module):
    findings = []
    gueltige_ids = {m["modul_id"] for m in module}
    for m in module:
        for dep in m.get("abhaengigkeiten", []):
            if dep not in gueltige_ids:
                findings.append(
                    f"FEHLENDE_ABHAENGIGKEIT modul='{m['modul_id']}' "
                    f"referenziert unbekanntes Modul '{dep}'"
                )
    return findings


def pruefung_03_widerspruechliche_modulnamen(module):
    findings = []
    name_map = {}
    for m in module:
        name = m["modulname"]
        name_map.setdefault(name, []).append((m["modul_id"], m["pfad"]))
    for name, entries in name_map.items():
        if len(entries) > 1:
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    id1, p1 = entries[i]
                    id2, p2 = entries[j]
                    if id1 != id2 or p1 != p2:
                        findings.append(
                            f"WIDERSPRUCH modulname='{name}' -> id1='{id1}'(pfad={p1}) "
                            f"vs id2='{id2}'(pfad={p2})"
                        )
    return findings


def pruefung_04_ohne_eingabe_ausgabe_teststatus(module):
    findings = []
    for m in module:
        mid = m["modul_id"]
        e = m.get("eingabe", "")
        a = m.get("ausgabe", "")
        t = m.get("teststatus", "")
        if not e or ist_platzhalter(e, PLATZHALTER_EINGABE):
            findings.append(f"LEER_EINGABE modul='{mid}' eingabe='{e}'")
        if not a or ist_platzhalter(a, PLATZHALTER_AUSGABE):
            findings.append(f"LEER_AUSGABE modul='{mid}' ausgabe='{a}'")
        if t in ("", "unbekannt", None):
            findings.append(f"LEER_TESTSTATUS modul='{mid}' teststatus='{t}'")
    return findings


def pruefung_05_aufrufrechte_ohne_ressourcen(module):
    findings = []
    for m in module:
        if m.get("darf_aufgerufen_werden", False) is True:
            leer_tools = len(m.get("benoetigte_tools", [])) == 0
            leer_res = len(m.get("benoetigte_ressourcen", [])) == 0
            leer_skills = len(m.get("benoetigte_skills", [])) == 0
            if leer_tools and leer_res and leer_skills:
                findings.append(
                    f"AUFRUF_OHNE_RESSOURCEN modul='{m['modul_id']}' "
                    f"darf_aufgerufen_werden=true aber keine tools/res/skills"
                )
    return findings


def pruefung_06_db_aendernde_module(module):
    findings = []
    for m in module:
        if m.get("darf_datenbank_aendern", False) is True:
            findings.append(
                f"DB_AENDERUNG modul='{m['modul_id']}' "
                f"modultyp='{m.get('modultyp')}' bereich='{m.get('bereich')}'"
            )
    return findings


def pruefung_07_online_faehige_module(module):
    findings = []
    for m in module:
        if m.get("darf_online_gehen", False) is True:
            findings.append(
                f"ONLINE_FAEHIG modul='{m['modul_id']}' "
                f"modultyp='{m.get('modultyp')}' bereich='{m.get('bereich')}'"
            )
    return findings


def pruefung_08_unklare_schnittstellen(module):
    findings = []
    for m in module:
        mid = m["modul_id"]
        e = m.get("eingabe", "")
        a = m.get("ausgabe", "")
        if ist_platzhalter(e, PLATZHALTER_EINGABE):
            findings.append(f"UNKLAR_EINGABE modul='{mid}' eingabe='{e}'")
        if ist_platzhalter(a, PLATZHALTER_AUSGABE):
            findings.append(f"UNKLAR_AUSGABE modul='{mid}' ausgabe='{a}'")
    return findings


def pruefung_09_uebergaben_ohne_schema(module):
    findings = []
    # Wir pruefen, ob es Module gibt, die liefert_an haben, aber kein passendes
    # Schema im 03_Schnittstellen/-Verzeichnis referenzieren.
    # Da Module keine direkte Schema-Referenz besitzen, pruefen wir heuristisch:
    # Jede existierende Handoff-Schema-Datei sollte von mind. einem Modul
    # als 'liefert_an' oder via bereich abgedeckt werden.
    # Stattdessen: Sammle alle liefert_an Eintraege und pruefe ob es Module gibt,
    # die Schnittstellen produzieren koennten (modultyp=schnittstelle oder bereich
    # enthaelt posteingang/sekretariat/weiche/anwalt/ocr/ruecklauf).
    bereiche_mit_schema = {
        "posteingang", "sekretariat", "weiche", "anwalt", "ocr", "ruecklauf",
        "schnittstellen",
    }
    for m in module:
        mid = m["modul_id"]
        bereich = m.get("bereich", "").lower()
        liefert = m.get("liefert_an", [])
        if liefert and not any(b in bereich for b in bereiche_mit_schema):
            findings.append(
                f"SCHEMA_LUECKE modul='{mid}' liefert_an={liefert} "
                f"aber bereich='{bereich}' passt zu keinem Schnittstellen-Schema"
            )

    # Pruefe, ob alle 7 Schemas physikalisch vorhanden sind
    for schema in SCHNITTSTELLEN_SCHEMAS:
        if not (SCHNITTSTELLEN_DIR / schema).exists():
            findings.append(f"FEHLENDES_SCHEMA datei='{schema}' nicht gefunden")
    return findings


def pruefung_10_querregister_verknuepfungen(module, tools, ressourcen, skills, quellen):
    findings = []
    tool_ids = {t["tool_id"] for t in tools}
    res_ids = {r["resource_id"] for r in ressourcen}
    skill_ids = {s["skill_id"] for s in skills}
    quelle_ids = {q["quelle_id"] for q in quellen}

    for m in module:
        mid = m["modul_id"]
        for t in m.get("benoetigte_tools", []):
            if t not in tool_ids:
                findings.append(f"UNGUELTIGES_TOOL modul='{mid}' tool='{t}'")
        for r in m.get("benoetigte_ressourcen", []):
            if r not in res_ids:
                findings.append(f"UNGUELTIGE_RESSOURCE modul='{mid}' ressource='{r}'")
        for s in m.get("benoetigte_skills", []):
            if s not in skill_ids:
                findings.append(f"UNGUELTIGER_SKILL modul='{mid}' skill='{s}'")
        for q in m.get("benoetigte_quellen", []):
            if q not in quelle_ids:
                findings.append(f"UNGUELTIGE_QUELLE modul='{mid}' quelle='{q}'")
    return findings


def pruefung_11_bidirektionale_abhaengigkeiten(module):
    findings = []
    modul_dict = {m["modul_id"]: m for m in module}
    for m in module:
        mid = m["modul_id"]
        for dep in m.get("abhaengigkeiten", []):
            target = modul_dict.get(dep)
            if target:
                liefert = target.get("liefert_an", [])
                if mid not in liefert:
                    findings.append(
                        f"BIDIREKTION modul='{mid}' haengt ab von '{dep}', "
                        f"aber '{dep}' liefert_an enthält nicht '{mid}'"
                    )
        for lief in m.get("liefert_an", []):
            target = modul_dict.get(lief)
            if target:
                deps = target.get("abhaengigkeiten", [])
                if mid not in deps:
                    findings.append(
                        f"BIDIREKTION modul='{mid}' liefert an '{lief}', "
                        f"aber '{lief}' abhaengigkeiten enthaelt nicht '{mid}'"
                    )
    return findings


def pruefung_12_agents_md_konformitaet(module):
    findings = []
    for m in module:
        mid = m["modul_id"]
        if m.get("darf_rechtsbewerten", True) is not False:
            findings.append(f"AGENTS_VERSTOSS modul='{mid}' darf_rechtsbewerten != false")
        if m.get("darf_beweiswuerdigen", True) is not False:
            findings.append(f"AGENTS_VERSTOSS modul='{mid}' darf_beweiswuerdigen != false")
    return findings


# ---------------------------------------------------------------------------
# Berichtserstellung
# ---------------------------------------------------------------------------
def schreibe_berichte(ergebnisse, module, tools, ressourcen, skills, quellen):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Konsistenz-Bericht (uebersichtlich)
    konsistenz_pfad = REPORTS_DIR / "ALIN_CORE10_KONSISTENZ_BERICHT.txt"
    with open(konsistenz_pfad, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-10 KONSISTENZ-BERICHT\n")
        f.write(f"Erstellt: {zeitstempel}\n")
        f.write("Auftrag: Modulabhaengigkeiten, Schnittstellen, Registerkonsistenz\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Gepruefte Module:       {len(module)}\n")
        f.write(f"Gepruefte Tools:        {len(tools)}\n")
        f.write(f"Gepruefte Ressourcen:   {len(ressourcen)}\n")
        f.write(f"Gepruefte Skills:       {len(skills)}\n")
        f.write(f"Gepruefte Quellen:      {len(quellen)}\n")
        f.write(f"Schnittstellen-Schemas: {len(SCHNITTSTELLEN_SCHEMAS)}\n\n")

        for num, (titel, findings) in enumerate(ergebnisse, start=1):
            f.write(f"\n{'-' * 70}\n")
            f.write(f"Pruefung {num:02d}: {titel}\n")
            f.write(f"{'-' * 70}\n")
            if not findings:
                f.write("  OK – keine Auffaelligkeiten.\n")
            else:
                f.write(f"  ANZAHL FINDINGS: {len(findings)}\n")
                # Zeige maximal 20 pro Kategorie im Konsistenzbericht
                for i, line in enumerate(findings[:20], 1):
                    f.write(f"  {i:3}. {line}\n")
                if len(findings) > 20:
                    f.write(f"  ... und {len(findings) - 20} weitere (siehe Pruefbericht).\n")
        f.write(f"\n{'=' * 70}\n")
        f.write("ENDE KONSISTENZ-BERICHT\n")
        f.write("=" * 70 + "\n")

    # Detail-Pruefbericht
    pruef_pfad = REPORTS_DIR / "ALIN_CORE10_PRUEFBERICHT.txt"
    with open(pruef_pfad, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-10 DETAIL-PRUEFBERICHT\n")
        f.write(f"Erstellt: {zeitstempel}\n")
        f.write("=" * 70 + "\n\n")
        for num, (titel, findings) in enumerate(ergebnisse, start=1):
            f.write(f"\n{'-' * 70}\n")
            f.write(f"Pruefung {num:02d}: {titel}\n")
            f.write(f"{'-' * 70}\n")
            if not findings:
                f.write("OK – keine Auffaelligkeiten.\n")
            else:
                for line in findings:
                    f.write(f"{line}\n")
        f.write(f"\n{'=' * 70}\n")
        f.write("ENDE DETAIL-PRUEFBERICHT\n")
        f.write("=" * 70 + "\n")

    print(f"\nBerichte geschrieben:")
    print(f"  - {konsistenz_pfad}")
    print(f"  - {pruef_pfad}")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main():
    print("CORE-10 Konsistenzpruefung gestartet...")

    # Register laden
    modul_data = lade_json(DATEIEN["modul"])
    tool_data = lade_json(DATEIEN["tool"])
    res_data = lade_json(DATEIEN["ressource"])
    skill_data = lade_json(DATEIEN["skill"])
    quelle_data = lade_json(DATEIEN["quelle"])

    module = modul_data.get("eintraege", [])
    tools = tool_data.get("eintraege", [])
    ressourcen = res_data.get("eintraege", [])
    skills = skill_data.get("eintraege", [])
    quellen = quelle_data.get("eintraege", [])

    print(f"  Module:     {len(module)}")
    print(f"  Tools:      {len(tools)}")
    print(f"  Ressourcen: {len(ressourcen)}")
    print(f"  Skills:     {len(skills)}")
    print(f"  Quellen:    {len(quellen)}")

    # Pruefungen durchfuehren
    ergebnisse = [
        ("Modul-ID-Eindeutigkeit", pruefung_01_modul_id_eindeutigkeit(module)),
        ("Fehlende Abhaengigkeiten", pruefung_02_fehlende_abhaengigkeiten(module)),
        ("Widerspruechliche Modulnamen", pruefung_03_widerspruechliche_modulnamen(module)),
        ("Module ohne Eingabe/Ausgabe/Teststatus", pruefung_04_ohne_eingabe_ausgabe_teststatus(module)),
        ("Aufrufrechte ohne Ressourcen", pruefung_05_aufrufrechte_ohne_ressourcen(module)),
        ("Datenbank-aendernde Module", pruefung_06_db_aendernde_module(module)),
        ("Online-faehige Module", pruefung_07_online_faehige_module(module)),
        ("Unklare Schnittstellen", pruefung_08_unklare_schnittstellen(module)),
        ("Uebergaben ohne Schema-Abdeckung", pruefung_09_uebergaben_ohne_schema(module)),
        ("Querregister-Verknuepfungen", pruefung_10_querregister_verknuepfungen(module, tools, ressourcen, skills, quellen)),
        ("Bidirektionale Abhaengigkeiten", pruefung_11_bidirektionale_abhaengigkeiten(module)),
        ("AGENTS.md-Konformitaet", pruefung_12_agents_md_konformitaet(module)),
    ]

    # Zusammenfassung auf Konsole
    total_findings = sum(len(f) for _, f in ergebnisse)
    print(f"\n{'=' * 60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'=' * 60}")
    for num, (titel, findings) in enumerate(ergebnisse, start=1):
        status = "OK" if not findings else f"{len(findings)} FINDING(S)"
        print(f"  {num:02d}. {titel:<45} {status}")
    print(f"\nGesamt-Findings: {total_findings}")
    if total_findings == 0:
        print("\nAlle Pruefungen bestanden ohne Auffaelligkeiten.")
    else:
        print("\nBitte Detail-Pruefbericht zur Analyse heranziehen.")

    schreibe_berichte(ergebnisse, module, tools, ressourcen, skills, quellen)
    print("\nCORE-10 Pruefung abgeschlossen.")
    return 0 if total_findings == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
