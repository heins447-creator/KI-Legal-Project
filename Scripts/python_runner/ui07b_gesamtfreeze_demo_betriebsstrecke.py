#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI07b – Gesamtfreeze Demo-Betriebsstrecke ohne Produktivfreigabe
Prüft: Existenz aller UI03–UI07-Dateien, Git-Status, erzeugt Freeze-Übersicht.
KEINE neue Fachlogik. Nur Zusammenfassung und Validierung der bestehenden Strecke.
"""

import json, os, sys, datetime, subprocess

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dirs(cfg):
    for key in ["logs", "pruefseiten"]:
        rel = cfg.get("ausgabe", {}).get(key, "")
        if rel:
            d = os.path.dirname(rel) if "." in os.path.basename(rel) else rel
            if d:
                os.makedirs(d, exist_ok=True)

def git_status_datei(pfad):
    """Prüft Git-Status einer Datei."""
    try:
        result = subprocess.run(
            ["git", "status", "--short", pfad],
            capture_output=True, text=True, check=False, cwd="."
        )
        line = result.stdout.strip()
        if not line:
            return {"status": "committed", "code": "", "beschreibung": "Committed"}
        code = line[:2].strip()
        if code == "":
            return {"status": "committed", "code": "", "beschreibung": "Committed"}
        if code == "??":
            return {"status": "untracked", "code": "??", "beschreibung": "Untracked"}
        if code in ("M", " M", "M "):
            return {"status": "modified", "code": "M", "beschreibung": "Modified"}
        if code in ("A", " A"):
            return {"status": "added", "code": "A", "beschreibung": "Added"}
        return {"status": "other", "code": code, "beschreibung": f"Git-Code: {code}"}
    except Exception as e:
        return {"status": "error", "code": "", "beschreibung": str(e)}

def pruefe_modul(modul):
    global FEHLER, WARNUNGEN
    ergebnis = {"id": modul["id"], "name": modul["name"], "dateien": []}
    alle_ok = True
    for key in ["config", "runner", "check", "starter", "doku"]:
        if key not in modul:
            continue
        pfad = modul[key]
        exists = os.path.isfile(pfad)
        git = git_status_datei(pfad)
        status = "OK" if (exists and git["status"] == "committed") else "WARNUNG"
        if not exists:
            status = "FEHLER"
            FEHLER += 1
            alle_ok = False
        elif git["status"] != "committed":
            if git["status"] in ("untracked", "modified"):
                WARNUNGEN += 1
                alle_ok = False
            elif git["status"] == "error":
                WARNUNGEN += 1
        ergebnis["dateien"].append({
            "typ": key,
            "pfad": pfad,
            "exists": exists,
            "git_status": git["status"],
            "git_code": git["code"],
            "git_beschreibung": git["beschreibung"],
            "status": status
        })
    ergebnis["modul_ok"] = alle_ok
    return ergebnis

def pruefe_ergaenzende(dateien, kategorie):
    global FEHLER, WARNUNGEN
    ergebnis = []
    for pfad in dateien:
        exists = os.path.isfile(pfad)
        git = git_status_datei(pfad)
        status = "OK" if (exists and git["status"] == "committed") else "WARNUNG"
        if not exists:
            status = "FEHLER"
            FEHLER += 1
        elif git["status"] != "committed":
            WARNUNGEN += 1
        ergebnis.append({
            "pfad": pfad,
            "kategorie": kategorie,
            "exists": exists,
            "git_status": git["status"],
            "git_code": git["code"],
            "status": status
        })
    return ergebnis

def generiere_status_json(ergebnisse, cfg):
    module = ergebnisse.get("module", [])
    modul_ok_count = sum(1 for m in module if m.get("modul_ok"))
    return {
        "modul_id": "UI07b",
        "modulname": "Gesamtfreeze Demo-Betriebsstrecke",
        "version": cfg.get("version", "1.0.0"),
        "version_status": cfg.get("version_status", "freeze"),
        "freeze_status": cfg.get("freeze_status", "eingefroren"),
        "freeze_datum": cfg.get("freeze_datum"),
        "produktiv_freigegeben": False,
        "timestamp": datetime.datetime.now().isoformat(),
        "module_gesamt": len(module),
        "module_ok": modul_ok_count,
        "module_fehler": len(module) - modul_ok_count,
        "fehler": FEHLER,
        "warnungen": WARNUNGEN,
        "gesamtstatus": "FEHLER" if FEHLER > 0 else ("WARNUNG" if WARNUNGEN > 0 else "OK"),
        "freeze_regeln": cfg.get("freeze_regeln", [])
    }

def generiere_html(ergebnisse, cfg, status_json):
    def badge(text, color):
        return f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:0.75rem;font-weight:600;">{text}</span>'

    def row(label, value, cls=""):
        return f'<tr><td style="padding:6px 12px;border-bottom:1px solid #e5e7eb;font-weight:500;">{label}</td><td style="padding:6px 12px;border-bottom:1px solid #e5e7eb;{cls}">{value}</td></tr>'

    warnung = cfg.get("warnung", "")
    module = ergebnisse.get("module", [])
    erg_doku = ergebnisse.get("ergaenzende_doku", [])
    erg_runner = ergebnisse.get("ergaenzende_runner", [])

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{cfg.get("modulname","Gesamtfreeze")}</title>
<style>
:root {{ --bg:#f3f4f6; --card:#fff; --text:#111827; --text-secondary:#6b7280; --border:#e5e7eb; --ok:#16a34a; --warn:#ca8a04; --err:#dc2626; --accent:#2563eb; }}
body {{ font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); margin:0; padding:20px; }}
.container {{ max-width:1100px; margin:0 auto; }}
.freeze-banner {{ border:4px solid #dc2626; border-radius:12px; padding:20px; background:#fef2f2; margin-bottom:24px; }}
.freeze-banner h1 {{ color:#991b1b; margin:0 0 8px; font-size:1.6rem; }}
.freeze-banner p {{ color:#7f1d1d; margin:0; font-size:1rem; }}
.panel {{ background:var(--card); border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:20px; overflow:hidden; }}
.panel-header {{ background:#f9fafb; padding:14px 20px; border-bottom:1px solid var(--border); font-weight:600; font-size:1.05rem; }}
.panel-body {{ padding:16px 20px; }}
table {{ width:100%; border-collapse:collapse; font-size:0.88rem; }}
th {{ text-align:left; padding:8px 12px; background:#f9fafb; border-bottom:2px solid var(--border); font-weight:600; }}
td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
.status-ok {{ color:var(--ok); font-weight:600; }}
.status-warn {{ color:var(--warn); font-weight:600; }}
.status-err {{ color:var(--err); font-weight:600; }}
.footer {{ text-align:center; color:var(--text-secondary); font-size:0.8rem; margin-top:24px; padding:16px; }}
.modul-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }}
.modul-karte {{ border:1px solid var(--border); border-radius:8px; padding:12px; background:#f9fafb; }}
.modul-karte.ok {{ border-left:4px solid var(--ok); }}
.modul-karte.warn {{ border-left:4px solid var(--warn); }}
.modul-karte.err {{ border-left:4px solid var(--err); }}
.freeze-regel {{ background:#fffbeb; border-left:4px solid #ca8a04; padding:8px 12px; margin-bottom:6px; border-radius:4px; font-size:0.88rem; }}
</style>
</head>
<body>
<div class="container">

<div class="freeze-banner">
<h1>🧊 {cfg.get("modulname","Gesamtfreeze")}</h1>
<p><strong>{warnung}</strong></p>
</div>

<div class="panel">
<div class="panel-header">Freeze-Status</div>
<div class="panel-body">
<table>
{row("Freeze-Status", cfg.get("freeze_status","unbekannt").upper(), "font-weight:700;color:#dc2626;")}
{row("Freeze-Datum", cfg.get("freeze_datum","unbekannt"))}
{row("Version", cfg.get("version","1.0.0"))}
{row("Version-Status", cfg.get("version_status","freeze"))}
{row("Gesamtstatus", badge(status_json["gesamtstatus"], "#16a34a" if status_json["gesamtstatus"]=="OK" else ("#ca8a04" if status_json["gesamtstatus"]=="WARNUNG" else "#dc2626")), "font-weight:700;")}
{row("Module OK", f'{status_json["module_ok"]}/{status_json["module_gesamt"]}')}
{row("Fehler", str(FEHLER), "color:#dc2626;font-weight:600;" if FEHLER>0 else "")}
{row("Warnungen", str(WARNUNGEN), "color:#ca8a04;font-weight:600;" if WARNUNGEN>0 else "")}
</table>
</div>
</div>

<div class="panel">
<div class="panel-header">Freeze-Regeln</div>
<div class="panel-body">
"""
    for regel in cfg.get("freeze_regeln", []):
        html += f'<div class="freeze-regel">{regel}</div>\n'
    html += """</div></div>

<div class="panel">
<div class="panel-header">Module Übersicht (UI03–UI07)</div>
<div class="panel-body">
<div class="modul-grid">
"""
    for m in module:
        kls = "ok" if m.get("modul_ok") else ("err" if any(d["status"]=="FEHLER" for d in m.get("dateien",[])) else "warn")
        html += f'<div class="modul-karte {kls}"><strong>{m["id"]}</strong><br><span style="font-size:0.85rem;">{m["name"]}</span><br><span style="font-size:0.75rem;color:var(--text-secondary);">{"✓ Alle Dateien" if m.get("modul_ok") else "⚠ Prüfung erforderlich"}</span></div>\n'
    html += """</div></div></div>

<div class="panel">
<div class="panel-header">Modul-Details</div>
<div class="panel-body">
"""
    for m in module:
        html += f'<h4 style="margin-top:16px;margin-bottom:6px;">{m["id"]} – {m["name"]}</h4>\n'
        html += '<table><tr><th>Typ</th><th>Pfad</th><th>Existiert</th><th>Git-Status</th><th>Status</th></tr>\n'
        for d in m.get("dateien", []):
            cls = "status-ok" if d["status"] == "OK" else ("status-err" if d["status"] == "FEHLER" else "status-warn")
            html += f'<tr><td>{d["typ"]}</td><td>{d["pfad"]}</td><td>{"Ja" if d["exists"] else "Nein"}</td><td>{d["git_beschreibung"]}</td><td class="{cls}">{d["status"]}</td></tr>\n'
        html += '</table>\n'
    html += """</div></div>

<div class="panel">
<div class="panel-header">Ergänzende Dateien</div>
<div class="panel-body">
<table>
<tr><th>Kategorie</th><th>Pfad</th><th>Existiert</th><th>Git-Status</th><th>Status</th></tr>
"""
    for d in erg_doku + erg_runner:
        cls = "status-ok" if d["status"] == "OK" else ("status-err" if d["status"] == "FEHLER" else "status-warn")
        html += f'<tr><td>{d["kategorie"]}</td><td>{d["pfad"]}</td><td>{"Ja" if d["exists"] else "Nein"}</td><td>{d["git_beschreibung"]}</td><td class="{cls}">{d["status"]}</td></tr>\n'
    html += f"""</table></div></div>

<div class="footer">
KI Legal – UI07b Gesamtfreeze | Version {cfg.get("version","1.0.0")} | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
Demo-Betriebsstrecke eingefroren. Keine Änderungen ohne expliziten Auftrag.
</div>

</div>
</body>
</html>"""
    return html

def schreibe_bericht(ergebnisse, cfg, status_json):
    lines = []
    lines.append("=" * 60)
    lines.append("UI07B GESAMTFREEZE DEMO-BETRIEBSSTRECKE BERICHT")
    lines.append("=" * 60)
    lines.append(f"Zeitstempel: {datetime.datetime.now().isoformat()}")
    lines.append(f"Freeze-Status: {cfg.get('freeze_status','unbekannt').upper()}")
    lines.append(f"Freeze-Datum: {cfg.get('freeze_datum','unbekannt')}")
    lines.append(f"Version: {cfg.get('version','1.0.0')}")
    lines.append("")
    lines.append("WARNUNG: " + cfg.get("warnung",""))
    lines.append("")
    lines.append("FREEZE-REGELN:")
    for r in cfg.get("freeze_regeln", []):
        lines.append(f"  - {r}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("MODUL-PRÜFUNG")
    lines.append("-" * 40)
    for m in ergebnisse.get("module", []):
        ok_text = "OK" if m.get("modul_ok") else "NICHT OK"
        lines.append(f"\n[{ok_text}] {m['id']} – {m['name']}")
        for d in m.get("dateien", []):
            git_info = f"[{d['git_beschreibung']}]"
            lines.append(f"      [{d['status']}] {d['typ']}: {d['pfad']} {git_info}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("ERGÄNZENDE DATEIEN")
    lines.append("-" * 40)
    for d in ergebnisse.get("ergaenzende_doku", []) + ergebnisse.get("ergaenzende_runner", []):
        lines.append(f"  [{d['status']}] {d['kategorie']}: {d['pfad']} [{d['git_beschreibung']}]")
    lines.append("")
    lines.append("-" * 40)
    lines.append("ZUSAMMENFASSUNG")
    lines.append("-" * 40)
    lines.append(f"Module gesamt: {status_json['module_gesamt']}")
    lines.append(f"Module OK: {status_json['module_ok']}")
    lines.append(f"Module mit Fehlern: {status_json['module_fehler']}")
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
    cfg = load_json("Config/ui07b_gesamtfreeze_demo_betriebsstrecke_v1.json")
    ensure_dirs(cfg)

    print("UI07b Gesamtfreeze – Start")
    print("=" * 50)
    print("WARNUNG:", cfg.get("warnung", ""))
    print("=" * 50)

    ergebnisse = {}

    print("\n[1/3] UI03–UI07 Module prüfen...")
    module_ergebnis = []
    for mod in cfg["strecke_ui03_bis_ui07"]["module"]:
        res = pruefe_modul(mod)
        module_ergebnis.append(res)
        status_icon = "✓" if res["modul_ok"] else "✗"
        print(f"      {status_icon} {res['id']} – {res['name']}")
    ergebnisse["module"] = module_ergebnis
    ok_count = sum(1 for m in module_ergebnis if m["modul_ok"])
    print(f"      {ok_count}/{len(module_ergebnis)} Module vollständig committed.")

    print("\n[2/3] Ergänzende Dokumentation prüfen...")
    erg_doku = pruefe_ergaenzende(cfg["strecke_ui03_bis_ui07"].get("ergaenzende_doku", []), "Doku")
    ergebnisse["ergaenzende_doku"] = erg_doku
    print(f"      {sum(1 for d in erg_doku if d['status']=='OK')}/{len(erg_doku)} Dokus OK.")

    print("\n[3/3] Ergänzende Runner prüfen...")
    erg_runner = pruefe_ergaenzende(cfg["strecke_ui03_bis_ui07"].get("ergaenzende_runner", []), "Runner")
    ergebnisse["ergaenzende_runner"] = erg_runner
    print(f"      {sum(1 for d in erg_runner if d['status']=='OK')}/{len(erg_runner)} Runner OK.")

    status_json = generiere_status_json(ergebnisse, cfg)

    # JSON
    json_pfad = cfg["ausgabe"]["json_status"]
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(status_json, f, ensure_ascii=False, indent=2)
    print(f"\nStatus-JSON: {json_pfad}")

    # HTML
    html_pfad = cfg["ausgabe"]["html_freeze_uebersicht"]
    os.makedirs(os.path.dirname(html_pfad), exist_ok=True)
    html = generiere_html(ergebnisse, cfg, status_json)
    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Freeze-Übersicht: {html_pfad}")

    # Bericht
    bericht_pfad = cfg["ausgabe"]["bericht"]
    bericht = schreibe_bericht(ergebnisse, cfg, status_json)
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write(bericht)
    print(f"Bericht: {bericht_pfad}")

    print("\n" + "=" * 50)
    print(f"GESAMTSTATUS: {status_json['gesamtstatus']}")
    print(f"Fehler: {FEHLER} | Warnungen: {WARNUNGEN}")
    print("=" * 50)
    print("\nHINWEIS: Demo-Betriebsstrecke eingefroren. Keine Änderungen ohne expliziten Auftrag.")
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
    print("UI07b SELBSTTEST =====================================")
    cfg = load_json("Config/ui07b_gesamtfreeze_demo_betriebsstrecke_v1.json")
    t("Config geladen", cfg["modul_id"] == "UI07b")
    t("freeze_status eingefroren", cfg.get("freeze_status") == "eingefroren")
    t("produktiv_freigegeben False", cfg.get("produktiv_freigegeben") is False)
    t("warnung vorhanden", len(cfg.get("warnung","")) > 0)
    t("module definiert", len(cfg.get("strecke_ui03_bis_ui07",{}).get("module",[])) > 0)
    t("freeze_regeln definiert", len(cfg.get("freeze_regeln",[])) > 0)
    t("ausgabe definiert", "html_freeze_uebersicht" in cfg.get("ausgabe",{}))
    t("version_status freeze", cfg.get("version_status") == "freeze")
    print(f"\nSelbsttest: {'OK' if FEHLER==0 else 'FEHLER'} ({FEHLER} Fehler)")
    return FEHLER == 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    ok = hauptlauf()
    sys.exit(0 if ok else 1)
