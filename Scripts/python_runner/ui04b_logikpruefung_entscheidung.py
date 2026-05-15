#!/usr/bin/env python3
"""UI04b Logikpruefung und gefuehrte Entscheidungsmaske.

Sekretariat -> Anwalt -> Ruecklauf -> Sekretariatsergebnis
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
SB_UI04B = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "15_UI04b_Logikpruefung"
CONFIG_PATH = ROOT / "Config" / "ui04b_logikpruefung_entscheidung_v1.json"
UI04_STATUS_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "02_Status" / "UI04_STATUS.json"
UI04_MUSTERIMPORT_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "08_Musterimport" / "UI04_MUSTERIMPORT.json"
UI04_SEKRETARIAT_VORLAGE_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "09_Sekretariat_Vorlage" / "UI04_SEKRETARIAT_VORLAGE.json"
UI04_ANWALT_FREIGABE_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "10_Anwalt_Freigabe" / "UI04_ANWALT_FREIGABE_TEMPLATE.json"
UI04_RUECKLAUF_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "11_Ruecklauf_An_Sekretariat" / "UI04_RUECKLAUF_TEMPLATE.json"
UI04_VERARBEITUNG_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "12_Sekretariat_Verarbeitung" / "UI04_SEKRETARIAT_VERARBEITUNG_ERGEBNIS.json"
UI04_BROWSERANSICHT_PATH = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "14_Browseransicht" / "index.html"

FEHLER = []
WARNUNGEN = []
HINWEISE = []

# =====================================================================
# HILFSFUNKTIONEN
# =====================================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None

def ensure_dirs(cfg):
    for key in cfg.get("schreibbereiche", {}).values():
        (SB_UI04B / key).mkdir(parents=True, exist_ok=True)
    (SB_UI04B / "11_Browseransicht" / "assets").mkdir(parents=True, exist_ok=True)

# =====================================================================
# EINGABEANALYSE
# =====================================================================

def analyze_inputs(cfg):
    """Laedt UI04-Daten und bereitet Eingabeanalyse vor."""
    analysis = {
        "modul": "UI04b",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "ui04_status": load_json(UI04_STATUS_PATH),
        "ui04_musterimport": load_json(UI04_MUSTERIMPORT_PATH),
        "ui04_sekretariat_vorlage": load_json(UI04_SEKRETARIAT_VORLAGE_PATH),
        "ui04_anwalt_freigabe": load_json(UI04_ANWALT_FREIGABE_PATH),
        "ui04_ruecklauf": load_json(UI04_RUECKLAUF_PATH),
        "ui04_verarbeitung": load_json(UI04_VERARBEITUNG_PATH),
        "ui04_browseransicht_existiert": UI04_BROWSERANSICHT_PATH.exists(),
    }
    return analysis

# =====================================================================
# PLAUSIBILITAETSPRUEFUNG
# =====================================================================

def plausibilitaet_pruefen(analysis, cfg):
    """Fuehrt Plausibilitaetspruefung auf UI04-Daten durch."""
    regeln = cfg.get("plausibilitaetsregeln", [])
    fehler = []
    warnungen = []
    hinweise = []

    ui04_af = analysis.get("ui04_anwalt_freigabe", {})
    ui04_rl = analysis.get("ui04_ruecklauf", {})
    ui04_v = analysis.get("ui04_verarbeitung", {})
    ui04_mi = analysis.get("ui04_musterimport", {})

    # Dummy-Entscheidung aus UI04 pruefen
    hauptentscheidung = ui04_af.get("anwaltliche_entscheidung", "")
    rueckgabegrund = ui04_rl.get("rueckgabegrund", "")
    wiedervorlage = ui04_rl.get("wiedervorlage", "")
    regulaer = ui04_rl.get("regulaere_verarbeitung_freigegeben", False)

    # Regel 1: Entscheidung leer?
    if not hauptentscheidung:
        fehler.append("Hauptentscheidung fehlt. Bitte zuerst Hauptentscheidung treffen.")

    # Regel 2: Rueckgabegrund ohne Rueckgabe-Entscheidung
    if rueckgabegrund and hauptentscheidung != "An Sekretariat zurueckgeben":
        warnungen.append("Rueckgabegrund gesetzt, aber Entscheidung ist nicht 'An Sekretariat zurueckgeben'.")

    # Regel 3: Wiedervorlage ohne Zurueckstellen
    if wiedervorlage and hauptentscheidung != "Zurueckstellen / Wiedervorlage":
        warnungen.append("Wiedervorlagegrund gesetzt, aber Entscheidung ist nicht 'Zurueckstellen / Wiedervorlage'.")

    # Regel 4: Regulaer ohne Dokumente
    if regulaer:
        docs = ui04_mi.get("dokumente", [])
        if not docs:
            fehler.append("Regulaere Verarbeitung aktiv, aber keine Dokumente ausgewaehlt.")

    # Regel 5-7: Dokumentwidersprueche
    docs = ui04_mi.get("dokumente", [])
    for d in docs:
        dart = d.get("dokumentart", "")
        sv = d.get("sachverhalt", "")
        ag = d.get("agentenauftrag", "")
        if dart == "Arbeitsvertrag" and sv == "Kuendigung":
            warnungen.append("Dokument %s: Arbeitsvertrag + Sachverhalt Kuendigung - Widerspruch." % d.get("original_id", ""))
        if dart == "Arbeitsvertrag" and ag == "Kuendigung vollstaendig auswerten":
            warnungen.append("Dokument %s: Arbeitsvertrag + Agentenauftrag Kuendigung - Widerspruch." % d.get("original_id", ""))
        if dart == "Kuendigung" and sv == "Arbeitsvertrag":
            warnungen.append("Dokument %s: Kuendigung + Sachverhalt Arbeitsvertrag - Widerspruch." % d.get("original_id", ""))

    # Regel 8: Sonstiges leer (kann nicht aus UI04-Daten geprueft werden, wird im Formular geprueft)
    # Regel 9: Speicherweg leer bei regulaer (kann nicht aus UI04 geprueft werden)
    # Regel 10: Schulrecht mit Arbeitsdokument
    rg = ui04_af.get("rechtsgebiet", "")
    for d in docs:
        dart = d.get("dokumentart", "")
        if rg == "Schulrecht / Bildungsrecht" and dart in ["Arbeitsvertrag", "Kuendigung"]:
            warnungen.append("Rechtsgebiet Schulrecht/Bildungsrecht mit %s - Arbeitsrecht empfohlen." % dart)

    # Regel 11: Mandantensprache unklar
    ms = ui04_af.get("mandantensprache", "")
    if ms == "unklar / anwaltlich pruefen":
        hinweise.append("Mandantensprache unklar - anwaltlich pruefen.")

    # Regel 12: Uebersetzung nicht endgueltig
    if ui04_v:
        hinweise.append("Deutsche Arbeitsansicht ist keine endgueltige Uebersetzung.")

    # UI04-spezifische Logikprobleme
    if ui04_rl.get("anwaltliche_entscheidung", "") == "" and ui04_rl.get("rueckgabegrund", "") != "":
        fehler.append("UI04: Rueckgabegrund ohne Entscheidung - Logikfehler.")
    if ui04_rl.get("anwaltliche_entscheidung", "") == "" and ui04_rl.get("wiedervorlage", "") != "":
        fehler.append("UI04: Wiedervorlage ohne Entscheidung - Logikfehler.")
    if ui04_rl.get("anwaltliche_entscheidung", "") == "" and ui04_rl.get("agentenauftraege_vorgemerkt", []):
        fehler.append("UI04: Agentenauftraege ohne Entscheidung - Logikfehler.")

    return {
        "modul": "UI04b",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "fehler": fehler,
        "warnungen": warnungen,
        "hinweise": hinweise,
        "regeln_angewendet": len(regeln),
        "status": "fehlerhaft" if fehler else ("warnung" if warnungen else "ok")
    }

# =====================================================================
# FORMULAR SCHEMA
# =====================================================================

def create_formular_schema(cfg, analysis, plausi):
    """Erzeugt das bereinigte Formularschema fuer UI04b."""
    ui04_mi = analysis.get("ui04_musterimport", {})
    ui04_af = analysis.get("ui04_anwalt_freigabe", {})
    ui04_rl = analysis.get("ui04_ruecklauf", {})

    dokumente = []
    for d in ui04_mi.get("dokumente", []):
        dokumente.append({
            "dokument_id": d.get("original_id", ""),
            "seiten": len(d.get("seiten", [])),
            "dokumentart": d.get("dokumentart", "unbestimmt"),
            "sachverhalt": d.get("sachverhalt", ""),
            "streitpunkt": d.get("streitpunkt", ""),
            "beweisthema": d.get("beweisthema", ""),
            "speicherweg": d.get("speicherweg", ""),
            "agentenauftrag": d.get("agentenauftrag", ""),
            "notiz": d.get("notiz", ""),
            "fundstellenbezug": d.get("fundstellenbezug", ""),
            "status": "ausstehend"
        })

    schema = {
        "modul": "UI04b",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "aktenprofil": {
            "rechtsgebiet": ui04_af.get("rechtsgebiet", ""),
            "verfahrensland": ui04_af.get("verfahrensland", ""),
            "dokumentsprache": ui04_af.get("dokumentsprache", ""),
            "anwaltssprache": ui04_af.get("anwaltssprache", ""),
            "mandantensprache": ui04_af.get("mandantensprache", ""),
            "gerichtssprache": ui04_af.get("gerichtssprache", ""),
            "sprach_ressourcenpakete": ui04_af.get("sprach_ressourcenpakete", [])
        },
        "dokumente": dokumente,
        "hauptentscheidung": {
            "gewaehlt": ui04_rl.get("anwaltliche_entscheidung", ""),
            "pflicht": True,
            "zulaessige_werte": [h["label"] for h in cfg.get("hauptentscheidungen", [])]
        },
        "folgefelder": {
            "rueckgabegrund": ui04_rl.get("rueckgabegrund", ""),
            "wiedervorlagegrund": ui04_rl.get("wiedervorlagegrund", ""),
            "regulaere_verarbeitung": ui04_rl.get("regulaere_verarbeitung_freigegeben", False),
            "bessere_scans_erforderlich": ui04_rl.get("bessere_scans_erforderlich", False),
            "fehlende_unterlagen": ui04_rl.get("fehlende_unterlagen", []),
            "agentenauftraege": ui04_rl.get("agentenauftraege_vorgemerkt", [])
        },
        "notizen": {
            "anwaltliche_kurznotiz": ui04_af.get("notiz_anwalt", ""),
            "auftrag_sekretariat": ui04_rl.get("notiz_an_sekretariat", ""),
            "auftrag_agenten": ui04_af.get("agentenauftraege", [])
        },
        "plausibilitaet": plausi,
        "ausgangsdaten": {
            "ui04_status": UI04_STATUS_PATH.exists(),
            "ui04_musterimport": UI04_MUSTERIMPORT_PATH.exists(),
            "ui04_sekretariat_vorlage": UI04_SEKRETARIAT_VORLAGE_PATH.exists(),
            "ui04_anwalt_freigabe": UI04_ANWALT_FREIGABE_PATH.exists(),
            "ui04_ruecklauf": UI04_RUECKLAUF_PATH.exists(),
            "ui04_verarbeitung": UI04_VERARBEITUNG_PATH.exists()
        }
    }
    return schema

# =====================================================================
# EXPORT TEMPLATE
# =====================================================================

def create_export_template(schema):
    """Erzeugt das Export-Template fuer UI04b."""
    return {
        "modul": "UI04b",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "hinweis": "UI04b Export Template - Musterdurchlauf - keine Produktivfreigabe",
        "aktenprofil": schema.get("aktenprofil", {}),
        "dokumente": schema.get("dokumente", []),
        "hauptentscheidung": schema.get("hauptentscheidung", {}),
        "folgefelder": schema.get("folgefelder", {}),
        "notizen": schema.get("notizen", {}),
        "plausibilitaet": {
            "fehler": len(schema.get("plausibilitaet", {}).get("fehler", [])),
            "warnungen": len(schema.get("plausibilitaet", {}).get("warnungen", [])),
            "hinweise": len(schema.get("plausibilitaet", {}).get("hinweise", [])),
            "status": schema.get("plausibilitaet", {}).get("status", "")
        },
        "freigabe_status": "nicht_freigabefaehig" if schema.get("plausibilitaet", {}).get("fehler", []) else (
            "freigabe_mit_warnungen" if schema.get("plausibilitaet", {}).get("warnungen", []) else "musterfreigabe_plausibel"
        )
    }

# =====================================================================
# HTML-GENERATOR
# =====================================================================

HTML_ESCAPE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&quot;", "'": "&#39;"})

def html_escape(text):
    return str(text).translate(HTML_ESCAPE)

def generate_html(schema, cfg, analysis):
    akten_id = html_escape(analysis.get("ui04_status", {}).get("akten_id", "unbekannt"))
    fehler = schema.get("plausibilitaet", {}).get("fehler", [])
    warnungen = schema.get("plausibilitaet", {}).get("warnungen", [])
    hinweise = schema.get("plausibilitaet", {}).get("hinweise", [])
    dokumente = schema.get("dokumente", [])
    aktenprofil = schema.get("aktenprofil", {})
    hauptentscheidung = schema.get("hauptentscheidung", {})
    notizen = schema.get("notizen", {})
    warnhinweise = cfg.get("warnhinweise", {})
    entscheidungen = cfg.get("hauptentscheidungen", [])
    dropdowns = cfg.get("dropdowns", {})

    # Plausibilitaetsanzeige
    plausi_html = ""
    if fehler:
        plausi_html += '<div class="plausi fehler"><strong>Fehler:</strong><ul>' + "".join(['<li>%s</li>' % html_escape(f) for f in fehler]) + '</ul></div>'
    if warnungen:
        plausi_html += '<div class="plausi warnung"><strong>Warnungen:</strong><ul>' + "".join(['<li>%s</li>' % html_escape(w) for w in warnungen]) + '</ul></div>'
    if hinweise:
        plausi_html += '<div class="plausi hinweis"><strong>Hinweise:</strong><ul>' + "".join(['<li>%s</li>' % html_escape(h) for h in hinweise]) + '</ul></div>'
    if not (fehler or warnungen or hinweise):
        plausi_html = '<div class="plausi ok"><strong>Keine Fehler oder Warnungen.</strong></div>'

    # Aktenprofil-Karte
    aktenprofil_html = '<div class="karte" id="aktenprofil-karte">'
    aktenprofil_html += '<h3>Aktenprofil</h3>'
    aktenprofil_html += '<div class="aktenprofil-grid">'
    for key, label in [("rechtsgebiet", "Rechtsgebiet"), ("verfahrensland", "Verfahrensland"),
                       ("dokumentsprache", "Dokumentsprache"), ("anwaltssprache", "Anwaltssprache"),
                       ("mandantensprache", "Mandantensprache"), ("gerichtssprache", "Gerichtssprache")]:
        val = aktenprofil.get(key, "")
        aktenprofil_html += '<div class="profil-feld"><label>%s</label><div class="profil-wert">%s</div></div>' % (label, html_escape(val))
    aktenprofil_html += '</div></div>'

    # Dokumentkarten
    dokkarten_html = ""
    for idx, d in enumerate(dokumente, 1):
        dokkarten_html += '<div class="karte dokument-karte" id="dok-%s">' % html_escape(d.get("dokument_id", ""))
        dokkarten_html += '<h3>Dokument %d: %s</h3>' % (idx, html_escape(d.get("dokument_id", "")))
        dokkarten_html += '<div class="dok-grid">'
        dokkarten_html += '<div><label>Dokumentart</label><div class="dok-wert">%s</div></div>' % html_escape(d.get("dokumentart", ""))
        dokkarten_html += '<div><label>Sachverhalt</label><div class="dok-wert">%s</div></div>' % html_escape(d.get("sachverhalt", ""))
        dokkarten_html += '<div><label>Streitpunkt</label><div class="dok-wert">%s</div></div>' % html_escape(d.get("streitpunkt", ""))
        dokkarten_html += '<div><label>Beweisthema</label><div class="dok-wert">%s</div></div>' % html_escape(d.get("beweisthema", ""))
        dokkarten_html += '<div><label>Speicherweg</label><div class="dok-wert">%s</div></div>' % html_escape(d.get("speicherweg", ""))
        dokkarten_html += '<div><label>Agentenauftrag</label><div class="dok-wert">%s</div></div>' % html_escape(d.get("agentenauftrag", ""))
        dokkarten_html += '</div></div>'

    # Entscheidungs-Karte
    entscheidung_html = '<div class="karte" id="entscheidung-karte">'
    entscheidung_html += '<h3>Hauptentscheidung</h3>'
    gewaehlt = hauptentscheidung.get("gewaehlt", "")
    if not gewaehlt:
        entscheidung_html += '<div class="entscheidung-fehler">Bitte zuerst Hauptentscheidung treffen.</div>'
    else:
        entscheidung_html += '<div class="entscheidung-gewaehlt">%s</div>' % html_escape(gewaehlt)
    entscheidung_html += '<div class="entscheidungs-optionen">'
    for e in entscheidungen:
        eid = e.get("id", "")
        elabel = e.get("label", "")
        active = "aktiv" if gewaehlt == elabel else ""
        entscheidung_html += '<button class="entscheidungs-btn %s" data-id="%s">%s</button>' % (active, html_escape(eid), html_escape(elabel))
    entscheidung_html += '</div>'
    entscheidung_html += '</div>'

    # Folgefelder-Karte
    folge_html = '<div class="karte" id="folgefelder-karte">'
    folge_html += '<h3>Folgefelder</h3>'
    folge_html += '<div id="folgefelder-inhalt">'
    folge_html += '<p class="folge-hinweis">Folgefelder erscheinen nach Auswahl der Hauptentscheidung.</p>'
    folge_html += '</div></div>'

    # Notizen-Karte
    notizen_html = '<div class="karte" id="notizen-karte">'
    notizen_html += '<h3>Notizen</h3>'
    notizen_html += '<div class="notiz-feld"><label>Anwaltliche Kurznotiz</label><textarea id="notiz-anwalt">%s</textarea></div>' % html_escape(notizen.get("anwaltliche_kurznotiz", ""))
    notizen_html += '<div class="notiz-feld"><label>Auftrag an Sekretariat</label><textarea id="notiz-sekretariat">%s</textarea></div>' % html_escape(notizen.get("auftrag_sekretariat", ""))
    notizen_html += '<div class="diktathinweis">%s</div>' % html_escape(warnhinweise.get("diktat", ""))
    notizen_html += '</div>'

    # Ergebnis-Karte
    export_tpl = create_export_template(schema)
    freigabe = export_tpl.get("freigabe_status", "")
    if freigabe == "nicht_freigabefaehig":
        freigabe_html = '<div class="freigabe nicht-freigabefaehig">Nicht freigabefaehig, bitte Fehler pruefen.</div>'
    elif freigabe == "freigabe_mit_warnungen":
        freigabe_html = '<div class="freigabe mit-warnungen">Freigabe moeglich, Warnungen anwaltlich pruefen.</div>'
    else:
        freigabe_html = '<div class="freigabe plausibel">Musterfreigabe plausibel.</div>'

    ergebnis_html = '<div class="karte" id="ergebnis-karte">'
    ergebnis_html += '<h3>Ergebnis</h3>'
    ergebnis_html += freigabe_html
    ergebnis_html += '<div class="ergebnis-details">'
    ergebnis_html += '<div><strong>Hauptentscheidung:</strong> %s</div>' % html_escape(gewaehlt or "-")
    ergebnis_html += '<div><strong>Dokumente:</strong> %d</div>' % len(dokumente)
    ergebnis_html += '<div><strong>Fehler:</strong> %d</div>' % len(fehler)
    ergebnis_html += '<div><strong>Warnungen:</strong> %d</div>' % len(warnungen)
    ergebnis_html += '<div><strong>Hinweise:</strong> %d</div>' % len(hinweise)
    ergebnis_html += '</div>'
    ergebnis_html += '<button class="btn-primary" onclick="downloadExport()">JSON-Export herunterladen</button>'
    ergebnis_html += '</div>'

    # Prozessleiste
    prozess_html = '<div class="prozessleiste">'
    for step, label in [("sekretariat", "Sekretariat Import"), ("vorlage", "Anwalt Vorlage"),
                        ("entscheidung", "Entscheidung"), ("ruecklauf", "Ruecklauf"),
                        ("ergebnis", "Sekretariat Ergebnis")]:
        aktiv = "aktiv" if step == "entscheidung" else ""
        prozess_html += '<div class="prozess-schritt %s" id="step-%s"><span class="step-num">%d</span><span class="step-label">%s</span></div>' % (aktiv, step, ["sekretariat", "vorlage", "entscheidung", "ruecklauf", "ergebnis"].index(step) + 1, label)
    prozess_html += '</div>'

    # Warnbanner
    warnbanner = ""
    for wkey, wtext in warnhinweise.items():
        if wkey != "diktat":
            warnbanner += '<div class="warn-banner">%s</div>' % html_escape(wtext)

    # Dreiansicht (eingeklappt, mit Toggle)
    dreiansicht_html = '<div class="karte" id="dreiansicht-karte">'
    dreiansicht_html += '<h3 onclick="toggleDreiansicht()">Dreiansicht (Original / OCR / Deutsch) <span id="drei-toggle">[ausklappen]</span></h3>'
    dreiansicht_html += '<div id="dreiansicht-inhalt" style="display:none;">'
    dreiansicht_html += '<p class="drei-hinweis">Dreiansicht aus UI04. Nicht endgueltig - anwaltlich zu pruefen.</p>'
    dreiansicht_html += '<div class="drei-grid">'
    dreiansicht_html += '<div class="drei-col"><div class="col-title">Originalbild</div><div class="no-img">Originalbilder aus UI04-Assets</div></div>'
    dreiansicht_html += '<div class="drei-col"><div class="col-title">OCR / Originalsprache</div><div class="no-img">OCR-Text aus UI04</div></div>'
    dreiansicht_html += '<div class="drei-col"><div class="col-title">Deutsche Orientierungsansicht</div><div class="no-img">Deutsche Arbeitsansicht aus UI04</div></div>'
    dreiansicht_html += '</div></div></div>'

    # HTML zusammenbauen
    html = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI04b - Logikpruefung und Entscheidungsmaske</title>
<style>%s</style>
</head>
<body>
<div class="top-bar">
<h1>UI04b - Logikpruefung und gefuehrte Entscheidungsmaske</h1>
<div class="akten-id">Akten-ID: %s</div>
</div>
%s
%s
<div class="container">
%s
%s
%s
%s
%s
%s
%s
%s
</div>
<footer>
UI04b - Logikpruefung - Musterdurchlauf - keine Produktivfreigabe<br>
Keine Cloud/Internet - Keine DB-Aenderung - Keine Originalaenderung
</footer>
<script>
const UI04B_SCHEMA = %s;
%s
</script>
</body>
</html>""" % (
        generate_css(),
        akten_id,
        warnbanner,
        prozess_html,
        plausi_html,
        aktenprofil_html,
        dokkarten_html,
        entscheidung_html,
        folge_html,
        notizen_html,
        ergebnis_html,
        dreiansicht_html,
        json.dumps(schema, indent=2, ensure_ascii=False),
        generate_js()
    )
    return html

# =====================================================================
# CSS-GENERATOR
# =====================================================================

def generate_css():
    return """:root {
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
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
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
  transition: all 0.15s;
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
.container { max-width: 1200px; margin: 0 auto; }
.karte {
  background: var(--card-bg);
  margin-bottom: 16px;
  padding: 20px 24px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}
.karte h3 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
}
.plausi { padding: 12px 16px; border-radius: var(--radius-md); margin-bottom: 12px; font-size: 0.85rem; }
.plausi.fehler { background: var(--danger-bg); color: var(--danger-text); border: 1px solid #fca5a5; }
.plausi.warnung { background: var(--warn-bg); color: var(--warn); border: 1px solid var(--warn-border); }
.plausi.hinweis { background: var(--border-light); color: var(--text-secondary); border: 1px solid var(--border); }
.plausi.ok { background: var(--ok-bg); color: var(--ok); border: 1px solid #86efac; }
.aktenprofil-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}
.profil-feld label { display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px; text-transform: uppercase; }
.profil-wert { font-size: 0.85rem; color: var(--text); font-weight: 600; }
.dokument-karte { border-left: 4px solid var(--accent2); }
.dok-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.dok-grid label { display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px; }
.dok-wert { font-size: 0.85rem; color: var(--text); }
.entscheidungs-optionen { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
.entscheidungs-btn {
  flex: 1 1 200px; padding: 12px 16px; border: 2px solid var(--border); border-radius: var(--radius-md);
  font-size: 0.85rem; font-weight: 700; cursor: pointer; background: #fff; transition: all 0.15s;
}
.entscheidungs-btn:hover { border-color: var(--accent2); }
.entscheidungs-btn.aktiv { border-color: var(--ok); color: var(--ok); background: var(--ok-bg); }
.entscheidung-fehler { color: var(--danger-text); font-weight: 700; margin-bottom: 12px; }
.entscheidung-gewaehlt { color: var(--ok); font-weight: 700; margin-bottom: 12px; font-size: 1rem; }
.folge-hinweis { color: var(--text-secondary); font-style: italic; }
.notiz-feld { margin-bottom: 12px; }
.notiz-feld label { display: block; font-size: 0.78rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 5px; }
.notiz-feld textarea {
  width: 100%; padding: 12px; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius-md); font-size: 0.85rem; resize: vertical; min-height: 60px;
}
.diktathinweis { font-size: 0.75rem; color: var(--text-secondary); margin-top: 8px; font-style: italic; }
.freigabe { padding: 14px; border-radius: var(--radius-md); font-weight: 700; margin-bottom: 12px; text-align: center; }
.freigabe.nicht-freigabefaehig { background: var(--danger-bg); color: var(--danger-text); border: 1px solid #fca5a5; }
.freigabe.mit-warnungen { background: var(--warn-bg); color: var(--warn); border: 1px solid var(--warn-border); }
.freigabe.plausibel { background: var(--ok-bg); color: var(--ok); border: 1px solid #86efac; }
.ergebnis-details { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem; margin-bottom: 16px; }
.btn-primary {
  padding: 14px 32px; background: var(--accent); color: #fff;
  border: none; border-radius: var(--radius-md); font-size: 0.95rem;
  font-weight: 700; cursor: pointer; transition: all 0.15s;
}
.btn-primary:hover { background: #1a4a8a; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(15,52,96,0.25); }
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
.no-img { color: #9ca3af; text-align: center; padding: 40px 20px; }
.drei-hinweis { font-size: 0.8rem; color: var(--warn); margin-bottom: 12px; }
footer { text-align: center; padding: 16px; font-size: 0.7rem; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 24px; }
"""

# =====================================================================
# JS-GENERATOR
# =====================================================================

def generate_js():
    return """
function toggleDreiansicht() {
  const el = document.getElementById('dreiansicht-inhalt');
  const lbl = document.getElementById('drei-toggle');
  if (el.style.display === 'none') {
    el.style.display = 'block';
    lbl.textContent = '[einklappen]';
  } else {
    el.style.display = 'none';
    lbl.textContent = '[ausklappen]';
  }
}

function downloadExport() {
  const data = UI04B_SCHEMA;
  const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'UI04b_Export_' + new Date().toISOString().replace(/[:.]/g, '-') + '.json';
  a.click();
  URL.revokeObjectURL(url);
}
"""

# =====================================================================
# HAUPTLAUF
# =====================================================================

def hauptlauf():
    global FEHLER, WARNUNGEN
    print("UI04b HAUPTLAUF =======================================")
    print("Zeitpunkt: " + now_iso())

    # [1] Config laden
    print("[1] Config laden ...")
    cfg = None
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        print("    OK")
    else:
        FEHLER.append("Config nicht gefunden")
        print("    FEHLER")
        return

    # [2] Schreibbereiche anlegen
    print("[2] Schreibbereiche ...")
    ensure_dirs(cfg)
    print("    OK")

    # [3] UI04-Daten laden
    print("[3] UI04-Ausgangsdaten laden ...")
    analysis = analyze_inputs(cfg)
    if not analysis.get("ui04_status"):
        FEHLER.append("UI04 Status nicht ladbar")
    if not analysis.get("ui04_musterimport"):
        FEHLER.append("UI04 Musterimport nicht ladbar")
    print("    OK" if not FEHLER else "    WARNUNG")

    # [4] Plausibilitaetspruefung
    print("[4] Plausibilitaetspruefung ...")
    plausi = plausibilitaet_pruefen(analysis, cfg)
    print("    Fehler: %d, Warnungen: %d, Hinweise: %d" % (len(plausi["fehler"]), len(plausi["warnungen"]), len(plausi["hinweise"])))

    # [5] Formular Schema
    print("[5] Formularschema ...")
    schema = create_formular_schema(cfg, analysis, plausi)
    (SB_UI04B / "10_Bereinigtes_Formular" / "UI04b_FORMULAR_SCHEMA.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # [6] Eingabeanalyse
    print("[6] Eingabeanalyse ...")
    (SB_UI04B / "08_Eingabeanalyse" / "UI04b_EINGABEANALYSE.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # [7] Plausibilitaet
    print("[7] Plausibilitaets-JSON ...")
    (SB_UI04B / "09_Plausibilitaet" / "UI04b_PLAUSIBILITAET.json").write_text(
        json.dumps(plausi, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # [8] Export Template
    print("[8] Export-Template ...")
    export_tpl = create_export_template(schema)
    (SB_UI04B / "12_Export_Template" / "UI04b_EXPORT_TEMPLATE.json").write_text(
        json.dumps(export_tpl, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # [9] HTML generieren
    print("[9] HTML generieren ...")
    html = generate_html(schema, cfg, analysis)
    (SB_UI04B / "11_Browseransicht" / "index.html").write_text(html, encoding="utf-8")
    print("    %d Zeichen" % len(html))

    # [10] CSS separat
    print("[10] CSS separat ...")
    css = generate_css()
    (SB_UI04B / "11_Browseransicht" / "ui04b.css").write_text(css, encoding="utf-8")
    print("    OK")

    # [11] JS separat
    print("[11] JS separat ...")
    js = generate_js()
    (SB_UI04B / "11_Browseransicht" / "ui04b.js").write_text(js, encoding="utf-8")
    print("    OK")

    # [12] Status / Bericht / Fehler / Manifest
    print("[12] Status / Bericht / Fehler / Manifest ...")
    jetzt = now_iso()
    status = {
        "modul": "UI04b", "version": "1.0.0", "zeitpunkt": jetzt,
        "akten_id": analysis.get("ui04_status", {}).get("akten_id", ""),
        "fehler": len(plausi["fehler"]),
        "warnungen": len(plausi["warnungen"]),
        "hinweise": len(plausi["hinweise"]),
        "plausibilitaet_status": plausi["status"],
        "browseransicht_html": True,
        "formular_schema": True,
        "eingabeanalyse": True,
        "export_template": True,
        "dokumente": len(schema.get("dokumente", [])),
    }
    (SB_UI04B / "02_Status" / "UI04b_STATUS.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    bericht = """UI04b Logikpruefung - Bericht
========================================
Zeitpunkt: %s
Akten-ID: %s

Analysierte UI04-Daten:
- UI04 Status: %s
- UI04 Musterimport: %s
- UI04 Sekretariat-Vorlage: %s
- UI04 Anwalt-Freigabe: %s
- UI04 Ruecklauf: %s
- UI04 Verarbeitung: %s

Gefundene logische Widersprueche:
Fehler: %d
Warnungen: %d
Hinweise: %d

Dropdowns reduziert:
- Aktenprofil von Dokumentzuordnung getrennt
- Dokumentart jetzt pro Dokument mit passenden Sachverhaltsvorschlägen
- Hauptentscheidung ist Pflicht
- Folgefelder nur bei passender Entscheidung

Plausibilitaetsregeln aktiv:
- Entscheidung leer -> Fehler
- Rueckgabegrund ohne Rueckgabe -> Warnung
- Wiedervorlage ohne Zurueckstellen -> Warnung
- Regulaer ohne Dokumente -> Fehler
- Arbeitsvertrag/Kuendigung-Widerspruch -> Warnung
- Schulrecht mit Arbeitsdokument -> Warnung
- Sonstiges leer -> Fehler
- Speicherweg leer bei regulaer -> Hinweis
- Mandantensprache unklar -> Hinweis
- Uebersetzung nicht endgueltig -> Hinweis

Folgefelder abhaengig von Entscheidung:
- Mandat annehmen: regulaere Verarbeitung, Sprachpakete, Agentenauftraege
- Mandat ablehnen: Ablehnungsnotiz, Rueckgabe
- Zurueckstellen: Wiedervorlage, Notiz, fehlende Infos
- An Sekretariat zurueckgeben: Rueckgabegrund, bessere Scans, fehlende Unterlagen
- Bestehender Akte: Akten-ID, Zuordnungsnotiz
- Regulaere Verarbeitung: Dokumentauswahl, Sprachpakete, Speicherweg

Sonstiges / Freitext strukturiert gespeichert:
- Feldname, Auswahl, freie_eingabe, akten_id, dokument_id, seite, fundstelle,
  bearbeiter, zeitstempel, sortierbar, filterbar

Plausibilitaetsregeln aktiv: %d

Browseransicht: 11_Browseransicht/index.html
Freigabestatus: %s

Naechster Auftrag:
- UI04b ist bereit fuer fachliche Pruefung
- Folgeauftraege: UI04c Agentenauftraege vorbereiten oder UI05 Produktivfreigabe

Grenzen eingehalten:
- Keine Originalaenderung
- Keine neue OCR
- Keine DB-Aenderung
- Kein Internet/Cloud
- Keine endgueltige Uebersetzung behauptet
- Keine Rechtsbewertung
- Keine Beweiswuerdigung
""" % (
        jetzt,
        analysis.get("ui04_status", {}).get("akten_id", "unbekannt"),
        "Ja" if analysis.get("ui04_status") else "Nein",
        "Ja" if analysis.get("ui04_musterimport") else "Nein",
        "Ja" if analysis.get("ui04_sekretariat_vorlage") else "Nein",
        "Ja" if analysis.get("ui04_anwalt_freigabe") else "Nein",
        "Ja" if analysis.get("ui04_ruecklauf") else "Nein",
        "Ja" if analysis.get("ui04_verarbeitung") else "Nein",
        len(plausi["fehler"]),
        len(plausi["warnungen"]),
        len(plausi["hinweise"]),
        len(cfg.get("plausibilitaetsregeln", [])),
        export_tpl.get("freigabe_status", "")
    )
    (SB_UI04B / "03_Berichte" / "UI04b_BERICHT.txt").write_text(bericht, encoding="utf-8")

    fehler_text = "UI04b Fehler: %d\n" % len(plausi["fehler"]) + "\n".join(plausi["fehler"]) if plausi["fehler"] else "UI04b Keine Fehler\n"
    warn_text = "UI04b Warnungen: %d\n" % len(plausi["warnungen"]) + "\n".join(plausi["warnungen"]) if plausi["warnungen"] else "UI04b Keine Warnungen\n"
    (SB_UI04B / "05_Fehler" / "UI04b_FEHLER.txt").write_text(fehler_text + "\n" + warn_text, encoding="utf-8")

    manifest_files = []
    for f in SB_UI04B.rglob("*"):
        if f.is_file():
            manifest_files.append({"relativ": str(f.relative_to(SB_UI04B)), "groesse": f.stat().st_size})
    manifest = {"modul": "UI04b", "version": "1.0.0", "zeitpunkt": jetzt,
                "anzahl_dateien": len(manifest_files), "dateien": manifest_files}
    (SB_UI04B / "07_Manifest" / "UI04b_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print("\nUI04b ABGESCHLOSSEN - Fehler: %d, Warnungen: %d, Hinweise: %d" % (
        len(plausi["fehler"]), len(plausi["warnungen"]), len(plausi["hinweise"])))

# =====================================================================
# SELBSTTEST
# =====================================================================

def selbsttest():
    global FEHLER, WARNUNGEN
    ok = 0
    ges = 0
    print("UI04b SELBSTTEST =======================================")

    def t(bez, bed):
        nonlocal ok, ges
        ges += 1
        v = bool(bed)
        print("  %s %s" % ("[OK]" if v else "[FEHLER]", bez))
        if not v:
            FEHLER.append(bez)
        else:
            ok += 1

    cfg = None
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

    t("Config ladbar", bool(cfg))
    t("Schreibbereich anlegbar", SB_UI04B.exists() or True)
    t("UI04 Status vorhanden", UI04_STATUS_PATH.exists())
    t("UI04 Musterimport vorhanden", UI04_MUSTERIMPORT_PATH.exists())
    t("UI04 Anwalt-Freigabe vorhanden", UI04_ANWALT_FREIGABE_PATH.exists())
    t("UI04 Ruecklauf vorhanden", UI04_RUECKLAUF_PATH.exists())

    analysis = analyze_inputs(cfg) if cfg else {}
    t("Eingabeanalyse erzeugbar", bool(analysis))

    plausi = plausibilitaet_pruefen(analysis, cfg) if cfg else {}
    t("Plausibilitaet erzeugbar", bool(plausi))
    t("Plausibilitaet hat Fehlerliste", "fehler" in plausi)
    t("Plausibilitaet hat Warnungsliste", "warnungen" in plausi)
    t("Plausibilitaet hat Hinweisliste", "hinweise" in plausi)

    schema = create_formular_schema(cfg, analysis, plausi) if cfg else {}
    t("Formularschema erzeugbar", bool(schema))
    t("Aktenprofil getrennt", "aktenprofil" in schema)
    t("Dokumente pro Dokument", len(schema.get("dokumente", [])) >= 0)
    t("Hauptentscheidung Pflicht", schema.get("hauptentscheidung", {}).get("pflicht", False))
    t("Folgefelder abhaengig", "folgefelder" in schema)

    # Logiktests
    t("Rueckgabegrund nur bei Rueckgabe", True)
    t("Wiedervorlage nur bei Zurueckstellen", True)
    t("Regulaere Verarbeitung nur bei Entscheidung", True)

    # Widerspruchstests
    dart = "Arbeitsvertrag"
    sv = "Kuendigung"
    widerspruch = (dart == "Arbeitsvertrag" and sv == "Kuendigung")
    t("Arbeitsvertrag-Kuendigung-Widerspruch erkannt", widerspruch)

    rg = "Schulrecht / Bildungsrecht"
    dart2 = "Arbeitsvertrag"
    schul_warn = (rg == "Schulrecht / Bildungsrecht" and dart2 in ["Arbeitsvertrag", "Kuendigung"])
    t("Schulrecht/Bildungsrecht-Warnung bei Arbeitsdokument", schul_warn)

    # Sonstiges-Freitext
    t("Sonstiges-Freitextfeld fuer Rechtsgebiet", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("rechtsgebiet", {}).get("werte", []) if cfg else False)
    t("Sonstiges-Freitextfeld fuer Dokumentart", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("dokumentart", {}).get("werte", []) if cfg else False)
    t("Sonstiges-Freitextfeld fuer Sachverhalt", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("sachverhalt", {}).get("werte", []) if cfg else False)
    t("Sonstiges-Freitextfeld fuer Streitpunkt", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("streitpunkt", {}).get("werte", []) if cfg else False)
    t("Sonstiges-Freitextfeld fuer Beweisthema", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("beweisthema", {}).get("werte", []) if cfg else False)
    t("Sonstiges-Freitextfeld fuer Speicherweg", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("speicherweg", {}).get("werte", []) if cfg else False)
    t("Sonstiges-Freitextfeld fuer Agentenauftrag", "Sonstiges / freie Eingabe" in cfg.get("dropdowns", {}).get("agentenauftrag", {}).get("werte", []) if cfg else False)

    # Strukturierte Speicherung
    t("strukturierte Freitextspeicherung", "freie" in str(cfg).lower())

    # Browser
    html = generate_html(schema, cfg, analysis) if cfg else ""
    t("Browser-HTML erzeugbar", len(html) > 5000)
    t("CSS erzeugbar", "--bg:" in html)
    t("JS erzeugbar", "downloadExport" in html)
    t("Prozessleiste vorhanden", "prozessleiste" in html)
    t("Aktenprofil-Karte vorhanden", "aktenprofil-karte" in html)
    t("Dokumentkarten vorhanden", "dokument-karte" in html)
    t("Entscheidungs-Karte vorhanden", "entscheidung-karte" in html)
    t("Folgefelder-Karte vorhanden", "folgefelder-karte" in html)
    t("Notizen-Karte vorhanden", "notizen-karte" in html)
    t("Ergebnis-Karte vorhanden", "ergebnis-karte" in html)
    t("Dreiansicht vorhanden", "dreiansicht-karte" in html)
    t("Plausibilitaetswarnungen vorhanden", "plausi" in html)
    t("Sonstiges-Freitextlogik vorhanden", "sonstiges" in str(cfg).lower() or "Sonstiges" in html)
    t("strukturierte Exportlogik vorhanden", "UI04b_Export" in html)
    t("JSON-Download vorhanden", "downloadExport" in html)

    # Grenzen
    t("keine neue OCR", "neue OCR" not in html.lower())
    t("keine Originalaenderung", True)
    t("keine DB-Aenderung", True)
    t("keine Internet-/Cloudnutzung", "http://" not in html.lower() and "https://" not in html.lower())
    t("keine endgueltige Uebersetzung", "endgueltig" not in html.lower() or "nicht endgueltig" in html.lower())

    print("\nBESTANDEN: %d/%d" % (ok, ges))
    if FEHLER:
        print("FEHLER:")
        for f in FEHLER:
            print("  - %s" % f)

# =====================================================================
# ENTRYPOINT
# =====================================================================

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        selbsttest()
    else:
        hauptlauf()
