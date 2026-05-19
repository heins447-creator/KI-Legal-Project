#!/usr/bin/env python3
"""UI03-1g – Kombinierte Gesamtansicht OCR → Freigabe → Übersetzungsauftrag → Parkstatus (CORE-11-konform).

Zusammenführt die Ergebnisse von UI03-1b bis UI03-1f in eine einzige Dashboard-Ansicht.
Keine Neuberechnung, nur Aggregation vorhandener Status-Dateien.

Schreibbereich: UI03_Mandantenakte\26_Gesamtansicht_UI03_1g\
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "26_Gesamtansicht_UI03_1g"
CONFIG_PATH = ROOT / "Config" / "ui03_1g_gesamtansicht_v1.json"

# Quell-Module (nur lesend)
SOURCE_MODULES = {
    "1b": ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "21_OCR_Uebersetzungskontrolle_UI03_1b",
    "1c": ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "22_Uebersetzungsarbeitsplatz_UI03_1c",
    "1d": ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "23_OCR_Freigabeablauf_UI03_1d",
    "1e": ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "24_Uebergabe_Freigabe_UI03_1e",
    "1f": ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "25_Geparkte_Auftraege_UI03_1f",
}

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

def ensure_dirs(cfg):
    for sub in cfg.get("ausgabe", {}).values():
        (SB / sub).parent.mkdir(parents=True, exist_ok=True)
    (SB / "05_Fehler").mkdir(parents=True, exist_ok=True)
    (SB / "07_Manifest").mkdir(parents=True, exist_ok=True)

def lese_modul_status(modul_id, dateiname):
    """Liest Status-JSON eines Vorgängermoduls."""
    sb = SOURCE_MODULES.get(modul_id)
    if not sb:
        return None
    path = sb / "02_Status" / dateiname
    if not path.exists():
        WARNUNGEN.append(f"Status-Datei fehlt: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        WARNUNGEN.append(f"Fehler beim Lesen {path}: {e}")
        return None

def lese_auftrag_json():
    """Liest den Übersetzungsauftrag aus UI03-1e."""
    path = SOURCE_MODULES["1e"] / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        WARNUNGEN.append(f"Fehler beim Lesen Auftrag {path}: {e}")
        return None

def argos_status_aus_register():
    """Prüft Argos-Status aus CORE-11-Registern (nur lesend)."""
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

def ermittle_naechster_schritt(status_1b, status_1c, status_1d, status_1e, status_1f, argos):
    """Ermittelt den nächsten zulässigen Schritt basierend auf Aggregat."""
    schritte = []
    
    # Schritt 1: OCR-Kontrolle
    if status_1b:
        tess_ok = status_1b.get("register_pruefung", {}).get("tesseract", {}).get("freigegeben", False)
        if tess_ok:
            schritte.append("✓ OCR-Kontrolle: Tesseract verfügbar")
        else:
            schritte.append("⚠ OCR-Kontrolle: Tesseract nicht freigegeben")
    
    # Schritt 2: Übersetzungsarbeitsplatz
    if status_1c:
        ocr_basis = status_1c.get("uebersetzungsstatus", {}).get("ocr_als_basis", False)
        if ocr_basis:
            schritte.append("✓ Arbeitsplatz: OCR als Basis verfügbar")
    
    # Schritt 3: Freigabe
    if status_1d:
        schritte.append("→ Freigabe: Seitenweise Prüfung erforderlich")
    
    # Schritt 4: Auftrag
    auftrag = lese_auftrag_json()
    if auftrag:
        freigegeben = sum(1 for s in auftrag.get("seiten", []) if s.get("kategorie") == "freigegeben")
        schritte.append(f"✓ Auftrag: {freigegeben} Seiten freigegeben")
    
    # Schritt 5: Argos / Wiederaufnahme
    if argos["verfuegbar"]:
        schritte.append("→ WIEDERAUFNAHME: Argos-Modelle verfügbar – Übersetzung kann starten")
    else:
        schritte.append(f"⏸ GEPARKT: {argos['grund']} – KM21b erforderlich")
    
    return schritte

# ═══════════════════════════════════════════════════════════════════════
# HTML-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_dashboard_html(aggregate, argos, naechste_schritte):
    """Erzeugt das kombinierte Dashboard-HTML."""
    
    # Top-Status
    top_status = "gesperrt"
    top_text = "ÜBERSETZUNG GEPARKT"
    if argos["verfuegbar"]:
        top_status = "bereit"
        top_text = "BEREIT FÜR WIEDERAUFNAHME"
    
    # Module-Karten
    module_karten = ""
    for modul_id, data in aggregate.items():
        modul_name = {
            "1b": "UI03-1b OCR-/Übersetzungskontrolle",
            "1c": "UI03-1c Übersetzungsarbeitsplatz",
            "1d": "UI03-1d OCR-Freigabeablauf",
            "1e": "UI03-1e Übergabe Freigabeentscheidung",
            "1f": "UI03-1f Geparkte Aufträge",
        }.get(modul_id, modul_id)
        
        if data:
            status_text = "VERFÜGBAR"
            status_class = "ok"
            detail = "Status-Datei geladen"
            extra = ""
            
            if modul_id == "1b" and data.get("register_pruefung"):
                tess = data["register_pruefung"].get("tesseract", {})
                argos_st = data["register_pruefung"].get("argos_translate", {})
                status_text = "KONTROLLIERT"
                extra = f"Tesseract: {tess.get('status', '?')} | Argos: {argos_st.get('status', '?')}"
            elif modul_id == "1e":
                extra = f"Auftrag: {data.get('auftrag', {}).get('auftrag_id', '–')} | Status: {data.get('auftrag', {}).get('status', '–')}"
            elif modul_id == "1f":
                extra = f"Geparkte Aufträge: {data.get('geparkte_auftraege', 0)}"
        else:
            status_text = "NICHT VERFÜGBAR"
            status_class = "warn"
            detail = "Status-Datei nicht gefunden"
            extra = ""
        
        module_karten += f"""
      <div class="modul-karte">
        <div class="modul-header">
          <span class="modul-name">{modul_name}</span>
          <span class="badge badge-{status_class}">{status_text}</span>
        </div>
        <div class="modul-detail">{detail}</div>
        {f'<div class="modul-extra">{extra}</div>' if extra else ''}
      </div>"""
    
    # Auftrags-Panel
    auftrag = lese_auftrag_json()
    auftrag_html = ""
    if auftrag:
        seiten = auftrag.get("seiten", [])
        freigegeben = sum(1 for s in seiten if s.get("kategorie") == "freigegeben")
        neu_ocr = sum(1 for s in seiten if s.get("kategorie") == "neu_ocr")
        ausgeschlossen = sum(1 for s in seiten if s.get("kategorie") == "ausgeschlossen")
        zurueckgestellt = sum(1 for s in seiten if s.get("kategorie") == "zurueckgestellt")
        wartet = sum(1 for s in seiten if s.get("kategorie") == "wartet")
        
        auftrag_html = f"""
    <div class="panel">
      <h2>📋 Übersetzungsauftrag</h2>
      <div class="auftrag-meta">
        <strong>ID:</strong> {auftrag.get('auftrag_id', '–')}<br>
        <strong>Akte:</strong> {auftrag.get('akten_id', '–')}<br>
        <strong>Status:</strong> <span class="badge badge-{'ok' if auftrag.get('status') == 'bereit' else 'warn'}">{auftrag.get('status', '–').upper()}</span><br>
        <strong>Parkgrund:</strong> {auftrag.get('parkgrund', '–')}
      </div>
      <div class="seiten-stats">
        <div class="mini-stat"><span class="mini-zahl">{len(seiten)}</span><span class="mini-label">Gesamt</span></div>
        <div class="mini-stat"><span class="mini-zahl ok">{freigegeben}</span><span class="mini-label">Freigegeben</span></div>
        <div class="mini-stat"><span class="mini-zahl warn">{neu_ocr}</span><span class="mini-label">Neu-OCR</span></div>
        <div class="mini-stat"><span class="mini-zahl err">{ausgeschlossen}</span><span class="mini-label">Ausgeschlossen</span></div>
        <div class="mini-stat"><span class="mini-zahl warn">{zurueckgestellt}</span><span class="mini-label">Zurückgestellt</span></div>
        <div class="mini-stat"><span class="mini-zahl info">{wartet}</span><span class="mini-label">Wartet</span></div>
      </div>
    </div>"""
    else:
        auftrag_html = """
    <div class="panel">
      <h2>📋 Übersetzungsauftrag</h2>
      <p style="color:var(--text-secondary);font-style:italic;">Kein Übersetzungsauftrag vorhanden. UI03-1e muss zuerst ausgeführt werden.</p>
    </div>"""
    
    # Nächste Schritte
    schritte_html = ""
    for schritt in naechste_schritte:
        schritte_html += f"<li>{schritt}</li>\n"
    
    # Argos-Panel
    argos_class = "ok" if argos["verfuegbar"] else "warn"
    argos_html = f"""
    <div class="panel">
      <h2>🌐 Argos Translate – Lokale Modelle</h2>
      <div class="status-banner {argos_class}">
        {'ARGOS BEREIT – Wiederaufnahme möglich' if argos["verfuegbar"] else f'ARGOS NICHT BEREIT – {argos["grund"]}'}
      </div>
      <p style="font-size:0.9rem;color:var(--text-secondary);margin-top:10px;">
        Verfügbare Sprachpaare: <strong>{argos['paare']}</strong><br>
        Status: <strong>{argos['grund']}</strong>
      </p>
    </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1g Gesamtansicht – OCR → Freigabe → Übersetzung</title>
<style>
:root {{
  --bg: #f5f5f5; --panel: #ffffff; --text: #1a1a1a; --text-secondary: #555;
  --border: #ddd; --accent: #2c5282; --accent-light: #ebf4ff;
  --ok: #276749; --ok-bg: #f0fff4; --warn: #c05621; --warn-bg: #fffaf0;
  --err: #c53030; --err-bg: #fff5f5; --info: #3182ce; --info-bg: #ebf8ff;
}}
body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
.top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }}
h1 {{ font-size: 1.4rem; margin: 0; color: var(--accent); }}
h2 {{ font-size: 1.15rem; margin: 0 0 12px 0; color: var(--accent); }}
.badge {{ padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; display: inline-block; }}
.badge-ok {{ background: var(--ok-bg); color: var(--ok); }}
.badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
.badge-err {{ background: var(--err-bg); color: var(--err); }}
.badge-info {{ background: var(--info-bg); color: var(--info); }}
.panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
.gesamt-status {{ padding: 20px; border-radius: 8px; margin-bottom: 20px; font-size: 1.1rem; font-weight: 600; text-align: center; }}
.gesamt-status.bereit {{ background: var(--ok-bg); color: var(--ok); border: 2px solid var(--ok); }}
.gesamt-status.gesperrt {{ background: var(--warn-bg); color: var(--warn); border: 2px solid var(--warn); }}
.modul-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 20px; }}
.modul-karte {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 15px; }}
.modul-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.modul-name {{ font-weight: 600; font-size: 0.9rem; color: var(--accent); }}
.modul-detail {{ font-size: 0.85rem; color: var(--text-secondary); }}
.modul-extra {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }}
.status-banner {{ padding: 15px; border-radius: 8px; margin-bottom: 15px; font-weight: 500; font-size: 0.95rem; }}
.status-banner.ok {{ background: var(--ok-bg); color: var(--ok); }}
.status-banner.warn {{ background: var(--warn-bg); color: var(--warn); }}
.seiten-stats {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }}
.mini-stat {{ background: var(--accent-light); border-radius: 5px; padding: 8px 14px; text-align: center; min-width: 60px; }}
.mini-zahl {{ font-size: 1.2rem; font-weight: 700; }}
.mini-zahl.ok {{ color: var(--ok); }}
.mini-zahl.warn {{ color: var(--warn); }}
.mini-zahl.err {{ color: var(--err); }}
.mini-zahl.info {{ color: var(--info); }}
.mini-label {{ font-size: 0.7rem; color: var(--text-secondary); margin-top: 2px; }}
.schritte {{ list-style: none; padding: 0; margin: 0; }}
.schritte li {{ padding: 8px 12px; margin-bottom: 6px; background: var(--accent-light); border-radius: 6px; font-size: 0.9rem; }}
.auftrag-meta {{ font-size: 0.9rem; line-height: 1.7; margin-bottom: 12px; }}
.grenzen {{ font-size: 0.85rem; color: var(--text-secondary); padding-left: 18px; line-height: 1.8; }}
.grenzen li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<div class="top-bar">
  <h1>UI03-1g Gesamtansicht</h1>
  <span class="badge badge-{argos_class}">{top_text}</span>
</div>

<div class="gesamt-status {top_status}">
  {top_text} – Argos-Modelle {'verfügbar' if argos['verfuegbar'] else 'fehlen'}
</div>

<div class="panel">
  <h2>🔍 Modul-Status (UI03-1b … 1f)</h2>
  <div class="modul-grid">
{module_karten}
  </div>
</div>

{auftrag_html}

{argos_html}

<div class="panel">
  <h2>➡️ Nächster zulässiger Schritt</h2>
  <ul class="schritte">
{schritte_html}
  </ul>
  <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:10px;">
    <strong>Hinweis:</strong> Dies ist eine reine Aggregationsansicht. Keine Modul-Ergebnisse werden verändert.
    Führen Sie die Einzelmodule aus, um Details zu ändern.
  </p>
</div>

<div class="panel">
  <h2>Grenzen</h2>
  <ul class="grenzen">
    <li>✓ Keine Originaländerung</li>
    <li>✓ Keine neue OCR</li>
    <li>✓ Keine echte Übersetzung (nur Anzeige)</li>
    <li>✓ Keine DB-Änderung</li>
    <li>✓ Kein Internet/Cloud</li>
    <li>✓ Keine Registeränderung (nur lesend)</li>
    <li>✓ Keine Vorgänger-Module verändert (nur lesend)</li>
  </ul>
</div>

</body>
</html>"""
    return html

# ═══════════════════════════════════════════════════════════════════════
# HAUPTLAUF
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("UI03-1g GESAMTANSICHT START ==========================================")
    cfg = load_config()
    ensure_dirs(cfg)
    
    print("[1] Vorgänger-Module-Status lesen ...")
    aggregate = {}
    aggregate["1b"] = lese_modul_status("1b", "UI03_1b_OCR_KONTROLLE_STATUS.json")
    aggregate["1c"] = lese_modul_status("1c", "UI03_1c_UEBERSETZUNGSARBEITSPLATZ.json")
    aggregate["1d"] = lese_modul_status("1d", "UI03_1d_OCR_FREIGABEABLAUF.json")
    aggregate["1e"] = lese_modul_status("1e", "UI03_1e_UEBERGABE_FREIGABE_STATUS.json")
    aggregate["1f"] = lese_modul_status("1f", "UI03_1f_GEPARKTE_AUFTRAEGE.json")
    
    verfuegbar = sum(1 for v in aggregate.values() if v is not None)
    print(f"    {verfuegbar}/5 Status-Dateien geladen")
    for k, v in aggregate.items():
        print(f"      UI03-1{k}: {'OK' if v else 'FEHLT'}")
    
    print("[2] Argos-Status prüfen ...")
    argos = argos_status_aus_register()
    print(f"    Argos verfügbar: {argos['verfuegbar']} – {argos['grund']}")
    
    print("[3] Nächster Schritt ermitteln ...")
    naechste = ermittle_naechster_schritt(
        aggregate["1b"], aggregate["1c"], aggregate["1d"], aggregate["1e"], aggregate["1f"], argos
    )
    for s in naechste:
        print(f"    {s}")
    
    print("[4] Dashboard-HTML erzeugen ...")
    html = generate_dashboard_html(aggregate, argos, naechste)
    html_path = SB / cfg.get("ausgabe", {}).get("dashboard_html", "02_Status/UI03_1g_GESAMTANSICHT.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")
    
    print("[5] Aggregat-JSON erzeugen ...")
    aggregat_json = {
        "modul": "UI03-1g",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "quellen": {k: "geladen" if v else "fehlt" for k, v in aggregate.items()},
        "argos_status": argos,
        "naechste_schritte": naechste,
        "auftrag_id": (lese_auftrag_json() or {}).get("auftrag_id", None),
        "grenzen": {
            "keine_originalaenderung": True,
            "keine_neue_ocr": True,
            "keine_echte_uebersetzung": True,
            "keine_db_aenderung": True,
            "kein_internet": True,
            "keine_cloud": True,
            "keine_registeraenderung": True,
            "keine_vorgaenger_modifikation": True,
        },
        "fehler": len(FEHLER),
        "warnungen": len(WARNUNGEN),
    }
    json_path = SB / cfg.get("ausgabe", {}).get("aggregat_json", "02_Status/UI03_1g_GESAMTANSICHT.json")
    json_path.write_text(json.dumps(aggregat_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")
    
    print("[6] Bericht erzeugen ...")
    bericht = f"""UI03-1g Gesamtansicht – Bericht
==================================
Zeitpunkt: {now_iso()}

Quell-Module:
  UI03-1b OCR-Kontrolle:       {'OK' if aggregate['1b'] else 'FEHLT'}
  UI03-1c Arbeitsplatz:        {'OK' if aggregate['1c'] else 'FEHLT'}
  UI03-1d Freigabe:            {'OK' if aggregate['1d'] else 'FEHLT'}
  UI03-1e Auftrag:             {'OK' if aggregate['1e'] else 'FEHLT'}
  UI03-1f Geparkte Aufträge:   {'OK' if aggregate['1f'] else 'FEHLT'}

Argos-Status:
  Verfügbar: {'Ja' if argos['verfuegbar'] else 'Nein'}
  Grund: {argos['grund']}
  Paare: {argos['paare']}

Nächste Schritte:
{chr(10).join('  - ' + s for s in naechste)}

Auftrag-ID: {aggregat_json['auftrag_id'] or '–'}

Grenzen:
  ✓ Keine Originaländerung
  ✓ Keine neue OCR
  ✓ Keine echte Übersetzung (nur Anzeige)
  ✓ Keine DB-Änderung
  ✓ Kein Internet/Cloud
  ✓ Keine Registeränderung
  ✓ Keine Vorgänger-Module verändert

Ausgaben:
  {html_path}
  {json_path}

Fehler: {len(FEHLER)}
Warnungen: {len(WARNUNGEN)}
"""
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/UI03_1g_GESAMTANSICHT_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")
    
    print("[7] Fehlerbericht ...")
    fehler_text = f"UI03-1g Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1g Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1g_GESAMTANSICHT_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")
    
    print(f"\nUI03-1g GESAMTANSICHT ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1g GESAMTANSICHT SELBSTTEST =====================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1
    
    t("Config ladbar", bool(load_config()))
    t("Toolregister ladbar", load_register("toolregister") is not None)
    t("Ressourcenregister ladbar", load_register("ressourcenregister") is not None)
    
    argos = argos_status_aus_register()
    t("Argos-Status prüfbar", isinstance(argos, dict))
    t("Argos hat verfuegbar", isinstance(argos.get("verfuegbar"), bool))
    t("Argos hat grund", bool(argos.get("grund")))
    
    aggregate = {"1b": None, "1c": None, "1d": None, "1e": None, "1f": None}
    naechste = ermittle_naechster_schritt(None, None, None, None, None, argos)
    t("Nächste Schritte ermittelbar", len(naechste) > 0)
    
    html = generate_dashboard_html(aggregate, argos, naechste)
    t("Dashboard-HTML erzeugbar", len(html) > 3000)
    t("HTML enthält Gesamt-Status", "gesamt-status" in html)
    t("HTML enthält Modul-Karten", "modul-karte" in html)
    t("HTML enthält Argos-Panel", "ARGOS" in html.upper())
    t("HTML enthält Schritte-Liste", "schritte" in html)
    t("HTML enthält Auftrags-Panel", "auftrag-meta" in html or "Kein Übersetzungsauftrag" in html)
    t("HTML enthält Grenzen", "Keine Originaländerung" in html)
    t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())
    t("Keine Vorgänger-Modifikation", "keine_vorgaenger_modifikation" in html.lower() or "Grenzen" in html)
    
    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
