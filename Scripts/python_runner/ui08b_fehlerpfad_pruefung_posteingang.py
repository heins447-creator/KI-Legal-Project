#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI08b – Fehlerpfadprüfung / Plausibilitätsprüfung Posteingang
Prüft 9 Fehlerlagen in der bestehenden Posteingang-Infrastruktur.
Erzeugt Fehler-Übersicht als HTML/JSON/Bericht.
KEINE neue Fachlogik. Nur Prüfung und Visualisierung.
"""

import json, os, sys, datetime, glob
from pathlib import Path

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dirs(cfg):
    for key in ["html_fehlerpfad_uebersicht", "json_status", "bericht"]:
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

def lese_duckdb_fehler(db_pfad, tabelle, bedingung, max_rows=10):
    """Liest Fehlerzeilen aus DuckDB."""
    try:
        import duckdb
        con = duckdb.connect(str(db_pfad))
        # Prüfe, ob Tabelle existiert
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        if tabelle not in tables:
            con.close()
            return []
        sql = f"SELECT * FROM {tabelle} WHERE {bedingung} LIMIT {max_rows}"
        rows = con.execute(sql).fetchall()
        cols = [desc[0] for desc in con.execute(f"SELECT * FROM {tabelle} LIMIT 0").description]
        con.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception:
        return []

def lese_json_fehler(patterns, feld, fehler_werte, max_files=10):
    """Sucht JSON-Karten mit Fehlerwerten."""
    fehler = []
    for pattern in patterns:
        for pfad in glob.glob(pattern, recursive=True)[:max_files]:
            try:
                data = load_json(pfad)
                wert = data.get(feld, "")
                if wert in fehler_werte or str(wert).upper() in [str(f).upper() for f in fehler_werte]:
                    fehler.append({
                        "pfad": pfad,
                        "filename": os.path.basename(pfad),
                        "feld": feld,
                        "wert": wert,
                        "intake_id": data.get("intake_id", "unbekannt")
                    })
            except Exception:
                pass
    return fehler

def pruefe_datei_existenz(pattern, invert=False):
    """Prüft, ob Dateien existieren (oder nicht existieren bei invert=True)."""
    dateien = glob.glob(pattern, recursive=True)
    if invert:
        return len(dateien) == 0
    return len(dateien) > 0

def pruefe_fehlerpfad(fehlerpfad, cfg):
    global FEHLER, WARNUNGEN
    db_pfad = cfg.get("abhaengigkeiten", {}).get("datenbank", "Database/Legal_Brain.duckdb")
    ergebnis = {
        "id": fehlerpfad["id"],
        "name": fehlerpfad["name"],
        "schwere": fehlerpfad.get("schwere", "MITTEL"),
        "db_fehler": [],
        "json_fehler": [],
        "datei_fehler": False,
        "gesamt": 0
    }
    
    # DB-Prüfung
    db_cfg = fehlerpfad.get("db_pruefung", {})
    if db_cfg:
        tabelle = db_cfg.get("tabelle", "")
        bedingung = db_cfg.get("bedingung", "")
        if tabelle and bedingung:
            db_fehler = lese_duckdb_fehler(db_pfad, tabelle, bedingung)
            ergebnis["db_fehler"] = db_fehler
            ergebnis["gesamt"] += len(db_fehler)
    
    # JSON-Prüfung
    json_cfg = fehlerpfad.get("json_pruefung", {})
    if json_cfg:
        feld = json_cfg.get("feld", "")
        fehler_werte = json_cfg.get("fehler_werte", [])
        patterns = []
        for bereich in cfg.get("anzeige_bereiche", []):
            patterns.extend(bereich.get("json_patterns", []))
        if not patterns:
            patterns = ["Posteingang/**/*.json"]
        json_fehler = lese_json_fehler(patterns, feld, fehler_werte)
        ergebnis["json_fehler"] = json_fehler
        ergebnis["gesamt"] += len(json_fehler)
    
    # Datei-Prüfung
    datei_cfg = fehlerpfad.get("datei_pruefung", {})
    if datei_cfg:
        pattern = datei_cfg.get("pattern", "")
        invert = datei_cfg.get("invert", False)
        if pattern:
            datei_ok = pruefe_datei_existenz(pattern, invert)
            ergebnis["datei_fehler"] = not datei_ok
            if not datei_ok:
                ergebnis["gesamt"] += 1
    
    return ergebnis

def generiere_status_json(ergebnisse, cfg, sperrregister):
    fehlerpfade = ergebnisse.get("fehlerpfade", [])
    gesamt_fehler = sum(f["gesamt"] for f in fehlerpfade)
    kritisch = sum(f["gesamt"] for f in fehlerpfade if f.get("schwere") == "KRITISCH")
    hoch = sum(f["gesamt"] for f in fehlerpfade if f.get("schwere") == "HOCH")
    mittel = sum(f["gesamt"] for f in fehlerpfade if f.get("schwere") == "MITTEL")
    
    return {
        "modul_id": "UI08b",
        "modulname": "Fehlerpfadprüfung Posteingang",
        "version": cfg.get("version", "1.0.0"),
        "version_status": cfg.get("version_status", "entwicklung"),
        "produktiv_freigegeben": False,
        "timestamp": datetime.datetime.now().isoformat(),
        "betriebsmodus": cfg.get("betriebsmodus", "demo"),
        "sperrregister": sperrregister,
        "fehlerpfade": [{"id": f["id"], "name": f["name"], "schwere": f["schwere"], "anzahl": f["gesamt"]} for f in fehlerpfade],
        "gesamt_fehler": gesamt_fehler,
        "kritisch": kritisch,
        "hoch": hoch,
        "mittel": mittel,
        "fehler": FEHLER,
        "warnungen": WARNUNGEN,
        "gesamtstatus": "FEHLER" if (FEHLER > 0 or kritisch > 0) else ("WARNUNG" if (WARNUNGEN > 0 or hoch > 0 or mittel > 0) else "OK")
    }

def generiere_html(ergebnisse, cfg, status_json, sperrregister):
    def badge(text, color):
        return f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:0.75rem;font-weight:600;">{text}</span>'
    
    fehlerpfade = ergebnisse.get("fehlerpfade", [])
    warnung = cfg.get("warnung", "")
    
    schwere_farben = {"KRITISCH": "#dc2626", "HOCH": "#ea580c", "MITTEL": "#ca8a04"}
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI08b – Fehlerpfadprüfung Posteingang</title>
<style>
:root {{ --bg:#f3f4f6; --card:#fff; --text:#111827; --text-secondary:#6b7280; --border:#e5e7eb; }}
body {{ font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); margin:0; padding:20px; }}
.container {{ max-width:1200px; margin:0 auto; }}
.demo-banner {{ border:3px solid #dc2626; border-radius:10px; padding:16px; background:#fef2f2; margin-bottom:20px; }}
.demo-banner h1 {{ color:#991b1b; margin:0 0 6px; font-size:1.4rem; }}
.demo-banner p {{ color:#7f1d1d; margin:0; font-size:0.9rem; }}
.panel {{ background:var(--card); border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:16px; overflow:hidden; }}
.panel-header {{ padding:12px 16px; border-bottom:1px solid var(--border); font-weight:600; font-size:1rem; color:#fff; background:#4b5563; }}
.panel-body {{ padding:14px 16px; }}
.fehler-tabelle {{ width:100%; border-collapse:collapse; font-size:0.88rem; }}
.fehler-tabelle th {{ text-align:left; padding:8px 12px; background:#f9fafb; border-bottom:2px solid var(--border); font-weight:600; }}
.fehler-tabelle td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
.fehler-karte {{ background:var(--card); border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:12px; overflow:hidden; }}
.fehler-karte-header {{ padding:10px 14px; color:#fff; font-weight:600; font-size:0.9rem; }}
.fehler-karte-body {{ padding:10px 14px; font-size:0.85rem; }}
.stat {{ display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #f3f4f6; }}
.footer {{ text-align:center; color:var(--text-secondary); font-size:0.8rem; margin-top:20px; padding:14px; }}
.status-ok {{ color:#16a34a; font-weight:600; }}
.status-warn {{ color:#ca8a04; font-weight:600; }}
.status-err {{ color:#dc2626; font-weight:600; }}
.fehler-detail {{ font-size:0.8rem; color:var(--text-secondary); padding-left:12px; border-left:3px solid var(--border); margin:4px 0; }}
</style>
</head>
<body>
<div class="container">

<div class="demo-banner">
<h1>🚨 UI08b – Fehlerpfadprüfung Posteingang</h1>
<p><strong>{warnung}</strong></p>
</div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Gesamtstatus</div>
<div class="panel-body">
<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:10px;">
<div><strong>Modus:</strong> {cfg.get("betriebsmodus","demo").upper()}</div>
<div><strong>Version:</strong> {cfg.get("version","1.0.0")}</div>
<div><strong>Gesamtstatus:</strong> {badge(status_json["gesamtstatus"], "#16a34a" if status_json["gesamtstatus"]=="OK" else ("#ca8a04" if status_json["gesamtstatus"]=="WARNUNG" else "#dc2626"))}</div>
<div><strong>Fehler gesamt:</strong> <span style="color:#dc2626;font-weight:600;">{status_json["gesamt_fehler"]}</span></div>
<div><strong>Kritisch:</strong> <span style="color:#dc2626;">{status_json["kritisch"]}</span></div>
<div><strong>Hoch:</strong> <span style="color:#ea580c;">{status_json["hoch"]}</span></div>
<div><strong>Mittel:</strong> <span style="color:#ca8a04;">{status_json["mittel"]}</span></div>
</div>
</div>
</div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Fehlerpfade Übersicht</div>
<div class="panel-body">
<table class="fehler-tabelle">
<tr><th>ID</th><th>Name</th><th>Schwere</th><th>Anzahl</th><th>Status</th></tr>
"""
    for f in fehlerpfade:
        farbe = schwere_farben.get(f.get("schwere","MITTEL"), "#6b7280")
        status_text = "FEHLER" if f["gesamt"] > 0 else "OK"
        status_cls = "status-err" if f["gesamt"] > 0 else "status-ok"
        html += f'<tr><td>{f["id"]}</td><td>{f["name"]}</td><td><span style="color:{farbe};font-weight:600;">{f.get("schwere","MITTEL")}</span></td><td>{f["gesamt"]}</td><td class="{status_cls}">{status_text}</td></tr>\n'
    
    html += """</table></div></div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Detaillierte Fehlerlagen</div>
<div class="panel-body">
"""
    for f in fehlerpfade:
        if f["gesamt"] == 0:
            continue
        farbe = schwere_farben.get(f.get("schwere","MITTEL"), "#6b7280")
        html += f'<div class="fehler-karte">\n'
        html += f'<div class="fehler-karte-header" style="background:{farbe};">{f["id"]} – {f["name"]} ({f["gesamt"]} Fehler)</div>\n'
        html += '<div class="fehler-karte-body">\n'
        
        if f.get("db_fehler"):
            html += '<p style="margin:4px 0;font-weight:600;">DB-Fehler:</p>\n'
            for df in f["db_fehler"][:5]:
                intake = df.get("intake_id", df.get("document_language_id", "unbekannt"))
                html += f'<div class="fehler-detail">Intake: {intake}</div>\n'
        
        if f.get("json_fehler"):
            html += '<p style="margin:4px 0;font-weight:600;">JSON-Fehler:</p>\n'
            for jf in f["json_fehler"][:5]:
                html += f'<div class="fehler-detail">{jf["filename"]} – {jf["feld"]}={jf["wert"]} (Intake: {jf["intake_id"]})</div>\n'
        
        if f.get("datei_fehler"):
            html += '<p style="margin:4px 0;font-weight:600;color:#dc2626;">Datei-Prüfung: FEHLER</p>\n'
        
        html += '</div></div>\n'
    
    if all(f["gesamt"] == 0 for f in fehlerpfade):
        html += '<p style="color:#16a34a;font-weight:600;">✓ Keine Fehler gefunden.</p>\n'
    
    html += f"""</div></div>

<div class="panel">
<div class="panel-header" style="background:#4b5563;">Sperrregister-Status</div>
<div class="panel-body">
<p><strong>Status:</strong> <span class="{'status-ok' if sperrregister.get('status')=='OK' else 'status-err'}">{sperrregister.get('status','UNBEKANNT')}</span></p>
<p>{sperrregister.get('grund','') or sperrregister.get('blockierende_eintraege','') or ''}</p>
</div>
</div>

<div class="footer">
KI Legal – UI08b Fehlerpfadprüfung | Version {cfg.get("version","1.0.0")} | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
Demo-Modus. Keine Produktivfreigabe. Keine echten Mandantendaten.
</div>

</div>
</body>
</html>"""
    return html

def schreibe_bericht(ergebnisse, cfg, status_json, sperrregister):
    lines = []
    lines.append("=" * 60)
    lines.append("UI08B FEHLERPFADPRÜFUNG POSTEINGANG BERICHT")
    lines.append("=" * 60)
    lines.append(f"Zeitstempel: {datetime.datetime.now().isoformat()}")
    lines.append(f"Betriebsmodus: {cfg.get('betriebsmodus','demo').upper()}")
    lines.append(f"Version: {cfg.get('version','1.0.0')}")
    lines.append("")
    lines.append("WARNUNG: " + cfg.get("warnung",""))
    lines.append("")
    lines.append("SPERRREGISTER:")
    lines.append(f"  Status: {sperrregister.get('status','UNBEKANNT')}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("FEHLERPFADE")
    lines.append("-" * 40)
    for f in ergebnisse.get("fehlerpfade", []):
        status_text = "FEHLER" if f["gesamt"] > 0 else "OK"
        lines.append(f"\n[{status_text}] {f['id']} – {f['name']} (Schwere: {f.get('schwere','MITTEL')})")
        lines.append(f"  Gesamt: {f['gesamt']} Fehler")
        if f.get("db_fehler"):
            lines.append(f"  DB-Fehler: {len(f['db_fehler'])}")
        if f.get("json_fehler"):
            lines.append(f"  JSON-Fehler: {len(f['json_fehler'])}")
        if f.get("datei_fehler"):
            lines.append(f"  Datei-Prüfung: FEHLER")
    lines.append("")
    lines.append("-" * 40)
    lines.append("ZUSAMMENFASSUNG")
    lines.append("-" * 40)
    lines.append(f"Gesamtfehler: {status_json['gesamt_fehler']}")
    lines.append(f"Kritisch: {status_json['kritisch']}")
    lines.append(f"Hoch: {status_json['hoch']}")
    lines.append(f"Mittel: {status_json['mittel']}")
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
    cfg = load_json("Config/ui08b_fehlerpfad_pruefung_posteingang_v1.json")
    ensure_dirs(cfg)

    print("UI08b Fehlerpfadprüfung Posteingang – Start")
    print("=" * 50)
    print("WARNUNG:", cfg.get("warnung", ""))
    print("=" * 50)

    # Sperrregister
    print("\n[0/9] Sperrregister prüfen...")
    sperrregister = pruefe_sperrregister(cfg)
    print(f"      Status: {sperrregister.get('status','UNBEKANNT')}")
    if sperrregister.get("status") == "BLOCKIERT":
        print("      BLOCKIERT – Abbruch.")
        return False

    # Fehlerpfade prüfen
    ergebnisse = {"fehlerpfade": []}
    fehlerpfade_cfg = cfg.get("fehlerpfade", [])
    
    for i, fp in enumerate(fehlerpfade_cfg):
        print(f"\n[{i+1}/9] {fp['id']} – {fp['name']}...")
        res = pruefe_fehlerpfad(fp, cfg)
        ergebnisse["fehlerpfade"].append(res)
        status_icon = "✗" if res["gesamt"] > 0 else "✓"
        print(f"      {status_icon} {res['gesamt']} Fehler (DB:{len(res['db_fehler'])}, JSON:{len(res['json_fehler'])}, Datei:{'FEHLER' if res['datei_fehler'] else 'OK'})")

    status_json = generiere_status_json(ergebnisse, cfg, sperrregister)

    # JSON
    json_pfad = cfg["ausgabe"]["json_status"]
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(status_json, f, ensure_ascii=False, indent=2)
    print(f"\nStatus-JSON: {json_pfad}")

    # HTML
    html_pfad = cfg["ausgabe"]["html_fehlerpfad_uebersicht"]
    html = generiere_html(ergebnisse, cfg, status_json, sperrregister)
    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Fehlerpfad-Übersicht: {html_pfad}")

    # Bericht
    bericht_pfad = cfg["ausgabe"]["bericht"]
    bericht = schreibe_bericht(ergebnisse, cfg, status_json, sperrregister)
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write(bericht)
    print(f"Bericht: {bericht_pfad}")

    print("\n" + "=" * 50)
    print(f"GESAMTSTATUS: {status_json['gesamtstatus']}")
    print(f"Fehler: {status_json['gesamt_fehler']} (K:{status_json['kritisch']}/H:{status_json['hoch']}/M:{status_json['mittel']})")
    print(f"System-Fehler: {FEHLER} | Warnungen: {WARNUNGEN}")
    print("=" * 50)
    print("\nHINWEIS: Demo-Modus. Keine Produktivfreigabe.")
    return FEHLER == 0 and status_json["kritisch"] == 0

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
    print("UI08b SELBSTTEST =====================================")
    cfg = load_json("Config/ui08b_fehlerpfad_pruefung_posteingang_v1.json")
    t("Config geladen", cfg["modul_id"] == "UI08b")
    t("betriebsmodus demo", cfg.get("betriebsmodus") == "demo")
    t("produktiv_freigegeben False", cfg.get("produktiv_freigegeben") is False)
    t("warnung vorhanden", len(cfg.get("warnung","")) > 0)
    t("fehlerpfade definiert", len(cfg.get("fehlerpfade",[])) == 9)
    t("sperrregister_pruefung aktiv", cfg.get("sperrregister_pruefung",{}).get("aktiv") is True)
    t("demo_modus nur_musterdaten", cfg.get("demo_modus",{}).get("nur_musterdaten") is True)
    t("ausgabe definiert", "html_fehlerpfad_uebersicht" in cfg.get("ausgabe",{}))
    print(f"\nSelbsttest: {'OK' if FEHLER==0 else 'FEHLER'} ({FEHLER} Fehler)")
    return FEHLER == 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    ok = hauptlauf()
    sys.exit(0 if ok else 1)
