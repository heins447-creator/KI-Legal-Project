#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI08 – Posteingang / Importstrecke – Visuelle Arbeitsübersicht
Liest bestehende Posteingang-Infrastruktur (DuckDB, JSON, CSV) ein
und erzeugt eine HTML-Übersicht über alle 7 Posteingangsbereiche.
KEINE neue Fachlogik. Nur Visualisierung der bestehenden Daten.
"""

import json, os, sys, datetime, glob, csv
from pathlib import Path

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dirs(cfg):
    for key in ["html_posteingang_uebersicht", "json_status", "bericht"]:
        rel = cfg.get("ausgabe", {}).get(key, "")
        if rel:
            d = os.path.dirname(rel)
            if d:
                os.makedirs(d, exist_ok=True)

def pruefe_sperrregister(cfg):
    global FEHLER, WARNUNGEN
    sperr = cfg.get("sperrregister_pruefung", {})
    if not sperr.get("aktiv", False):
        return {"status": "INAKTIV"}
    pfad = sperr.get("pfad", "")
    if not os.path.isfile(pfad):
        WARNUNGEN += 1
        return {"status": "WARNUNG", "grund": "Sperrregister nicht gefunden"}
    try:
        data = load_json(pfad)
        eintraege = data.get("eintraege", [])
        blockierend = [e for e in eintraege if e.get("blockierend", False)]
        if blockierend:
            FEHLER += 1
            return {"status": "BLOCKIERT", "blockierende_eintraege": [e.get("modul_id", "?") for e in blockierend]}
        return {"status": "OK", "anzahl": len(eintraege)}
    except Exception as e:
        WARNUNGEN += 1
        return {"status": "WARNUNG", "grund": str(e)}

def lese_duckdb_tabellen(db_pfad, tabellen):
    """Liest Daten aus DuckDB-Tabellen."""
    ergebnis = {}
    try:
        import duckdb
        con = duckdb.connect(str(db_pfad))
        for tabelle in tabellen:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {tabelle}").fetchone()[0]
                # Lese nur erste 10 Zeilen für die Übersicht
                rows = con.execute(f"SELECT * FROM {tabelle} LIMIT 10").fetchall()
                cols = [desc[0] for desc in con.execute(f"SELECT * FROM {tabelle} LIMIT 0").description]
                ergebnis[tabelle] = {
                    "count": count,
                    "zeilen": [dict(zip(cols, row)) for row in rows]
                }
            except Exception as e:
                ergebnis[tabelle] = {"count": 0, "fehler": str(e)}
        con.close()
    except ImportError:
        for tabelle in tabellen:
            ergebnis[tabelle] = {"count": 0, "fehler": "duckdb nicht verfügbar"}
    except Exception as e:
        for tabelle in tabellen:
            ergebnis[tabelle] = {"count": 0, "fehler": str(e)}
    return ergebnis

def lese_json_karten(patterns, max_pro_bereich=10):
    """Liest JSON-Karten aus dem Dateisystem."""
    ergebnis = []
    for pattern in patterns:
        for pfad in glob.glob(pattern, recursive=True)[:max_pro_bereich]:
            try:
                data = load_json(pfad)
                data["_pfad"] = pfad
                data["_filename"] = os.path.basename(pfad)
                ergebnis.append(data)
            except Exception:
                pass
    return ergebnis

def lese_csv_listen(patterns, max_pro_bereich=5):
    """Liest CSV-Listen aus dem Dateisystem."""
    ergebnis = []
    for pattern in patterns:
        for pfad in glob.glob(pattern, recursive=True)[:max_pro_bereich]:
            try:
                with open(pfad, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f, delimiter=";")
                    rows = list(reader)[:5]  # Nur erste 5 Zeilen
                    ergebnis.append({"pfad": pfad, "filename": os.path.basename(pfad), "zeilen": rows})
            except Exception:
                pass
    return ergebnis

def sammle_bereichsdaten(bereich, cfg):
    """Sammelt alle Daten für einen Bereich."""
    db_pfad = cfg.get("abhaengigkeiten", {}).get("datenbank", "Database/Legal_Brain.duckdb")
    db_tabellen = bereich.get("db_tabellen", [])
    json_patterns = bereich.get("json_patterns", [])
    
    db_daten = lese_duckdb_tabellen(db_pfad, db_tabellen) if db_tabellen else {}
    json_daten = lese_json_karten(json_patterns)
    csv_daten = lese_csv_listen([p.replace(".json", ".csv") for p in json_patterns])
    
    return {
        "db": db_daten,
        "json": json_daten,
        "csv": csv_daten,
        "gesamt_dokumente": len(json_daten) + sum(d.get("count", 0) for d in db_daten.values())
    }

def generiere_status_json(ergebnisse, cfg, sperrregister):
    bereiche = ergebnisse.get("bereiche", {})
    gesamt_dokumente = sum(b.get("gesamt_dokumente", 0) for b in bereiche.values())
    return {
        "modul_id": "UI08",
        "modulname": "Posteingang / Importstrecke",
        "version": cfg.get("version", "1.0.0"),
        "version_status": cfg.get("version_status", "entwicklung"),
        "produktiv_freigegeben": False,
        "timestamp": datetime.datetime.now().isoformat(),
        "betriebsmodus": cfg.get("betriebsmodus", "demo"),
        "sperrregister": sperrregister,
        "bereiche": {bid: {"name": b["name"], "dokumente": b.get("gesamt_dokumente", 0)} for bid, b in bereiche.items()},
        "gesamt_dokumente": gesamt_dokumente,
        "fehler": FEHLER,
        "warnungen": WARNUNGEN,
        "gesamtstatus": "FEHLER" if FEHLER > 0 else ("WARNUNG" if WARNUNGEN > 0 else "OK")
    }

def generiere_html(ergebnisse, cfg, status_json):
    def badge(text, color):
        return f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:0.75rem;font-weight:600;">{text}</span>'

    bereiche = ergebnisse.get("bereiche", {})
    demo = cfg.get("demo_modus", {})
    warnung = cfg.get("warnung", "")
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI08 – Posteingang / Importstrecke</title>
<style>
:root {{ --bg:#f3f4f6; --card:#fff; --text:#111827; --text-secondary:#6b7280; --border:#e5e7eb; --ok:#16a34a; --warn:#ca8a04; --err:#dc2626; }}
body {{ font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); margin:0; padding:20px; }}
.container {{ max-width:1200px; margin:0 auto; }}
.demo-banner {{ border:3px solid #ca8a04; border-radius:10px; padding:16px; background:#fffbeb; margin-bottom:20px; }}
.demo-banner h1 {{ color:#92400e; margin:0 0 6px; font-size:1.4rem; }}
.demo-banner p {{ color:#78350f; margin:0; font-size:0.9rem; }}
.panel {{ background:var(--card); border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:16px; overflow:hidden; }}
.panel-header {{ padding:12px 16px; border-bottom:1px solid var(--border); font-weight:600; font-size:1rem; color:#fff; }}
.panel-body {{ padding:14px 16px; }}
.bereich-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; margin-bottom:20px; }}
.bereich-karte {{ background:var(--card); border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); overflow:hidden; }}
.bereich-karte-header {{ padding:12px 16px; color:#fff; font-weight:600; font-size:0.95rem; }}
.bereich-karte-body {{ padding:12px 16px; }}
.stat {{ display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #f3f4f6; font-size:0.85rem; }}
.stat:last-child {{ border-bottom:none; }}
.json-list {{ font-size:0.8rem; color:var(--text-secondary); max-height:120px; overflow-y:auto; }}
.json-item {{ padding:3px 0; border-bottom:1px solid #f3f4f6; }}
.footer {{ text-align:center; color:var(--text-secondary); font-size:0.8rem; margin-top:20px; padding:14px; }}
.status-ok {{ color:var(--ok); font-weight:600; }}
.status-warn {{ color:var(--warn); font-weight:600; }}
.status-err {{ color:var(--err); font-weight:600; }}
</style>
</head>
<body>
<div class="container">

<div class="demo-banner">
<h1>📥 UI08 – Posteingang / Importstrecke</h1>
<p><strong>{warnung}</strong></p>
</div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Gesamtstatus</div>
<div class="panel-body">
<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:10px;">
<div><strong>Modus:</strong> {cfg.get("betriebsmodus","demo").upper()}</div>
<div><strong>Version:</strong> {cfg.get("version","1.0.0")}</div>
<div><strong>Gesamtstatus:</strong> {badge(status_json["gesamtstatus"], "#16a34a" if status_json["gesamtstatus"]=="OK" else ("#ca8a04" if status_json["gesamtstatus"]=="WARNUNG" else "#dc2626"))}</div>
<div><strong>Dokumente:</strong> {status_json["gesamt_dokumente"]}</div>
<div><strong>Fehler:</strong> <span style="color:#dc2626;">{FEHLER}</span></div>
<div><strong>Warnungen:</strong> <span style="color:#ca8a04;">{WARNUNGEN}</span></div>
</div>
</div>
</div>

<div class="bereich-grid">
"""
    for bid, bcfg in cfg.get("anzeige_bereiche", []).items() if isinstance(cfg.get("anzeige_bereiche"), dict) else enumerate(cfg.get("anzeige_bereiche", [])):
        if isinstance(bcfg, tuple):
            bid, bcfg = bcfg
        else:
            bid = bcfg.get("id", "unknown")
        bdata = bereiche.get(bid, {})
        farbe = bcfg.get("farbe", "#6b7280")
        db_count = sum(d.get("count", 0) for d in bdata.get("db", {}).values())
        json_count = len(bdata.get("json", []))
        
        html += f"""
<div class="bereich-karte">
<div class="bereich-karte-header" style="background:{farbe};">{bcfg.get("name", bid)}</div>
<div class="bereich-karte-body">
<div class="stat"><span>DB-Einträge:</span><span>{db_count}</span></div>
<div class="stat"><span>JSON-Karten:</span><span>{json_count}</span></div>
<div class="stat"><span>Gesamt:</span><span><strong>{bdata.get("gesamt_dokumente", 0)}</strong></span></div>
"""
        if bdata.get("json"):
            html += '<div class="json-list">'
            for j in bdata["json"][:5]:
                name = j.get("_filename", j.get("original_name", "Unbekannt"))
                html += f'<div class="json-item">{name}</div>\n'
            html += '</div>'
        html += '</div></div>\n'
    
    html += f"""</div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Sperrregister-Status</div>
<div class="panel-body">
<p><strong>Status:</strong> <span class="{'status-ok' if sperrregister.get('status')=='OK' else 'status-err'}">{sperrregister.get('status','UNBEKANNT')}</span></p>
<p>{sperrregister.get('grund','') or sperrregister.get('blockierende_eintraege','') or ''}</p>
</div>
</div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Demo-Modus Einschränkungen</div>
<div class="panel-body">
<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:8px; font-size:0.85rem;">
<div>Max. Dokumente: {demo.get("max_dokumente",10)}</div>
<div>Nur Musterdaten: {"Ja" if demo.get("nur_musterdaten",True) else "Nein"}</div>
<div>Echte Daten: {"Nein" if not demo.get("echte_daten_erlaubt",False) else "Ja"}</div>
<div>Wasserzeichen: {demo.get("wasserzeichen","DEMO")}</div>
</div>
</div>
</div>

<div class="footer">
KI Legal – UI08 Posteingang / Importstrecke | Version {cfg.get("version","1.0.0")} | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
Dies ist eine Demo-Ausbaustufe. Keine Produktivfreigabe.
</div>

</div>
</body>
</html>"""
    return html

def schreibe_bericht(ergebnisse, cfg, status_json, sperrregister):
    lines = []
    lines.append("=" * 60)
    lines.append("UI08 POSTEINGANG / IMPORTSTRECKE BERICHT")
    lines.append("=" * 60)
    lines.append(f"Zeitstempel: {datetime.datetime.now().isoformat()}")
    lines.append(f"Betriebsmodus: {cfg.get('betriebsmodus','demo').upper()}")
    lines.append(f"Version: {cfg.get('version','1.0.0')}")
    lines.append("")
    lines.append("WARNUNG: " + cfg.get("warnung",""))
    lines.append("")
    lines.append("SPERRREGISTER:")
    lines.append(f"  Status: {sperrregister.get('status','UNBEKANNT')}")
    if sperrregister.get("grund"):
        lines.append(f"  Grund: {sperrregister['grund']}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("BEREICHE")
    lines.append("-" * 40)
    for bid, bdata in ergebnisse.get("bereiche", {}).items():
        lines.append(f"\n[{bid}]")
        lines.append(f"  DB-Einträge: {sum(d.get('count',0) for d in bdata.get('db',{}).values())}")
        lines.append(f"  JSON-Karten: {len(bdata.get('json',[]))}")
        lines.append(f"  Gesamt: {bdata.get('gesamt_dokumente',0)}")
        for tabelle, tdata in bdata.get("db", {}).items():
            if tdata.get("count", 0) > 0:
                lines.append(f"    DB {tabelle}: {tdata['count']} Einträge")
    lines.append("")
    lines.append("-" * 40)
    lines.append("ZUSAMMENFASSUNG")
    lines.append("-" * 40)
    lines.append(f"Gesamtdokumente: {status_json['gesamt_dokumente']}")
    lines.append(f"Fehler: {FEHLER}")
    lines.append(f"Warnungen: {WARNUNGEN}")
    lines.append(f"Gesamtstatus: {status_json['gesamtstatus']}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("ENDE BERICHT")
    lines.append("=" * 60)
    return "\n".join(lines)

def hauptlauf():
    global FEHLER, WARNUNGEN
    cfg = load_json("Config/ui08_posteingang_importstrecke_v1.json")
    ensure_dirs(cfg)

    print("UI08 Posteingang / Importstrecke – Start")
    print("=" * 50)
    print("WARNUNG:", cfg.get("warnung", ""))
    print("=" * 50)

    # Sperrregister
    print("\n[0/7] Sperrregister prüfen...")
    sperrregister = pruefe_sperrregister(cfg)
    print(f"      Status: {sperrregister.get('status','UNBEKANNT')}")
    if sperrregister.get("status") == "BLOCKIERT":
        print("      BLOCKIERT – Abbruch.")
        return False

    # Bereiche sammeln
    ergebnisse = {"bereiche": {}}
    bereiche_list = cfg.get("anzeige_bereiche", [])
    
    for i, bereich in enumerate(bereiche_list):
        bid = bereich.get("id", f"bereich_{i}")
        print(f"\n[{i+1}/7] {bereich.get('name', bid)}...")
        bdata = sammle_bereichsdaten(bereich, cfg)
        ergebnisse["bereiche"][bid] = bdata
        print(f"      DB: {sum(d.get('count',0) for d in bdata.get('db',{}).values())} | JSON: {len(bdata.get('json',[]))} | Gesamt: {bdata.get('gesamt_dokumente',0)}")

    status_json = generiere_status_json(ergebnisse, cfg, sperrregister)

    # JSON
    json_pfad = cfg["ausgabe"]["json_status"]
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(status_json, f, ensure_ascii=False, indent=2)
    print(f"\nStatus-JSON: {json_pfad}")

    # HTML
    html_pfad = cfg["ausgabe"]["html_posteingang_uebersicht"]
    html = generiere_html(ergebnisse, cfg, status_json)
    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Posteingang-Übersicht: {html_pfad}")

    # Bericht
    bericht_pfad = cfg["ausgabe"]["bericht"]
    bericht = schreibe_bericht(ergebnisse, cfg, status_json, sperrregister)
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write(bericht)
    print(f"Bericht: {bericht_pfad}")

    print("\n" + "=" * 50)
    print(f"GESAMTSTATUS: {status_json['gesamtstatus']}")
    print(f"Dokumente: {status_json['gesamt_dokumente']} | Fehler: {FEHLER} | Warnungen: {WARNUNGEN}")
    print("=" * 50)
    print("\nHINWEIS: Dies ist eine Demo-Ausbaustufe. Keine Produktivfreigabe.")
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
    print("UI08 SELBSTTEST =====================================")
    cfg = load_json("Config/ui08_posteingang_importstrecke_v1.json")
    t("Config geladen", cfg["modul_id"] == "UI08")
    t("betriebsmodus demo", cfg.get("betriebsmodus") == "demo")
    t("produktiv_freigegeben False", cfg.get("produktiv_freigegeben") is False)
    t("warnung vorhanden", len(cfg.get("warnung","")) > 0)
    t("anzeige_bereiche definiert", len(cfg.get("anzeige_bereiche",[])) > 0)
    t("sperrregister_pruefung aktiv", cfg.get("sperrregister_pruefung",{}).get("aktiv") is True)
    t("demo_modus nur_musterdaten", cfg.get("demo_modus",{}).get("nur_musterdaten") is True)
    t("ausgabe definiert", "html_posteingang_uebersicht" in cfg.get("ausgabe",{}))
    print(f"\nSelbsttest: {'OK' if FEHLER==0 else 'FEHLER'} ({FEHLER} Fehler)")
    return FEHLER == 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    ok = hauptlauf()
    sys.exit(0 if ok else 1)
