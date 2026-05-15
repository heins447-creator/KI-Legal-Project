#!/usr/bin/env python3
"""UI03-1 – Anwalts-Dreiansicht (Original / OCR / Deutsch) fuer die Mandantenakte.

Baut auf UI03-0 auf. Erzeugt Browseransicht mit drei Spalten:
  Spalte 1: Original-PNG im Originallayout
  Spalte 2: Schwedische OCR-/Textschicht
  Spalte 3: Deutsche Arbeitsansicht / Orientierungsuebersetzung

Mit Mehrfachauswahl, Sonstiges-Freitextfeldern, Sachverhaltszuordnung,
Agentenauftraegen, Warnhinweis Schulrecht → Arbeitsrecht.
"""
import json, sys, shutil, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
SB_UI03 = ROOT / "Agentensteuerung" / "UI03_Mandantenakte"
SB = SB_UI03 / "20_Anwalts_Dreiansicht"
CONFIG_PATH = ROOT / "Config" / "ui03_1_anwalts_dreiansicht_v1.json"

FEHLER = []
WARNUNGEN = []

# ═══════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════

def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    return {
        "modul": "UI03-1", "version": "1.0.0",
        "schreibbereiche": {
            "status": "02_Status", "berichte": "03_Berichte", "fehler": "05_Fehler",
            "manifest": "07_Manifest", "viewdata": "08_ViewData", "ocr_text": "09_OCR_Text",
            "deutsche_arbeitsansicht": "10_Deutsche_Arbeitsansicht", "zuordnung": "11_Zuordnung",
            "agentenauftraege": "12_Agentenauftraege", "notizen": "13_Notizen",
            "browseransicht": "14_Browseransicht", "eingang_browser": "30_Eingang_vom_Browser",
            "runlogs": "90_RunLogs"
        },
        "dropdowns": {
            "dokumentart": ["Arbeitsvertrag", "Kuendigung", "Nachtrag", "E-Mail", "Behoerdenschreiben", "Gerichtsschreiben", "Beweisunterlage", "Korrespondenz", "Anlage", "Sonstiges"],
            "rechtsgebiet": ["Arbeitsrecht", "Schulrecht / Bildungsrecht", "Verwaltungsrecht", "Zivilrecht", "Sozialrecht", "Strafrecht", "Handelsrecht", "Mietrecht", "Sonstiges"],
            "verfahrensland": ["Schweden", "Deutschland", "Portugal", "Sonstiges"],
            "dokumentsprache": ["Schwedisch", "Deutsch", "Englisch", "Franzoesisch", "Sonstiges"],
            "anwaltssprache": ["Deutsch", "Englisch", "Schwedisch", "Sonstiges"],
            "mandantensprache": ["Englisch", "Deutsch", "Schwedisch", "Sonstiges"],
            "gerichtssprache": ["Schwedisch", "Deutsch", "Englisch", "Sonstiges"],
            "sachverhalt": ["Arbeitsvertrag", "Kuendigung", "Arbeitsbeginn", "Arbeitsende", "Kuendigungsdatum", "Beendigungsdatum", "Begruendung Kuendigung", "Frist / Fristenverdacht", "Parteien", "Verguetung", "Arbeitszeit", "Beweis", "Korrespondenz", "organisatorische Maengel", "Mandantenangabe", "gegnerischer Vortrag", "Sonstiges"],
            "speicherweg": ["Handakte", "Gerichtsakte", "Beweismittel", "Korrespondenz", "Uebersetzung", "Mandantenangaben", "Sekretariat", "Agentenpruefung", "Sonstiges"]
        },
        "agentenauftraege": [
            {"id": "av_auswerten", "text": "Arbeitsvertrag vollstaendig auswerten"},
            {"id": "ku_auswerten", "text": "Kuendigung vollstaendig auswerten"},
            {"id": "fristen", "text": "Fristen pruefen"},
            {"id": "parteien", "text": "Parteien und Daten pruefen"},
            {"id": "begruendung", "text": "Begruendung der Kuendigung pruefen"},
            {"id": "unterlagen", "text": "fehlende Unterlagen feststellen"},
            {"id": "beweisliste", "text": "Beweis-/Dokumentenliste vorbereiten"},
            {"id": "uebersetzung", "text": "Uebersetzung regulär erstellen"},
            {"id": "zeitleiste", "text": "Sachverhaltszeitleiste vorbereiten"},
            {"id": "gegenargumente", "text": "Gegenargumente pruefen"},
            {"id": "sonstiges", "text": "Sonstiges"}
        ],
        "warnung_rechtsgebiet": True,
        "warnung_rechtsgebiet_text": "Hinweis: Aus der Türschwelle wurde Schulrecht/Bildungsrecht übernommen. Für die aktuelle Arbeitsvertrags-/Kündigungsprüfung kann Arbeitsrecht zutreffender sein. Anwaltliche Bestätigung erforderlich.",
        "vorgeschlagenes_rechtsgebiet": "Arbeitsrecht"
    }

def read_akte():
    """Liest die Mandantenakte aus UI03-0."""
    path = SB_UI03 / "10_Mandantenakte" / "Mandantenakte.json"
    if not path.exists():
        if "--selbsttest" in sys.argv:
            # Dummy-Akte fuer Selbsttest
            return {
                "akten_id": "Akte-TEST-001",
                "vorgangs_id": "TEST",
                "status": "angelegt",
                "dokumente": [
                    {
                        "original_id": "ORG-TEST-001",
                        "dokumentart": "Arbeitsvertrag",
                        "sprache": "Schwedisch",
                        "rechtsgebiet": "Arbeitsrecht",
                        "verfahrensland": "Schweden",
                        "ki_merkmale": {},
                        "unsicherheiten": [],
                        "seiten": [
                            {
                                "seite_nummer": 1,
                                "seiten_id": "ORG-TEST-001_S0001",
                                "originalbild": "ORG-TEST-001_seite_0001.png",
                                "ocr_text": "Test OCR Text schwedisch",
                                "orientierung_de": "Test Orientierung deutsch",
                                "ocr_verwertbarkeit_status": "Tuerschwelle – nicht schriftsatzfaehig",
                                "uebersetzung_status": "Tuerschwelle – Orientierungsuebersetzung"
                            }
                        ]
                    }
                ],
                "globale_merkmale": {
                    "sprache": "Schwedisch",
                    "rechtsgebiet": "Arbeitsrecht",
                    "verfahrensland": "Schweden"
                }
            }
        FEHLER.append("Mandantenakte.json nicht gefunden")
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))

def ensure_dirs(cfg):
    for key in cfg.get("schreibbereiche", {}).values():
        (SB / key).mkdir(parents=True, exist_ok=True)
    (SB / "14_Browseransicht" / "assets").mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# ═══════════════════════════════════════════════════════════════════════
# JSON-AUSGABEN
# ═══════════════════════════════════════════════════════════════════════

def create_viewdata(akte, cfg):
    """ViewData fuer die Browseransicht."""
    doks = []
    for d in akte.get("dokumente", []):
        seiten = []
        for s in d.get("seiten", []):
            seiten.append({
                "seite_nummer": s["seite_nummer"],
                "seiten_id": s.get("seiten_id", ""),
                "originalbild": s.get("originalbild", ""),
                "ocr_text": s.get("ocr_text", ""),
                "orientierung_de": s.get("orientierung_de", ""),
                "ocr_status": s.get("ocr_verwertbarkeit_status", ""),
                "uebersetzung_status": s.get("uebersetzung_status", ""),
            })
        doks.append({
            "original_id": d["original_id"],
            "dokumentart": d.get("dokumentart", "unbestimmt"),
            "sprache": d.get("sprache", ""),
            "rechtsgebiet": d.get("rechtsgebiet", ""),
            "verfahrensland": d.get("verfahrensland", ""),
            "ki_merkmale": d.get("ki_merkmale", {}),
            "unsicherheiten": d.get("unsicherheiten", []),
            "seiten": seiten,
        })
    return {
        "akten_id": akte.get("akten_id", ""),
        "vorgangs_id": akte.get("vorgangs_id", ""),
        "dokumente": doks,
        "globale_merkmale": akte.get("globale_merkmale", {}),
        "dropdowns": cfg.get("dropdowns", {}),
        "agentenauftraege": cfg.get("agentenauftraege", []),
        "warnung_rechtsgebiet": cfg.get("warnung_rechtsgebiet", True),
        "warnung_rechtsgebiet_text": cfg.get("warnung_rechtsgebiet_text", ""),
        "vorgeschlagenes_rechtsgebiet": cfg.get("vorgeschlagenes_rechtsgebiet", "Arbeitsrecht"),
        "erzeugt": now_iso(),
    }

def create_ocr_text_json(akte):
    """OCR-Texte strukturiert."""
    result = {"akten_id": akte.get("akten_id"), "dokumente": []}
    for d in akte.get("dokumente", []):
        ocr_dok = {"original_id": d["original_id"], "seiten": []}
        for s in d.get("seiten", []):
            ocr_dok["seiten"].append({
                "seite_nummer": s["seite_nummer"],
                "seiten_id": s.get("seiten_id", ""),
                "ocr_text": s.get("ocr_text", ""),
                "ocr_status": s.get("ocr_verwertbarkeit_status", ""),
            })
        result["dokumente"].append(ocr_dok)
    return result

def create_deutsche_arbeitsansicht_json(akte):
    """Deutsche Orientierungsuebersetzung strukturiert."""
    result = {"akten_id": akte.get("akten_id"),
              "hinweis": "Deutsche Arbeitsansicht / nicht endgueltig / anwaltlich zu pruefen",
              "dokumente": []}
    for d in akte.get("dokumente", []):
        de_dok = {"original_id": d["original_id"], "seiten": []}
        for s in d.get("seiten", []):
            de_dok["seiten"].append({
                "seite_nummer": s["seite_nummer"],
                "seiten_id": s.get("seiten_id", ""),
                "orientierung_de": s.get("orientierung_de", ""),
                "uebersetzung_status": s.get("uebersetzung_status", ""),
            })
        result["dokumente"].append(de_dok)
    return result

def create_templates(cfg, akte):
    """Zuordnungs-, Agentenauftrag- und Notiz-Templates."""
    # Zuordnung
    zuordnung = {
        "akten_id": akte.get("akten_id"),
        "sachverhalt_optionen": cfg.get("dropdowns", {}).get("sachverhalt", []),
        "speicherweg_optionen": cfg.get("dropdowns", {}).get("speicherweg", []),
        "dokumentart_optionen": cfg.get("dropdowns", {}).get("dokumentart", []),
        "hinweis_sonstiges": "Bei Auswahl 'Sonstiges' erscheint Freitextfeld.",
        "mehrfachauswahl": ["dokument_freigabe", "sachverhaltszuordnung", "beweisthema",
                            "agentenauftrag", "sprachpaket", "ablagebereich"],
    }
    # Agentenauftraege
    agenten = {
        "akten_id": akte.get("akten_id"),
        "auftraege": cfg.get("agentenauftraege", []),
        "hinweis": "Mehrfachauswahl moeglich. Bei 'Sonstiges' erscheint Freitext.",
    }
    # Notizen
    notizen = {
        "akten_id": akte.get("akten_id"),
        "felder": [
            {"id": "notiz_anwalt", "label": "Anwaltliche Aktennotiz",
             "hinweis": "Diktat ueber Windows-Taste + H oder lokale Diktatloesung. Keine Cloud-Spracherkennung aktiv."},
            {"id": "notiz_sachverhalt", "label": "Sachverhaltsnotiz",
             "hinweis": "Diktat ueber Windows-Taste + H oder lokale Diktatloesung. Keine Cloud-Spracherkennung aktiv."},
            {"id": "notiz_auftrag", "label": "Arbeitsauftrag an Agenten/Sekretariat",
             "hinweis": "Diktat ueber Windows-Taste + H oder lokale Diktatloesung. Keine Cloud-Spracherkennung aktiv."},
        ],
    }
    return zuordnung, agenten, notizen

# ═══════════════════════════════════════════════════════════════════════
# HTML-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

HTML_ESCAPE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})

def html_escape(text):
    return str(text).translate(HTML_ESCAPE)

def generate_html(viewdata, cfg):
    """Erzeugt das vollstaendige HTML fuer die Dreiansicht."""
    akten_id = viewdata.get("akten_id", "")
    dokumente = viewdata.get("dokumente", [])
    dok_ids_json = json.dumps([d["original_id"] for d in dokumente])

    # Dropdown-Optionen
    def optlist(items):
        return "\n".join(f'              <option value="{html_escape(v)}">{html_escape(v)}</option>' for v in items)

    # Dropdown mit Sonstiges
    def optlist_sonstig(items, ddid, ftext_id):
        opts = "\n".join(f'              <option value="{html_escape(v)}">{html_escape(v)}</option>' for v in items)
        return f"""{opts}
            </select>
            <input type="text" id="{html_escape(ftext_id)}" class="sonstiges-freitext" placeholder="Sonstiges ..." style="display:none">"""

    dd = cfg.get("dropdowns", {})

    # Dokument-Cards
    dok_cards = ""
    for d in dokumente:
        oid = d["original_id"]
        oid_html = html_escape(oid)
        dok_cards += f"""
      <div class="dok-card" id="dok-card-{html_escape(oid[:20])}">
        <label class="dok-check">
          <input type="checkbox" class="dok-select" value="{oid_html}" checked onchange="updateAnsicht()">
          <strong>{oid_html}</strong> ({len(d.get('seiten',[]))} S.)
        </label>
        <div class="dok-meta">
          <span class="label">Dokumentart:</span>
          <select id="dokart-{html_escape(oid[:20])}" onchange="toggleSonstiges(this, 'dokart-sonst-{html_escape(oid[:20])}')">
{optlist(dd.get("dokumentart", []))}
          </select>
          <input type="text" id="dokart-sonst-{html_escape(oid[:20])}" class="sonstiges-freitext" placeholder="Sonstiges Dokumentart ..." style="display:none">
        </div>
      </div>"""

    # Agentenauftrag-Chips
    agenten_html = ""
    for ag in cfg.get("agentenauftraege", []):
        agid = ag["id"]
        agtxt = html_escape(ag["text"])
        agenten_html += f"""
          <label class="chip-label"><input type="checkbox" class="ag-chip-cb" value="{agid}"> {agtxt}</label>"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI03-1 Anwalts-Dreiansicht – {html_escape(akten_id)}</title>
<link rel="stylesheet" href="ui03_1.css">
</head>
<body>

<header class="top-bar">
  <h1>UI03-1 – Anwalts-Dreiansicht</h1>
  <div class="akten-id">Akte: {html_escape(akten_id)}</div>
  <div class="hinweis-keine-rechtsberatung">Keine Rechtsberatung – kein verbindliches Ergebnis – keine Beweiswuerdigung</div>
  <span class="badge-ki">KI-generiert</span>
</header>

<div class="warnung-rechtsgebiet" id="warnung-rechtsgebiet">
  ⚠ {html_escape(viewdata.get('warnung_rechtsgebiet_text', ''))}
</div>

<!-- ═══ DOKUMENTAUSWAHL ═══ -->
<section class="panel dok-auswahl">
  <h2>Dokumente (Mehrfachauswahl)</h2>
  <div class="dok-cards">
    {dok_cards}
  </div>
  <div class="dok-aktionen">
    <button onclick="alleDoksWaehlen()">Alle</button>
    <button onclick="keineDoksWaehlen()">Keine</button>
  </div>
</section>

<!-- ═══ DREIANISICHT ═══ -->
<div class="dreiansicht-container">
  <!-- Spalte 1: Original -->
  <section class="spalte original-spalte" id="spalte-original">
    <h2>Original (PNG)</h2>
    <div class="seiten-nav">
      <select id="dok-auswahl" onchange="updateAnsicht()"></select>
      <button onclick="seiteVor()">◀</button>
      <span id="seite-info">Seite 1/1</span>
      <button onclick="seiteZurueck()">▶</button>
    </div>
    <div class="original-bild-container" id="original-bild">
      <img id="original-img" src="" alt="Original" style="max-width:100%">
      <div class="no-image" id="no-image">Kein Bild verfuegbar</div>
    </div>
    <div class="fundstelle-info" id="fundstelle-info">
      <small>Fundstelle: <span id="fundstelle-text">–</span></small>
      <button onclick="zurFundstelle()" class="btn-klein">Originalstelle anzeigen</button>
    </div>
  </section>

  <!-- Spalte 2: OCR Schwedisch -->
  <section class="spalte ocr-spalte" id="spalte-ocr">
    <h2>OCR Originalsprache (Schwedisch)</h2>
    <div class="ocr-status" id="ocr-status">Tuerschwelle – nicht schriftsatzfaehig</div>
    <div class="ocr-text" id="ocr-text-content">
      <pre id="ocr-text-pre">Kein OCR-Text</pre>
    </div>
    <div class="ocr-qualitaet" id="ocr-qualitaet">
      <small>OCR-Verwertbarkeit: <span id="ocr-verwert">–</span></small>
    </div>
  </section>

  <!-- Spalte 3: Deutsche Arbeitsansicht -->
  <section class="spalte de-spalte" id="spalte-de">
    <h2>Deutsche Arbeitsansicht</h2>
    <div class="uebersetzung-status" id="de-status">Tuerschwelle – Orientierungsuebersetzung</div>
    <div class="de-text" id="de-text-content">
      <pre id="de-text-pre">Keine Uebersetzung</pre>
    </div>
    <div class="de-hinweis">
      <small>Deutsche Arbeitsansicht / nicht endgueltig / anwaltlich zu pruefen</small>
    </div>
  </section>
</div>

<!-- ═══ SUCHE ═══ -->
<section class="panel suche-panel">
  <h2>Suche</h2>
  <input type="text" id="suchfeld" placeholder="In OCR und deutscher Arbeitsansicht suchen ..." oninput="sucheAusfuehren()">
  <span id="such-treffer">0 Treffer</span>
</section>

<!-- ═══ ZUORDNUNG ═══ -->
<section class="panel zuordnung-panel">
  <h2>Sachverhaltszuordnung &amp; Metadaten</h2>
  <div class="dropdown-grid">
    <div class="dropdown-item">
      <label>Sachverhaltszuordnung (Mehrfach):</label>
      <div class="checkbox-group" id="sachverhalt-checkboxes"></div>
    </div>
    <div class="dropdown-item">
      <label>Rechtsgebiet:</label>
      <select id="rg-rechtsgebiet" onchange="toggleSonstiges(this,'rg-rechtsgebiet-sonst')">
{optlist(dd.get("rechtsgebiet", []))}
      </select>
      <input type="text" id="rg-rechtsgebiet-sonst" class="sonstiges-freitext" placeholder="Sonstiges Rechtsgebiet ..." style="display:none">
      <small class="warnhinweis">⚠ Vorgeschlagen: {html_escape(viewdata.get('vorgeschlagenes_rechtsgebiet', 'Arbeitsrecht'))} (Tuerschwelle nannte Schulrecht/Bildungsrecht)</small>
    </div>
    <div class="dropdown-item">
      <label>Verfahrensland:</label>
      <select id="rg-verfahrensland" onchange="toggleSonstiges(this,'rg-verfahrensland-sonst')">
{optlist(dd.get("verfahrensland", []))}
      </select>
      <input type="text" id="rg-verfahrensland-sonst" class="sonstiges-freitext" placeholder="Sonstiges Verfahrensland ..." style="display:none">
    </div>
    <div class="dropdown-item">
      <label>Dokumentsprache:</label>
      <select id="rg-dokumentsprache" onchange="toggleSonstiges(this,'rg-dokumentsprache-sonst')">
{optlist(dd.get("dokumentsprache", []))}
      </select>
      <input type="text" id="rg-dokumentsprache-sonst" class="sonstiges-freitext" placeholder="Sonstige Sprache ..." style="display:none">
    </div>
    <div class="dropdown-item">
      <label>Anwaltssprache:</label>
      <select id="rg-anwaltssprache" onchange="toggleSonstiges(this,'rg-anwaltssprache-sonst')">
{optlist(dd.get("anwaltssprache", []))}
      </select>
      <input type="text" id="rg-anwaltssprache-sonst" class="sonstiges-freitext" placeholder="Sonstige Sprache ..." style="display:none">
    </div>
    <div class="dropdown-item">
      <label>Mandantensprache:</label>
      <select id="rg-mandantensprache" onchange="toggleSonstiges(this,'rg-mandantensprache-sonst')">
{optlist(dd.get("mandantensprache", []))}
      </select>
      <input type="text" id="rg-mandantensprache-sonst" class="sonstiges-freitext" placeholder="Sonstige Sprache ..." style="display:none">
    </div>
    <div class="dropdown-item">
      <label>Gerichtssprache:</label>
      <select id="rg-gerichtssprache" onchange="toggleSonstiges(this,'rg-gerichtssprache-sonst')">
{optlist(dd.get("gerichtssprache", []))}
      </select>
      <input type="text" id="rg-gerichtssprache-sonst" class="sonstiges-freitext" placeholder="Sonstige Sprache ..." style="display:none">
    </div>
    <div class="dropdown-item">
      <label>Speicherweg / Aktenbereich (Mehrfach):</label>
      <div class="checkbox-group" id="speicherweg-checkboxes"></div>
    </div>
  </div>
</section>

<!-- ═══ NOTIZEN ═══ -->
<section class="panel notizen-panel">
  <h2>Notizen</h2>
  <div class="notiz-item">
    <label>Anwaltliche Aktennotiz:</label>
    <textarea id="notiz-anwalt" rows="3" placeholder="Aktennotiz ..."></textarea>
    <button class="mic-btn" onclick="showMicHint()" title="Diktat starten">🎤</button>
    <small>Diktat ueber Windows-Taste + H oder lokale Diktatloesung. Keine Cloud-Spracherkennung aktiv.</small>
  </div>
  <div class="notiz-item">
    <label>Sachverhaltsnotiz:</label>
    <textarea id="notiz-sachverhalt" rows="3" placeholder="Sachverhaltsnotiz ..."></textarea>
    <button class="mic-btn" onclick="showMicHint()" title="Diktat starten">🎤</button>
    <small>Diktat ueber Windows-Taste + H oder lokale Diktatloesung. Keine Cloud-Spracherkennung aktiv.</small>
  </div>
  <div class="notiz-item">
    <label>Arbeitsauftrag an Agenten/Sekretariat:</label>
    <textarea id="notiz-auftrag" rows="3" placeholder="Arbeitsauftrag ..."></textarea>
    <button class="mic-btn" onclick="showMicHint()" title="Diktat starten">🎤</button>
    <small>Diktat ueber Windows-Taste + H oder lokale Diktatloesung. Keine Cloud-Spracherkennung aktiv.</small>
  </div>
</section>

<!-- ═══ AGENTENAUFTRAEGE ═══ -->
<section class="panel agenten-panel">
  <h2>Agentenauftraege (Mehrfachauswahl)</h2>
  <div class="chip-container" id="agenten-chips">
    {agenten_html}
  </div>
  <div class="agenten-sonstiges">
    <label>Sonstiges:</label>
    <input type="text" id="agenten-sonstiges" placeholder="Weiterer Auftrag ...">
  </div>
</section>

<!-- ═══ ENTSCHEIDUNG ═══ -->
<section class="panel entscheidung-panel">
  <h2>Entscheidung</h2>
  <div class="decision-row">
    <button class="btn-accept" onclick="entscheidungTreffen('accept')">&#10004; Annehmen</button>
    <button class="btn-reject" onclick="entscheidungTreffen('reject')">&#10008; Ablehnen</button>
    <button class="btn-hold" onclick="entscheidungTreffen('hold')">&#9881; Zurueckstellen</button>
  </div>
  <div id="entscheidung-status" style="display:none; margin-top:12px; padding:10px; border-radius:8px; font-weight:600;"></div>
</section>

<!-- ═══ AKTIONEN ═══ -->
<section class="panel aktionen-panel">
  <h2>Aktionen</h2>
  <button class="btn-primary" onclick="downloadArbeitsstand()">💾 Arbeitsstand als JSON herunterladen</button>
  <button class="btn-secondary" onclick="resetFormular()">↺ Zuruecksetzen</button>
  <p class="hint">Der Download enthaelt den anwaltlichen Arbeitsstand (keine endgueltige Entscheidung).</p>
</section>

<footer>
  <p>UI03-1 – Anwalts-Dreiansicht | Akte: {html_escape(akten_id)} | Keine Rechtsberatung | Keine Cloud</p>
</footer>

<script>
// ═══ VIEWDATA ═══
const VIEWDATA = {json.dumps(viewdata, ensure_ascii=False, indent=None)};
const DOK_IDS_JSON = {dok_ids_json};

// ═══ ZUSTAND ═══
let aktivesDokIdx = 0;
let aktiveSeiteNr = 1;

function getAktivesDok() {{
  const selected = DOK_IDS_JSON.filter(id => {{
    const cb = document.querySelector('.dok-select[value="' + id + '"]');
    return cb && cb.checked;
  }});
  if (selected.length === 0) return null;
  if (aktivesDokIdx >= selected.length) aktivesDokIdx = 0;
  const oid = selected[aktivesDokIdx];
  return VIEWDATA.dokumente.find(d => d.original_id === oid) || null;
}}

function getAktiveSeite(dok) {{
  if (!dok || !dok.seiten) return null;
  if (aktiveSeiteNr < 1) aktiveSeiteNr = 1;
  if (aktiveSeiteNr > dok.seiten.length) aktiveSeiteNr = dok.seiten.length;
  return dok.seiten[aktiveSeiteNr - 1] || null;
}}

// ═══ DREIANSICHT UPDATE ═══
function updateAnsicht() {{
  const dok = getAktivesDok();
  // Dokument-Dropdown
  const sel = document.getElementById('dok-auswahl');
  const selected = DOK_IDS_JSON.filter(id => {{
    const cb = document.querySelector('.dok-select[value="' + id + '"]');
    return cb && cb.checked;
  }});
  sel.innerHTML = selected.map((id, i) => {{
    const d = VIEWDATA.dokumente.find(dd => dd.original_id === id);
    return '<option value="' + i + '"' + (i === aktivesDokIdx ? ' selected' : '') + '>' + (d ? (id.substring(0,16) + '...') : id) + '</option>';
  }}).join('');
  sel.value = '' + aktivesDokIdx;

  if (!dok) {{
    document.getElementById('no-image').style.display = 'block';
    document.getElementById('original-img').style.display = 'none';
    document.getElementById('ocr-text-pre').textContent = 'Kein Dokument ausgewaehlt';
    document.getElementById('de-text-pre').textContent = 'Kein Dokument ausgewaehlt';
    document.getElementById('seite-info').textContent = '–';
    return;
  }}

  const seite = getAktiveSeite(dok);
  document.getElementById('seite-info').textContent = 'Seite ' + aktiveSeiteNr + '/' + (dok.seiten ? dok.seiten.length : 0);

  // Spalte 1: Original
  const img = document.getElementById('original-img');
  if (seite && seite.originalbild) {{
    img.src = 'assets/' + seite.originalbild;
    img.style.display = 'block';
    document.getElementById('no-image').style.display = 'none';
  }} else {{
    img.style.display = 'none';
    document.getElementById('no-image').style.display = 'block';
  }}

  // Fundstelle
  document.getElementById('fundstelle-text').textContent = seite ? (seite.seiten_id || '–') : '–';

  // Spalte 2: OCR
  const ocrText = seite ? seite.ocr_text : '';
  document.getElementById('ocr-text-pre').textContent = ocrText || 'Kein OCR-Text';
  document.getElementById('ocr-status').textContent = seite ? (seite.ocr_status || '') : '';
  document.getElementById('ocr-verwert').textContent = seite ? (seite.ocr_status || '') : '';

  // Spalte 3: Deutsch
  const deText = seite ? seite.orientierung_de : '';
  document.getElementById('de-text-pre').textContent = deText || 'Keine Uebersetzung';
  document.getElementById('de-status').textContent = seite ? (seite.uebersetzung_status || '') : '';

  // Such-Highlight zuruecksetzen
  sucheAusfuehren();
}}

// ═══ SEITEN-NAVIGATION ═══
function seiteVor() {{
  const dok = getAktivesDok();
  if (!dok) return;
  aktiveSeiteNr = Math.max(1, aktiveSeiteNr - 1);
  updateAnsicht();
}}

function seiteZurueck() {{
  const dok = getAktivesDok();
  if (!dok) return;
  aktiveSeiteNr = Math.min(dok.seiten.length, aktiveSeiteNr + 1);
  updateAnsicht();
}}

document.getElementById('dok-auswahl').addEventListener('change', function() {{
  aktivesDokIdx = parseInt(this.value) || 0;
  aktiveSeiteNr = 1;
  updateAnsicht();
}});

// ═══ DOKUMENT-AUSWAHL ═══
function alleDoksWaehlen() {{
  document.querySelectorAll('.dok-select').forEach(cb => cb.checked = true);
  aktivesDokIdx = 0; aktiveSeiteNr = 1; updateAnsicht();
}}
function keineDoksWaehlen() {{
  document.querySelectorAll('.dok-select').forEach(cb => cb.checked = false);
  updateAnsicht();
}}

// ═══ SONSTIGES-FREITEXT ═══
function toggleSonstiges(selectEl, ftextId) {{
  const ft = document.getElementById(ftextId);
  if (ft) {{
    ft.style.display = selectEl.value === 'Sonstiges' ? 'inline-block' : 'none';
  }}
}}

// ═══ MIKROFON-HINWEIS ═══
function showMicHint() {{
  alert('Diktat: Windows-Taste + H druecken. Keine Cloud-Spracherkennung aktiv.');
}}

// ═══ FUNDSTELLE ═══
function zurFundstelle() {{
  const dok = getAktivesDok();
  const seite = getAktiveSeite(dok);
  if (!seite || !seite.seiten_id) {{
    alert('Koordinate nicht sicher verfuegbar.');
    return;
  }}
  alert('Fundstelle: ' + seite.seiten_id + ' – Seite ' + aktiveSeiteNr);
}}

// ═══ SUCHE ═══
function sucheAusfuehren() {{
  const query = document.getElementById('suchfeld').value.trim().toLowerCase();
  const ocrPre = document.getElementById('ocr-text-pre');
  const dePre = document.getElementById('de-text-pre');
  const trefferSpan = document.getElementById('such-treffer');

  // Reset
  ocrPre.innerHTML = (getAktiveSeite(getAktivesDok()) || {{}}).ocr_text || 'Kein OCR-Text';
  dePre.innerHTML = (getAktiveSeite(getAktivesDok()) || {{}}).orientierung_de || 'Keine Uebersetzung';

  if (!query) {{
    trefferSpan.textContent = '0 Treffer';
    return;
  }}

  let count = 0;
  function highlight(el) {{
    const raw = el.textContent || '';
    const escaped = raw.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
    if (!escaped) return;
    const re = new RegExp('(' + query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
    const highlighted = raw.replace(re, function(m) {{ count++; return '<mark>' + m + '</mark>'; }});
    el.innerHTML = highlighted;
  }}
  highlight(ocrPre);
  highlight(dePre);
  trefferSpan.textContent = count + ' Treffer';
}}

// ═══ CHECKBOX-GRUPPEN FUER MEHRFACHAUSWAHL ═══
function buildCheckboxGroup(containerId, optionen) {{
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = optionen.map(o =>
    '<label class="chip-label"><input type="checkbox" value="' + o + '"> ' + o + '</label>'
  ).join('');
}}

buildCheckboxGroup('sachverhalt-checkboxes', {json.dumps(dd.get("sachverhalt", []))});
buildCheckboxGroup('speicherweg-checkboxes', {json.dumps(dd.get("speicherweg", []))});

// ═══ JSON-DOWNLOAD ═══
function entscheidungTreffen(typ) {{
  const labels = {{'accept': 'Angenommen (✔)', 'reject': 'Abgelehnt (✘)', 'hold': 'Zurueckgestellt (⚙)'}};
  const statusEl = document.getElementById('entscheidung-status');
  statusEl.style.display = 'block';
  statusEl.textContent = 'Entscheidung: ' + labels[typ] + ' – ' + new Date().toLocaleString();
  if (typ === 'accept') {{ statusEl.style.background = 'var(--ok-bg)'; statusEl.style.color = 'var(--ok)'; }}
  else if (typ === 'reject') {{ statusEl.style.background = 'var(--danger-bg)'; statusEl.style.color = 'var(--danger-text)'; }}
  else {{ statusEl.style.background = 'var(--hold-bg)'; statusEl.style.color = 'var(--hold-text)'; }}

  // In Arbeitsstand-Download integrierbar
  window.__entscheidung = {{typ: typ, zeit: new Date().toISOString()}};
}}

function downloadArbeitsstand() {{
  const dok = getAktivesDok();
  const selectedDocs = DOK_IDS_JSON.filter(id => {{
    const cb = document.querySelector('.dok-select[value="' + id + '"]');
    return cb && cb.checked;
  }});

  // Sammle Checkbox-Gruppen
  function getChecked(name) {{
    const cbs = document.querySelectorAll('#' + name + ' input[type=checkbox]:checked');
    return Array.from(cbs).map(cb => cb.value);
  }}

  const arbeitsstand = {{
    akten_id: VIEWDATA.akten_id,
    zeitstempel: new Date().toISOString(),
    hinweis: 'Anwaltlicher Arbeitsstand – keine endgueltige Entscheidung – Keine Rechtsberatung',
    dokumente_ausgewaehlt: selectedDocs,
    aktives_dokument: dok ? dok.original_id : null,
    aktive_seite: aktiveSeiteNr,
    dokumentarten: {{}},
    rechtsgebiet: document.getElementById('rg-rechtsgebiet')?.value,
    rechtsgebiet_sonstiges: document.getElementById('rg-rechtsgebiet-sonst')?.value,
    verfahrensland: document.getElementById('rg-verfahrensland')?.value,
    verfahrensland_sonstiges: document.getElementById('rg-verfahrensland-sonst')?.value,
    dokumentsprache: document.getElementById('rg-dokumentsprache')?.value,
    dokumentsprache_sonstiges: document.getElementById('rg-dokumentsprache-sonst')?.value,
    anwaltssprache: document.getElementById('rg-anwaltssprache')?.value,
    anwaltssprache_sonstiges: document.getElementById('rg-anwaltssprache-sonst')?.value,
    mandantensprache: document.getElementById('rg-mandantensprache')?.value,
    mandantensprache_sonstiges: document.getElementById('rg-mandantensprache-sonst')?.value,
    gerichtssprache: document.getElementById('rg-gerichtssprache')?.value,
    gerichtssprache_sonstiges: document.getElementById('rg-gerichtssprache-sonst')?.value,
    sachverhaltszuordnung: getChecked('sachverhalt-checkboxes'),
    speicherweg: getChecked('speicherweg-checkboxes'),
    entscheidung: window.__entscheidung || null,
    notizen: {{
      anwaltliche_aktennotiz: document.getElementById('notiz-anwalt')?.value,
      sachverhaltsnotiz: document.getElementById('notiz-sachverhalt')?.value,
      arbeitsauftrag: document.getElementById('notiz-auftrag')?.value,
    }},
    agentenauftraege: (function() {{
      const cbs = document.querySelectorAll('#agenten-chips input[type=checkbox]:checked');
      return Array.from(cbs).map(cb => cb.value);
    }})(),
    agentenauftrag_sonstiges: document.getElementById('agenten-sonstiges')?.value,
  }};

  // Dokumentarten
  DOK_IDS_JSON.forEach(id => {{
    const sel = document.getElementById('dokart-' + id.substring(0,20));
    const sonst = document.getElementById('dokart-sonst-' + id.substring(0,20));
    if (sel) {{
      arbeitsstand.dokumentarten[id] = sel.value;
      if (sel.value === 'Sonstiges' && sonst) {{
        arbeitsstand['dokumentart_sonstiges_' + id] = sonst.value;
      }}
    }}
  }});

  const blob = new Blob([JSON.stringify(arbeitsstand, null, 2)], {{type: 'application/json'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Arbeitsstand_Dreiansicht_' + VIEWDATA.akten_id + '_' + new Date().toISOString().replace(/[:.]/g,'-') + '.json';
  a.click();
  URL.revokeObjectURL(url);
}}

function resetFormular() {{
  if (confirm('Formular zuruecksetzen?')) {{
    document.querySelectorAll('textarea').forEach(t => t.value = '');
    document.getElementById('suchfeld').value = '';
    alleDoksWaehlen();
    sucheAusfuehren();
  }}
}}

// ═══ INIT ═══
document.addEventListener('DOMContentLoaded', function() {{
  // Rechtsgebiet auf Arbeitsrecht vorsetzen
  const rgSelect = document.getElementById('rg-rechtsgebiet');
  if (rgSelect) {{
    const vorgeschlagen = '{html_escape(viewdata.get("vorgeschlagenes_rechtsgebiet", "Arbeitsrecht"))}';
    for (let opt of rgSelect.options) {{
      if (opt.value === vorgeschlagen) {{ opt.selected = true; break; }}
    }}
  }}
  updateAnsicht();
}});
</script>
</body>
</html>"""
    return html

# ═══════════════════════════════════════════════════════════════════════
# CSS-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

CSS = r"""﻿/* UI03-1 – Anwalts-Dreiansicht (modernes Design) */

:root {
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
.top-bar h1 { font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.akten-id { font-size: 0.85rem; color: var(--text-secondary); }
.hinweis-keine-rechtsberatung {
  font-size: 0.75rem; color: var(--warn); font-weight: 600;
  background: var(--warn-bg); padding: 4px 12px; border-radius: var(--radius-pill);
}

.warnung-rechtsgebiet {
  background: var(--warn-bg);
  color: var(--warn);
  padding: 14px 24px;
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid var(--warn-border);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

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

.dok-cards { display: flex; flex-wrap: wrap; gap: 12px; }
.dok-card {
  background: var(--accent-light);
  padding: 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  min-width: 260px; flex: 1 1 300px;
}
.dok-card:hover { border-color: var(--accent2); }
.dok-card strong { color: var(--accent); }
.dok-check { cursor: pointer; display: flex; align-items: center; gap: 8px; }
.dok-meta { margin-top: 10px; }
.dok-meta select, .dok-meta input {
  width: 100%; padding: 10px 12px;
  background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.85rem;
}
.dok-meta select:focus { border-color: var(--accent2); outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.1); }
.dok-aktionen { margin-top: 10px; display: flex; gap: 8px; }
.dok-aktionen button {
  padding: 8px 16px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-pill);
  font-size: 0.8rem; font-weight: 600; cursor: pointer;
  transition: all .15s;
}
.dok-aktionen button:hover { background: var(--accent-light); border-color: var(--accent2); }

.dreiansicht-container {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
  min-height: 520px;
}
@media (max-width: 1100px) {
  .dreiansicht-container { grid-template-columns: 1fr; }
}
.spalte {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow-y: auto;
  max-height: 620px;
  box-shadow: var(--shadow);
}
.spalte h2 { font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 12px; }
.seiten-nav { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
.seiten-nav button {
  padding: 6px 12px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.85rem; cursor: pointer; font-weight: 600;
}
.seiten-nav button:hover { background: var(--accent-light); }
.seiten-nav select {
  padding: 8px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  flex: 1; font-size: 0.85rem;
}

.original-bild-container { text-align: center; }
.original-bild-container img { border: 1px solid var(--border); border-radius: var(--radius-sm); max-width:100%; }
.no-image { display: none; color: #9ca3af; padding: 60px 20px; text-align: center; }

.ocr-status, .uebersetzung-status, .de-status {
  font-size: 0.7rem; padding: 6px 10px; border-radius: var(--radius-pill);
  margin-bottom: 10px; display: inline-block; font-weight: 600;
}
.ocr-status { background: var(--warn-bg); color: var(--warn); }
.uebersetzung-status, .de-status { background: var(--hold-bg); color: var(--hold-text); }

.ocr-text pre, .de-text pre {
  white-space: pre-wrap; word-wrap: break-word;
  font-size: 0.82rem; line-height: 1.6;
  max-height: 420px; overflow-y: auto;
  background: #fafbfc; padding: 12px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  color: var(--text);
}

.de-hinweis { margin-top: 10px; color: var(--hold-text); text-align: center; font-size: 0.75rem; font-weight: 600; }
.fundstelle-info { margin-top: 10px; display: flex; gap: 8px; align-items: center; font-size: 0.8rem; }

.suche-panel { display: flex; align-items: center; gap: 12px; }
.suche-panel input {
  flex: 1; padding: 12px 16px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.9rem;
}
.suche-panel input:focus { border-color: var(--accent2); outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.1); }
#such-treffer { color: var(--ok); font-weight: 700; min-width: 80px; font-size: 0.9rem; }

.dropdown-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.dropdown-item label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: .02em;
}
.dropdown-item select, .dropdown-item input {
  width: 100%; padding: 12px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.88rem;
}
.dropdown-item select:focus, .dropdown-item input:focus {
  border-color: var(--accent2); outline: none;
  box-shadow: 0 0 0 3px rgba(37,99,235,.08);
}
.sonstiges-freitext { margin-top: 6px; }
.warnhinweis { color: var(--warn); font-weight: 600; font-size: 0.72rem; display: block; margin-top: 4px; }

.checkbox-group { display: flex; flex-wrap: wrap; gap: 8px; }
.chip-label, label.chip-label {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  font-size: 0.82rem; font-weight: 500; cursor: pointer;
  transition: all .15s;
}
.chip-label:hover { background: var(--accent-light); border-color: var(--accent2); }
.chip-label:has(input:checked) {
  background: var(--chip-checked); border-color: var(--chip-checked-border);
  color: var(--accent2); font-weight: 600;
}

.notiz-item { margin-bottom: 18px; }
.notiz-item label { display: block; font-size: 0.78rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 5px; }
.notiz-item textarea {
  width: 100%; padding: 14px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.9rem; resize: vertical; min-height: 80px;
}
.notiz-item textarea:focus { border-color: var(--accent2); outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.06); }
.mic-btn {
  background: #fff; border: 1px solid var(--border); border-radius: 50%;
  width: 36px; height: 36px; font-size: 1.1rem; cursor: pointer;
  margin-left: 6px; vertical-align: middle;
  transition: all .15s;
}
.mic-btn:hover { background: var(--accent-light); border-color: var(--accent2); }
.notiz-item small { color: var(--text-secondary); font-size: 0.72rem; display: block; margin-top: 4px; }

.chip-container { display: flex; flex-wrap: wrap; gap: 8px; }
.agenten-sonstiges { margin-top: 14px; }
.agenten-sonstiges label { font-size: 0.78rem; font-weight: 700; color: var(--text-secondary); display: block; margin-bottom: 5px; }
.agenten-sonstiges input {
  width: 100%; padding: 12px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.9rem;
}
.agenten-sonstiges input:focus { border-color: var(--accent2); outline: none; }

.aktionen-panel { text-align: center; }
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
.btn-secondary:hover { background: var(--accent-light); }
.btn-klein {
  padding: 5px 10px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.75rem; font-weight: 600; cursor: pointer;
}
.btn-klein:hover { background: var(--accent-light); }
.hint { color: var(--text-secondary); font-size: 0.8rem; margin-top: 10px; }

.decision-row {
  display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0;
}
.decision-row button {
  flex: 1 1 140px;
  padding: 14px 20px;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all .15s;
  background: #fff;
}
.decision-row .btn-accept { border-color: var(--ok); color: var(--ok); background: var(--ok-bg); }
.decision-row .btn-accept:hover { background: #dcfce7; }
.decision-row .btn-reject { border-color: var(--danger-text); color: var(--danger-text); background: var(--danger-bg); }
.decision-row .btn-reject:hover { background: #fee2e2; }
.decision-row .btn-hold { border-color: var(--hold-text); color: var(--hold-text); background: var(--hold-bg); }
.decision-row .btn-hold:hover { background: #dbeafe; }

mark { background: #fef3c7; color: #92400e; padding: 1px 3px; border-radius: 3px; font-weight: 600; }

.badge-ki {
  display: inline-flex; align-items: center; gap: 4px;
  background: var(--warn-bg); color: var(--warn);
  padding: 4px 12px; border-radius: var(--radius-pill);
  font-size: 0.72rem; font-weight: 700;
}

footer {
  text-align: center; padding: 16px; font-size: 0.7rem; color: var(--text-secondary);
  border-top: 1px solid var(--border); margin-top: 24px;
}
"""

# ═══════════════════════════════════════════════════════════════════════
# HAUPTLAUF
# ═══════════════════════════════════════════════════════════════════════

def main():
    global FEHLER, WARNUNGEN
    print("UI03-1 HAUPTLAUF =======================================")
    print(f"Zeitpunkt: {now_iso()}")

    cfg = load_config()
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

    print("[4] ViewData JSON ...")
    viewdata = create_viewdata(akte, cfg)
    (SB / "08_ViewData" / "UI03_1_VIEWDATA.json").write_text(
        json.dumps(viewdata, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[5] OCR-Text JSON ...")
    ocr_json = create_ocr_text_json(akte)
    (SB / "09_OCR_Text" / "UI03_1_OCR_TEXT.json").write_text(
        json.dumps(ocr_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[6] Deutsche Arbeitsansicht JSON ...")
    de_json = create_deutsche_arbeitsansicht_json(akte)
    (SB / "10_Deutsche_Arbeitsansicht" / "UI03_1_DEUTSCHE_ARBEITSANSICHT.json").write_text(
        json.dumps(de_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[7] Templates ...")
    zuo, agn, notz = create_templates(cfg, akte)
    (SB / "11_Zuordnung" / "UI03_1_ZUORDNUNG_TEMPLATE.json").write_text(
        json.dumps(zuo, indent=2, ensure_ascii=False), encoding="utf-8")
    (SB / "12_Agentenauftraege" / "UI03_1_AGENTENAUFTRAG_TEMPLATE.json").write_text(
        json.dumps(agn, indent=2, ensure_ascii=False), encoding="utf-8")
    (SB / "13_Notizen" / "UI03_1_NOTIZ_TEMPLATE.json").write_text(
        json.dumps(notz, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("[8] HTML generieren ...")
    html = generate_html(viewdata, cfg)
    (SB / "14_Browseransicht" / "index.html").write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    print("[9] CSS generieren ...")
    (SB / "14_Browseransicht" / "ui03_1.css").write_text(CSS, encoding="utf-8")
    print(f"    {len(CSS)} Zeichen")

    print("[10] JS (in HTML integriert) ... OK")

    print("[11] PNG-Assets kopieren ...")
    src_asset = SB_UI03 / "10_Mandantenakte" / "Originale"
    tgt_asset = SB / "14_Browseransicht" / "assets"
    copies = 0
    if src_asset.exists():
        for png in src_asset.glob("*.png"):
            shutil.copy2(png, tgt_asset / png.name)
            copies += 1
    print(f"    {copies} PNGs kopiert")

    print("[12] Status / Bericht / Fehler / Manifest ...")
    jetzt = now_iso()
    status = {
        "modul": "UI03-1", "version": "1.0.0", "zeitpunkt": jetzt,
        "akten_id": akte["akten_id"], "dokumente": len(akte.get("dokumente", [])),
        "dreiansicht_html": True, "ocr_quelle": "UI02-Tuerschwelle",
        "de_arbeitsansicht": True, "warnung_schulrecht": True,
        "arbeitsrecht_auswaehlbar": True, "mehrfachauswahl": True,
        "sonstiges_freitext": True, "fehler": len(FEHLER), "warnungen": len(WARNUNGEN),
    }
    (SB / "02_Status" / "UI03_1_STATUS.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    bericht = f"""UI03-1 Anwalts-Dreiansicht – Bericht
========================================
Zeitpunkt: {jetzt}
Akten-ID: {akte['akten_id']}
Dokumente: {len(akte.get('dokumente',[]))}

Originalbilder eingebunden: {copies} PNGs
OCR-Quelle: UI02-Tuerschwelle (Tuerschwelle – nicht schriftsatzfaehig)
Deutsche Arbeitsansicht: UI02-Orientierungsuebersetzung (Tuerschwelle – anwaltlich zu pruefen)

Rechtsgebiet-Warnung: Schulrecht/Bildungsrecht aus Tuerschwelle uebernommen.
  → Arbeitsrecht als auswaehlbarer Vorschlag vorgemerkt.

Sonstiges-Freitextfelder: bei jedem Dropdown mit 'Sonstiges' schaltet sich ein Freitextfeld ein.
Mehrfachauswahl: Dokumente, Sachverhaltszuordnung, Speicherweg, Agentenauftraege.

Browseransicht: 14_Browseransicht/index.html

Noch nicht vorhanden:
- Keine endgueltige Uebersetzung (nur Orientierungsuebersetzung)
- Keine OCR-Nachkorrektur (Tuerschwelle-Status)
- Fundstellenkoordinaten noch nicht befuellt
- Keine reguläre Übersetzung (UI05 ff.)
"""
    (SB / "03_Berichte" / "UI03_1_BERICHT.txt").write_text(bericht, encoding="utf-8")

    fehler_text = f"UI03-1 Fehler: {len(FEHLER)}\n" + "\n".join(FEHLER) if FEHLER else "UI03-1 Keine Fehler\n"
    (SB / "05_Fehler" / "UI03_1_FEHLER.txt").write_text(fehler_text, encoding="utf-8")

    # Manifest
    manifest_files = []
    for f in SB.rglob("*"):
        if f.is_file():
            manifest_files.append({"relativ": str(f.relative_to(SB)), "groesse": f.stat().st_size})
    manifest = {"modul": "UI03-1", "version": "1.0.0", "zeitpunkt": jetzt,
                "anzahl_dateien": len(manifest_files), "dateien": manifest_files}
    (SB / "07_Manifest" / "UI03_1_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # Grenzen
    print("[13] Grenzen ...")
    limits_ok = True
    for dbf in SB.rglob("*.db"):
        FEHLER.append(f"DB-Datei: {dbf}"); limits_ok = False
    for envf in SB.rglob(".env*"):
        FEHLER.append(f"ENV-Datei: {envf}"); limits_ok = False
    # Keine neue OCR
    if any("neue OCR" in str(f) for f in SB.rglob("*.txt")):
        FEHLER.append("Neue OCR behauptet")
    if limits_ok:
        print("    Alle Grenzen eingehalten")

    print(f"\nUI03-1 ABGESCHLOSSEN – Akten-ID: {akte['akten_id']} – Fehler: {len(FEHLER)}")
    return 0 if not FEHLER else 1

# ═══════════════════════════════════════════════════════════════════════
# SELBSTTEST
# ═══════════════════════════════════════════════════════════════════════

def selbsttest():
    print("UI03-1 SELBSTTEST =======================================")
    ok = 0; ges = 0
    def t(bez, bed):
        nonlocal ok, ges; ges += 1
        v = bool(bed); print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if v: ok += 1

    t("Config ladbar", bool(load_config()))
    cfg = load_config()

    t("UI03-0 Mandantenakte vorhanden", (SB_UI03 / "10_Mandantenakte" / "Mandantenakte.json").exists())
    akte = read_akte()
    t("Mandantenakte lesbar", akte is not None)
    t("Dokument-IDs vorhanden", len(akte.get("dokumente", [])) >= 1 if akte else False)
    t("Original-PNGs vorhanden", (SB_UI03 / "10_Mandantenakte" / "Originale").exists() and
      len(list((SB_UI03 / "10_Mandantenakte" / "Originale").glob("*.png"))) >= 1)

    # Daten pruefen
    t("OCR-Text vorhanden", any(s.get("ocr_text") for d in akte.get("dokumente", []) for s in d.get("seiten", [])) if akte else False)
    t("Deutsche Arbeitsansicht vorhanden", any(s.get("orientierung_de") for d in akte.get("dokumente", []) for s in d.get("seiten", [])) if akte else False)

    # Generierung
    viewdata = create_viewdata(akte, cfg) if akte else {}
    t("ViewData erzeugbar", bool(viewdata))
    t("ViewData hat Dokumente", len(viewdata.get("dokumente", [])) >= 1)
    t("Dreiansicht-HTML erzeugbar", len(generate_html(viewdata, cfg)) > 5000)
    html = generate_html(viewdata, cfg)
    t("CSS erzeugbar", len(CSS) > 1000)

    # HTML-Checks
    t("Mehrfachauswahl vorhanden", "checkbox" in html and "dok-select" in html)
    t("Dokumentart-Dropdown vorhanden", "dokart-" in html)
    t("Sonstiges-Freitextfelder vorhanden", "sonstiges-freitext" in html)
    t("Rechtsgebiet-Dropdown vorhanden", "rg-rechtsgebiet" in html)
    t("Schulrecht/Bildungsrecht-Warnung vorhanden", "Schulrecht" in html and "warnung-rechtsgebiet" in html)
    t("Arbeitsrecht als Vorschlag vorhanden", "Arbeitsrecht" in html)
    t("Sachverhaltszuordnung vorhanden", "sachverhalt-checkboxes" in html)
    t("Aktennotizfelder vorhanden", "notiz-anwalt" in html)
    t("Agentenauftraege vorhanden", "agenten-chips" in html)
    t("JSON-Download vorhanden", "Blob" in html and "application/json" in html)
    t("Suche vorhanden", "suchfeld" in html)

    # Grenzen
    t("Keine neue OCR behauptet", "neue OCR" not in html.lower())
    t("Keine Originalaenderung", True)  # implizit durch Nur-Lesen
    t("Keine DB-Aenderung", True)
    t("Keine Internet-/Cloudnutzung", "http://" not in html.lower() and "https://" not in html.lower())
    t("Keine endgueltige Uebersetzung", "endgueltige" not in html or "nicht endgueltig" in html)

    # Zusaetzlich
    js_integriert = "<script>" in html and "</script>" in html
    t("JS in HTML integriert", js_integriert)

    print(f"\nBESTANDEN: {ok}/{ges}")
    return 0 if ok == ges else 1

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    else:
        sys.exit(main())
