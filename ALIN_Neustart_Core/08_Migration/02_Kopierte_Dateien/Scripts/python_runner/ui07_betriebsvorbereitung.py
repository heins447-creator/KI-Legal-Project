#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI07 – Betriebsvorbereitung ohne Produktivfreigabe
Prüft Start-/Ordnerstruktur, Register, Sperrregister, Healthcheck.
Erzeugt Prüfstartseite mit rotem Rahmen: KEINE PRODUKTIVFREIGABE.
"""

import json, os, sys, datetime, pathlib

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dirs(cfg):
    for key, rel in cfg.get("verzeichnisse", {}).items():
        os.makedirs(rel, exist_ok=True)

def pruefe_verzeichnisse(cfg):
    global FEHLER, WARNUNGEN
    ergebnis = []
    for name, rel in cfg.get("verzeichnisse", {}).items():
        exists = os.path.isdir(rel)
        status = "OK" if exists else "ERSTELLT"
        if not exists:
            os.makedirs(rel, exist_ok=True)
        ergebnis.append({"name": name, "pfad": rel, "status": status, "exists": exists})
    return ergebnis

def pruefe_register(cfg):
    global FEHLER, WARNUNGEN
    ergebnis = []
    reg_cfg = cfg.get("register_pruefung", {})
    base = reg_cfg.get("pfad", "ALIN_Neustart_Core/01_Register")
    for datei in reg_cfg.get("erforderlich", []):
        pfad = os.path.join(base, datei)
        exists = os.path.isfile(pfad)
        try:
            if exists:
                load_json(pfad)
                valid = True
            else:
                valid = False
        except Exception:
            valid = False
        status = "OK" if (exists and valid) else "FEHLER"
        if not (exists and valid):
            FEHLER += 1
        ergebnis.append({"datei": datei, "pfad": pfad, "exists": exists, "valid": valid, "status": status})
    return ergebnis

def pruefe_sperrregister(cfg):
    global FEHLER, WARNUNGEN
    sperr = cfg.get("sperrregister_pruefung", {})
    pfad = sperr.get("pfad", "ALIN_Neustart_Core/01_Register/sperrregister.json")
    if not os.path.isfile(pfad):
        FEHLER += 1
        return {"status": "FEHLER", "grund": "Datei nicht gefunden", "kritisch": True}
    try:
        data = load_json(pfad)
        eintraege = data.get("eintraege", [])
        kritisch = [e for e in eintraege if e.get("kritisch", False)]
        blockierend = [e for e in eintraege if e.get("blockierend", False)]
        return {
            "status": "OK",
            "anzahl_eintraege": len(eintraege),
            "kritisch": len(kritisch),
            "blockierend": len(blockierend),
            "kritische_eintraege": [e.get("modul_id", "?") for e in kritisch],
            "blockierende_eintraege": [e.get("modul_id", "?") for e in blockierend]
        }
    except Exception as e:
        FEHLER += 1
        return {"status": "FEHLER", "grund": str(e), "kritisch": True}

def healthcheck_dateien(cfg):
    global FEHLER, WARNUNGEN
    ergebnis = []
    hc = cfg.get("healthcheck", {})
    for kategorie, dateien in [
        ("Register", hc.get("pruefe_register", [])),
        ("Schnittstellen", hc.get("pruefe_schnittstellen", [])),
        ("Statusmodelle", hc.get("pruefe_statusmodelle", []))
    ]:
        for pfad in dateien:
            exists = os.path.isfile(pfad)
            try:
                if exists:
                    load_json(pfad)
                    valid = True
                else:
                    valid = False
            except Exception:
                valid = False
            status = "OK" if (exists and valid) else "FEHLER"
            if not (exists and valid):
                FEHLER += 1
            ergebnis.append({"kategorie": kategorie, "pfad": pfad, "status": status})
    return ergebnis

def pruefe_ui_module(cfg):
    global FEHLER, WARNUNGEN
    module = cfg.get("startseite", {}).get("anzeige_module", [])
    ergebnis = []
    for mod in module:
        # Prüfe, ob zugehörige Config existiert
        config_pattern = f"Config/ui{mod.lower().replace('-', '_')}_*"
        import glob
        configs = glob.glob(config_pattern) + glob.glob(f"Config/ui{mod.lower().replace('-', '')}_*")
        # Prüfe, ob Runner existiert
        runner_pattern = f"Scripts/python_runner/ui{mod.lower().replace('-', '_')}_*.py"
        runners = glob.glob(runner_pattern) + glob.glob(f"Scripts/python_runner/ui{mod.lower().replace('-', '')}_*.py")
        status = "OK" if (configs or runners) else "WARNUNG"
        if not (configs or runners):
            WARNUNGEN += 1
        ergebnis.append({
            "modul": mod,
            "config_gefunden": len(configs) > 0,
            "runner_gefunden": len(runners) > 0,
            "status": status
        })
    return ergebnis

def generiere_status_json(ergebnisse, cfg):
    status = {
        "modul_id": "UI07",
        "modulname": "Betriebsvorbereitung",
        "version": cfg.get("version", "1.0.0"),
        "version_status": cfg.get("version_status", "vorbereitung"),
        "produktiv_freigegeben": False,
        "timestamp": datetime.datetime.now().isoformat(),
        "betriebsmodus": cfg.get("betriebsmodus", "vorbereitung"),
        "warnung": cfg.get("warnung_roter_rahmen", ""),
        "verzeichnisse": ergebnisse.get("verzeichnisse", []),
        "register": ergebnisse.get("register", []),
        "sperrregister": ergebnisse.get("sperrregister", {}),
        "healthcheck": ergebnisse.get("healthcheck", []),
        "ui_module": ergebnisse.get("ui_module", []),
        "fehler": FEHLER,
        "warnungen": WARNUNGEN,
        "gesamtstatus": "FEHLER" if FEHLER > 0 else ("WARNUNG" if WARNUNGEN > 0 else "OK")
    }
    return status

def generiere_html(ergebnisse, cfg, status_json):
    warnung = cfg.get("warnung_roter_rahmen", "")
    demo = cfg.get("demo_modus", {})
    backup = cfg.get("backup", {})

    def row(label, value, cls=""):
        return f'<tr><td style="padding:6px 12px;border-bottom:1px solid #e5e7eb;font-weight:500;">{label}</td><td style="padding:6px 12px;border-bottom:1px solid #e5e7eb;{cls}">{value}</td></tr>'

    def badge(text, color):
        return f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:0.8rem;font-weight:600;">{text}</span>'

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{cfg["startseite"]["titel"]}</title>
<style>
:root {{ --bg:#f3f4f6; --card:#fff; --text:#111827; --text-secondary:#6b7280; --border:#e5e7eb; --ok:#16a34a; --warn:#ca8a04; --err:#dc2626; --accent:#2563eb; }}
body {{ font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); margin:0; padding:20px; }}
.container {{ max-width:960px; margin:0 auto; }}
.roter-rahmen {{ border:4px solid #dc2626; border-radius:12px; padding:20px; background:#fef2f2; margin-bottom:24px; }}
.roter-rahmen h1 {{ color:#991b1b; margin:0 0 8px; font-size:1.6rem; }}
.roter-rahmen p {{ color:#7f1d1d; margin:0; font-size:1rem; }}
.panel {{ background:var(--card); border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:20px; overflow:hidden; }}
.panel-header {{ background:#f9fafb; padding:14px 20px; border-bottom:1px solid var(--border); font-weight:600; font-size:1.05rem; }}
.panel-body {{ padding:16px 20px; }}
table {{ width:100%; border-collapse:collapse; font-size:0.9rem; }}
th {{ text-align:left; padding:8px 12px; background:#f9fafb; border-bottom:2px solid var(--border); font-weight:600; }}
td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
.status-ok {{ color:var(--ok); font-weight:600; }}
.status-warn {{ color:var(--warn); font-weight:600; }}
.status-err {{ color:var(--err); font-weight:600; }}
.footer {{ text-align:center; color:var(--text-secondary); font-size:0.8rem; margin-top:24px; padding:16px; }}
.modul-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }}
.modul-karte {{ border:1px solid var(--border); border-radius:8px; padding:12px; background:#f9fafb; }}
.modul-karte.ok {{ border-left:4px solid var(--ok); }}
.modul-karte.warn {{ border-left:4px solid var(--warn); }}
.modul-karte.err {{ border-left:4px solid var(--err); }}
</style>
</head>
<body>
<div class="container">

<div class="roter-rahmen">
<h1>⚠️ {cfg["startseite"]["titel"]}</h1>
<p><strong>{warnung}</strong></p>
</div>

<div class="panel">
<div class="panel-header">Betriebsstatus</div>
<div class="panel-body">
<table>
{row("Betriebsmodus", cfg.get("betriebsmodus","vorbereitung").upper(), "font-weight:700;color:#2563eb;")}
{row("Produktiv freigegeben", "NEIN", "font-weight:700;color:#dc2626;")}
{row("Version", cfg.get("version","1.0.0"))}
{row("Version-Status", cfg.get("version_status","vorbereitung"))}
{row("Gesamtstatus", badge(status_json["gesamtstatus"], "#16a34a" if status_json["gesamtstatus"]=="OK" else ("#ca8a04" if status_json["gesamtstatus"]=="WARNUNG" else "#dc2626")), "font-weight:700;")}
{row("Fehler", str(FEHLER), "color:#dc2626;font-weight:600;" if FEHLER>0 else "")}
{row("Warnungen", str(WARNUNGEN), "color:#ca8a04;font-weight:600;" if WARNUNGEN>0 else "")}
</table>
</div>
</div>

<div class="panel">
<div class="panel-header">Verzeichnisstruktur</div>
<div class="panel-body">
<table>
<tr><th>Verzeichnis</th><th>Pfad</th><th>Status</th></tr>
"""
    for v in ergebnisse.get("verzeichnisse", []):
        cls = "status-ok" if v["status"] == "OK" else "status-warn"
        html += f'<tr><td>{v["name"]}</td><td>{v["pfad"]}</td><td class="{cls}">{v["status"]}</td></tr>\n'
    html += """</table></div></div>

<div class="panel">
<div class="panel-header">Register-Prüfung</div>
<div class="panel-body">
<table>
<tr><th>Datei</th><th>Gefunden</th><th>Valide</th><th>Status</th></tr>
"""
    for r in ergebnisse.get("register", []):
        cls = "status-ok" if r["status"] == "OK" else "status-err"
        html += f'<tr><td>{r["datei"]}</td><td>{"Ja" if r["exists"] else "Nein"}</td><td>{"Ja" if r["valid"] else "Nein"}</td><td class="{cls}">{r["status"]}</td></tr>\n'
    html += """</table></div></div>

<div class="panel">
<div class="panel-header">Sperrregister-Prüfung</div>
<div class="panel-body">
"""
    sperr = ergebnisse.get("sperrregister", {})
    if sperr.get("status") == "OK":
        html += f'<p><strong>Status:</strong> <span class="status-ok">OK</span></p>\n'
        html += f'<p>Einträge gesamt: {sperr.get("anzahl_eintraege",0)} | Kritisch: {sperr.get("kritisch",0)} | Blockierend: {sperr.get("blockierend",0)}</p>\n'
        if sperr.get("kritische_eintraege"):
            html += f'<p style="color:#dc2626;font-size:0.85rem;">Kritische Module: {", ".join(sperr["kritische_eintraege"])}</p>\n'
    else:
        html += f'<p><strong>Status:</strong> <span class="status-err">{sperr.get("status","FEHLER")}</span></p>\n'
        html += f'<p style="color:#dc2626;">{sperr.get("grund","")}</p>\n'
    html += """</div></div>

<div class="panel">
<div class="panel-header">Healthcheck – Kritische Dateien</div>
<div class="panel-body">
<table>
<tr><th>Kategorie</th><th>Datei</th><th>Status</th></tr>
"""
    for h in ergebnisse.get("healthcheck", []):
        cls = "status-ok" if h["status"] == "OK" else "status-err"
        html += f'<tr><td>{h["kategorie"]}</td><td>{h["pfad"]}</td><td class="{cls}">{h["status"]}</td></tr>\n'
    html += """</table></div></div>

<div class="panel">
<div class="panel-header">UI-Module Übersicht</div>
<div class="panel-body">
<div class="modul-grid">
"""
    for m in ergebnisse.get("ui_module", []):
        kls = "ok" if m["status"] == "OK" else "warn"
        html += f'<div class="modul-karte {kls}"><strong>{m["modul"]}</strong><br><span style="font-size:0.8rem;color:var(--text-secondary);">Config: {"Ja" if m["config_gefunden"] else "Nein"} | Runner: {"Ja" if m["runner_gefunden"] else "Nein"}</span></div>\n'
    html += f"""</div></div></div>

<div class="panel">
<div class="panel-header">Backup-Hinweis</div>
<div class="panel-body">
<p><strong>Letztes Backup:</strong> {backup.get("letztes_backup_datum") or "Kein Backup vorhanden"}</p>
<p><strong>Empfohlene Häufigkeit:</strong> {backup.get("empfohlene_haeufigkeit","taeglich")}</p>
<p><strong>Backup-Verzeichnis:</strong> {backup.get("backup_verzeichnis","Windows_App/Backup")}</p>
<p style="color:#dc2626;font-size:0.85rem;margin-top:8px;">⚠️ Vor Inbetriebnahme ein Backup erstellen. Dies ist eine Vorbereitung, keine Produktivfreigabe.</p>
</div>
</div>

<div class="panel">
<div class="panel-header">Demo-Modus Einschränkungen</div>
<div class="panel-body">
<table>
{row("Max. Dokumente", str(demo.get("max_dokumente",3)))}
{row("Nur Musterdaten", "Ja" if demo.get("nur_musterdaten",True) else "Nein")}
{row("Echte Daten erlaubt", "Nein" if not demo.get("echte_daten_erlaubt",False) else "Ja", "color:#dc2626;font-weight:600;")}
{row("Wasserzeichen", demo.get("wasserzeichen","DEMO"))}
</table>
</div>
</div>

<div class="footer">
KI Legal – UI07 Betriebsvorbereitung | Version {cfg.get("version","1.0.0")} | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
Dies ist eine Vorbereitung. Keine Produktivfreigabe. Keine echten Mandantendaten.
</div>

</div>
</body>
</html>"""
    return html

def schreibe_bericht(ergebnisse, cfg):
    lines = []
    lines.append("=" * 60)
    lines.append("UI07 BETRIEBSVORBEREITUNG BERICHT")
    lines.append("=" * 60)
    lines.append(f"Zeitstempel: {datetime.datetime.now().isoformat()}")
    lines.append(f"Betriebsmodus: {cfg.get('betriebsmodus','vorbereitung').upper()}")
    lines.append(f"Produktiv freigegeben: NEIN")
    lines.append(f"Version: {cfg.get('version','1.0.0')}")
    lines.append("")
    lines.append("WARNUNG: " + cfg.get("warnung_roter_rahmen",""))
    lines.append("")
    lines.append("-" * 40)
    lines.append("VERZEICHNISSE")
    lines.append("-" * 40)
    for v in ergebnisse.get("verzeichnisse", []):
        lines.append(f"  [{v['status']}] {v['name']}: {v['pfad']}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("REGISTER")
    lines.append("-" * 40)
    for r in ergebnisse.get("register", []):
        lines.append(f"  [{r['status']}] {r['datei']} (gefunden={r['exists']}, valide={r['valid']})")
    lines.append("")
    lines.append("-" * 40)
    lines.append("SPERRREGISTER")
    lines.append("-" * 40)
    sperr = ergebnisse.get("sperrregister", {})
    lines.append(f"  Status: {sperr.get('status','UNBEKANNT')}")
    if sperr.get("status") == "OK":
        lines.append(f"  Einträge: {sperr.get('anzahl_eintraege',0)}")
        lines.append(f"  Kritisch: {sperr.get('kritisch',0)}")
        lines.append(f"  Blockierend: {sperr.get('blockierend',0)}")
    else:
        lines.append(f"  Grund: {sperr.get('grund','')}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("HEALTHCHECK")
    lines.append("-" * 40)
    for h in ergebnisse.get("healthcheck", []):
        lines.append(f"  [{h['status']}] {h['kategorie']}: {h['pfad']}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("UI-MODULE")
    lines.append("-" * 40)
    for m in ergebnisse.get("ui_module", []):
        lines.append(f"  [{m['status']}] {m['modul']} (Config={'Ja' if m['config_gefunden'] else 'Nein'}, Runner={'Ja' if m['runner_gefunden'] else 'Nein'})")
    lines.append("")
    lines.append("-" * 40)
    lines.append("ZUSAMMENFASSUNG")
    lines.append("-" * 40)
    lines.append(f"Fehler: {FEHLER}")
    lines.append(f"Warnungen: {WARNUNGEN}")
    gesamt = "FEHLER" if FEHLER > 0 else ("WARNUNG" if WARNUNGEN > 0 else "OK")
    lines.append(f"Gesamtstatus: {gesamt}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("ENDE BERICHT")
    lines.append("=" * 60)
    return "\n".join(lines)

def hauptlauf():
    global FEHLER, WARNUNGEN
    cfg = load_json("Config/ui07_betriebsvorbereitung_v1.json")
    ensure_dirs(cfg)

    print("UI07 Betriebsvorbereitung – Start")
    print("=" * 50)
    print("WARNUNG:", cfg.get("warnung_roter_rahmen", ""))
    print("=" * 50)

    ergebnisse = {}

    print("\n[1/5] Verzeichnisstruktur prüfen...")
    ergebnisse["verzeichnisse"] = pruefe_verzeichnisse(cfg)
    print(f"      {len(ergebnisse['verzeichnisse'])} Verzeichnisse geprüft.")

    print("\n[2/5] Register-Prüfung...")
    ergebnisse["register"] = pruefe_register(cfg)
    ok_reg = sum(1 for r in ergebnisse["register"] if r["status"] == "OK")
    print(f"      {ok_reg}/{len(ergebnisse['register'])} Register OK.")

    print("\n[3/5] Sperrregister-Prüfung...")
    ergebnisse["sperrregister"] = pruefe_sperrregister(cfg)
    print(f"      Status: {ergebnisse['sperrregister'].get('status','FEHLER')}")

    print("\n[4/5] Healthcheck...")
    ergebnisse["healthcheck"] = healthcheck_dateien(cfg)
    ok_hc = sum(1 for h in ergebnisse["healthcheck"] if h["status"] == "OK")
    print(f"      {ok_hc}/{len(ergebnisse['healthcheck'])} Dateien OK.")

    print("\n[5/5] UI-Module prüfen...")
    ergebnisse["ui_module"] = pruefe_ui_module(cfg)
    ok_mod = sum(1 for m in ergebnisse["ui_module"] if m["status"] == "OK")
    print(f"      {ok_mod}/{len(ergebnisse['ui_module'])} Module OK.")

    status_json = generiere_status_json(ergebnisse, cfg)

    # JSON schreiben
    json_pfad = cfg["ausgabe"]["json_status"]
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(status_json, f, ensure_ascii=False, indent=2)
    print(f"\nStatus-JSON geschrieben: {json_pfad}")

    # HTML schreiben
    html_pfad = cfg["ausgabe"]["html_pruefstartseite"]
    os.makedirs(os.path.dirname(html_pfad), exist_ok=True)
    html = generiere_html(ergebnisse, cfg, status_json)
    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Prüfstartseite geschrieben: {html_pfad}")

    # Bericht schreiben
    bericht_pfad = cfg["ausgabe"]["bericht"]
    bericht = schreibe_bericht(ergebnisse, cfg)
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write(bericht)
    print(f"Bericht geschrieben: {bericht_pfad}")

    print("\n" + "=" * 50)
    gesamt = status_json["gesamtstatus"]
    print(f"GESAMTSTATUS: {gesamt}")
    print(f"Fehler: {FEHLER} | Warnungen: {WARNUNGEN}")
    print("=" * 50)
    print("\nHINWEIS: Dies ist eine Vorbereitung. Keine Produktivfreigabe.")
    return FEHLER == 0

def selbsttest():
    global FEHLER, WARNUNGEN
    FEHLER = 0; WARNUNGEN = 0
    def t(bez, bed):
        global FEHLER
        if not bed:
            FEHLER += 1
            print(f"  [FAIL] {bez}")
        else:
            print(f"  [OK]   {bez}")
    print("UI07 SELBSTTEST =====================================")
    cfg = load_json("Config/ui07_betriebsvorbereitung_v1.json")
    t("Config geladen", cfg["modul_id"] == "UI07")
    t("Betriebsmodus ist vorbereitung", cfg.get("betriebsmodus") == "vorbereitung")
    t("produktiv_freigegeben ist False", cfg.get("produktiv_freigegeben") is False)
    t("Warnung vorhanden", len(cfg.get("warnung_roter_rahmen","")) > 0)
    t("Verzeichnisse definiert", len(cfg.get("verzeichnisse",{})) > 0)
    t("Register-Prüfung konfiguriert", len(cfg.get("register_pruefung",{}).get("erforderlich",[])) > 0)
    t("Sperrregister-Prüfung aktiv", cfg.get("sperrregister_pruefung",{}).get("aktiv") is True)
    t("Demo-Modus nur Musterdaten", cfg.get("demo_modus",{}).get("nur_musterdaten") is True)
    t("Echte Daten nicht erlaubt", cfg.get("demo_modus",{}).get("echte_daten_erlaubt") is False)
    t("Ausgabepfade definiert", "html_pruefstartseite" in cfg.get("ausgabe",{}))
    print(f"\nSelbsttest: {'OK' if FEHLER==0 else 'FEHLER'} ({FEHLER} Fehler)")
    return FEHLER == 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    ok = hauptlauf()
    sys.exit(0 if ok else 1)
