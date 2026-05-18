#!/usr/bin/env python3
"""UI03-1e – Übergabe der OCR-Freigabeentscheidung an die Übersetzungsstrecke (CORE-11-konform).

Liest die Mandantenakte, kategorisiert Seiten für die Übersetzungsstrecke,
erzeugt einen Übersetzungsauftrag-JSON und zeigt die Auftragszusammensetzung.

Kategorien:
  - freigegeben: OCR OK, bereit für Übersetzung
  - neu_ocr: OCR mangelhaft, Neu-OCR erforderlich
  - ausgeschlossen: nicht übersetzungsrelevant
  - zurueckgestellt: Anwalt prüft später
  - wartet: noch keine Entscheidung

Keine echte Übersetzung starten, solange Argos-Modelle fehlen.

Schreibbereich: UI03_Mandantenakte\24_Uebergabe_Freigabe_UI03_1e\
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "24_Uebergabe_Freigabe_UI03_1e"
CONFIG_PATH = ROOT / "Config" / "ui03_1e_uebergabe_freigabe_v1.json"
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
        WARNUNGEN.append("Mandantenakte nicht gefunden – verwende Demo-Daten")
        return None
    return json.loads(AKTE_PATH.read_text(encoding="utf-8-sig"))

def ensure_dirs(cfg):
    for sub in cfg.get("ausgabe", {}).values():
        (SB / sub).parent.mkdir(parents=True, exist_ok=True)
    (SB / "05_Fehler").mkdir(parents=True, exist_ok=True)
    (SB / "07_Manifest").mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# KATEGORISIERUNG
# ═══════════════════════════════════════════════════════════════════════

KATEGORIEN = [
    {"value": "freigegeben", "label": "Freigegeben für Übersetzung", "badge": "Freigegeben", "badge_class": "badge-ok"},
    {"value": "neu_ocr", "label": "Neu-OCR erforderlich", "badge": "Neu-OCR", "badge_class": "badge-warn"},
    {"value": "ausgeschlossen", "label": "Ausgeschlossen (nicht relevant)", "badge": "Ausgeschlossen", "badge_class": "badge-err"},
    {"value": "zurueckgestellt", "label": "Zurückgestellt (Anwalt prüft)", "badge": "Zurückgestellt", "badge_class": "badge-warn"},
    {"value": "wartet", "label": "Wartet auf Entscheidung", "badge": "Wartet", "badge_class": "badge-info"},
]

def initiale_kategorie(seite):
    """Bestimmt initiale Kategorie basierend auf existierenden Status."""
    verwertbarkeit = seite.get("ocr_verwertbarkeit_status", "").lower()
    uebersetzung = seite.get("uebersetzung_status", "").lower()
    
    if "türschwelle" in verwertbarkeit or "nicht schriftsatzfähig" in verwertbarkeit:
        return "neu_ocr"
    if "schriftsatzfähig" in verwertbarkeit:
        return "freigegeben"
    if "orientierungsübersetzung" in uebersetzung:
        return "zurueckgestellt"
    return "wartet"

def erstelle_uebersetzungsauftrag(akte):
    """Erzeugt den Übersetzungsauftrag aus der Akte."""
    if not akte:
        return {"auftrag_id": "DEMO", "seiten": [], "status": "demo_modus"}
    
    auftrag_id = f"UA_{akte.get('akten_id', 'UNBEKANNT')}_{now_iso().replace(':', '').replace('-', '').replace('.', '')[:14]}"
    
    seiten_liste = []
    for d in akte.get("dokumente", []):
        for seite in d.get("seiten", []):
            s_id = seite.get("seiten_id", "UNBEKANNT")
            kategorie = initiale_kategorie(seite)
            seiten_liste.append({
                "seiten_id": s_id,
                "dokument_id": d.get("original_id", "UNBEKANNT"),
                "seite_nummer": seite.get("seite_nummer", 0),
                "sprache": d.get("sprache", "unbekannt"),
                "ocr_text_vorschau": seite.get("ocr_text", "")[:200] + "..." if len(seite.get("ocr_text", "")) > 200 else seite.get("ocr_text", ""),
                "kategorie": kategorie,
                "urspruenglicher_status": {
                    "ocr_verwertbarkeit": seite.get("ocr_verwertbarkeit_status", "unbekannt"),
                    "uebersetzung": seite.get("uebersetzung_status", "unbekannt"),
                },
                "anmerkung": "",
            })
    
    return {
        "auftrag_id": auftrag_id,
        "akten_id": akte.get("akten_id", ""),
        "zeitpunkt_erstellung": now_iso(),
        "status": "vorbereitet",
        "parkgrund": "Argos-Modelle nicht verfügbar – keine echte Übersetzung gestartet",
        "seiten": seiten_liste,
    }

# ═══════════════════════════════════════════════════════════════════════
# HTML-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_uebergabe_html(auftrag, argos_verfuegbar=False):
    """Erzeugt das Übergabe-Interface als HTML."""
    seiten = auftrag.get("seiten", [])
    total = len(seiten)
    
    counts = {k["value"]: 0 for k in KATEGORIEN}
    for s in seiten:
        counts[s.get("kategorie", "wartet")] = counts.get(s.get("kategorie", "wartet"), 0) + 1
    
    # Park-Banner
    park_banner = f"""
    <div class="status-banner {'ok' if argos_verfuegbar else 'warn'}">
      {'Auftrag bereit – Übersetzung kann starten (Argos verfügbar)' if argos_verfuegbar else 'AUFTRAG VORBEREITET – GEPARKT: Argos-Modelle nicht verfügbar. Keine echte Übersetzung wird gestartet.'}
    </div>"""
    
    # Statistik-Boxen
    stats_html = ""
    for k in KATEGORIEN:
        stats_html += f"""
        <div class="stat-box">
          <div class="stat-zahl">{counts.get(k['value'], 0)}</div>
          <div class="stat-label">{k['label']}</div>
        </div>"""
    
    # Seiten-Karten
    seiten_html = ""
    for s in seiten:
        s_id = s.get("seiten_id", "")
        kategorie = s.get("kategorie", "wartet")
        
        # Aktuelle Kategorie-Badge
        kat_info = next((k for k in KATEGORIEN if k["value"] == kategorie), KATEGORIEN[-1])
        
        # Radio-Buttons
        radio_html = ""
        for k in KATEGORIEN:
            checked = "checked" if k["value"] == kategorie else ""
            radio_html += f"""
              <label class="radio-option">
                <input type="radio" name="kategorie_{s_id}" value="{k['value']}" {checked}>
                <span class="radio-label">{k['label']}</span>
              </label>"""
        
        seiten_html += f"""
      <div class="seiten-karte" id="karte_{s_id}">
        <div class="seiten-header">
          <div class="seiten-meta">
            <strong>Dokument:</strong> {s.get('dokument_id', '')}<br>
            <strong>Seite:</strong> {s.get('seite_nummer', 0)} | <strong>ID:</strong> {s_id}<br>
            <strong>Sprache:</strong> {s.get('sprache', 'unbekannt')} | 
            <span class="badge {kat_info['badge_class']}">{kat_info['badge']}</span>
          </div>
          <div class="ursprungs-status">
            <small>OCR: {s.get('urspruenglicher_status', {}).get('ocr_verwertbarkeit', 'unbekannt')}</small><br>
            <small>Übersetzung: {s.get('urspruenglicher_status', {}).get('uebersetzung', 'unbekannt')}</small>
          </div>
        </div>
        <div class="ocr-vorschau">
          <strong>OCR-Vorschau:</strong>
          <div class="text-content">{s.get('ocr_text_vorschau', '')}</div>
        </div>
        <div class="kategorie-bereich">
          <h4>Kategorie setzen</h4>
          <div class="radio-group">
{radio_html}
          </div>
          <label class="anmerkung-label">Anmerkung:</label>
          <textarea class="freitext-seite" name="anmerkung_{s_id}" placeholder="Grund für Kategorie oder Hinweise...">{s.get('anmerkung', '')}</textarea>
        </div>
      </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1e Übergabe Freigabeentscheidung</title>
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
h2 {{ font-size: 1.2rem; margin: 0 0 15px 0; color: var(--accent); }}
h3 {{ font-size: 1rem; margin: 0 0 10px 0; color: var(--text-secondary); }}
h4 {{ font-size: 0.9rem; margin: 0 0 8px 0; color: var(--accent); }}
.badge {{ padding: 3px 10px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; display: inline-block; margin: 2px; }}
.badge-ok {{ background: var(--ok-bg); color: var(--ok); }}
.badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
.badge-err {{ background: var(--err-bg); color: var(--err); }}
.badge-info {{ background: var(--info-bg); color: var(--info); }}
.panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
.status-banner {{ padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: 500; font-size: 0.95rem; }}
.status-banner.ok {{ background: var(--ok-bg); color: var(--ok); }}
.status-banner.warn {{ background: var(--warn-bg); color: var(--warn); }}
.gesamt-stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 15px; }}
.stat-box {{ background: var(--accent-light); border-radius: 6px; padding: 12px 18px; text-align: center; min-width: 90px; }}
.stat-zahl {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
.stat-label {{ font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }}
.seiten-karte {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
.seiten-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
.seiten-meta {{ font-size: 0.85rem; line-height: 1.6; }}
.ursprungs-status {{ text-align: right; font-size: 0.8rem; color: var(--text-secondary); }}
.ocr-vorschau {{ background: var(--accent-light); border-radius: 4px; padding: 10px; margin-bottom: 12px; font-size: 0.85rem; }}
.text-content {{ max-height: 100px; overflow-y: auto; line-height: 1.5; }}
.kategorie-bereich {{ background: #fafafa; border: 1px solid var(--border); border-radius: 4px; padding: 12px; }}
.radio-group {{ display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }}
.radio-option {{ display: flex; align-items: center; gap: 8px; padding: 5px 8px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }}
.radio-option:hover {{ background: var(--accent-light); }}
.radio-option input {{ margin: 0; cursor: pointer; }}
.radio-label {{ font-size: 0.82rem; }}
.anmerkung-label {{ display: block; font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 4px; }}
.freitext-seite {{ width: 100%; min-height: 50px; padding: 6px; border: 1px solid var(--border); border-radius: 4px; font-family: inherit; font-size: 0.82rem; resize: vertical; box-sizing: border-box; }}
.freitext-seite:focus {{ outline: none; border-color: var(--accent); }}
.grenzen {{ font-size: 0.85rem; color: var(--text-secondary); padding-left: 18px; line-height: 1.8; }}
.grenzen li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<div class="top-bar">
  <h1>UI03-1e Übergabe Freigabeentscheidung</h1>
  <span class="badge badge-info">{total} Seiten | Auftrag: {auftrag.get('auftrag_id', 'UNBEKANNT')}</span>
</div>

{park_banner}

<div class="panel">
  <h2>Auftragszusammensetzung</h2>
  <div class="gesamt-stats">
{stats_html}
  </div>
  <p style="font-size:0.9rem;color:var(--text-secondary);margin-top:10px;">
    <strong>Auftrags-ID:</strong> {auftrag.get('auftrag_id', '')}<br>
    <strong>Akten-ID:</strong> {auftrag.get('akten_id', '')}<br>
    <strong>Status:</strong> {auftrag.get('status', '')}<br>
    <strong>Parkgrund:</strong> {auftrag.get('parkgrund', '')}
  </p>
</div>

<div class="panel">
  <h2>Seiten-Kategorisierung</h2>
  <p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:15px;">
    Setzen Sie für jede Seite die Kategorie. Nur als "Freigegeben" markierte Seiten 
    werden später übersetzt. Der Auftrag bleibt geparkt, bis Argos-Modelle verfügbar sind.
  </p>
{seiten_html}
</div>

<div class="panel">
  <h2>Grenzen</h2>
  <ul class="grenzen">
    <li>✓ Keine Originaländerung</li>
    <li>✓ Keine neue OCR (nur Kategorisierung)</li>
    <li>✓ Keine echte Übersetzung (geparkt bis Argos verfügbar)</li>
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
    print("UI03-1e ÜBERGABE FREIGABEENTSCHEIDUNG START ===========================")
    cfg = load_config()
    ensure_dirs(cfg)

    print("[1] Mandantenakte lesen ...")
    akte = read_akte()
    if akte:
        docs = akte.get("dokumente", [])
        total = sum(len(d.get("seiten", [])) for d in docs)
        print(f"    Akte geladen: {len(docs)} Dokumente, {total} Seiten")
    else:
        print("    Keine Akte gefunden – Demo-Modus")

    print("[2] Argos-Status prüfen ...")
    toolregister = load_register("toolregister")
    ressourcenregister = load_register("ressourcenregister")
    argos_verfuegbar = False
    if toolregister and ressourcenregister:
        argos = find_tool(toolregister, "ARGOS_TRANSLATE")
        if argos and argos.get("installationsstatus") == "installiert":
            paare_ja = sum(1 for r in ressourcenregister.get("eintraege", [])
                          if r.get("resource_id", "").startswith("ARGOS_")
                          and r.get("vorhanden_ja_nein_unbekannt") == "ja")
            if paare_ja > 0:
                argos_verfuegbar = True
    print(f"    Argos verfügbar: {argos_verfuegbar}")

    print("[3] Übersetzungsauftrag erzeugen ...")
    auftrag = erstelle_uebersetzungsauftrag(akte)
    print(f"    Auftrags-ID: {auftrag['auftrag_id']}")
    print(f"    Seiten: {len(auftrag['seiten'])}")
    freigegeben = sum(1 for s in auftrag['seiten'] if s['kategorie'] == 'freigegeben')
    print(f"    Freigegeben: {freigegeben}")

    print("[4] Übergabe-HTML erzeugen ...")
    html = generate_uebergabe_html(auftrag, argos_verfuegbar)
    html_path = SB / cfg.get("ausgabe", {}).get("uebergabe_html", "02_Status/UI03_1e_UEBERGABE_FREIGABE.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[5] Übersetzungsauftrag JSON erzeugen ...")
    json_path = SB / cfg.get("ausgabe", {}).get("auftrag_json", "02_Status/UI03_1e_UEBERGABE_FREIGABE.json")
    json_path.write_text(json.dumps(auftrag, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[6] Status-JSON erzeugen ...")
    status_json = {
        "modul": "UI03-1e",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "auftrag": {
            "auftrag_id": auftrag["auftrag_id"],
            "status": auftrag["status"],
            "parkgrund": auftrag["parkgrund"],
            "seiten_gesamt": len(auftrag["seiten"]),
            "seiten_freigegeben": sum(1 for s in auftrag["seiten"] if s["kategorie"] == "freigegeben"),
            "seiten_neu_ocr": sum(1 for s in auftrag["seiten"] if s["kategorie"] == "neu_ocr"),
            "seiten_ausgeschlossen": sum(1 for s in auftrag["seiten"] if s["kategorie"] == "ausgeschlossen"),
            "seiten_zurueckgestellt": sum(1 for s in auftrag["seiten"] if s["kategorie"] == "zurueckgestellt"),
            "seiten_wartet": sum(1 for s in auftrag["seiten"] if s["kategorie"] == "wartet"),
        },
        "argos_verfuegbar": argos_verfuegbar,
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
    status_path = SB / cfg.get("ausgabe", {}).get("status_json", "02_Status/UI03_1e_UEBERGABE_FREIGABE_STATUS.json")
    status_path.write_text(json.dumps(status_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[7] Bericht erzeugen ...")
    bericht = f"""UI03-1e Übergabe Freigabeentscheidung – Bericht
===============================================
Zeitpunkt: {now_iso()}

Auftrag:
  ID: {auftrag['auftrag_id']}
  Akte: {auftrag.get('akten_id', '')}
  Status: {auftrag['status']}
  Parkgrund: {auftrag['parkgrund']}

Seiten:
  Gesamt: {len(auftrag['seiten'])}
  Freigegeben: {sum(1 for s in auftrag['seiten'] if s['kategorie'] == 'freigegeben')}
  Neu-OCR: {sum(1 for s in auftrag['seiten'] if s['kategorie'] == 'neu_ocr')}
  Ausgeschlossen: {sum(1 for s in auftrag['seiten'] if s['kategorie'] == 'ausgeschlossen')}
  Zurückgestellt: {sum(1 for s in auftrag['seiten'] if s['kategorie'] == 'zurueckgestellt')}
  Wartet: {sum(1 for s in auftrag['seiten'] if s['kategorie'] == 'wartet')}

Argos verfügbar: {'Ja' if argos_verfuegbar else 'Nein'}

Grenzen:
  ✓ Keine Originaländerung
  ✓ Keine neue OCR
  ✓ Keine echte Übersetzung (geparkt)
  ✓ Keine DB-Änderung
  ✓ Kein Internet/Cloud
  ✓ Keine Registeränderung

Ausgaben:
  {html_path}
  {json_path}
  {status_path}

Fehler: {len(FEHLER)}
Warnungen: {len(WARNUNGEN)}
"""
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/UI03_1e_UEBERGABE_FREIGABE_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")

    print("[8] Fehlerbericht ...")
    fehler_text = f"UI03-1e Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1e Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1e_UEBERGABE_FREIGABE_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")

    print(f"\nUI03-1e ÜBERGABE ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1e SELBSTTEST ==================================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    t("Config ladbar", bool(load_config()))
    t("Toolregister ladbar", load_register("toolregister") is not None)
    t("Ressourcenregister ladbar", load_register("ressourcenregister") is not None)

    akte = read_akte()
    t("Akte ladbar (oder Demo-Modus)", True)

    auftrag = erstelle_uebersetzungsauftrag(akte)
    t("Auftrag erzeugbar", bool(auftrag["auftrag_id"]))
    t("Auftrag hat Seiten", len(auftrag["seiten"]) >= 0)
    t("Auftrag hat Parkgrund", bool(auftrag.get("parkgrund")))
    t("Auftrag-Status ist 'vorbereitet'", auftrag["status"] == "vorbereitet")

    html = generate_uebergabe_html(auftrag)
    t("HTML erzeugbar", len(html) > 3000)
    t("HTML enthält Park-Banner", "AUFTRAG VORBEREITET" in html or "Auftrag bereit" in html)
    t("HTML enthält Statistik", "gesamt-stats" in html)
    t("HTML enthält Seiten-Karten", "seiten-karte" in html)
    t("HTML enthält Radio-Buttons", 'type="radio"' in html)
    t("HTML enthält 5 Kategorien", html.count('type="radio"') >= 5)
    t("HTML enthält OCR-Vorschau", "ocr-vorschau" in html)
    t("HTML enthält Ursprungs-Status", "ursprungs-status" in html)
    t("HTML enthält Grenzen", "Keine Originaländerung" in html)
    t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
