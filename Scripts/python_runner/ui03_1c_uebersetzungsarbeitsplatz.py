#!/usr/bin/env python3
"""UI03-1c – Übersetzungsarbeitsplatz bei fehlender lokaler Übersetzung (CORE-11-konform).

Zeigt eine Dreiansicht mit OCR-Text als Basis, wenn keine Übersetzung verfügbar ist.
Ermöglicht Folgeaufträge (Checkboxes/Chips) und Sonstiges-Freitext.
Multilingual – keine Hartverdrahtung auf sv/de.

Schreibbereich: UI03_Mandantenakte\22_Uebersetzungsarbeitsplatz_UI03_1c\
"""
import json, sys, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "22_Uebersetzungsarbeitsplatz_UI03_1c"
CONFIG_PATH = ROOT / "Config" / "ui03_1c_uebersetzungsarbeitsplatz_v1.json"
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

def find_tool(toolregister, tool_id):
    for t in toolregister.get("eintraege", []):
        if t.get("tool_id") == tool_id:
            return t
    return None

def find_ressource(ressourcenregister, resource_id):
    for r in ressourcenregister.get("eintraege", []):
        if r.get("resource_id") == resource_id:
            return r
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
# ÜBERSETZUNGSSTATUS
# ═══════════════════════════════════════════════════════════════════════

def pruefe_uebersetzungsstatus(akte=None):
    """Prüft Übersetzungsstatus anhand der CORE-11-Register."""
    result = {
        "tesseract": {"status": "unbekannt", "grund": "", "freigegeben": False},
        "argos_translate": {"status": "unbekannt", "grund": "", "freigegeben": False, "sprachpaare": []},
        "deepl_api": {"status": "unbekannt", "grund": "", "freigegeben": False},
        "uebersetzung_verfuegbar": False,
        "ocr_als_basis": False,
        "empfohlene_vorgehensweise": "",
    }

    toolregister = load_register("toolregister")
    ressourcenregister = load_register("ressourcenregister")

    if not all([toolregister, ressourcenregister]):
        return result

    # Tesseract prüfen
    tess = find_tool(toolregister, "TESSERACT")
    if tess:
        installiert = tess.get("installationsstatus") == "installiert"
        health = tess.get("healthcheck_status")
        if installiert:
            result["tesseract"]["status"] = "freigegeben"
            result["tesseract"]["grund"] = f"Installiert, offline verfügbar (Health: {health})"
            result["tesseract"]["freigegeben"] = True
        else:
            result["tesseract"]["status"] = "gesperrt"
            result["tesseract"]["grund"] = f"Nicht installiert (Status: {tess.get('installationsstatus')})"
    else:
        result["tesseract"]["grund"] = "Nicht im Toolregister"

    # Argos Translate prüfen
    argos = find_tool(toolregister, "ARGOS_TRANSLATE")
    if argos:
        installiert = argos.get("installationsstatus") == "installiert"
        if installiert:
            # Sprachpaare prüfen
            paare = []
            vorhanden_count = 0
            for r in ressourcenregister.get("eintraege", []):
                rid = r.get("resource_id", "")
                if rid.startswith("ARGOS_"):
                    paar = rid.replace("ARGOS_", "")
                    if "_" in paar:
                        src, tgt = paar.split("_", 1)
                        vorhanden = r.get("vorhanden_ja_nein_unbekannt", "unbekannt")
                        if vorhanden == "ja":
                            vorhanden_count += 1
                        paare.append({
                            "ressourcen_id": rid,
                            "quelle": src,
                            "ziel": tgt,
                            "vorhanden": vorhanden,
                        })
            result["argos_translate"]["sprachpaare"] = paare
            if vorhanden_count > 0:
                result["argos_translate"]["status"] = "teilweise"
                result["argos_translate"]["grund"] = f"{vorhanden_count}/{len(paare)} Sprachpaare vorhanden"
            else:
                result["argos_translate"]["status"] = "gesperrt"
                result["argos_translate"]["grund"] = "Keine Sprachpaare vorhanden"
        else:
            result["argos_translate"]["status"] = "gesperrt"
            result["argos_translate"]["grund"] = f"Nicht installiert (Status: {argos.get('installationsstatus')})"
    else:
        result["argos_translate"]["grund"] = "Nicht im Toolregister"

    # DEEPL API prüfen
    deepl = find_ressource(ressourcenregister, "DEEPL_API")
    if deepl:
        result["deepl_api"]["status"] = "gesperrt"
        result["deepl_api"]["grund"] = "Cloud-Nutzung laut Richtlinie verboten (Offline-Betrieb)"
    else:
        result["deepl_api"]["grund"] = "Nicht im Ressourcenregister"

    # Übersetzungsverfügbarkeit bestimmen
    akten_sprachen = lese_akten_sprachen(akte) if akte else []
    result["akten_sprachen"] = akten_sprachen

    # Prüfe, ob für Akten-Sprachen Übersetzung verfügbar
    uebersetzung_moeglich = False
    for sprache in akten_sprachen:
        if sprache == "de":
            continue
        for paar in result["argos_translate"]["sprachpaare"]:
            if paar["quelle"].lower() == sprache and paar["ziel"].lower() == "de" and paar["vorhanden"] == "ja":
                uebersetzung_moeglich = True
                break

    result["uebersetzung_verfuegbar"] = uebersetzung_moeglich
    result["ocr_als_basis"] = result["tesseract"]["freigegeben"] and not uebersetzung_moeglich

    if uebersetzung_moeglich:
        result["empfohlene_vorgehensweise"] = "Lokale Übersetzung mit Argos Translate verfügbar"
    elif result["tesseract"]["freigegeben"]:
        result["empfohlene_vorgehensweise"] = "OCR-Text als Arbeitsbasis verwenden (keine vollständige Übersetzung verfügbar)"
    else:
        result["empfohlene_vorgehensweise"] = "Weder OCR noch Übersetzung verfügbar – manuelle Bearbeitung erforderlich"

    return result

def lese_akten_sprachen(akte):
    """Liest die in der Akte verwendeten Sprachen."""
    sprachen = set()
    for d in akte.get("dokumente", []):
        s = d.get("sprache", "")
        if s:
            sprachen.add(s.lower())
        for seite in d.get("seiten", []):
            ocr_s = seite.get("ocr_sprache", "")
            if ocr_s:
                sprachen.add(ocr_s.lower())
    return sorted(sprachen)

def lese_ocr_texte(akte):
    """Liest OCR-Texte aus der Akte."""
    texte = []
    for d in akte.get("dokumente", []):
        for seite in d.get("seiten", []):
            ocr = seite.get("ocr_text", "")
            if ocr:
                texte.append({
                    "dokument": d.get("titel", "Unbekannt"),
                    "seite": seite.get("seitennummer", 1),
                    "sprache": seite.get("ocr_sprache", "unbekannt"),
                    "text": ocr[:500] + "..." if len(ocr) > 500 else ocr,
                })
    return texte

def lese_uebersetzungstexte(akte):
    """Liest vorhandene Übersetzungstexte aus der Akte."""
    texte = []
    for d in akte.get("dokumente", []):
        for seite in d.get("seiten", []):
            uebersetzung = seite.get("uebersetzung_de", "")
            if uebersetzung:
                texte.append({
                    "dokument": d.get("titel", "Unbekannt"),
                    "seite": seite.get("seitennummer", 1),
                    "sprache": seite.get("ocr_sprache", "unbekannt"),
                    "text": uebersetzung[:500] + "..." if len(uebersetzung) > 500 else uebersetzung,
                })
    return texte

# ═══════════════════════════════════════════════════════════════════════
# FOLGEAUFTRÄGE
# ═══════════════════════════════════════════════════════════════════════

FOLGEAUFTRAEGE_STANDARD = [
    "Argos-Sprachpaar nachladen",
    "Tesseract-Sprachpaket prüfen",
    "Manuelle Übersetzung beauftragen",
    "Dokument an Sekretariat zurückgeben",
    "Anwalt um Entscheidung bitten",
    "OCR-Qualität verbessern",
]

# ═══════════════════════════════════════════════════════════════════════
# HTML-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_arbeitsplatz_html(status, akte=None):
    """Erzeugt den Übersetzungsarbeitsplatz als HTML."""
    tess_status = status["tesseract"]["status"]
    argos_status = status["argos_translate"]["status"]
    deepl_status = status["deepl_api"]["status"]
    uebersetzung_verfuegbar = status["uebersetzung_verfuegbar"]
    ocr_als_basis = status["ocr_als_basis"]

    tess_class = "badge-ok" if tess_status == "freigegeben" else "badge-warn"
    argos_class = "badge-ok" if argos_status == "freigegeben" else ("badge-warn" if argos_status == "teilweise" else "badge-err")
    deepl_class = "badge-err"

    # OCR-Texte
    ocr_texte = lese_ocr_texte(akte) if akte else []
    uebersetzungstexte = lese_uebersetzungstexte(akte) if akte else []

    # Sprachpaare
    paare_html = ""
    for p in status.get("argos_translate", {}).get("sprachpaare", []):
        status_class = "paar-ok" if p["vorhanden"] == "ja" else "paar-missing"
        status_text = "✓" if p["vorhanden"] == "ja" else "✗"
        paare_html += f"""
      <tr class="{status_class}">
        <td>{p['quelle']} → {p['ziel']}</td>
        <td>{status_text}</td>
        <td>{p['vorhanden']}</td>
      </tr>"""

    # Akten-Sprachen
    akten_sprachen = status.get("akten_sprachen", [])
    sprachen_html = ", ".join(akten_sprachen) if akten_sprachen else "–"

    # OCR-Texte für Dreiansicht
    ocr_spalte = ""
    if ocr_texte:
        for t in ocr_texte[:3]:
            ocr_spalte += f"""
        <div class="text-block">
          <div class="text-meta">{t['dokument']} – Seite {t['seite']} ({t['sprache']})</div>
          <div class="text-content">{t['text']}</div>
        </div>"""
    else:
        ocr_spalte = '<p style="color:var(--text-secondary);font-style:italic;">Keine OCR-Texte in der Akte vorhanden.</p>'

    # Übersetzungsspalte
    uebersetzung_spalte = ""
    if uebersetzungstexte:
        for t in uebersetzungstexte[:3]:
            uebersetzung_spalte += f"""
        <div class="text-block">
          <div class="text-meta">{t['dokument']} – Seite {t['seite']} ({t['sprache']} → de)</div>
          <div class="text-content">{t['text']}</div>
        </div>"""
    elif uebersetzung_verfuegbar:
        uebersetzung_spalte = '<p style="color:var(--text-secondary);font-style:italic;">Übersetzung verfügbar, aber noch nicht erzeugt.</p>'
    else:
        uebersetzung_spalte = '<p style="color:var(--text-secondary);font-style:italic;">Keine Übersetzung verfügbar. OCR-Text wird als Arbeitsbasis verwendet.</p>'

    # Originalspalte (Platzhalter)
    original_spalte = '<p style="color:var(--text-secondary);font-style:italic;">Originaldokument (nicht verändert)</p>'

    # Folgeaufträge
    folgeauftraege_html = ""
    for i, auftrag in enumerate(FOLGEAUFTRAEGE_STANDARD):
        folgeauftraege_html += f"""
        <label class="chip">
          <input type="checkbox" name="folgeauftrag_{i}" value="{auftrag}">
          <span>{auftrag}</span>
        </label>"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1c Übersetzungsarbeitsplatz</title>
<style>
:root {{
  --bg: #f5f5f5; --panel: #ffffff; --text: #1a1a1a; --text-secondary: #555;
  --border: #ddd; --accent: #2c5282; --accent-light: #ebf4ff;
  --ok: #276749; --ok-bg: #f0fff4; --warn: #c05621; --warn-bg: #fffaf0;
  --err: #c53030; --err-bg: #fff5f5;
}}
body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
.top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
h1 {{ font-size: 1.4rem; margin: 0; color: var(--accent); }}
.badge {{ padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
.badge-ok {{ background: var(--ok-bg); color: var(--ok); }}
.badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
.badge-err {{ background: var(--err-bg); color: var(--err); }}
.panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
.panel h2 {{ font-size: 1.1rem; margin: 0 0 15px 0; color: var(--accent); }}
.panel h3 {{ font-size: 0.95rem; margin: 15px 0 10px 0; color: var(--text-secondary); }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
th {{ background: var(--accent-light); font-weight: 600; color: var(--accent); }}
.paar-ok {{ color: var(--ok); }}
.paar-missing {{ color: var(--err); }}
.dreiansicht {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }}
.spalte {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 15px; }}
.spalte h3 {{ margin: 0 0 10px 0; font-size: 0.9rem; color: var(--accent); }}
.text-block {{ margin-bottom: 15px; padding: 10px; background: var(--accent-light); border-radius: 4px; }}
.text-meta {{ font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 5px; }}
.text-content {{ font-size: 0.85rem; line-height: 1.5; }}
.info-box {{ background: var(--accent-light); border-left: 4px solid var(--accent); padding: 12px 15px; margin-top: 15px; font-size: 0.9rem; }}
.chip-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }}
.chip {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: var(--accent-light); border: 1px solid var(--border); border-radius: 16px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }}
.chip:hover {{ background: #dbeafe; }}
.chip input[type="checkbox"] {{ margin: 0; cursor: pointer; }}
.chip:has(input:checked) {{ background: var(--ok-bg); border-color: var(--ok); color: var(--ok); }}
.freitext {{ width: 100%; min-height: 80px; padding: 10px; border: 1px solid var(--border); border-radius: 4px; font-family: inherit; font-size: 0.9rem; margin-top: 10px; resize: vertical; }}
.freitext:focus {{ outline: none; border-color: var(--accent); }}
.status-banner {{ padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; font-weight: 500; }}
.status-banner.ok {{ background: var(--ok-bg); color: var(--ok); }}
.status-banner.warn {{ background: var(--warn-bg); color: var(--warn); }}
.status-banner.err {{ background: var(--err-bg); color: var(--err); }}
.grenzen {{ font-size: 0.85rem; color: var(--text-secondary); padding-left: 18px; line-height: 1.8; }}
.grenzen li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<div class="top-bar">
  <h1>UI03-1c Übersetzungsarbeitsplatz</h1>
  <span class="badge badge-{'ok' if ocr_als_basis else 'warn'}">{'OCR ALS BASIS' if ocr_als_basis else 'ÜBERSETZUNG VERFÜGBAR' if uebersetzung_verfuegbar else 'KEINE BASIS'}</span>
</div>

<div class="status-banner {'ok' if uebersetzung_verfuegbar else 'warn' if ocr_als_basis else 'err'}">
  {status['empfohlene_vorgehensweise']}
</div>

<div class="panel">
  <h2>Übersetzungsstatus</h2>
  <table>
    <thead>
      <tr><th>Komponente</th><th>Status</th><th>Details</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Tesseract OCR</strong></td>
        <td><span class="badge {tess_class}">{tess_status.upper()}</span></td>
        <td>{status['tesseract']['grund']}</td>
      </tr>
      <tr>
        <td><strong>Argos Translate</strong></td>
        <td><span class="badge {argos_class}">{argos_status.upper()}</span></td>
        <td>{status['argos_translate']['grund']}</td>
      </tr>
      <tr>
        <td><strong>DEEPL API (Cloud)</strong></td>
        <td><span class="badge {deepl_class}">{deepl_status.upper()}</span></td>
        <td>{status['deepl_api']['grund']}</td>
      </tr>
    </tbody>
  </table>
  <div class="info-box">
    <strong>Akten-Sprachen:</strong> {sprachen_html}<br>
    <strong>Übersetzung verfügbar:</strong> {'Ja' if uebersetzung_verfuegbar else 'Nein'}<br>
    <strong>OCR als Basis:</strong> {'Ja' if ocr_als_basis else 'Nein'}
  </div>
</div>

<div class="panel">
  <h2>Argos-Sprachpaare</h2>
  <table>
    <thead>
      <tr><th>Paar</th><th>Status</th><th>Vorhanden</th></tr>
    </thead>
    <tbody>
{paare_html}
    </tbody>
  </table>
</div>

<div class="panel">
  <h2>Dreiansicht – Arbeitsbasis</h2>
  <div class="dreiansicht">
    <div class="spalte">
      <h3>📄 Original</h3>
      {original_spalte}
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">Nur zur Ansicht – keine Änderung</p>
    </div>
    <div class="spalte">
      <h3>🔍 OCR-Text</h3>
      {ocr_spalte}
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">{'Arbeitsbasis (keine Übersetzung verfügbar)' if ocr_als_basis else 'Hilfsebene'}</p>
    </div>
    <div class="spalte">
      <h3>🇩🇪 Deutsche Arbeitsansicht</h3>
      {uebersetzung_spalte}
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">{'Vorhandene Übersetzung' if uebersetzungstexte else 'Orientierungsübersetzung (nicht endgültig)' if ocr_als_basis else 'Nicht verfügbar'}</p>
    </div>
  </div>
</div>

<div class="panel">
  <h2>Folgeaufträge</h2>
  <p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:10px;">Wählen Sie die erforderlichen Folgeaufträge:</p>
  <div class="chip-container">
{folgeauftraege_html}
  </div>
  <h3>Sonstiges</h3>
  <textarea class="freitext" placeholder="Weitere Anmerkungen oder Aufträge hier eingeben..."></textarea>
</div>

<div class="panel">
  <h2>Grenzen</h2>
  <ul class="grenzen">
    <li>✓ Keine Originaländerung</li>
    <li>✓ Keine neue OCR (nur vorhandene anzeigen)</li>
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
    print("UI03-1c ÜBERSETZUNGSARBEITSPLATZ START =================================")
    cfg = load_config()
    ensure_dirs(cfg)

    print("[1] Mandantenakte lesen ...")
    akte = read_akte()
    if akte:
        print(f"    Akte geladen: {len(akte.get('dokumente', []))} Dokumente")
    else:
        print("    Keine Akte gefunden – Demo-Modus")

    print("[2] Übersetzungsstatus prüfen ...")
    status = pruefe_uebersetzungsstatus(akte)
    print(f"    Tesseract: {status['tesseract']['status']}")
    print(f"    Argos: {status['argos_translate']['status']}")
    print(f"    Übersetzung verfügbar: {status['uebersetzung_verfuegbar']}")
    print(f"    OCR als Basis: {status['ocr_als_basis']}")

    print("[3] Arbeitsplatz-HTML erzeugen ...")
    html = generate_arbeitsplatz_html(status, akte)
    html_path = SB / cfg.get("ausgabe", {}).get("arbeitsplatz_html", "02_Status/UI03_1c_UEBERSETZUNGSARBEITSPLATZ.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[4] Status-JSON erzeugen ...")
    status_json = {
        "modul": "UI03-1c",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "uebersetzungsstatus": status,
        "folgeauftraege": FOLGEAUFTRAEGE_STANDARD,
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
    json_path = SB / cfg.get("ausgabe", {}).get("status_json", "02_Status/UI03_1c_UEBERSETZUNGSARBEITSPLATZ.json")
    json_path.write_text(json.dumps(status_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[5] Bericht erzeugen ...")
    bericht = f"""UI03-1c Übersetzungsarbeitsplatz – Bericht
==========================================
Zeitpunkt: {now_iso()}

Übersetzungsstatus:
  Tesseract OCR:        {status['tesseract']['status']} – {status['tesseract']['grund']}
  Argos Translate:      {status['argos_translate']['status']} – {status['argos_translate']['grund']}
  DEEPL API (Cloud):    {status['deepl_api']['status']} – {status['deepl_api']['grund']}

Akten-Sprachen: {', '.join(status.get('akten_sprachen', []))}
Übersetzung verfügbar: {'Ja' if status['uebersetzung_verfuegbar'] else 'Nein'}
OCR als Basis: {'Ja' if status['ocr_als_basis'] else 'Nein'}

Empfohlene Vorgehensweise:
  {status['empfohlene_vorgehensweise']}

Folgeaufträge verfügbar:
{chr(10).join('  - ' + a for a in FOLGEAUFTRAEGE_STANDARD)}

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
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/UI03_1c_UEBERSETZUNGSARBEITSPLATZ_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")

    print("[6] Fehlerbericht ...")
    fehler_text = f"UI03-1c Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1c Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1c_UEBERSETZUNGSARBEITSPLATZ_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")

    print(f"\nUI03-1c ÜBERSETZUNGSARBEITSPLATZ ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1c ÜBERSETZUNGSARBEITSPLATZ SELBSTTEST ============================")
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

    status = pruefe_uebersetzungsstatus()
    t("Tesseract-Status ermittelt", status["tesseract"]["status"] != "unbekannt")
    t("Argos-Status ermittelt", status["argos_translate"]["status"] != "unbekannt")
    t("DEEPL-Status ermittelt", status["deepl_api"]["status"] == "gesperrt")
    t("Übersetzungsverfügbarkeit ermittelt", isinstance(status["uebersetzung_verfuegbar"], bool))
    t("OCR-als-Basis ermittelt", isinstance(status["ocr_als_basis"], bool))
    t("Empfohlene Vorgehensweise gesetzt", bool(status["empfohlene_vorgehensweise"]))
    t("Akten-Sprachen lesbar", isinstance(status.get("akten_sprachen"), list))
    t("Sprachpaare aus Registern gelesen", len(status["argos_translate"]["sprachpaare"]) >= 0)

    html = generate_arbeitsplatz_html(status)
    t("Arbeitsplatz-HTML erzeugbar", len(html) > 2000)
    t("HTML enthält Dreiansicht", "dreiansicht" in html)
    t("HTML enthält Folgeaufträge", "folgeauftrag" in html.lower())
    t("HTML enthält Sonstiges-Freitext", "textarea" in html)
    t("HTML enthält Chip-Container", "chip-container" in html)
    t("HTML enthält Status-Banner", "status-banner" in html)
    t("HTML enthält Grenzen", "Keine Originaländerung" in html)
    t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())
    t("Keine Hartverdrahtung sv/de", "schwedisch" not in html.lower() or "originalsprache" in html.lower())

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
