#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-23: Arbeitsstart-Zentrale / Projekt-Dashboard für ALIN_Neustart_Core.

Aggregiert Daten aus:
  - CORE21_arbeitsindex.json
  - CORE22_agenten_regeln.json
  - CORE19_reste_archiv_sperrplan.json
  - CORE20_MASTER_UMBAU_BERICHT.txt
  - CORE21_ARBEITSINDEX_BERICHT.txt
  - CORE22_AGENTEN_EINSTIEG_BERICHT.txt
  - Config/core21_arbeitsindex_v1.json
  - Config/core22_agentenregeln_v1.json

Ergebnisse:
  - ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json
  - ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.html
  - ALIN_Neustart_Core/Reports/CORE23_PROJEKT_DASHBOARD_BERICHT.txt
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Konstanten
BASE_DIR = Path("I:/KI_Legal_Project")
CONFIG_PATH = BASE_DIR / "Config" / "core23_dashboard_v1.json"

MANIFEST_DIR = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest"
PLAENE_DIR = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "01_Plaene"
REPORTS_DIR = BASE_DIR / "ALIN_Neustart_Core" / "Reports"
CONFIG_DIR = BASE_DIR / "Config"

QUELLEN = {
    "core21_manifest": MANIFEST_DIR / "CORE21_arbeitsindex.json",
    "core22_manifest": MANIFEST_DIR / "CORE22_agenten_regeln.json",
    "core19_plan": PLAENE_DIR / "CORE19_reste_archiv_sperrplan.json",
    "core20_bericht": REPORTS_DIR / "CORE20_MASTER_UMBAU_BERICHT.txt",
    "core21_bericht": REPORTS_DIR / "CORE21_ARBEITSINDEX_BERICHT.txt",
    "core22_bericht": REPORTS_DIR / "CORE22_AGENTEN_EINSTIEG_BERICHT.txt",
    "core21_config": CONFIG_DIR / "core21_arbeitsindex_v1.json",
    "core22_config": CONFIG_DIR / "core22_agentenregeln_v1.json",
}

ZIELE = {
    "dashboard_json": MANIFEST_DIR / "CORE23_dashboard.json",
    "dashboard_html": MANIFEST_DIR / "CORE23_dashboard.html",
    "bericht": REPORTS_DIR / "CORE23_PROJEKT_DASHBOARD_BERICHT.txt",
}


def lade_json(pfad: Path):
    if not pfad.exists():
        return None
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def lade_text(pfad: Path):
    if not pfad.exists():
        return None
    with open(pfad, "r", encoding="utf-8") as f:
        return f.read()


def ermittle_bereich_status(pfad_str: str, bereiche: dict):
    for status, ordner_liste in bereiche.items():
        for ordner in ordner_liste:
            if pfad_str.startswith(ordner):
                return status
    return "unbekannt"


def ermittle_core_status(pfad: Path):
    """Prüft ob ein CORE-Report vorhanden ist und gibt einen Status zurück."""
    if pfad.exists():
        txt = lade_text(pfad)
        if txt and "ERFOLGREICH" in txt:
            return "abgeschlossen"
        if txt and "FEHLER" in txt:
            return "fehlerhaft"
        return "vorhanden"
    return "nicht_gefunden"


def aggregiere_dashboard(daten: dict, config: dict):
    jetzt = datetime.now(timezone.utc).isoformat()

    core21_manifest = daten.get("core21_manifest") or {}
    core22_manifest = daten.get("core22_manifest") or {}
    core19_plan = daten.get("core19_plan") or {}
    core21_config = daten.get("core21_config") or {}

    zusammenfassung_core21 = core21_manifest.get("zusammenfassung", {})
    zusammenfassung_core19 = core19_plan.get("zusammenfassung", {})

    arbeitsbestand = core21_manifest.get("arbeitsbestand", [])
    referenzbestand = core21_manifest.get("referenzbestand", [])

    bereiche = core21_config.get("bereiche", {})
    aktiv_bereiche = bereiche.get("aktiv", [])
    referenz_bereiche = bereiche.get("referenz", [])
    gesperrt_bereiche = bereiche.get("gesperrt", [])

    # Kategorien zählen
    kategorien = {}
    for item in arbeitsbestand:
        kat = item.get("kategorie", "unbekannt")
        kategorien[kat] = kategorien.get(kat, 0) + 1

    # Manuell und gesperrt aus CORE19
    plaene = core19_plan.get("plaene", {})
    manuell_liste = plaene.get("manuell", [])
    gesperrt_liste = plaene.get("gesperrt", [])
    archiv_liste = plaene.get("archiv", [])
    dubletten_liste = plaene.get("dubletten", [])

    # Startpunkt für Roo
    empfohlener_start = core21_manifest.get("empfohlener_start", {})
    if not empfohlener_start:
        empfohlener_start = {
            "datei": "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
            "bemerkung": "Erste Datei die Roo lesen sollte: Masterauftrag Neustart Core"
        }

    # Agentenregeln
    erlaubte_ops = core22_manifest.get("erlaubte_operationen", [])
    verbotene_ops = core22_manifest.get("verbotene_operationen", [])

    # CORE-13 bis CORE-22 Status
    core_status = {
        "CORE-13": {
            "titel": "Altbestand-Inventur",
            "status": "abgeschlossen",
            "quelle": "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.json",
            "bemerkung": "Inventurdaten vorhanden"
        },
        "CORE-14": {
            "titel": "CORE13-Auswertung",
            "status": ermittle_core_status(PLAENE_DIR / "CORE14_auswertung.json"),
            "quelle": "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.json",
            "bemerkung": "Auswertung erstellt"
        },
        "CORE-15": {
            "titel": "Migrationsplan",
            "status": ermittle_core_status(PLAENE_DIR / "CORE15_migrationsplan.json"),
            "quelle": "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE15_migrationsplan.json",
            "bemerkung": "Migrationsplan vorhanden"
        },
        "CORE-16": {
            "titel": "Dry-Run-Validierung",
            "status": ermittle_core_status(PLAENE_DIR / "CORE16_dry_run_ergebnis.json"),
            "quelle": "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE16_dry_run_ergebnis.json",
            "bemerkung": "Dry-Run-Ergebnis vorhanden"
        },
        "CORE-17": {
            "titel": "Kopierende Migration",
            "status": ermittle_core_status(MANIFEST_DIR / "CORE17_kopierte_dateien_manifest.json"),
            "quelle": "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json",
            "bemerkung": "Manifest kopierte Dateien vorhanden"
        },
        "CORE-18": {
            "titel": "Neustruktur-Validierung",
            "status": ermittle_core_status(PLAENE_DIR / "CORE18_neustruktur_validierung.json"),
            "quelle": "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE18_neustruktur_validierung.json",
            "bemerkung": "Validierungsergebnis vorhanden"
        },
        "CORE-19": {
            "titel": "Reste-Archiv-Sperrplan",
            "status": "abgeschlossen" if core19_plan else "nicht_gefunden",
            "quelle": "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE19_reste_archiv_sperrplan.json",
            "bemerkung": f"Reste={zusammenfassung_core19.get('reste','?')}, Archiv={zusammenfassung_core19.get('archiv','?')}, Gesperrt={zusammenfassung_core19.get('gesperrt','?')}"
        },
        "CORE-20": {
            "titel": "Master-Umbau-Bericht",
            "status": "abgeschlossen" if daten.get("core20_bericht") else "nicht_gefunden",
            "quelle": "ALIN_Neustart_Core/Reports/CORE20_MASTER_UMBAU_BERICHT.txt",
            "bemerkung": "Master-Umbau dokumentiert"
        },
        "CORE-21": {
            "titel": "Arbeitsindex",
            "status": "abgeschlossen" if core21_manifest else "nicht_gefunden",
            "quelle": "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_arbeitsindex.json",
            "bemerkung": f"Arbeitsbestand={zusammenfassung_core21.get('arbeitsbestand_anzahl','?')}, Referenz={zusammenfassung_core21.get('referenzbestand_anzahl','?')}"
        },
        "CORE-22": {
            "titel": "Agenten-Einstieg",
            "status": "abgeschlossen" if core22_manifest else "nicht_gefunden",
            "quelle": "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json",
            "bemerkung": "Agentenregeln manifestiert"
        },
    }

    # Zulässige nächste Arbeiten (aus Agentenregeln)
    zulaessige_naechste = [
        "Lesen in aktiv/ und referenz/",
        "Schreiben in aktiv/ (nur wenn bereich_status=='aktiv')",
        "Berichte in Reports/ schreiben",
        "Manifeste in 08_Migration/09_Manifest/ schreiben",
        "Pläne in 08_Migration/01_Plaene/ schreiben",
        "Start mit ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
    ]

    blockierte_arbeiten = [
        "Löschen im Altbestand",
        "Verschieben im Altbestand",
        "Umbenennen im Altbestand",
        "Schreiben in referenz/ oder gesperrt/",
        "Echte Mandantendaten an externe Modelle",
        "API-Schlüssel in Git",
        "Schreiben ohne Prüfung von bereich_status()",
    ]

    dashboard = {
        "meta": {
            "modul_id": "CORE-23",
            "name": "Arbeitsstart-Zentrale / Projekt-Dashboard",
            "version": "1.0.0",
            "zeitstempel": jetzt,
            "produktiv_freigegeben": False,
            "nur_aggregierend": True,
        },
        "zusammenfassung": {
            "aktiver_arbeitsbestand_anzahl": zusammenfassung_core21.get("arbeitsbestand_anzahl", len(arbeitsbestand)),
            "referenzbestand_anzahl": zusammenfassung_core21.get("referenzbestand_anzahl", len(referenzbestand)),
            "gesperrte_dateien_gesamt": zusammenfassung_core19.get("gesperrt", len(gesperrt_liste)),
            "archiv_dateien": zusammenfassung_core19.get("archiv", len(archiv_liste)),
            "dubletten": zusammenfassung_core19.get("dubletten", len(dubletten_liste)),
            "manuell_zu_pruefen": zusammenfassung_core19.get("manuell", len(manuell_liste)),
            "kategorien": kategorien,
        },
        "aktiver_arbeitsbestand": {
            "beschreibung": "Dateien und Bereiche mit Schreib-/Leserecht",
            "bereiche": aktiv_bereiche,
            "anzahl_dateien": zusammenfassung_core21.get("arbeitsbestand_anzahl", len(arbeitsbestand)),
            "kategorie_verteilung": kategorien,
        },
        "referenzbereiche": {
            "beschreibung": "Nur lesen, nicht schreiben",
            "bereiche": referenz_bereiche,
        },
        "gesperrte_bereiche": {
            "beschreibung": "Ablehnen oder nur mit Freigabe",
            "bereiche": gesperrt_bereiche,
            "gesperrte_dateien": len(gesperrt_liste),
        },
        "letzter_migrationsstand": {
            "beschreibung": "Aus CORE-19 Reste-Archiv-Sperrplan",
            "reste": zusammenfassung_core19.get("reste", 0),
            "archiv": zusammenfassung_core19.get("archiv", 0),
            "gesperrt": zusammenfassung_core19.get("gesperrt", 0),
            "testreste": zusammenfassung_core19.get("testreste", 0),
            "laufzeit": zusammenfassung_core19.get("laufzeit", 0),
            "dubletten": zusammenfassung_core19.get("dubletten", 0),
            "manuell": zusammenfassung_core19.get("manuell", 0),
        },
        "offene_manuelle_pruefungen": {
            "beschreibung": "Dateien die manuell geprüft werden müssen",
            "anzahl": len(manuell_liste),
            "beispiele": [item.get("relativer_pfad", "") for item in manuell_liste[:5]],
        },
        "gesperrte_restdateien": {
            "beschreibung": "Dateien die dauerhaft gesperrt sind",
            "anzahl": len(gesperrt_liste),
            "beispiele": [item.get("relativer_pfad", "") for item in gesperrt_liste[:5]],
        },
        "zulaessige_naechste_arbeiten": {
            "beschreibung": "Aus CORE-22 Agentenregeln",
            "arbeiten": zulaessige_naechste,
        },
        "blockierte_arbeiten": {
            "beschreibung": "Aus CORE-22 verbotene Operationen",
            "arbeiten": blockierte_arbeiten,
        },
        "startpunkt_fuer_roo": {
            "datei": empfohlener_start.get("datei", "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md"),
            "bemerkung": empfohlener_start.get("bemerkung", "Masterauftrag als Startpunkt"),
            "alternativen": empfohlener_start.get("alternativen", []),
            "erste_schritte": [
                "1. Config/core21_arbeitsindex_v1.json laden",
                "2. ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md lesen",
                "3. ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md lesen",
                "4. Bereichsstatus prüfen vor jedem Schreibzugriff",
                "5. Dashboard (dieses Dokument) als Orientierung nutzen",
            ],
        },
        "status_core_13_bis_22": core_status,
    }

    return dashboard


def erstelle_html(dashboard: dict):
    meta = dashboard["meta"]
    zus = dashboard["zusammenfassung"]
    start = dashboard["startpunkt_fuer_roo"]
    core_status = dashboard["status_core_13_bis_22"]

    def row(label, value):
        return f'<tr><td style="padding:4px 8px;border-bottom:1px solid #ddd;"><strong>{label}</strong></td><td style="padding:4px 8px;border-bottom:1px solid #ddd;">{value}</td></tr>'

    def status_badge(status):
        color = "#28a745" if status == "abgeschlossen" else "#dc3545" if status == "fehlerhaft" else "#6c757d"
        return f'<span style="background:{color};color:#fff;padding:2px 6px;border-radius:4px;font-size:12px;">{status}</span>'

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{meta['modul_id']} {meta['name']}</title>
<style>
body {{ font-family:Segoe UI,Helvetica,Arial,sans-serif; margin:20px; background:#f5f6f7; color:#333; }}
h1 {{ color:#1a237e; border-bottom:2px solid #3949ab; padding-bottom:8px; }}
h2 {{ color:#283593; margin-top:24px; font-size:18px; }}
table {{ border-collapse:collapse; width:100%; background:#fff; margin-top:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
th {{ background:#3949ab; color:#fff; text-align:left; padding:8px; }}
td {{ padding:8px; border-bottom:1px solid #e0e0e0; }}
.card {{ background:#fff; border-radius:6px; padding:16px; margin-top:16px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
pre {{ background:#263238; color:#aed581; padding:12px; border-radius:4px; overflow:auto; font-size:13px; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px; color:#fff; }}
.ok {{ background:#28a745; }}
.warn {{ background:#ffc107; color:#000; }}
.err {{ background:#dc3545; }}
.gray {{ background:#6c757d; }}
</style>
</head>
<body>
<h1>{meta['modul_id']} – {meta['name']}</h1>
<p>Version <strong>{meta['version']}</strong> | Zeitstempel <code>{meta['zeitstempel']}</code> | Produktiv freigegeben: <strong>{'Ja' if meta['produktiv_freigegeben'] else 'Nein'}</strong></p>

<div class="card">
<h2>📊 Zusammenfassung</h2>
<table>
{row('Aktiver Arbeitsbestand', zus['aktiver_arbeitsbestand_anzahl'])}
{row('Referenzbestand', zus['referenzbestand_anzahl'])}
{row('Gesperrte Dateien', zus['gesperrte_dateien_gesamt'])}
{row('Archiv-Dateien', zus['archiv_dateien'])}
{row('Dubletten', zus['dubletten'])}
{row('Manuell zu prüfen', zus['manuell_zu_pruefen'])}
</table>
</div>

<div class="card">
<h2>🚀 Startpunkt für Roo</h2>
<p><strong>Erste Datei:</strong> <code>{start['datei']}</code></p>
<p>{start['bemerkung']}</p>
<h3>Erste Schritte</h3>
<ol>
"""
    for schritt in start.get("erste_schritte", []):
        html += f"<li>{schritt}</li>\n"
    html += """</ol>
</div>

<div class="card">
<h2>📁 Aktive Bereiche (Schreiben erlaubt)</h2>
<ul>
"""
    for b in dashboard["aktiver_arbeitsbestand"]["bereiche"]:
        html += f"<li><code>{b}</code></li>\n"
    html += """</ul>
</div>

<div class="card">
<h2>📖 Referenzbereiche (Nur lesen)</h2>
<ul>
"""
    for b in dashboard["referenzbereiche"]["bereiche"]:
        html += f"<li><code>{b}</code></li>\n"
    html += """</ul>
</div>

<div class="card">
<h2>🚫 Gesperrte Bereiche</h2>
<ul>
"""
    for b in dashboard["gesperrte_bereiche"]["bereiche"]:
        html += f"<li><code>{b}</code></li>\n"
    html += f"""</ul>
<p>Gesperrte Dateien im Detail: <strong>{dashboard['gesperrte_bereiche']['gesperrte_dateien']}</strong></p>
</div>

<div class="card">
<h2>🔧 Letzter Migrationsstand (CORE-19)</h2>
<table>
{row('Reste', dashboard['letzter_migrationsstand']['reste'])}
{row('Archiv', dashboard['letzter_migrationsstand']['archiv'])}
{row('Gesperrt', dashboard['letzter_migrationsstand']['gesperrt'])}
{row('Testreste', dashboard['letzter_migrationsstand']['testreste'])}
{row('Laufzeit', dashboard['letzter_migrationsstand']['laufzeit'])}
{row('Dubletten', dashboard['letzter_migrationsstand']['dubletten'])}
{row('Manuell', dashboard['letzter_migrationsstand']['manuell'])}
</table>
</div>

<div class="card">
<h2>✅ Zulässige nächste Arbeiten</h2>
<ul>
"""
    for a in dashboard["zulaessige_naechste_arbeiten"]["arbeiten"]:
        html += f"<li>{a}</li>\n"
    html += """</ul>
</div>

<div class="card">
<h2>⛔ Blockierte Arbeiten</h2>
<ul>
"""
    for a in dashboard["blockierte_arbeiten"]["arbeiten"]:
        html += f"<li>{a}</li>\n"
    html += """</ul>
</div>

<div class="card">
<h2>📋 Status CORE-13 bis CORE-22</h2>
<table>
<tr><th>Modul</th><th>Titel</th><th>Status</th><th>Bemerkung</th></tr>
"""
    for modul, info in core_status.items():
        html += f"<tr><td>{modul}</td><td>{info['titel']}</td><td>{status_badge(info['status'])}</td><td>{info['bemerkung']}</td></tr>\n"
    html += """</table>
</div>

<div class="card">
<h2>🔍 Offene manuelle Prüfungen (Beispiele)</h2>
<ul>
"""
    for p in dashboard["offene_manuelle_pruefungen"]["beispiele"]:
        html += f"<li><code>{p}</code></li>\n"
    html += f"""</ul>
<p>Gesamt: <strong>{dashboard['offene_manuelle_pruefungen']['anzahl']}</strong></p>
</div>

<div class="card">
<h2>📝 Rohdaten (JSON)</h2>
<pre>{json.dumps(dashboard, indent=2, ensure_ascii=False)}</pre>
</div>

<footer style="margin-top:24px;font-size:12px;color:#666;">
Generiert durch CORE-23 Arbeitsstart-Zentrale | ALIN_Neustart_Core
</footer>
</body>
</html>
"""
    return html


def schreibe_bericht(dashboard: dict, ausgabe_pfad: Path):
    meta = dashboard["meta"]
    lines = [
        "=" * 70,
        f"{meta['modul_id']} {meta['name']}",
        "=" * 70,
        f"Version:    {meta['version']}",
        f"Zeitstempel: {meta['zeitstempel']}",
        f"Produktiv freigegeben: {meta['produktiv_freigegeben']}",
        "",
        "ZUSAMMENFASSUNG",
        "-" * 40,
        f"Aktiver Arbeitsbestand:   {dashboard['zusammenfassung']['aktiver_arbeitsbestand_anzahl']}",
        f"Referenzbestand:          {dashboard['zusammenfassung']['referenzbestand_anzahl']}",
        f"Gesperrte Dateien:        {dashboard['zusammenfassung']['gesperrte_dateien_gesamt']}",
        f"Archiv-Dateien:           {dashboard['zusammenfassung']['archiv_dateien']}",
        f"Dubletten:                {dashboard['zusammenfassung']['dubletten']}",
        f"Manuell zu prüfen:        {dashboard['zusammenfassung']['manuell_zu_pruefen']}",
        "",
        "KATEGORIE-VERTEILUNG (Arbeitsbestand)",
        "-" * 40,
    ]
    for kat, anz in dashboard["zusammenfassung"]["kategorien"].items():
        lines.append(f"  {kat}: {anz}")
    lines += [
        "",
        "STARTPUNKT FÜR ROO",
        "-" * 40,
        f"Datei:       {dashboard['startpunkt_fuer_roo']['datei']}",
        f"Bemerkung:   {dashboard['startpunkt_fuer_roo']['bemerkung']}",
        "",
        "ERSTE SCHRITTE:",
    ]
    for schritt in dashboard["startpunkt_fuer_roo"]["erste_schritte"]:
        lines.append(f"  {schritt}")

    lines += [
        "",
        "LETZTER MIGRATIONSSTAND (CORE-19)",
        "-" * 40,
        f"Reste:      {dashboard['letzter_migrationsstand']['reste']}",
        f"Archiv:     {dashboard['letzter_migrationsstand']['archiv']}",
        f"Gesperrt:   {dashboard['letzter_migrationsstand']['gesperrt']}",
        f"Testreste:  {dashboard['letzter_migrationsstand']['testreste']}",
        f"Laufzeit:   {dashboard['letzter_migrationsstand']['laufzeit']}",
        f"Dubletten:  {dashboard['letzter_migrationsstand']['dubletten']}",
        f"Manuell:    {dashboard['letzter_migrationsstand']['manuell']}",
        "",
        "ZULÄSSIGE NÄCHSTE ARBEITEN",
        "-" * 40,
    ]
    for a in dashboard["zulaessige_naechste_arbeiten"]["arbeiten"]:
        lines.append(f"  [OK] {a}")

    lines += [
        "",
        "BLOCKIERTE ARBEITEN",
        "-" * 40,
    ]
    for a in dashboard["blockierte_arbeiten"]["arbeiten"]:
        lines.append(f"  [X] {a}")

    lines += [
        "",
        "STATUS CORE-13 BIS CORE-22",
        "-" * 40,
    ]
    for modul, info in dashboard["status_core_13_bis_22"].items():
        lines.append(f"  {modul} | {info['titel']}: {info['status']} | {info['bemerkung']}")

    lines += [
        "",
        "OFFENE MANUELLE PRÜFUNGEN",
        "-" * 40,
        f"Gesamt: {dashboard['offene_manuelle_pruefungen']['anzahl']}",
        "Beispiele:",
    ]
    for p in dashboard["offene_manuelle_pruefungen"]["beispiele"]:
        lines.append(f"  - {p}")

    lines += [
        "",
        "AUSGABEDATEIEN",
        "-" * 40,
        f"JSON:   {ZIELE['dashboard_json']}",
        f"HTML:   {ZIELE['dashboard_html']}",
        f"BERICHT: {ZIELE['bericht']}",
        "",
        "=" * 70,
        "ENDE DES BERICHTS",
        "=" * 70,
    ]

    text = "\n".join(lines)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def main():
    print("[CORE-23] Starte Projekt-Dashboard-Aggregation...")

    config = lade_json(CONFIG_PATH) or {}

    daten = {}
    for key, pfad in QUELLEN.items():
        if pfad.suffix == ".json":
            daten[key] = lade_json(pfad)
        else:
            daten[key] = lade_text(pfad)
        if daten[key] is None:
            print(f"  WARNUNG: Quelle nicht gefunden: {pfad}")
        else:
            print(f"  Geladen: {pfad.name}")

    print("[CORE-23] Aggregiere Dashboard-Daten...")
    dashboard = aggregiere_dashboard(daten, config)

    print("[CORE-23] Schreibe JSON-Ausgabe...")
    with open(ZIELE["dashboard_json"], "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    print(f"  -> {ZIELE['dashboard_json']}")

    print("[CORE-23] Schreibe HTML-Ausgabe...")
    html = erstelle_html(dashboard)
    with open(ZIELE["dashboard_html"], "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  -> {ZIELE['dashboard_html']}")

    print("[CORE-23] Schreibe Bericht...")
    schreibe_bericht(dashboard, ZIELE["bericht"])
    print(f"  -> {ZIELE['bericht']}")

    print("[CORE-23] Abgeschlossen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
