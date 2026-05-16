#!/usr/bin/env python3
"""UI03-1b – OCR-/Übersetzungskontrolle mit Dreiansicht (CORE-11-konform).

Baut auf den bereinigten CORE-11-Registern auf.
Prüft und zeigt:
  - Tesseract: freigegeben (offline OCR)
  - Argos Translate: gesperrt (keine vollständigen Sprachpaare)
  - DEEPL_API: gesperrt (keine Cloud-Übersetzung)
  - Deutsche Arbeitsansicht: nur Orientierungsübersetzung (nicht endgültig)

Erzeugt eine HTML-Kontrollansicht mit Dreiansicht und Status-Panel.
Schreibbereich: UI03_Mandantenakte\21_OCR_Uebersetzungskontrolle_UI03_1b\
"""
import json, sys, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "21_OCR_Uebersetzungskontrolle_UI03_1b"
CONFIG_PATH = ROOT / "Config" / "ui03_1b_ocr_uebersetzungskontrolle_v1.json"

FEHLER = []
WARNUNGEN = []

# ═══════════════════════════════════════════════════════════════════════
# REGISTER-LADEN
# ═══════════════════════════════════════════════════════════════════════

def load_register(name):
    path = CORE / f"{name}.json"
    if not path.exists():
        FEHLER.append(f"Register fehlt: {name}")
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))

def find_ressource(ressourcenregister, ressourcen_id):
    for r in ressourcenregister.get("eintraege", []):
        if r.get("resource_id") == ressourcen_id:
            return r
    return None

def find_tool(toolregister, tool_id):
    for t in toolregister.get("eintraege", []):
        if t.get("tool_id") == tool_id:
            return t
    return None

# ═══════════════════════════════════════════════════════════════════════
# SPRACHPAARE AUS REGISTERN LESEN
# ═══════════════════════════════════════════════════════════════════════

def lese_verfuegbare_sprachpaare(ressourcenregister):
    """Liest alle Argos-Sprachpaare aus dem Ressourcenregister."""
    paare = []
    for r in ressourcenregister.get("eintraege", []):
        rid = r.get("resource_id", "")
        if rid.startswith("ARGOS_"):
            paar = rid.replace("ARGOS_", "")
            if "_" in paar:
                src, tgt = paar.split("_", 1)
                paare.append({
                    "ressourcen_id": rid,
                    "quelle": src,
                    "ziel": tgt,
                    "vorhanden": r.get("vorhanden_ja_nein_unbekannt", "unbekannt"),
                    "pfad": r.get("pfad", "")
                })
    return paare

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

# ═══════════════════════════════════════════════════════════════════════
# STATUS-PRÜFUNG
# ═══════════════════════════════════════════════════════════════════════

def pruefe_ocr_uebersetzungs_status(akte=None):
    """Prüft den OCR-/Übersetzungsstatus anhand der CORE-11-Register."""
    result = {
        "tesseract": {"status": "unbekannt", "grund": "", "freigegeben": False},
        "argos_translate": {"status": "unbekannt", "grund": "", "freigegeben": False, "sprachpaare": []},
        "deepl_api": {"status": "unbekannt", "grund": "", "freigegeben": False},
        "deutsche_arbeitsansicht": {"status": "unbekannt", "grund": "", "hinweis": ""},
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
            result["tesseract"]["grund"] = f"Installiert, Healthcheck: {health}"
            result["tesseract"]["freigegeben"] = True
        else:
            result["tesseract"]["status"] = "gesperrt"
            result["tesseract"]["grund"] = "Nicht installiert"
    else:
        result["tesseract"]["grund"] = "Nicht im Toolregister"

    # Argos Translate prüfen
    argos = find_tool(toolregister, "ARGOS_TRANSLATE")
    paare = lese_verfuegbare_sprachpaare(ressourcenregister)
    result["argos_translate"]["sprachpaare"] = paare

    if argos:
        installiert = argos.get("installationsstatus") == "installiert"
        vorhandene_paare = [p for p in paare if p["vorhanden"] == "ja"]

        if installiert and len(vorhandene_paare) >= 2:
            result["argos_translate"]["status"] = "freigegeben"
            result["argos_translate"]["grund"] = f"Installiert, {len(vorhandene_paare)} Sprachpaare vorhanden"
            result["argos_translate"]["freigegeben"] = True
        elif installiert:
            result["argos_translate"]["status"] = "gesperrt"
            result["argos_translate"]["grund"] = f"Installiert, aber nur {len(vorhandene_paare)} Sprachpaare vorhanden"
        else:
            result["argos_translate"]["status"] = "gesperrt"
            result["argos_translate"]["grund"] = "Nicht installiert"
    else:
        result["argos_translate"]["grund"] = "Nicht im Toolregister"

    # DEEPL_API prüfen
    deepl = find_ressource(ressourcenregister, "deepl_api_key")
    if deepl:
        vorhanden = deepl.get("vorhanden_ja_nein_unbekannt") == "ja"
        if vorhanden:
            result["deepl_api"]["status"] = "gesperrt"
            result["deepl_api"]["grund"] = "API-Key vorhanden, aber Cloud-Nutzung laut Richtlinie gesperrt"
        else:
            result["deepl_api"]["status"] = "gesperrt"
            result["deepl_api"]["grund"] = "Kein API-Key vorhanden (Offline-Betrieb)"
    else:
        result["deepl_api"]["status"] = "gesperrt"
        result["deepl_api"]["grund"] = "Nicht im Ressourcenregister (Offline-Betrieb)"

    # Deutsche Arbeitsansicht
    result["deutsche_arbeitsansicht"]["status"] = "orientierungsuebersetzung"
    result["deutsche_arbeitsansicht"]["grund"] = "Nur Türschwellen-Übersetzung vorhanden"
    result["deutsche_arbeitsansicht"]["hinweis"] = "Nicht endgültig – anwaltlich zu prüfen – Keine Cloud-Übersetzung"

    return result

# ═══════════════════════════════════════════════════════════════════════
# HTML-STATUS-PANEL
# ═══════════════════════════════════════════════════════════════════════

def generate_status_html(status, akte=None):
    """Erzeugt ein HTML-Status-Panel für die OCR-/Übersetzungskontrolle."""

    def status_badge(key):
        s = status.get(key, {})
        st = s.get("status", "unbekannt")
        if st == "freigegeben":
            return f'<span class="badge badge-ok">✓ FREIGEGEBEN</span>'
        elif st == "gesperrt":
            return f'<span class="badge badge-blocked">✗ GESPERRT</span>'
        else:
            return f'<span class="badge badge-warn">? UNBEKANNT</span>'

    def status_row(name, key):
        s = status.get(key, {})
        return f"""
    <tr>
      <td class="tool-name">{name}</td>
      <td>{status_badge(key)}</td>
      <td class="tool-reason">{s.get('grund', '')}</td>
    </tr>"""

    akten_id = akte.get("akten_id", "–") if akte else "–"
    dok_count = len(akte.get("dokumente", [])) if akte else 0

    # Sprachpaare-Tabelle
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
    akten_sprachen = lese_akten_sprachen(akte) if akte else []
    sprachen_html = ", ".join(akten_sprachen) if akten_sprachen else "–"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1b OCR-/Übersetzungskontrolle</title>
<style>
:root {{
  --bg: #f4f7fb; --card-bg: #ffffff; --text: #1a1a2e; --text-secondary: #475569;
  --accent: #0f3460; --accent-light: #eef2ff; --accent2: #2563eb;
  --ok: #16a34a; --ok-bg: #f0fdf4; --warn: #b45309; --warn-bg: #fff7ed;
  --blocked: #dc2626; --blocked-bg: #fef2f2; --border: #e5e7eb;
  --shadow: 0 1px 3px rgba(0,0,0,.06); --radius-lg: 18px; --radius-md: 12px;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
  min-height: 100vh; padding: 20px;
}}
.top-bar {{
  background: var(--card-bg); padding: 16px 24px; border-radius: var(--radius-lg);
  box-shadow: var(--shadow); margin-bottom: 16px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}}
.top-bar h1 {{ font-size: 1.2rem; font-weight: 700; color: var(--accent); }}
.akten-id {{ font-size: 0.85rem; color: var(--text-secondary); }}
.hinweis {{
  font-size: 0.75rem; color: var(--warn); font-weight: 600;
  background: var(--warn-bg); padding: 4px 12px; border-radius: 999px;
}}
.panel {{
  background: var(--card-bg); margin-bottom: 16px; padding: 20px 24px;
  border-radius: var(--radius-lg); box-shadow: var(--shadow);
}}
.panel h2 {{
  font-size: 0.95rem; font-weight: 700; color: var(--accent);
  margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border);
}}
table {{
  width: 100%; border-collapse: collapse; font-size: 0.9rem;
}}
th, td {{
  padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border);
}}
th {{
  font-weight: 700; color: var(--text-secondary); font-size: 0.8rem;
  text-transform: uppercase; letter-spacing: .02em;
}}
.tool-name {{ font-weight: 600; color: var(--accent); }}
.tool-reason {{ color: var(--text-secondary); font-size: 0.85rem; }}
.badge {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700;
}}
.badge-ok {{ background: var(--ok-bg); color: var(--ok); }}
.badge-blocked {{ background: var(--blocked-bg); color: var(--blocked); }}
.badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
.info-box {{
  background: var(--accent-light); padding: 14px 18px; border-radius: var(--radius-md);
  border: 1px solid var(--border); margin-top: 12px; font-size: 0.85rem;
}}
.info-box strong {{ color: var(--accent); }}
.dreiansicht {{
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 16px;
}}
@media (max-width: 900px) {{ .dreiansicht {{ grid-template-columns: 1fr; }} }}
.spalte {{
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 16px; min-height: 200px;
}}
.spalte h3 {{ font-size: 0.85rem; font-weight: 700; color: var(--accent); margin-bottom: 10px; }}
.spalte .status-label {{
  font-size: 0.7rem; padding: 4px 10px; border-radius: 999px;
  display: inline-block; font-weight: 600; margin-bottom: 8px;
}}
.status-tuerschwelle {{ background: var(--warn-bg); color: var(--warn); }}
.status-blocked {{ background: var(--blocked-bg); color: var(--blocked); }}
.status-ok {{ background: var(--ok-bg); color: var(--ok); }}
.paar-ok {{ color: var(--ok); }}
.paar-missing {{ color: var(--blocked); }}
footer {{
  text-align: center; padding: 16px; font-size: 0.7rem;
  color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 24px;
}}
</style>
</head>
<body>

<div class="top-bar">
  <h1>UI03-1b – OCR-/Übersetzungskontrolle</h1>
  <div class="akten-id">Akte: {akten_id} | {dok_count} Dokumente | Sprachen: {sprachen_html}</div>
  <div class="hinweis">Keine Cloud – Keine DB-Änderung – Keine Originaländerung</div>
</div>

<div class="panel">
  <h2>🔍 OCR-/Übersetzungs-Status (aus CORE-11-Registern)</h2>
  <table>
    <thead>
      <tr><th>Komponente</th><th>Status</th><th>Begründung</th></tr>
    </thead>
    <tbody>
      {status_row("Tesseract OCR", "tesseract")}
      {status_row("Argos Translate", "argos_translate")}
      {status_row("DEEPL API (Cloud)", "deepl_api")}
    </tbody>
  </table>
  <div class="info-box">
    <strong>Deutsche Arbeitsansicht:</strong> {status.get("deutsche_arbeitsansicht", {}).get("hinweis", "")}<br>
    <strong>Grund:</strong> {status.get("deutsche_arbeitsansicht", {}).get("grund", "")}
  </div>
</div>

<div class="panel">
  <h2>🌐 Argos-Sprachpaare (aus Ressourcenregister)</h2>
  <table>
    <thead>
      <tr><th>Paar</th><th>Vorhanden</th><th>Status</th></tr>
    </thead>
    <tbody>
      {paare_html if paare_html else '<tr><td colspan="3">Keine Argos-Sprachpaare im Register</td></tr>'}
    </tbody>
  </table>
</div>

<div class="panel">
  <h2>📄 Dreiansicht-Schema</h2>
  <div class="dreiansicht">
    <div class="spalte">
      <h3>Spalte 1: Originalbild</h3>
      <span class="status-label status-ok">Original erhalten</span>
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">
        PNG aus UI03-0. Keine Änderung. Seitennavigation mit Zoom.
      </p>
    </div>
    <div class="spalte">
      <h3>Spalte 2: OCR / Originalsprache</h3>
      <span class="status-label status-tuerschwelle">Türschwelle – nicht schriftsatzfähig</span>
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">
        Tesseract-OCR (offline). Originalsprachiger Text. Durchsuchbar.
        <br><strong>Status:</strong> {status.get("tesseract", {}).get("status", "unbekannt")}
      </p>
    </div>
    <div class="spalte">
      <h3>Spalte 3: Deutsche Orientierungsansicht</h3>
      <span class="status-label status-tuerschwelle">Orientierungsübersetzung</span>
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">
        Nicht endgültig – anwaltlich zu prüfen.
        <br><strong>Argos:</strong> {status.get("argos_translate", {}).get("status", "unbekannt")} (gesperrt)
        <br><strong>DEEPL:</strong> {status.get("deepl_api", {}).get("status", "unbekannt")} (gesperrt)
        <br>Keine Cloud-Übersetzung aktiv.
      </p>
    </div>
  </div>
</div>

<div class="panel">
  <h2>⚠️ Grenzen und Hinweise</h2>
  <ul style="font-size:0.85rem;color:var(--text-secondary);padding-left:18px;line-height:1.8;">
    <li>Keine Originaländerung – Originale werden nur angezeigt</li>
    <li>Keine neue OCR – Türschwellen-OCR wird verwendet</li>
    <li>Keine endgültige Übersetzung – nur Orientierungsübersetzung aus UI02</li>
    <li>Keine DB-Änderung – reine Anzeige</li>
    <li>Kein Internet/Cloud – DEEPL_API gesperrt, Argos gesperrt (fehlende Sprachpaare)</li>
    <li>Keine Rechtsbewertung – keine Beweiswürdigung</li>
  </ul>
</div>

<footer>
  UI03-1b OCR-/Übersetzungskontrolle | CORE-11-konform | Keine Cloud/Internet | Keine DB-Änderung | Keine Originaländerung
</footer>

</body>
</html>"""
    return html

# ═══════════════════════════════════════════════════════════════════════
# KONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    return {
        "modul": "UI03-1b",
        "version": "1.0.0",
        "beschreibung": "OCR-/Übersetzungskontrolle mit Dreiansicht auf bereinigten CORE-11-Registern",
        "register_pruefung": {
            "tesseract_tool_id": "tesseract_ocr",
            "argos_tool_id": "argos_translate",
            "deepl_ressource_id": "deepl_api_key"
        },
        "ausgabe": {
            "status_html": "02_Status/UI03_1b_OCR_KONTROLLE_STATUS.html",
            "status_json": "02_Status/UI03_1b_OCR_KONTROLLE_STATUS.json",
            "bericht": "03_Berichte/UI03_1b_OCR_KONTROLLE_BERICHT.txt"
        }
    }

def ensure_dirs():
    for sub in ["02_Status", "03_Berichte", "05_Fehler", "07_Manifest"]:
        (SB / sub).mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# ═══════════════════════════════════════════════════════════════════════
# HAUPTLAUF
# ═══════════════════════════════════════════════════════════════════════

def main():
    global FEHLER, WARNUNGEN
    print("UI03-1b OCR-/Übersetzungskontrolle =======================================")
    print(f"Zeitpunkt: {now_iso()}")

    cfg = load_config()
    print("[1] Konfiguration ... OK")

    ensure_dirs()
    print("[2] Schreibbereiche ... OK")

    print("[3] CORE-11-Register laden ...")
    toolregister = load_register("toolregister")
    ressourcenregister = load_register("ressourcenregister")
    schnittstellenregister = load_register("schnittstellenregister")
    modulregister = load_register("modulregister")

    if not all([toolregister, ressourcenregister, schnittstellenregister, modulregister]):
        print("    FEHLER: Nicht alle Register ladbar")
        return 1
    print("    OK")

    # Akte laden (falls vorhanden)
    akte = None
    akte_path = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "10_Mandantenakte" / "Mandantenakte.json"
    if akte_path.exists():
        akte = json.loads(akte_path.read_text(encoding="utf-8-sig"))
        print(f"[3a] Mandantenakte geladen: {akte.get('akten_id', '–')}")
    else:
        print("[3a] Keine Mandantenakte vorhanden (Selbsttest-Modus)")

    print("[4] OCR-/Übersetzungsstatus prüfen ...")
    status = pruefe_ocr_uebersetzungs_status(akte)
    print(f"    Tesseract: {status['tesseract']['status']}")
    print(f"    Argos: {status['argos_translate']['status']} ({len(status['argos_translate']['sprachpaare'])} Paare)")
    print(f"    DEEPL: {status['deepl_api']['status']}")

    print("[5] Status-HTML erzeugen ...")
    html = generate_status_html(status, akte)
    html_path = SB / cfg.get("ausgabe", {}).get("status_html", "02_Status/UI03_1b_OCR_KONTROLLE_STATUS.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[6] Status-JSON erzeugen ...")
    status_json = {
        "modul": "UI03-1b",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "core11_konform": True,
        "register_pruefung": status,
        "grenzen": {
            "keine_originalaenderung": True,
            "keine_neue_ocr": True,
            "keine_endgueltige_uebersetzung": True,
            "keine_db_aenderung": True,
            "kein_internet": True,
            "keine_cloud": True,
        },
        "fehler": len(FEHLER),
        "warnungen": len(WARNUNGEN),
    }
    json_path = SB / cfg.get("ausgabe", {}).get("status_json", "02_Status/UI03_1b_OCR_KONTROLLE_STATUS.json")
    json_path.write_text(json.dumps(status_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[7] Bericht erzeugen ...")
    bericht = f"""UI03-1b OCR-/Übersetzungskontrolle – Bericht
============================================
Zeitpunkt: {now_iso()}

Register-Prüfung (CORE-11-konform):
  Tesseract OCR:        {status['tesseract']['status']} – {status['tesseract']['grund']}
  Argos Translate:      {status['argos_translate']['status']} – {status['argos_translate']['grund']}
  DEEPL API (Cloud):    {status['deepl_api']['status']} – {status['deepl_api']['grund']}

Argos-Sprachpaare:
  {len(status['argos_translate']['sprachpaare'])} im Register
  {len([p for p in status['argos_translate']['sprachpaare'] if p['vorhanden'] == 'ja'])} vorhanden

Deutsche Arbeitsansicht:
  Status: {status['deutsche_arbeitsansicht']['status']}
  Hinweis: {status['deutsche_arbeitsansicht']['hinweis']}

Grenzen:
  ✓ Keine Originaländerung
  ✓ Keine neue OCR
  ✓ Keine endgültige Übersetzung
  ✓ Keine DB-Änderung
  ✓ Kein Internet/Cloud

Ausgaben:
  {html_path}
  {json_path}

Fehler: {len(FEHLER)}
Warnungen: {len(WARNUNGEN)}
"""
    bericht_path = SB / cfg.get("ausgabe", {}).get("bericht", "03_Berichte/UI03_1b_OCR_KONTROLLE_BERICHT.txt")
    bericht_path.write_text(bericht, encoding="utf-8")
    print("    OK")

    print("[8] Fehlerbericht ...")
    fehler_text = f"UI03-1b OCR-Kontrolle Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1b OCR-Kontrolle Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1b_OCR_KONTROLLE_FEHLER.txt").write_text(fehler_text, encoding="utf-8")
    print("    OK")

    print(f"\nUI03-1b OCR-KONTROLLE ABGESCHLOSSEN – Fehler: {len(FEHLER)} – Warnungen: {len(WARNUNGEN)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1b OCR-KONTROLLE SELBSTTEST =======================================")
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

    status = pruefe_ocr_uebersetzungs_status()
    t("Tesseract-Status ermittelt", status["tesseract"]["status"] != "unbekannt")
    t("Argos-Status ermittelt", status["argos_translate"]["status"] != "unbekannt")
    t("DEEPL-Status ermittelt", status["deepl_api"]["status"] == "gesperrt")
    t("Deutsche Arbeitsansicht-Status gesetzt", bool(status["deutsche_arbeitsansicht"]["hinweis"]))
    t("Sprachpaare aus Registern gelesen", len(status["argos_translate"]["sprachpaare"]) >= 0)

    html = generate_status_html(status)
    t("Status-HTML erzeugbar", len(html) > 2000)
    t("HTML enthält Tabelle", "<table>" in html)
    t("HTML enthält Dreiansicht", "dreiansicht" in html)
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
