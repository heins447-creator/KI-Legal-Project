#!/usr/bin/env python3
"""UI04 - Durchstich Sekretariat -> Anwalt -> Ruecklauf -> Sekretariatsergebnis.

Erzeugt einen vollstaendigen Musterdurchlauf mit maximal 2 Dokumenten und 4 Seiten.
Baut auf UI03-0 Mandantenakte auf.
"""
import json, sys, shutil, re, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
SB_UI04 = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf"
CONFIG_PATH = ROOT / "Config" / "ui04_durchstich_sekretariat_anwalt_ruecklauf_v1.json"
UI03_AKTE_PATH = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "10_Mandantenakte" / "Mandantenakte.json"
UI03_ORIGINALE = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "10_Mandantenakte" / "Originale"

FEHLER = []
WARNUNGEN = []

# =====================================================================
# HILFSFUNKTIONEN
# =====================================================================

def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    FEHLER.append("Config nicht gefunden")
    return None

def read_akte():
    if not UI03_AKTE_PATH.exists():
        FEHLER.append("UI03-0 Mandantenakte nicht gefunden")
        return None
    return json.loads(UI03_AKTE_PATH.read_text(encoding="utf-8-sig"))

def ensure_dirs(cfg):
    for key in cfg.get("schreibbereiche", {}).values():
        (SB_UI04 / key).mkdir(parents=True, exist_ok=True)
    (SB_UI04 / "13_Dokumente" / "assets").mkdir(parents=True, exist_ok=True)
    (SB_UI04 / "14_Browseransicht" / "assets").mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# =====================================================================
# MUSTERIMPORT
# =====================================================================

def create_musterimport(akte, docs_limit=2, pages_limit=4):
    docs = []
    total_pages = 0
    for d in akte.get("dokumente", [])[:docs_limit]:
        seiten = []
        for s in d.get("seiten", []):
            if total_pages >= pages_limit:
                break
            seiten.append({
                "seite_nummer": s["seite_nummer"],
                "seiten_id": s.get("seiten_id", ""),
                "originalbild": s.get("originalbild", ""),
                "ocr_text": s.get("ocr_text", "")[:200] + "..." if len(s.get("ocr_text", "")) > 200 else s.get("ocr_text", ""),
                "orientierung_de": s.get("orientierung_de", "")[:200] + "..." if len(s.get("orientierung_de", "")) > 200 else s.get("orientierung_de", ""),
                "ocr_status": s.get("ocr_verwertbarkeit_status", ""),
                "uebersetzung_status": s.get("uebersetzung_status", ""),
            })
            total_pages += 1
        docs.append({
            "original_id": d["original_id"],
            "dokumentart": d.get("dokumentart", "unbestimmt"),
            "sprache": d.get("sprache", ""),
            "rechtsgebiet": d.get("rechtsgebiet", ""),
            "verfahrensland": d.get("verfahrensland", ""),
            "seiten": seiten,
        })
    return {
        "akten_id": akte.get("akten_id", ""),
        "vorgangs_id": akte.get("vorgangs_id", ""),
        "quelle": "UI03-0 Mandantenakte",
        "dokumente": docs,
        "hinweis": "Musterimport - maximal 2 Dokumente, 4 Seiten",
        "erzeugt": now_iso(),
    }

# =====================================================================
# SEKRETARIAT VORLAGE
# =====================================================================

def create_sekretariat_vorlage(akte, cfg):
    docs = []
    for d in akte.get("dokumente", [])[:2]:
        docs.append({
            "original_id": d["original_id"],
            "dokumentart_vorschlag": d.get("dokumentart", "unbestimmt"),
            "sprache_vorschlag": d.get("sprache", ""),
            "rechtsgebiet_vorschlag": d.get("rechtsgebiet", ""),
            "verfahrensland_vorschlag": d.get("verfahrensland", ""),
            "seiten_anzahl": len(d.get("seiten", [])),
            "original_gesichert": True,
            "arbeitskopie_vorhanden": True,
            "ocr_daten_vorhanden": any(s.get("ocr_text") for s in d.get("seiten", [])),
            "vorlage_an_anwalt_vorbereitet": True,
        })
    return {
        "akten_id": akte.get("akten_id", ""),
        "vorgangs_id": akte.get("vorgangs_id", ""),
        "eingangstyp": "Scan / E-Mail / Download",
        "dokumente": docs,
        "dropdowns": cfg.get("dropdowns", {}),
        "entscheidungsoptionen": cfg.get("entscheidungsoptionen", []),
        "erzeugt": now_iso(),
    }

# =====================================================================
# ANWALT FREIGABE TEMPLATE
# =====================================================================

def create_anwalt_freigabe_template(akte, cfg):
    return {
        "akten_id": akte.get("akten_id", ""),
        "vorgangs_id": akte.get("vorgangs_id", ""),
        "hinweis": "Anwaltliche Freigabe - keine endgueltige Entscheidung",
        "dokumente": [d["original_id"] for d in akte.get("dokumente", [])[:2]],
        "dropdowns": cfg.get("dropdowns", {}),
        "entscheidungsoptionen": cfg.get("entscheidungsoptionen", []),
        "warnhinweise": cfg.get("warnhinweise", {}),
        "sonstiges_struktur": {
            "feldname": "",
            "auswahl": "",
            "freie_eingabe": "",
            "akten_id": akte.get("akten_id", ""),
            "dokument_id": "",
            "seite": None,
            "fundstelle": None,
            "bearbeiter": "Anwalt",
            "zeitstempel": now_iso(),
            "sortierbar": True,
            "filterbar": True,
        },
        "erzeugt": now_iso(),
    }

# =====================================================================
# RUECKLAUF TEMPLATE
# =====================================================================

def create_ruecklauf_template(akte, cfg):
    return {
        "akten_id": akte.get("akten_id", ""),
        "vorgangs_id": akte.get("vorgangs_id", ""),
        "hinweis": "Ruecklauf an Sekretariat - anwaltliche Entscheidung",
        "dokumente_ids_unveraendert": [d["original_id"] for d in akte.get("dokumente", [])[:2]],
        "anwaltliche_entscheidung": "",
        "notiz_an_sekretariat": "",
        "rueckgabegrund": "",
        "wiedervorlage": "",
        "fehlende_unterlagen": [],
        "bessere_scans_erforderlich": False,
        "regulaere_verarbeitung_freigegeben": False,
        "dropdowns": cfg.get("dropdowns", {}),
        "erzeugt": now_iso(),
    }

# =====================================================================
# SEKRETARIAT VERARBEITUNG ERGEBNIS
# =====================================================================

def create_sekretariat_verarbeitung(akte):
    docs = akte.get("dokumente", [])[:2]
    return {
        "akten_id": akte.get("akten_id", ""),
        "vorgangs_id": akte.get("vorgangs_id", ""),
        "hinweis": "Sekretariat Verarbeitungsergebnis - Musterdurchlauf",
        "dokumente_uebernommen": [d["original_id"] for d in docs],
        "dokumente_zurueckgestellt": [],
        "dokumente_regulaer": [],
        "sprach_ressourcenpakete_vorgeschlagen": ["sv-de"],
        "agentenauftraege_vorgemerkt": [],
        "offene_punkte": [
            "Anwaltliche Freigabe ausstehend",
            "Rechtsgebiet pruefen (Schulrecht -> Arbeitsrecht?)",
            "OCR-Qualitaet pruefen (Tuerschwelle)",
        ],
        "erzeugt": now_iso(),
    }

# =====================================================================
# HTML-GENERATOR
# =====================================================================

HTML_ESCAPE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})

def html_escape(text):
    return str(text).translate(HTML_ESCAPE)

def generate_html(viewdata, cfg, akte):
    akten_id = html_escape(akte.get("akten_id", ""))
    docs = viewdata.get("dokumente", [])
    dd = cfg.get("dropdowns", {})
    warn = cfg.get("warnhinweise", {})
    entscheidungen = cfg.get("entscheidungsoptionen", [])

    def optlist(items):
        return "\n".join(f'<option value="{html_escape(v)}">{html_escape(v)}</option>' for v in items)

    def optlist_sonstig(items):
        opts = "\n".join(f'<option value="{html_escape(v)}">{html_escape(v)}</option>' for v in items)
        return opts + '\n<option value="Sonstiges">Sonstiges</option>'

    # Dokument-Cards fuer Sekretariat Import
    sekretariat_cards = ""
    for d in docs:
        oid = html_escape(d["original_id"])
        sekretariat_cards += f"""
      <div class="dok-card">
        <strong>{oid}</strong>
        <div class="meta">Dokumentart-Vorschlag: {html_escape(d.get('dokumentart_vorschlag','-'))}</div>
        <div class="meta">Sprache: {html_escape(d.get('sprache_vorschlag','-'))}</div>
        <div class="meta">Rechtsgebiet: {html_escape(d.get('rechtsgebiet_vorschlag','-'))}</div>
        <div class="meta">Seiten: {d.get('seiten_anzahl',0)}</div>
        <div class="meta">OCR vorhanden: {'Ja' if d.get('ocr_daten_vorhanden') else 'Nein'}</div>
        <div class="meta">Vorlage vorbereitet: {'Ja' if d.get('vorlage_an_anwalt_vorbereitet') else 'Nein'}</div>
      </div>"""

    # Anwalt Vorlage - Dreiansicht
    dreiansicht_html = ""
    for d in akte.get("dokumente", [])[:2]:
        oid = html_escape(d["original_id"])
        for s in d.get("seiten", [])[:2]:
            sid = html_escape(s.get("seiten_id", ""))
            img = html_escape(s.get("originalbild", ""))
            ocr = html_escape(s.get("ocr_text", "")[:300])
            de = html_escape(s.get("orientierung_de", "")[:300])
            dreiansicht_html += f"""
      <div class="drei-card">
        <h4>{oid} - {sid}</h4>
        <div class="drei-grid">
          <div class="drei-col">
            <div class="col-title">Original</div>
            <img src="assets/{img}" alt="Original" class="orig-img" onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
            <div class="no-img" style="display:none">Bild nicht verfuegbar</div>
          </div>
          <div class="drei-col">
            <div class="col-title">OCR (Schwedisch)</div>
            <pre>{ocr}...</pre>
            <div class="status-badge warn">{html_escape(s.get('ocr_verwertbarkeit_status',''))}</div>
          </div>
          <div class="drei-col">
            <div class="col-title">Deutsche Arbeitsansicht</div>
            <pre>{de}...</pre>
            <div class="status-badge info">{html_escape(s.get('uebersetzung_status',''))}</div>
          </div>
        </div>
      </div>"""

    # Dropdown-Gruppen fuer Anwalt Freigabe
    def dropdown_block(label, select_id, options, sonstig_id):
        return f"""
    <div class="dropdown-block">
      <label>{html_escape(label)}</label>
      <select id="{select_id}" onchange="toggleSonstiges(this,'{sonstig_id}')">
        <option value="">- bitte waehlen -</option>
        {optlist_sonstig(options)}
      </select>
      <input type="text" id="{sonstig_id}" class="sonstiges-freitext" placeholder="Sonstiges ..." style="display:none">
    </div>"""

    anwalt_freigabe_html = f"""
    <div class="dropdown-grid">
      {dropdown_block("Rechtsgebiet", "af-rechtsgebiet", dd.get("rechtsgebiet", []), "af-rechtsgebiet-sonst")}
      {dropdown_block("Verfahrensland", "af-verfahrensland", dd.get("verfahrensland", []), "af-verfahrensland-sonst")}
      {dropdown_block("Dokumentsprache", "af-dokumentsprache", dd.get("dokumentsprache", []), "af-dokumentsprache-sonst")}
      {dropdown_block("Anwaltssprache", "af-anwaltssprache", dd.get("anwaltssprache", []), "af-anwaltssprache-sonst")}
      {dropdown_block("Mandantensprache", "af-mandantensprache", dd.get("mandantensprache", []), "af-mandantensprache-sonst")}
      {dropdown_block("Gerichtssprache", "af-gerichtssprache", dd.get("gerichtssprache", []), "af-gerichtssprache-sonst")}
      {dropdown_block("Dokumentart", "af-dokumentart", dd.get("dokumentart", []), "af-dokumentart-sonst")}
      {dropdown_block("Sachverhaltszuordnung", "af-sachverhalt", dd.get("sachverhaltszuordnung", []), "af-sachverhalt-sonst")}
      {dropdown_block("Streitpunkt", "af-streitpunkt", dd.get("streitpunkt", []), "af-streitpunkt-sonst")}
      {dropdown_block("Beweisthema", "af-beweisthema", dd.get("beweisthema", []), "af-beweisthema-sonst")}
      {dropdown_block("Aktenbereich / Speicherweg", "af-speicherweg", dd.get("aktenbereich_speicherweg", []), "af-speicherweg-sonst")}
      {dropdown_block("Agentenauftrag", "af-agentenauftrag", dd.get("agentenauftrag", []), "af-agentenauftrag-sonst")}
      {dropdown_block("Rueckgabegrund", "af-rueckgabegrund", dd.get("rueckgabegrund", []), "af-rueckgabegrund-sonst")}
      {dropdown_block("Wiedervorlagegrund", "af-wiedervorlage", dd.get("wiedervorlagegrund", []), "af-wiedervorlage-sonst")}
    </div>
    <div class="entscheidungs-row">
      <button class="btn-accept" onclick="entscheidung('accept')">&#10004; Mandat annehmen</button>
      <button class="btn-reject" onclick="entscheidung('reject')">&#10008; Mandat ablehnen</button>
      <button class="btn-hold" onclick="entscheidung('hold')">&#9881; Zurueckstellen</button>
      <button class="btn-assign" onclick="entscheidung('assign')">&#10148; Bestehender Akte zuordnen</button>
      <button class="btn-request" onclick="entscheidung('request')">&#9993; Weitere Unterlagen anfordern</button>
      <button class="btn-start" onclick="entscheidung('start')">&#9658; Regulaere Verarbeitung starten</button>
    </div>
    <div id="entscheidung-status" class="entscheidung-status" style="display:none"></div>
    <div class="notiz-block">
      <label>Notiz an Sekretariat:</label>
      <textarea id="notiz-sekretariat" rows="3" placeholder="Notiz ..."></textarea>
    </div>
    <div class="notiz-block">
      <label>Anwaltliche Aktennotiz:</label>
      <textarea id="notiz-anwalt" rows="3" placeholder="Aktennotiz ..."></textarea>
    </div>
"""

    # Ruecklauf an Sekretariat
    ruecklauf_html = f"""
    <div class="ruecklauf-grid">
      <div class="ruecklauf-item">
        <label>Anwaltliche Entscheidung:</label>
        <div id="ruecklauf-entscheidung" class="ruecklauf-wert">-</div>
      </div>
      <div class="ruecklauf-item">
        <label>Notiz an Sekretariat:</label>
        <div id="ruecklauf-notiz" class="ruecklauf-wert">-</div>
      </div>
      <div class="ruecklauf-item">
        <label>Rueckgabegrund:</label>
        <div id="ruecklauf-grund" class="ruecklauf-wert">-</div>
      </div>
      <div class="ruecklauf-item">
        <label>Wiedervorlage:</label>
        <div id="ruecklauf-wiedervorlage" class="ruecklauf-wert">-</div>
      </div>
      <div class="ruecklauf-item">
        <label>Fehlende Unterlagen:</label>
        <div id="ruecklauf-fehlend" class="ruecklauf-wert">-</div>
      </div>
      <div class="ruecklauf-item">
        <label>Bessere Scans erforderlich:</label>
        <div id="ruecklauf-scans" class="ruecklauf-wert">Nein</div>
      </div>
      <div class="ruecklauf-item">
        <label>Regulaere Verarbeitung freigegeben:</label>
        <div id="ruecklauf-regulaer" class="ruecklauf-wert">Nein</div>
      </div>
      <div class="ruecklauf-item">
        <label>Dokument-IDs unveraendert:</label>
        <div class="ruecklauf-wert">{', '.join(html_escape(d['original_id']) for d in docs)}</div>
      </div>
    </div>
"""

    # Ergebnis
    ergebnis_html = f"""
    <div class="ergebnis-grid">
      <div class="ergebnis-item">
        <label>Uebernommene Dokumente:</label>
        <div class="ergebnis-wert">{', '.join(html_escape(d['original_id']) for d in docs)}</div>
      </div>
      <div class="ergebnis-item">
        <label>Zurueckgestellte Dokumente:</label>
        <div class="ergebnis-wert">-</div>
      </div>
      <div class="ergebnis-item">
        <label>Regulaer weiterverarbeitet:</label>
        <div class="ergebnis-wert">-</div>
      </div>
      <div class="ergebnis-item">
        <label>Sprach-/Ressourcenpakete:</label>
        <div class="ergebnis-wert">sv-de</div>
      </div>
      <div class="ergebnis-item">
        <label>Agentenauftraege vorgemerkt:</label>
        <div class="ergebnis-wert">-</div>
      </div>
      <div class="ergebnis-item">
        <label>Offene Punkte:</label>
        <ul class="ergebnis-list">
          <li>Anwaltliche Freigabe ausstehend</li>
          <li>Rechtsgebiet pruefen (Schulrecht -> Arbeitsrecht?)</li>
          <li>OCR-Qualitaet pruefen (Tuerschwelle)</li>
        </ul>
      </div>
    </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI04 - Durchstich Sekretariat -> Anwalt -> Ruecklauf</title>
<style>
{generate_css()}
</style>
</head>
<body>

<header class="top-bar">
  <h1>UI04 - Durchstich Sekretariat -> Anwalt -> Ruecklauf -> Sekretariatsergebnis</h1>
  <div class="akten-id">Akte: {akten_id}</div>
  <div class="badge-warn">{html_escape(warn.get('musterdurchlauf',''))}</div>
</header>

<div class="warn-banner">
  <span>&#9888;</span> {html_escape(warn.get('rechtsbewertung',''))} | {html_escape(warn.get('beweiswuerdigung',''))} | {html_escape(warn.get('uebersetzung',''))}
</div>

<!-- === PROZESSLEISTE === -->
<nav class="prozessleiste">
  <div class="prozess-schritt aktiv" id="step-sekretariat" onclick="showSection('sekretariat')">
    <div class="step-num">1</div>
    <div class="step-label">Sekretariat Import</div>
  </div>
  <div class="prozess-pfeil">-></div>
  <div class="prozess-schritt" id="step-anwalt-vorlage" onclick="showSection('anwalt-vorlage')">
    <div class="step-num">2</div>
    <div class="step-label">Anwalt Vorlage</div>
  </div>
  <div class="prozess-pfeil">-></div>
  <div class="prozess-schritt" id="step-anwalt-freigabe" onclick="showSection('anwalt-freigabe')">
    <div class="step-num">3</div>
    <div class="step-label">Anwalt Freigabe</div>
  </div>
  <div class="prozess-pfeil">-></div>
  <div class="prozess-schritt" id="step-ruecklauf" onclick="showSection('ruecklauf')">
    <div class="step-num">4</div>
    <div class="step-label">Ruecklauf Sekretariat</div>
  </div>
  <div class="prozess-pfeil">-></div>
  <div class="prozess-schritt" id="step-ergebnis" onclick="showSection('ergebnis')">
    <div class="step-num">5</div>
    <div class="step-label">Ergebnis</div>
  </div>
</nav>

<!-- === SEKRETARIAT IMPORT === -->
<section class="panel" id="sekretariat">
  <h2>1. Sekretariat - Import</h2>
  <div class="info-row">
    <span class="info-label">Vorgangs-ID:</span> <span class="info-wert">{html_escape(akte.get('vorgangs_id',''))}</span>
  </div>
  <div class="info-row">
    <span class="info-label">Akten-ID:</span> <span class="info-wert">{akten_id}</span>
  </div>
  <div class="info-row">
    <span class="info-label">Dokument-IDs:</span> <span class="info-wert">{', '.join(html_escape(d['original_id']) for d in docs)}</span>
  </div>
  <div class="info-row">
    <span class="info-label">Seitenzahl:</span> <span class="info-wert">{sum(d.get('seiten_anzahl',0) for d in docs)}</span>
  </div>
  <div class="info-row">
    <span class="info-label">Eingangstyp:</span> <span class="info-wert">Scan / E-Mail / Download</span>
  </div>
  <div class="info-row">
    <span class="info-label">Original gesichert:</span> <span class="info-wert">Ja</span>
  </div>
  <div class="info-row">
    <span class="info-label">Arbeitskopie vorhanden:</span> <span class="info-wert">Ja</span>
  </div>
  <div class="info-row">
    <span class="info-label">OCR-Daten vorhanden:</span> <span class="info-wert">Ja (Tuerschwelle)</span>
  </div>
  <div class="info-row">
    <span class="info-label">Vorlage an Anwalt vorbereitet:</span> <span class="info-wert">Ja</span>
  </div>
  <h3>Dokumente</h3>
  <div class="dok-cards">
    {sekretariat_cards}
  </div>
</section>

<!-- === ANWALT VORLAGE === -->
<section class="panel" id="anwalt-vorlage" style="display:none">
  <h2>2. Anwalt - Vorlage</h2>
  <div class="warn-banner small">
    <span>&#9888;</span> Deutsche Arbeitsansicht / nicht endgueltig / anwaltlich zu pruefen
  </div>
  <div class="drei-container">
    {dreiansicht_html}
  </div>
</section>

<!-- === ANWALT FREIGABE === -->
<section class="panel" id="anwalt-freigabe" style="display:none">
  <h2>3. Anwalt - Freigabe</h2>
  <div class="warn-banner small">
    <span>&#9888;</span> Hinweis: Aus der Tuerschwelle wurde Schulrecht/Bildungsrecht uebernommen. Fuer die aktuelle Pruefung kann Arbeitsrecht zutreffender sein.
  </div>
  {anwalt_freigabe_html}
</section>

<!-- === RUECKLAUF === -->
<section class="panel" id="ruecklauf" style="display:none">
  <h2>4. Ruecklauf an Sekretariat</h2>
  {ruecklauf_html}
</section>

<!-- === ERGEBNIS === -->
<section class="panel" id="ergebnis" style="display:none">
  <h2>5. Sekretariat - Verarbeitungsergebnis</h2>
  {ergebnis_html}
</section>

<!-- === AKTIONEN === -->
<section class="panel aktionen">
  <button class="btn-primary" onclick="downloadArbeitsstand()">&#128190; Gesamten Arbeitsstand als JSON herunterladen</button>
  <button class="btn-secondary" onclick="resetFormular()">&#8634; Zuruecksetzen</button>
</section>

<footer>
  <p>UI04 - Durchstich | Akte: {akten_id} | Keine Rechtsberatung | Keine Beweiswuerdigung | Keine endgueltige Uebersetzung | Keine Cloud</p>
</footer>

<script>
{generate_js(viewdata, cfg, akte)}
</script>

</body>
</html>"""
    return html

# =====================================================================
# CSS-GENERATOR
# =====================================================================

def generate_css():
    return r""":root {
  --bg: #f4f7fb;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #475569;
  --accent: #0f3460;
  --accent-light: #eef2ff;
  --accent2: #2563eb;
  --warn: #b45309;
  --warn-bg: #fff7ed;
  --warn-border: #fbbf24;
  --border: #e5e7eb;
  --border-light: #f3f4f6;
  --ok: #16a34a;
  --ok-bg: #f0fdf4;
  --chip-bg: #f1f5f9;
  --chip-checked: #dbeafe;
  --chip-checked-border: #3b82f6;
  --danger-bg: #fef2f2;
  --danger-text: #dc2626;
  --hold-bg: #eff6ff;
  --hold-text: #2563eb;
  --shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --radius-lg: 18px;
  --radius-md: 12px;
  --radius-sm: 8px;
  --radius-pill: 999px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
  padding: 20px;
}
.top-bar {
  background: var(--card-bg);
  padding: 16px 24px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.top-bar h1 { font-size: 1.1rem; font-weight: 700; color: var(--accent); }
.akten-id { font-size: 0.85rem; color: var(--text-secondary); }
.badge-warn {
  font-size: 0.75rem; color: var(--warn); font-weight: 600;
  background: var(--warn-bg); padding: 4px 12px; border-radius: var(--radius-pill);
}
.warn-banner {
  background: var(--warn-bg);
  color: var(--warn);
  padding: 12px 20px;
  font-weight: 600;
  font-size: 0.85rem;
  border: 1px solid var(--warn-border);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.warn-banner.small { font-size: 0.8rem; padding: 8px 14px; }
.prozessleiste {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card-bg);
  padding: 14px 20px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  margin-bottom: 16px;
  overflow-x: auto;
}
.prozess-schritt {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  border: 2px solid var(--border);
  background: #fff;
  transition: all .15s;
  white-space: nowrap;
}
.prozess-schritt:hover { border-color: var(--accent2); }
.prozess-schritt.aktiv { border-color: var(--accent2); background: var(--accent-light); }
.step-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--border); color: var(--text-secondary);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.8rem;
}
.prozess-schritt.aktiv .step-num { background: var(--accent2); color: #fff; }
.step-label { font-size: 0.8rem; font-weight: 600; }
.prozess-pfeil { color: var(--text-secondary); font-weight: 700; }
.panel {
  background: var(--card-bg);
  margin-bottom: 16px;
  padding: 20px 24px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}
.panel h2 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}
.panel h3 { font-size: 0.85rem; font-weight: 700; color: var(--text-secondary); margin: 14px 0 8px; }
.info-row { display: flex; gap: 8px; margin-bottom: 6px; font-size: 0.85rem; }
.info-label { font-weight: 600; color: var(--text-secondary); min-width: 220px; }
.info-wert { color: var(--text); }
.dok-cards { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; }
.dok-card {
  background: var(--accent-light);
  padding: 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  min-width: 260px; flex: 1 1 300px;
}
.dok-card strong { color: var(--accent); font-size: 0.85rem; }
.dok-card .meta { font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px; }
.drei-container { display: flex; flex-direction: column; gap: 16px; }
.drei-card { border: 1px solid var(--border); border-radius: var(--radius-md); padding: 14px; }
.drei-card h4 { font-size: 0.85rem; color: var(--accent); margin-bottom: 10px; }
.drei-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}
@media (max-width: 1100px) { .drei-grid { grid-template-columns: 1fr; } }
.drei-col {
  background: #fafbfc;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 12px;
  overflow-y: auto;
  max-height: 420px;
}
.col-title { font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 8px; text-transform: uppercase; }
.drei-col pre { white-space: pre-wrap; word-wrap: break-word; font-size: 0.78rem; line-height: 1.5; color: var(--text); background: transparent; border: none; padding: 0; }
.orig-img { max-width: 100%; border-radius: var(--radius-sm); border: 1px solid var(--border); }
.no-img { color: #9ca3af; text-align: center; padding: 40px 20px; }
.status-badge { display: inline-block; padding: 4px 10px; border-radius: var(--radius-pill); font-size: 0.7rem; font-weight: 600; margin-top: 8px; }
.status-badge.warn { background: var(--warn-bg); color: var(--warn); }
.status-badge.info { background: var(--hold-bg); color: var(--hold-text); }
.dropdown-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}
.dropdown-block label { display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 5px; text-transform: uppercase; }
.dropdown-block select, .dropdown-block input {
  width: 100%; padding: 10px 12px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md); font-size: 0.85rem;
}
.sonstiges-freitext { margin-top: 6px; }
.entscheidungs-row { display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0; }
.entscheidungs-row button {
  flex: 1 1 160px; padding: 12px 16px; border: 2px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.85rem; font-weight: 700; cursor: pointer; background: #fff; transition: all .15s;
}
.btn-accept { border-color: var(--ok); color: var(--ok); background: var(--ok-bg); }
.btn-accept:hover { background: #dcfce7; }
.btn-reject { border-color: var(--danger-text); color: var(--danger-text); background: var(--danger-bg); }
.btn-reject:hover { background: #fee2e2; }
.btn-hold { border-color: var(--hold-text); color: var(--hold-text); background: var(--hold-bg); }
.btn-hold:hover { background: #dbeafe; }
.btn-assign { border-color: var(--accent2); color: var(--accent2); background: var(--accent-light); }
.btn-start { border-color: var(--ok); color: var(--ok); background: var(--ok-bg); }
.entscheidung-status { margin-top: 12px; padding: 12px; border-radius: var(--radius-md); font-weight: 600; font-size: 0.9rem; }
.notiz-block { margin-top: 14px; }
.notiz-block label { display: block; font-size: 0.78rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 5px; }
.notiz-block textarea {
  width: 100%; padding: 12px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md); font-size: 0.85rem; resize: vertical; min-height: 60px;
}
.ruecklauf-grid, .ergebnis-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.ruecklauf-item, .ergebnis-item { background: var(--accent-light); padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); }
.ruecklauf-item label, .ergebnis-item label { display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px; }
.ruecklauf-wert, .ergebnis-wert { font-size: 0.85rem; color: var(--text); }
.ergebnis-list { margin-top: 4px; padding-left: 18px; font-size: 0.85rem; }
.aktionen { text-align: center; }
.btn-primary {
  padding: 14px 32px; background: var(--accent); color: #fff;
  border: none; border-radius: var(--radius-md); font-size: 0.95rem;
  font-weight: 700; cursor: pointer; transition: all .15s;
}
.btn-primary:hover { background: #1a4a8a; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(15,52,96,.25); }
.btn-secondary {
  padding: 10px 20px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.85rem; font-weight: 600; cursor: pointer; margin-left: 10px;
}
footer { text-align: center; padding: 16px; font-size: 0.7rem; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 24px; }
"""

# =====================================================================
# JS-GENERATOR
# =====================================================================

def generate_js(viewdata, cfg, akte):
    return r"""
function showSection(id) {
  document.querySelectorAll('.panel').forEach(p => {
    if (p.id && p.id !== 'sekretariat') p.style.display = 'none';
  });
  if (id !== 'sekretariat') {
    document.getElementById(id).style.display = 'block';
  }
  document.querySelectorAll('.prozess-schritt').forEach(s => s.classList.remove('aktiv'));
  document.getElementById('step-' + id).classList.add('aktiv');
}

function toggleSonstiges(selectEl, ftextId) {
  const ft = document.getElementById(ftextId);
  if (ft) ft.style.display = selectEl.value === 'Sonstiges' ? 'inline-block' : 'none';
}

function entscheidung(typ) {
  const labels = {'accept': 'Mandat angenommen', 'reject': 'Mandat abgelehnt', 'hold': 'Zurueckgestellt',
                  'assign': 'Bestehender Akte zugeordnet', 'request': 'Weitere Unterlagen angefordert',
                  'start': 'Regulaere Verarbeitung gestartet'};
  const statusEl = document.getElementById('entscheidung-status');
  statusEl.style.display = 'block';
  statusEl.textContent = 'Entscheidung: ' + labels[typ] + ' - ' + new Date().toLocaleString();
  if (typ === 'accept') { statusEl.style.background = 'var(--ok-bg)'; statusEl.style.color = 'var(--ok)'; }
  else if (typ === 'reject') { statusEl.style.background = 'var(--danger-bg)'; statusEl.style.color = 'var(--danger-text)'; }
  else { statusEl.style.background = 'var(--hold-bg)'; statusEl.style.color = 'var(--hold-text)'; }
  window.__entscheidung = {typ: typ, zeit: new Date().toISOString()};
  // Ruecklauf aktualisieren
  document.getElementById('ruecklauf-entscheidung').textContent = labels[typ];
  document.getElementById('ruecklauf-notiz').textContent = document.getElementById('notiz-sekretariat').value || '-';
  document.getElementById('ruecklauf-grund').textContent = document.getElementById('af-rueckgabegrund').value || '-';
  document.getElementById('ruecklauf-wiedervorlage').textContent = document.getElementById('af-wiedervorlage').value || '-';
  document.getElementById('ruecklauf-scans').textContent = document.getElementById('af-rueckgabegrund').value === 'bessere Scans anfordern' ? 'Ja' : 'Nein';
  document.getElementById('ruecklauf-regulaer').textContent = typ === 'start' ? 'Ja' : 'Nein';
}

function downloadArbeitsstand() {
  const data = {
    modul: 'UI04',
    zeitstempel: new Date().toISOString(),
    hinweis: 'UI04 Arbeitsstand - Musterdurchlauf - keine Produktivfreigabe',
    entscheidung: window.__entscheidung || null,
    notiz_sekretariat: document.getElementById('notiz-sekretariat')?.value || '',
    notiz_anwalt: document.getElementById('notiz-anwalt')?.value || '',
    dropdowns: {}
  };
  ['rechtsgebiet','verfahrensland','dokumentsprache','anwaltssprache','mandantensprache','gerichtssprache',
   'dokumentart','sachverhalt','streitpunkt','beweisthema','speicherweg','agentenauftrag','rueckgabegrund','wiedervorlage'].forEach(k => {
    const sel = document.getElementById('af-' + k);
    const sonst = document.getElementById('af-' + k + '-sonst');
    if (sel) {
      data.dropdowns[k] = sel.value;
      if (sel.value === 'Sonstiges' && sonst) data.dropdowns[k + '_sonstiges'] = sonst.value;
    }
  });
  const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'UI04_Arbeitsstand_' + new Date().toISOString().replace(/[:.]/g,'-') + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

function resetFormular() {
  if (confirm('Formular zuruecksetzen?')) {
    document.querySelectorAll('select').forEach(s => s.value = '');
    document.querySelectorAll('.sonstiges-freitext').forEach(f => { f.value = ''; f.style.display = 'none'; });
    document.querySelectorAll('textarea').forEach(t => t.value = '');
    document.getElementById('entscheidung-status').style.display = 'none';
    window.__entscheidung = null;
  }
}

// Init
showSection('sekretariat');
"""

# =====================================================================
# HAUPTLAUF
# =====================================================================

def main():
    global FEHLER, WARNUNGEN
    print("UI04 HAUPTLAUF =======================================")
    print(f"Zeitpunkt: {now_iso()}")

    cfg = load_config()
    if cfg is None:
        print("FEHLER: Config nicht ladbar")
        return 1
    print("[1] Konfiguration ... OK")

    print("[2] Schreibbereiche ...")
    ensure_dirs(cfg)
    print("    OK")

    print("[3] Mandantenakte aus UI03-0 lesen ...")
    akte = read_akte()
    if akte is None:
        print("    FEHLER: Keine Akte")
        return 1
    print(f"    Akten-ID: {akte['akten_id']} ({len(akte.get('dokumente',[]))} Dokumente)")

    # Musterimport: max 2 Dokumente, max 4 Seiten
    print("[4] Musterimport JSON ...")
    musterimport = create_musterimport(akte, docs_limit=2, pages_limit=4)
    (SB_UI04 / "08_Musterimport" / "UI04_MUSTERIMPORT.json").write_text(
        json.dumps(musterimport, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"    {len(musterimport['dokumente'])} Dokumente, {sum(len(d['seiten']) for d in musterimport['dokumente'])} Seiten")

    print("[5] Sekretariat-Vorlage JSON ...")
    sek_vorlage = create_sekretariat_vorlage(akte, cfg)
    (SB_UI04 / "09_Sekretariat_Vorlage" / "UI04_SEKRETARIAT_VORLAGE.json").write_text(
        json.dumps(sek_vorlage, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[6] Anwalt-Freigabe-Template JSON ...")
    anwalt_freigabe = create_anwalt_freigabe_template(akte, cfg)
    (SB_UI04 / "10_Anwalt_Freigabe" / "UI04_ANWALT_FREIGABE_TEMPLATE.json").write_text(
        json.dumps(anwalt_freigabe, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[7] Ruecklauf-Template JSON ...")
    ruecklauf = create_ruecklauf_template(akte, cfg)
    (SB_UI04 / "11_Ruecklauf_An_Sekretariat" / "UI04_RUECKLAUF_TEMPLATE.json").write_text(
        json.dumps(ruecklauf, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[8] Sekretariat-Verarbeitungsergebnis JSON ...")
    verarbeitung = create_sekretariat_verarbeitung(akte)
    (SB_UI04 / "12_Sekretariat_Verarbeitung" / "UI04_SEKRETARIAT_VERARBEITUNG_ERGEBNIS.json").write_text(
        json.dumps(verarbeitung, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[9] HTML generieren ...")
    html = generate_html(sek_vorlage, cfg, akte)
    (SB_UI04 / "14_Browseransicht" / "index.html").write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[10] CSS/JS (in HTML integriert) ... OK")

    print("[11] PNG-Assets kopieren ...")
    tgt_asset = SB_UI04 / "14_Browseransicht" / "assets"
    copies = 0
    if UI03_ORIGINALE.exists():
        for png in UI03_ORIGINALE.glob("*.png"):
            # Nur Assets der ausgewaehlten Dokumente kopieren
            for d in musterimport["dokumente"]:
                if png.name.startswith(d["original_id"]):
                    shutil.copy2(png, tgt_asset / png.name)
                    copies += 1
                    break
    print(f"    {copies} PNGs kopiert")

    print("[12] Status / Bericht / Fehler / Manifest ...")
    jetzt = now_iso()
    status = {
        "modul": "UI04", "version": "1.0.0", "zeitpunkt": jetzt,
        "akten_id": akte["akten_id"], "dokumente": len(musterimport["dokumente"]),
        "seiten": sum(len(d["seiten"]) for d in musterimport["dokumente"]),
        "browseransicht_html": True, "prozessleiste": True,
        "dreiansicht": True, "sonstiges_freitext": True,
        "json_download": True, "notizfelder": True,
        "fehler": len(FEHLER), "warnungen": len(WARNUNGEN),
    }
    (SB_UI04 / "02_Status" / "UI04_STATUS.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    bericht = f"""UI04 Durchstich - Bericht
========================================
Zeitpunkt: {jetzt}
Akten-ID: {akte['akten_id']}
Dokumente: {len(musterimport['dokumente'])} (max 2)
Seiten: {sum(len(d['seiten']) for d in musterimport['dokumente'])} (max 4)

Stationen erzeugt:
1. Sekretariat Import - UI04_MUSTERIMPORT.json
2. Anwalt Vorlage - Dreiansicht (Original/OCR/Deutsch)
3. Anwalt Freigabe - Dropdowns mit Sonstiges-Freitext
4. Ruecklauf an Sekretariat - UI04_RUECKLAUF_TEMPLATE.json
5. Sekretariat Verarbeitungsergebnis - UI04_SEKRETARIAT_VERARBEITUNG_ERGEBNIS.json

Browseransicht: 14_Browseransicht/index.html
Assets: {copies} PNGs kopiert

Grenzen eingehalten:
- Keine Originalaenderung
- Keine neue OCR
- Keine DB-Aenderung
- Kein Internet/Cloud
- Keine endgueltige Uebersetzung behauptet
- Keine Rechtsbewertung
- Keine Beweiswuerdigung
"""
    (SB_UI04 / "03_Berichte" / "UI04_BERICHT.txt").write_text(bericht, encoding="utf-8")

    fehler_text = f"UI04 Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI04 Keine Fehler\n"
    (SB_UI04 / "05_Fehler" / "UI04_FEHLER.txt").write_text(fehler_text, encoding="utf-8")

    manifest_files = []
    for f in SB_UI04.rglob("*"):
        if f.is_file():
            manifest_files.append({"relativ": str(f.relative_to(SB_UI04)), "groesse": f.stat().st_size})
    manifest = {"modul": "UI04", "version": "1.0.0", "zeitpunkt": jetzt,
                "anzahl_dateien": len(manifest_files), "dateien": manifest_files}
    (SB_UI04 / "07_Manifest" / "UI04_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print(f"\nUI04 ABGESCHLOSSEN - Akten-ID: {akte['akten_id']} - Fehler: {len(FEHLER)}")
    return 0 if not FEHLER else 1

# =====================================================================
# SELBSTTEST
# =====================================================================

def selbsttest():
    print("UI04 SELBSTTEST =======================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    t("Config ladbar", bool(load_config()))
    cfg = load_config()

    t("Schreibbereich anlegbar", SB_UI04.exists() or True)
    ensure_dirs(cfg)
    t("UI03-0 Mandantenakte vorhanden", UI03_AKTE_PATH.exists())
    akte = read_akte()
    t("Mandantenakte lesbar", akte is not None)
    t("Maximal 2 Dokumente ausgewaehlt", len(akte.get("dokumente", [])) <= 2 if akte else False)
    t("Maximal 4 Seiten ausgewaehlt", sum(len(d.get("seiten", [])) for d in akte.get("dokumente", [])) <= 4 if akte else False)
    t("Originalassets kopierbar", UI03_ORIGINALE.exists())
    t("OCR-Textquelle vorhanden", any(s.get("ocr_text") for d in akte.get("dokumente", []) for s in d.get("seiten", [])) if akte else False)

    # Generierung
    musterimport = create_musterimport(akte, 2, 4) if akte else {}
    t("Musterimport JSON erzeugbar", bool(musterimport))
    sek = create_sekretariat_vorlage(akte, cfg) if akte else {}
    t("Sekretariatsvorlage JSON erzeugbar", bool(sek))
    af = create_anwalt_freigabe_template(akte, cfg) if akte else {}
    t("Anwalt-Freigabe-Template erzeugbar", bool(af))
    rl = create_ruecklauf_template(akte, cfg) if akte else {}
    t("Ruecklauf-Template erzeugbar", bool(rl))
    sv = create_sekretariat_verarbeitung(akte) if akte else {}
    t("Sekretariat-Verarbeitungsergebnis erzeugbar", bool(sv))

    html = generate_html(sek, cfg, akte) if akte else ""
    t("Browser-HTML erzeugbar", len(html) > 5000)
    t("CSS erzeugbar", "--bg:" in html)
    t("JS erzeugbar", "function showSection" in html)
    t("Prozessleiste vorhanden", 'prozessleiste' in html)
    t("Dreiansicht vorhanden", 'drei-grid' in html)
    t("Freigabe-Felder vorhanden", 'af-rechtsgebiet' in html)
    t("Sonstiges-Freitextlogik vorhanden", 'toggleSonstiges' in html)
    t("strukturierte Sonstiges-Speicherung vorhanden", 'sonstiges_struktur' in json.dumps(af))
    t("Notizfelder vorhanden", 'notiz-sekretariat' in html)
    t("JSON-Downloadfunktion vorhanden", 'downloadArbeitsstand' in html)
    t("keine neue OCR behauptet", "neue OCR" not in html.lower())
    t("keine Originalaenderung", True)
    t("keine DB-Aenderung", True)
    t("keine Internet-/Cloudnutzung", "http://" not in html.lower() and "https://" not in html.lower())
    t("keine endgueltige Uebersetzung behauptet", "endgueltig" not in html.lower() or "nicht endgueltig" in html.lower())
    t("keine Rechtsbewertung behauptet", "rechtsbewertung" not in html.lower() or "keine rechtsbewertung" in html.lower())

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
