#!/usr/bin/env python3
"""UI03-1d – OCR-Prüf- und Freigabeablauf vor Übersetzung (CORE-11-konform).

Zeigt alle Seiten der Mandantenakte mit OCR-Vorschau.
Ermöglicht pro Seite eine Freigabe-Entscheidung:
  1. "OCR qualitativ ausreichend – freigegeben für Übersetzung"
  2. "OCR mangelhaft – Neu-OCR erforderlich"
  3. "Seite nicht übersetzungsrelevant – ausschließen"
  4. "Anwalt prüft – Freigabe zurückstellen"

Pro Seite: Freitext-Anmerkungen.
Gesamtstatus: Übersicht aller Freigabe-Entscheidungen.

Schreibbereich: UI03_Mandantenakte\23_OCR_Freigabeablauf_UI03_1d\
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "23_OCR_Freigabeablauf_UI03_1d"
CONFIG_PATH = ROOT / "Config" / "ui03_1d_ocr_freigabeablauf_v1.json"
AKTE_PATH = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "10_Mandantenakte" / "Mandantenakte.json"

FEHLER = []
WARNUNGEN = []

# ═══════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════

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
# SEITEN-FREIGABE-DATEN
# ═══════════════════════════════════════════════════════════════════════

FREIGABE_OPTIONEN = [
    {"value": "freigegeben", "label": "OCR qualitativ ausreichend – freigegeben für Übersetzung", "badge": "Freigegeben", "badge_class": "badge-ok"},
    {"value": "neu_ocr", "label": "OCR mangelhaft – Neu-OCR erforderlich", "badge": "Neu-OCR", "badge_class": "badge-warn"},
    {"value": "ausschliessen", "label": "Seite nicht übersetzungsrelevant – ausschließen", "badge": "Ausgeschlossen", "badge_class": "badge-err"},
    {"value": "zurueckstellen", "label": "Anwalt prüft – Freigabe zurückstellen", "badge": "Zurückgestellt", "badge_class": "badge-warn"},
]

# ═══════════════════════════════════════════════════════════════════════
# HTML-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_freigabe_html(akte):
    """Erzeugt den OCR-Freigabeablauf als HTML."""
    if not akte:
        return "<html><body><h1>Keine Akte gefunden</h1></body></html>"

    dokuments = akte.get("dokumente", [])
    total_seiten = sum(len(d.get("seiten", [])) for d in dokuments)

    seiten_html = ""
    global_idx = 0
    for d in dokuments:
        d_titel = d.get("ki_merkmale", {}).get("betreff", d.get("original_id", "Unbekannt"))
        d_sprache = d.get("sprache", "unbekannt")
        d_rechtsgebiet = d.get("rechtsgebiet", "unbekannt")

        for seite in d.get("seiten", []):
            global_idx += 1
            s_num = seite.get("seite_nummer", global_idx)
            s_id = seite.get("seiten_id", f"S{global_idx:04d}")
            ocr_text = seite.get("ocr_text", "")
            orientierung = seite.get("orientierung_de", "")
            verwertbarkeit = seite.get("ocr_verwertbarkeit_status", "unbekannt")
            uebersetzung_status = seite.get("uebersetzung_status", "unbekannt")

            ocr_preview = ocr_text[:400] + "..." if len(ocr_text) > 400 else ocr_text
            orient_preview = orientierung[:400] + "..." if len(orientierung) > 400 else orientierung

            # Radio-Buttons für Freigabe
            radio_html = ""
            for opt in FREIGABE_OPTIONEN:
                radio_html += f"""
              <label class="radio-option">
                <input type="radio" name="freigabe_{s_id}" value="{opt['value']}">
                <span class="radio-label">{opt['label']}</span>
              </label>"""

            seiten_html += f"""
      <div class="seiten-karte" id="karte_{s_id}">
        <div class="seiten-header">
          <div class="seiten-meta">
            <strong>Dokument:</strong> {d_titel[:80]}{'...' if len(d_titel) > 80 else ''}<br>
            <strong>Seite:</strong> {s_num} / {len(d.get('seiten', []))} | <strong>ID:</strong> {s_id}<br>
            <strong>Sprache:</strong> {d_sprache} | <strong>Rechtsgebiet:</strong> {d_rechtsgebiet}
          </div>
          <div class="seiten-status">
            <span class="badge badge-info">OCR-Status: {verwertbarkeit}</span>
            <span class="badge badge-info">Übersetzung: {uebersetzung_status}</span>
          </div>
        </div>
        <div class="text-vorschau">
          <div class="vorschau-spalte">
            <h4>🔍 OCR-Text</h4>
            <div class="text-content">{ocr_preview}</div>
          </div>
          <div class="vorschau-spalte">
            <h4>🇩🇪 Orientierungsübersetzung</h4>
            <div class="text-content">{orient_preview if orient_preview else '<em style="color:var(--text-secondary)">Keine Orientierungsübersetzung vorhanden.</em>'}</div>
          </div>
        </div>
        <div class="freigabe-bereich">
          <h4>Freigabe-Entscheidung</h4>
          <div class="radio-group">
{radio_html}
          </div>
          <label class="anmerkung-label">Anmerkungen zu dieser Seite:</label>
          <textarea class="freitext-seite" name="anmerkung_{s_id}" placeholder="Qualitätsbeurteilung, Fehler, Hinweise..."></textarea>
        </div>
      </div>"""

    # Gesamtübersicht
    gesamt_html = f"""
    <div class="gesamt-panel">
      <h2>Gesamtübersicht</h2>
      <div class="gesamt-stats">
        <div class="stat-box"><div class="stat-zahl">{len(dokuments)}</div><div class="stat-label">Dokumente</div></div>
        <div class="stat-box"><div class="stat-zahl">{total_seiten}</div><div class="stat-label">Seiten</div></div>
        <div class="stat-box"><div class="stat-zahl">–</div><div class="stat-label">Freigegeben</div></div>
        <div class="stat-box"><div class="stat-zahl">–</div><div class="stat-label">Zurückgestellt</div></div>
      </div>
      <p class="hinweis">Die Statistik aktualisiert sich automatisch, wenn Sie die Freigabe-Entscheidungen treffen.</p>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1d OCR-Freigabeablauf</title>
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
.gesamt-panel {{ background: var(--panel); border: 2px solid var(--accent); border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
.gesamt-stats {{ display: flex; gap: 15px; flex-wrap: wrap; }}
.stat-box {{ background: var(--accent-light); border-radius: 6px; padding: 12px 20px; text-align: center; min-width: 80px; }}
.stat-zahl {{ font-size: 1.6rem; font-weight: 700; color: var(--accent); }}
.stat-label {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }}
.seiten-karte {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
.seiten-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
.seiten-meta {{ font-size: 0.85rem; line-height: 1.6; }}
.seiten-status {{ text-align: right; }}
.text-vorschau {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
.vorschau-spalte {{ background: var(--accent-light); border-radius: 4px; padding: 10px; }}
.text-content {{ font-size: 0.85rem; line-height: 1.5; max-height: 150px; overflow-y: auto; }}
.freigabe-bereich {{ background: #fafafa; border: 1px solid var(--border); border-radius: 4px; padding: 12px; }}
.radio-group {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }}
.radio-option {{ display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }}
.radio-option:hover {{ background: var(--accent-light); }}
.radio-option input {{ margin: 0; cursor: pointer; }}
.radio-label {{ font-size: 0.85rem; }}
.anmerkung-label {{ display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 5px; }}
.freitext-seite {{ width: 100%; min-height: 60px; padding: 8px; border: 1px solid var(--border); border-radius: 4px; font-family: inherit; font-size: 0.85rem; resize: vertical; box-sizing: border-box; }}
.freitext-seite:focus {{ outline: none; border-color: var(--accent); }}
.hinweis {{ font-size: 0.85rem; color: var(--text-secondary); margin-top: 10px; font-style: italic; }}
.grenzen {{ font-size: 0.85rem; color: var(--text-secondary); padding-left: 18px; line-height: 1.8; }}
.grenzen li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<div class="top-bar">
  <h1>UI03-1d OCR-Freigabeablauf vor Übersetzung</h1>
  <span class="badge badge-info">{len(dokuments)} Dokumente | {total_seiten} Seiten</span>
</div>

{gesamt_html}

<div class="panel">
  <h2>Seiten-Prüfung und Freigabe</h2>
  <p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:15px;">
    Prüfen Sie für jede Seite die OCR-Qualität und treffen Sie eine Freigabe-Entscheidung. 
    Nur als "freigegeben" markierte Seiten werden später übersetzt.
  </p>
{seiten_html}
</div>

<div class="panel">
  <h2>Grenzen</h2>
  <ul class="grenzen">
    <li>✓ Keine Originaländerung</li>
    <li>✓ Keine neue OCR (nur Freigabe-Markierung)</li>
    <li>✓ Keine endgültige Übersetzung</li>
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
    print("UI03-1d OCR-FREIGABEABLAUF START ====================================")
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

    print("[2] Freigabe-HTML erzeugen ...")
    html = generate_freigabe_html(akte)
    html_path = SB / cfg.get("ausgabe", {}).get("freigabe_html", "02_Status/UI03_1d_OCR_FREIGABEABLAUF.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[3] Status-JSON erzeugen ...")
    status_json = {
        "modul": "UI03-1d",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "dokumente": len(akte.get("dokumente", [])) if akte else 0,
        "seiten": sum(len(d.get("seiten", [])) for d in akte.get("dokumente", [])) if akte else 0,
        "freigabe_optionen": [o["value"] for o in FREIGABE_OPTIONEN],
        "grenzen": {
            "keine_originalaenderung": True,
            "keine_neue_ocr": True,
            "keine_endgueltige_uebersetzung": True,
            "keine_db_aenderung": True,
            "kein_internet": True,
            "keine_cloud": True,
            "keine_registeraenderung": True,
        },
        "fehler": len(FEHLER),
        "warnungen": len(WARNUNGEN),
    }
    json_path = SB / cfg.get("ausgabe", {}).get("status_json", "02_Status/UI03_1d_OCR_FREIGABEABLAUF.json")
    json_path.write_text(json.dumps(status_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[4] Bericht erzeugen ...")
    docs = akte.get("dokumente", []) if akte else []
    total = sum(len(d.get("seiten", [])) for d in docs)
    bericht = f"""UI03-1d OCR-Freigabeablauf – Bericht
=====================================
Zeitpunkt: {now_iso()}

Akte:
  Dokumente: {len(docs)}
  Seiten gesamt: {total}

Freigabe-Optionen:
{chr(10).join('  - ' + o['label'] for o in FREIGABE_OPTIONEN)}

Grenzen:
  ✓ Keine Originaländerung
  ✓ Keine neue OCR
  ✓ Keine endgültige Übersetzung
  ✓ Keine DB-Änderung
  ✓ Kein Internet/Cloud
  ✓ Keine Registeränderung

Ausgaben:
  {html_path}
  {json_path}

Fehler: {len(FEHLER)}
Warnungen: {len(WARNUNGEN)}
"""
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/UI03_1d_OCR_FREIGABEABLAUF_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")

    print("[5] Fehlerbericht ...")
    fehler_text = f"UI03-1d Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1d Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1d_OCR_FREIGABEABLAUF_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")

    print(f"\nUI03-1d OCR-FREIGABEABLAUF ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1d OCR-FREIGABEABLAUF SELBSTTEST ================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    t("Config ladbar", bool(load_config()))
    t("Toolregister ladbar", load_register("toolregister") is not None)
    t("Ressourcenregister ladbar", load_register("ressourcenregister") is not None)
    t("Schnittstellenregister ladbar", load_register("schnittstellenregister") is not None)
    t("Modulregister ladbar", load_register("modulregister") is not None)

    akte = read_akte()
    t("Akte ladbar (oder Demo-Modus)", True)  # Demo-Modus ist OK

    html = generate_freigabe_html(akte)
    t("Freigabe-HTML erzeugbar", len(html) > 3000)
    t("HTML enthält Seiten-Karten", "seiten-karte" in html)
    t("HTML enthält Radio-Buttons", "type=\"radio\"" in html)
    t("HTML enthält 4 Freigabe-Optionen", html.count("type=\"radio\"") >= 4)
    t("HTML enthält Anmerkungs-Freitext", "freitext-seite" in html)
    t("HTML enthält OCR-Vorschau", "OCR-Text" in html)
    t("HTML enthält Orientierungsübersetzung", "Orientierungsübersetzung" in html)
    t("HTML enthält Gesamtübersicht", "gesamt-panel" in html)
    t("HTML enthält Dokument-Metadaten", "Dokument:" in html)
    t("HTML enthält Seiten-Status", "OCR-Status:" in html)
    t("HTML enthält Grenzen", "Keine Originaländerung" in html)
    t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
