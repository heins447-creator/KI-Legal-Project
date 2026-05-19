#!/usr/bin/env python3
"""UI03-1f – Geparkte Übersetzungsaufträge verwalten (CORE-11-konform).

Zeigt alle geparkten Übersetzungsaufträge aus dem Projekt.
Pro Auftrag: Parkgrund, fehlende Modelle, betroffene Seiten/Dokumente.
Status "wartet auf lokale Modelle" wird sauber geführt.
Wiederaufnahme wird vorbereitet, sobald Argos lokal freigegeben ist.
Keine echte Übersetzung starten.

Schreibbereich: UI03_Mandantenakte\25_Geparkte_Auftraege_UI03_1f\
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "25_Geparkte_Auftraege_UI03_1f"
CONFIG_PATH = ROOT / "Config" / "ui03_1f_geparkte_auftraege_v1.json"
AKTE_PATH = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "10_Mandantenakte" / "Mandantenakte.json"

FEHLER = []
WARNUNGEN = []

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_config():
    if not CONFIG_PATH.exists():
        FEHLER.append(f"Config fehlt: {CONFIG_PATH}")
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

def load_register(name):
    path = CORE / f"{name}.json"
    if not path.exists():
        FEHLER.append(f"Register fehlt: {name}")
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))

def find_tool(toolregister, tool_id):
    for t in toolregister.get("eintraege", []):
        if t.get("tool_id") == tool_id:
            return t
    return None

def read_akte():
    if not AKTE_PATH.exists():
        WARNUNGEN.append("Mandantenakte nicht gefunden")
        return None
    return json.loads(AKTE_PATH.read_text(encoding="utf-8-sig"))

def ensure_dirs(cfg):
    for sub in cfg.get("ausgabe", {}).values():
        (SB / sub).parent.mkdir(parents=True, exist_ok=True)
    (SB / "05_Fehler").mkdir(parents=True, exist_ok=True)
    (SB / "07_Manifest").mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# GEPARKTE AUFTRÄGE SUCHEN
# ═══════════════════════════════════════════════════════════════════════

def suche_geparkte_auftraege():
    """Sucht im Projekt nach geparkten Übersetzungsaufträgen."""
    geparkt = []
    
    # Suche in UI03-1e Schreibbereich
    ui03_1e_sb = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "24_Uebergabe_Freigabe_UI03_1e"
    if ui03_1e_sb.exists():
        for json_file in ui03_1e_sb.rglob("UI03_1e_UEBERGABE_FREIGABE.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if data.get("status") == "vorbereitet":
                    geparkt.append({
                        "quelle": "UI03-1e",
                        "pfad": str(json_file),
                        "auftrag_id": data.get("auftrag_id", "UNBEKANNT"),
                        "akten_id": data.get("akten_id", ""),
                        "zeitpunkt_erstellung": data.get("zeitpunkt_erstellung", ""),
                        "parkgrund": data.get("parkgrund", ""),
                        "seiten_gesamt": len(data.get("seiten", [])),
                        "seiten_freigegeben": sum(1 for s in data.get("seiten", []) if s.get("kategorie") == "freigegeben"),
                        "seiten_neu_ocr": sum(1 for s in data.get("seiten", []) if s.get("kategorie") == "neu_ocr"),
                        "seiten_ausgeschlossen": sum(1 for s in data.get("seiten", []) if s.get("kategorie") == "ausgeschlossen"),
                        "seiten_zurueckgestellt": sum(1 for s in data.get("seiten", []) if s.get("kategorie") == "zurueckgestellt"),
                        "seiten_wartet": sum(1 for s in data.get("seiten", []) if s.get("kategorie") == "wartet"),
                    })
            except Exception as e:
                WARNUNGEN.append(f"Fehler beim Lesen {json_file}: {e}")
    
    return geparkt

def pruefe_argos_status():
    """Prüft, ob Argos lokal freigegeben ist."""
    toolregister = load_register("toolregister")
    ressourcenregister = load_register("ressourcenregister")
    
    if not toolregister or not ressourcenregister:
        return {"verfuegbar": False, "grund": "Register nicht ladbar", "paare": 0}
    
    argos = find_tool(toolregister, "ARGOS_TRANSLATE")
    if not argos:
        return {"verfuegbar": False, "grund": "Argos nicht im Toolregister", "paare": 0}
    
    if argos.get("installationsstatus") != "installiert":
        return {"verfuegbar": False, "grund": f"Nicht installiert (Status: {argos.get('installationsstatus')})", "paare": 0}
    
    paare_ja = sum(1 for r in ressourcenregister.get("eintraege", [])
                  if r.get("resource_id", "").startswith("ARGOS_")
                  and r.get("vorhanden_ja_nein_unbekannt") == "ja")
    
    if paare_ja == 0:
        return {"verfuegbar": False, "grund": "Keine Argos-Sprachpaare vorhanden", "paare": 0}
    
    return {"verfuegbar": True, "grund": f"{paare_ja} Sprachpaare verfügbar", "paare": paare_ja}

# ═══════════════════════════════════════════════════════════════════════
# HTML-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_verwaltung_html(auftraege, argos_status):
    """Erzeugt das Verwaltungs-Interface für geparkte Aufträge."""
    
    total_auftraege = len(auftraege)
    total_seiten = sum(a.get("seiten_gesamt", 0) for a in auftraege)
    total_freigegeben = sum(a.get("seiten_freigegeben", 0) for a in auftraege)
    
    # Argos-Banner
    argos_banner_class = "ok" if argos_status["verfuegbar"] else "warn"
    argos_banner_text = ("ARGOS BEREIT – Wiederaufnahme möglich" if argos_status["verfuegbar"] 
                         else f"ARGOS NICHT BEREIT – {argos_status['grund']}")
    
    # Auftrags-Karten
    auftraege_html = ""
    for a in auftraege:
        auftraege_html += f"""
      <div class="auftrags-karte">
        <div class="auftrags-header">
          <div class="auftrags-titel">
            <strong>Auftrag:</strong> {a['auftrag_id']}<br>
            <strong>Akte:</strong> {a['akten_id']}<br>
            <strong>Erstellt:</strong> {a['zeitpunkt_erstellung'][:19] if a['zeitpunkt_erstellung'] else '-'}<br>
            <strong>Quelle:</strong> {a['quelle']}
          </div>
          <div class="auftrags-status">
            <span class="badge badge-warn">GEPARKT</span>
          </div>
        </div>
        <div class="parkgrund-box">
          <strong>Parkgrund:</strong> {a['parkgrund']}
        </div>
        <div class="seiten-stats">
          <div class="mini-stat"><span class="mini-zahl">{a['seiten_gesamt']}</span><span class="mini-label">Seiten</span></div>
          <div class="mini-stat"><span class="mini-zahl ok">{a['seiten_freigegeben']}</span><span class="mini-label">Freigegeben</span></div>
          <div class="mini-stat"><span class="mini-zahl warn">{a['seiten_neu_ocr']}</span><span class="mini-label">Neu-OCR</span></div>
          <div class="mini-stat"><span class="mini-zahl err">{a['seiten_ausgeschlossen']}</span><span class="mini-label">Ausgeschlossen</span></div>
          <div class="mini-stat"><span class="mini-zahl warn">{a['seiten_zurueckgestellt']}</span><span class="mini-label">Zurückgestellt</span></div>
          <div class="mini-stat"><span class="mini-zahl info">{a['seiten_wartet']}</span><span class="mini-label">Wartet</span></div>
        </div>
        <div class="aktionen">
          <button class="btn btn-wiederaufnahme" disabled={not argos_status['verfuegbar']} 
                  title="{'Wiederaufnahme vorbereiten' if argos_status['verfuegbar'] else 'Warte auf Argos-Modelle'}">
            🔄 Wiederaufnahme vorbereiten
          </button>
          <button class="btn btn-details" title="Details anzeigen">
            📋 Details
          </button>
        </div>
      </div>"""
    
    if not auftraege:
        auftraege_html = '<p style="color:var(--text-secondary);font-style:italic;padding:20px;">Keine geparkten Aufträge gefunden.</p>'
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1f Geparkte Übersetzungsaufträge</title>
<style>
:root {{
  --bg: #f5f5f5; --panel: #ffffff; --text: #1a1a1a; --text-secondary: #555;
  --border: #ddd; --accent: #2c5282; --accent-light: #ebf4ff;
  --ok: #276749; --ok-bg: #f0fff4; --warn: #c05621; --warn-bg: #fffaf0;
  --err: #c53030; --err-bg: #fff5f5; --info: #3182ce; --info-bg: #ebf8ff;
}}
body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
.top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
h1 {{ font-size: 1.4rem; margin: 0; color: var(--accent); }}
h2 {{ font-size: 1.1rem; margin: 0 0 12px 0; color: var(--accent); }}
.badge {{ padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
.badge-ok {{ background: var(--ok-bg); color: var(--ok); }}
.badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
.badge-err {{ background: var(--err-bg); color: var(--err); }}
.badge-info {{ background: var(--info-bg); color: var(--info); }}
.panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
.status-banner {{ padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: 500; font-size: 0.95rem; }}
.status-banner.ok {{ background: var(--ok-bg); color: var(--ok); }}
.status-banner.warn {{ background: var(--warn-bg); color: var(--warn); }}
.gesamt-stats {{ display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }}
.stat-box {{ background: var(--accent-light); border-radius: 6px; padding: 15px 22px; text-align: center; min-width: 100px; }}
.stat-zahl {{ font-size: 1.8rem; font-weight: 700; color: var(--accent); }}
.stat-label {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }}
.auftrags-karte {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin-bottom: 18px; }}
.auftrags-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
.auftrags-titel {{ font-size: 0.88rem; line-height: 1.7; }}
.auftrags-status {{ text-align: right; }}
.parkgrund-box {{ background: var(--warn-bg); border-left: 4px solid var(--warn); padding: 10px 14px; margin: 10px 0; font-size: 0.88rem; color: var(--warn); }}
.seiten-stats {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 12px 0; }}
.mini-stat {{ background: var(--accent-light); border-radius: 5px; padding: 8px 14px; text-align: center; min-width: 60px; }}
.mini-zahl {{ font-size: 1.2rem; font-weight: 700; }}
.mini-zahl.ok {{ color: var(--ok); }}
.mini-zahl.warn {{ color: var(--warn); }}
.mini-zahl.err {{ color: var(--err); }}
.mini-zahl.info {{ color: var(--info); }}
.mini-label {{ font-size: 0.7rem; color: var(--text-secondary); margin-top: 2px; }}
.aktionen {{ display: flex; gap: 10px; margin-top: 12px; }}
.btn {{ padding: 8px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }}
.btn-wiederaufnahme {{ background: var(--ok-bg); color: var(--ok); border-color: var(--ok); }}
.btn-wiederaufnahme:hover {{ background: #c6f6d5; }}
.btn-wiederaufnahme:disabled {{ background: #e2e8f0; color: #a0aec0; border-color: #cbd5e0; cursor: not-allowed; }}
.btn-details {{ background: var(--accent-light); color: var(--accent); border-color: var(--accent); }}
.btn-details:hover {{ background: #dbeafe; }}
.grenzen {{ font-size: 0.85rem; color: var(--text-secondary); padding-left: 18px; line-height: 1.8; }}
.grenzen li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<div class="top-bar">
  <h1>UI03-1f Geparkte Übersetzungsaufträge</h1>
  <span class="badge badge-info">{total_auftraege} Aufträge | {total_seiten} Seiten</span>
</div>

<div class="status-banner {argos_banner_class}">
  {argos_banner_text}
</div>

<div class="panel">
  <h2>Gesamtübersicht</h2>
  <div class="gesamt-stats">
    <div class="stat-box"><div class="stat-zahl">{total_auftraege}</div><div class="stat-label">Geparkte Aufträge</div></div>
    <div class="stat-box"><div class="stat-zahl">{total_seiten}</div><div class="stat-label">Seiten gesamt</div></div>
    <div class="stat-box"><div class="stat-zahl">{total_freigegeben}</div><div class="stat-label">Freigegeben</div></div>
    <div class="stat-box"><div class="stat-zahl">{argos_status['paare']}</div><div class="stat-label">Argos-Paare</div></div>
  </div>
  <p style="font-size:0.9rem;color:var(--text-secondary);">
    Status: <strong>{'WARTET AUF LOKALE MODELLE' if not argos_status['verfuegbar'] else 'BEREIT FÜR WIEDERAUFNAHME'}</strong><br>
    Argos-Status: {argos_status['grund']}
  </p>
</div>

<div class="panel">
  <h2>Auftragsliste</h2>
{auftraege_html}
</div>

<div class="panel">
  <h2>Grenzen</h2>
  <ul class="grenzen">
    <li>✓ Keine Originaländerung</li>
    <li>✓ Keine neue OCR</li>
    <li>✓ Keine echte Übersetzung (nur vorbereiten/parken)</li>
    <li>✓ Keine DB-Änderung</li>
    <li>✓ Kein Internet/Cloud</li>
    <li>✓ Keine Registeränderung (nur lesend)</li>
  </ul>
</div>

</body>
</html>"""
    return html

# ═══════════════════════════════════════════════════════════════════════
# HAUPTLAUF
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("UI03-1f GEPARKTE AUFTRÄGE VERWALTUNG START ============================")
    cfg = load_config()
    ensure_dirs(cfg)

    print("[1] Geparkte Aufträge suchen ...")
    auftraege = suche_geparkte_auftraege()
    print(f"    {len(auftraege)} geparkte Aufträge gefunden")
    for a in auftraege:
        print(f"      - {a['auftrag_id']}: {a['seiten_gesamt']} Seiten ({a['seiten_freigegeben']} freigegeben)")

    print("[2] Argos-Status prüfen ...")
    argos_status = pruefe_argos_status()
    print(f"    Argos verfügbar: {argos_status['verfuegbar']} – {argos_status['grund']}")

    print("[3] Verwaltungs-HTML erzeugen ...")
    html = generate_verwaltung_html(auftraege, argos_status)
    html_path = SB / cfg.get("ausgabe", {}).get("verwaltung_html", "02_Status/UI03_1f_GEPARKTE_AUFTRAEGE.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[4] Status-JSON erzeugen ...")
    status_json = {
        "modul": "UI03-1f",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "geparkte_auftraege": len(auftraege),
        "argos_status": argos_status,
        "gesamt_seiten": sum(a.get("seiten_gesamt", 0) for a in auftraege),
        "gesamt_freigegeben": sum(a.get("seiten_freigegeben", 0) for a in auftraege),
        "wartet_auf_modelle": not argos_status["verfuegbar"],
        "grenzen": {
            "keine_originalaenderung": True,
            "keine_neue_ocr": True,
            "keine_echte_uebersetzung": True,
            "keine_db_aenderung": True,
            "kein_internet": True,
            "keine_cloud": True,
            "keine_registeraenderung": True,
        },
        "fehler": len(FEHLER),
        "warnungen": len(WARNUNGEN),
    }
    json_path = SB / cfg.get("ausgabe", {}).get("status_json", "02_Status/UI03_1f_GEPARKTE_AUFTRAEGE.json")
    json_path.write_text(json.dumps(status_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[5] Bericht erzeugen ...")
    bericht = f"""UI03-1f Geparkte Aufträge – Bericht
=====================================
Zeitpunkt: {now_iso()}

Geparkte Aufträge: {len(auftraege)}
Gesamt-Seiten: {sum(a.get('seiten_gesamt', 0) for a in auftraege)}
Freigegeben: {sum(a.get('seiten_freigegeben', 0) for a in auftraege)}

Argos-Status:
  Verfügbar: {'Ja' if argos_status['verfuegbar'] else 'Nein'}
  Grund: {argos_status['grund']}
  Paare: {argos_status['paare']}

Warte auf lokale Modelle: {'Ja' if not argos_status['verfuegbar'] else 'Nein'}

Grenzen:
  ✓ Keine Originaländerung
  ✓ Keine neue OCR
  ✓ Keine echte Übersetzung (nur vorbereiten/parken)
  ✓ Keine DB-Änderung
  ✓ Kein Internet/Cloud
  ✓ Keine Registeränderung

Ausgaben:
  {html_path}
  {json_path}

Fehler: {len(FEHLER)}
Warnungen: {len(WARNUNGEN)}
"""
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/UI03_1f_GEPARKTE_AUFTRAEGE_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")

    print("[6] Fehlerbericht ...")
    fehler_text = f"UI03-1f Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1f Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1f_GEPARKTE_AUFTRAEGE_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")

    print(f"\nUI03-1f GEPARKTE AUFTRÄGE ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1f SELBSTTEST ==================================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    t("Config ladbar", bool(load_config()))
    t("Toolregister ladbar", load_register("toolregister") is not None)
    t("Ressourcenregister ladbar", load_register("ressourcenregister") is not None)

    auftraege = suche_geparkte_auftraege()
    t("Auftragssuche funktioniert", isinstance(auftraege, list))

    argos_status = pruefe_argos_status()
    t("Argos-Status prüfbar", isinstance(argos_status, dict))
    t("Argos-Status hat verfuegbar", isinstance(argos_status.get("verfuegbar"), bool))
    t("Argos-Status hat grund", bool(argos_status.get("grund")))

    html = generate_verwaltung_html(auftraege, argos_status)
    t("HTML erzeugbar", len(html) > 3000)
    t("HTML enthält Status-Banner", "status-banner" in html)
    t("HTML enthält Gesamtübersicht", "gesamt-stats" in html)
    t("HTML enthält Auftragsliste", "auftrags-karte" in html or "Keine geparkten Aufträge" in html)
    t("HTML enthält Argos-Info", "ARGOS" in html.upper())
    t("HTML enthält Grenzen", "Keine Originaländerung" in html)
    t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
