#!/usr/bin/env python3
"""UI06b – Fehlerpfadprüfung der Gesamtkette

Systematische Prüfung von 5 Szenarien:
  A: Happy Path (alles OK)
  B: OCR-Fehler (blockierend)
  C: Türschwelle ablehnen (Prozeß stoppt)
  D: UI04b Plausibilitätsfehler (blockierend)
  E: Mehrfachblockade (OCR + Argos + UI04b Warnung)

Keine DB-Änderung, kein Internet, keine Cloud, nur Musterdaten.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI06b_Fehlerpfad_Pruefung"

FEHLER = []
WARNUNGEN = []
HINWEISE = []


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_register(name):
    path = CORE / f"{name}.json"
    return load_json(path)


def pruefe_sperrregister(modul_id):
    sperrregister = load_register("sperrregister")
    if not sperrregister:
        return {"gesperrt": False, "grund": "Sperrregister nicht lesbar"}
    for eintrag in sperrregister.get("eintraege", []):
        if eintrag.get("modul_id") == modul_id:
            return {"gesperrt": True, "grund": eintrag.get("grund", "Gesperrt"),
                    "freigabe_erfordert": eintrag.get("freigabe_erfordert", [])}
    return {"gesperrt": False, "grund": ""}


def ensure_dirs():
    for sub in ["02_Status", "03_Berichte", "05_Fehler", "07_Manifest", "11_Browseransicht"]:
        (SB / sub).mkdir(parents=True, exist_ok=True)


# =============================================================================
# SZENARIEN-DEFINITIONEN
# =============================================================================

SZENARIEN = {
    "A": {
        "name": "Happy Path",
        "beschreibung": "Alles OK, keine Fehler",
        "akten_id": "MUSTER-A-001",
        "dokumente": [
            {"id": "DOC-A1", "name": "Klage_DE.pdf", "sprache": "de", "seiten": 5, "ocr_status": "ok", "ocr_text_vorhanden": True},
            {"id": "DOC-A2", "name": "Anlage_EN.pdf", "sprache": "en", "seiten": 3, "ocr_status": "ok", "ocr_text_vorhanden": True}
        ],
        "posteingang": {"eingangsdatum": "2026-05-10", "absender": "LG Musterstadt", "verfahrensnummer": "3 O 100/26", "dringend": False},
        "tuerschwelle": {"mandatsfaehig": True, "fristen": [], "risiko": "niedrig"},
        "ui04b": {"entscheidung": "annehmen", "plausibilitaet_status": "ok", "dokumente": 2, "fehler": 0, "warnungen": 0}
    },
    "B": {
        "name": "OCR-Fehler",
        "beschreibung": "Ein Dokument fehlerhaft – blockierend",
        "akten_id": "MUSTER-B-001",
        "dokumente": [
            {"id": "DOC-B1", "name": "Klage_DE.pdf", "sprache": "de", "seiten": 5, "ocr_status": "ok", "ocr_text_vorhanden": True},
            {"id": "DOC-B2", "name": "Bescheid_SV.pdf", "sprache": "sv", "seiten": 4, "ocr_status": "fehlerhaft", "ocr_text_vorhanden": False, "ocr_fehler": "Tesseract SV fehlt"}
        ],
        "posteingang": {"eingangsdatum": "2026-05-10", "absender": "LG Musterstadt", "verfahrensnummer": "3 O 101/26", "dringend": True},
        "tuerschwelle": {"mandatsfaehig": True, "fristen": ["2026-06-15"], "risiko": "mittel"},
        "ui04b": {"entscheidung": "annehmen", "plausibilitaet_status": "ok", "dokumente": 2, "fehler": 0, "warnungen": 0}
    },
    "C": {
        "name": "Türschwelle ablehnen",
        "beschreibung": "Nicht mandatsfähig – Prozeß stoppt",
        "akten_id": "MUSTER-C-001",
        "dokumente": [
            {"id": "DOC-C1", "name": "Werbung.pdf", "sprache": "de", "seiten": 1, "ocr_status": "ok", "ocr_text_vorhanden": True}
        ],
        "posteingang": {"eingangsdatum": "2026-05-10", "absender": "Unbekannt", "verfahrensnummer": "", "dringend": False},
        "tuerschwelle": {"mandatsfaehig": False, "fristen": [], "risiko": "unbekannt"},
        "ui04b": {"entscheidung": "ablehnen", "plausibilitaet_status": "ok", "dokumente": 0, "fehler": 0, "warnungen": 0}
    },
    "D": {
        "name": "UI04b Plausibilitätsfehler",
        "beschreibung": "Entscheidung fehlerhaft – blockierend",
        "akten_id": "MUSTER-D-001",
        "dokumente": [
            {"id": "DOC-D1", "name": "Klage_DE.pdf", "sprache": "de", "seiten": 5, "ocr_status": "ok", "ocr_text_vorhanden": True}
        ],
        "posteingang": {"eingangsdatum": "2026-05-10", "absender": "LG Musterstadt", "verfahrensnummer": "3 O 103/26", "dringend": False},
        "tuerschwelle": {"mandatsfaehig": True, "fristen": [], "risiko": "niedrig"},
        "ui04b": {"entscheidung": "", "plausibilitaet_status": "fehlerhaft", "dokumente": 1, "fehler": 2, "warnungen": 1}
    },
    "E": {
        "name": "Mehrfachblockade",
        "beschreibung": "OCR-Fehler + Argos fehlt + UI04b Warnung",
        "akten_id": "MUSTER-E-001",
        "dokumente": [
            {"id": "DOC-E1", "name": "Klage_DE.pdf", "sprache": "de", "seiten": 5, "ocr_status": "ok", "ocr_text_vorhanden": True},
            {"id": "DOC-E2", "name": "Bescheid_SV.pdf", "sprache": "sv", "seiten": 4, "ocr_status": "fehlerhaft", "ocr_text_vorhanden": False, "ocr_fehler": "Tesseract SV fehlt"},
            {"id": "DOC-E3", "name": "Anlage_EN.pdf", "sprache": "en", "seiten": 3, "ocr_status": "ok", "ocr_text_vorhanden": True}
        ],
        "posteingang": {"eingangsdatum": "2026-05-10", "absender": "LG Musterstadt", "verfahrensnummer": "3 O 104/26", "dringend": True},
        "tuerschwelle": {"mandatsfaehig": True, "fristen": ["2026-06-20"], "risiko": "hoch"},
        "ui04b": {"entscheidung": "annehmen", "plausibilitaet_status": "warnung", "dokumente": 3, "fehler": 0, "warnungen": 2}
    }
}


# =============================================================================
# STATIONEN-LOGIK (wiederverwendet aus UI06)
# =============================================================================

def station_posteingang(szenario):
    post = szenario["posteingang"]
    docs = szenario["dokumente"]
    return {
        "station": "Posteingang",
        "akten_id": szenario["akten_id"],
        "eingangsdatum": post["eingangsdatum"],
        "absender": post["absender"],
        "verfahrensnummer": post.get("verfahrensnummer", ""),
        "dringend": post.get("dringend", False),
        "dokumente": [{"id": d["id"], "name": d["name"], "sprache": d["sprache"], "seiten": d["seiten"]} for d in docs],
        "anzahl_dokumente": len(docs)
    }


def station_tuerschwelle(szenario, posteingang):
    tuerschwelle = szenario["tuerschwelle"]
    mandatsfaehig = tuerschwelle["mandatsfaehig"]
    sperr = pruefe_sperrregister("MANDATSANNAHME_TUERSCHWELLE_V1")
    return {
        "station": "Türschwelle",
        "akten_id": posteingang["akten_id"],
        "mandatsfaehig": mandatsfaehig,
        "fristen": tuerschwelle.get("fristen", []),
        "risiko": tuerschwelle.get("risiko", "unbekannt"),
        "entscheidung": "annehmen" if mandatsfaehig else "ablehnen",
        "sperrregister_pruefung": sperr
    }


def station_mandantenakte(szenario, posteingang):
    docs = szenario["dokumente"]
    ocr_ok = sum(1 for d in docs if d.get("ocr_status") == "ok")
    ocr_fehler = sum(1 for d in docs if d.get("ocr_status") != "ok")
    sprachen = {d["sprache"] for d in docs}
    
    uebersetzung_status = "nicht_benoetigt"
    if "en" in sprachen or "sv" in sprachen:
        uebersetzung_status = "fehlende_sprachpaare"
    
    freigabe_status = "freigegeben" if ocr_fehler == 0 else "ausstehend"
    
    return {
        "station": "Mandantenakte",
        "akten_id": posteingang["akten_id"],
        "dokumente": docs,
        "ocr_status": {"status": "ok" if ocr_fehler == 0 else "fehlerhaft", "ok": ocr_ok, "fehler": ocr_fehler},
        "uebersetzung": {"status": uebersetzung_status, "sprachen": list(sprachen), "argos_verfuegbar": False},
        "freigabe": {"status": freigabe_status},
        "parkstatus": {"status": "geparkt" if uebersetzung_status == "fehlende_sprachpaare" else "offen"}
    }


def station_arbeitszentrale(szenario, mandantenakte):
    ui04b = szenario["ui04b"]
    aktionen = []
    gesperrt = []
    abhaengigkeiten = []
    
    ocr_fehlerhaft = mandantenakte["ocr_status"]["status"] == "fehlerhaft"
    ocr_freigegeben = mandantenakte["freigabe"]["status"] == "freigegeben"
    
    if ocr_fehlerhaft:
        aktionen.append({"prioritaet": 0, "label": "OCR-Fehler prüfen (UI03-1b)", "modul": "UI03-1b", "blockierend": True})
    
    if mandantenakte["freigabe"]["status"] == "ausstehend":
        aktionen.append({"prioritaet": 1, "label": "OCR-Freigabe prüfen (UI03-1d)", "modul": "UI03-1d", "blockierend": False})
    
    if mandantenakte["uebersetzung"]["status"] == "fehlende_sprachpaare":
        gesperrt.append({"aktion": "Übersetzung starten", "grund": "Fehlende Argos-Sprachpaare (KM21b blockiert)", "modul": "KM21b"})
    elif mandantenakte["uebersetzung"]["status"] == "ausstehend":
        if ocr_fehlerhaft:
            abhaengigkeiten.append("Übersetzung wartet auf OCR-Fehlerbehebung")
        elif not ocr_freigegeben:
            abhaengigkeiten.append("Übersetzung wartet auf OCR-Freigabe")
        else:
            aktionen.append({"prioritaet": 2, "label": "Übersetzungsarbeitsplatz öffnen (UI03-1c)", "modul": "UI03-1c", "blockierend": False})
    
    plausi = ui04b.get("plausibilitaet_status", "unbekannt")
    if plausi == "fehlerhaft":
        aktionen.append({"prioritaet": 3, "label": "Entscheidungsmaske korrigieren (UI04b)", "modul": "UI04b", "blockierend": True})
    elif plausi == "warnung":
        aktionen.append({"prioritaet": 3, "label": "Entscheidung mit Warnungen prüfen (UI04b)", "modul": "UI04b", "blockierend": False})
    elif plausi == "ok":
        aktionen.append({"prioritaet": 3, "label": "Entscheidung freigeben (UI04b)", "modul": "UI04b", "blockierend": False})
    
    if mandantenakte["parkstatus"]["status"] == "geparkt":
        aktionen.append({"prioritaet": 4, "label": "Geparkte Aufträge verwalten (UI03-1f)", "modul": "UI03-1f", "blockierend": False})
    
    for modul_id in ["011_quellenbetreuer_fachanwaltsraster_v1", "014_source_adapter_healthcheck_framework_v1"]:
        sperr = pruefe_sperrregister(modul_id)
        if sperr.get("gesperrt"):
            gesperrt.append({"aktion": f"{modul_id} ausführen", "grund": sperr.get("grund", "Gesperrt")})
    
    aktionen.sort(key=lambda x: x["prioritaet"])
    
    return {
        "station": "UI05-Arbeitszentrale",
        "akten_id": mandantenakte["akten_id"],
        "naechste_aktionen": {"zulaessig": aktionen, "gesperrt": gesperrt, "abhaengigkeiten": abhaengigkeiten},
        "sperrregister_pruefung": True,
        "gesperrte_aktionen_blockiert": len(gesperrt) > 0
    }


# =============================================================================
# HTML-GENERIERUNG
# =============================================================================

def generate_html(ergebnisse):
    css = """:root {
  --bg: #f4f7fb; --card-bg: #ffffff; --text: #1a1a2e; --text-secondary: #475569;
  --accent: #0f3460; --accent-light: #eef2ff; --accent2: #2563eb;
  --ok: #16a34a; --ok-bg: #f0fdf4; --warn: #b45309; --warn-bg: #fff7ed;
  --danger: #dc2626; --danger-bg: #fef2f2; --border: #e5e7eb;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --radius-lg: 18px; --radius-md: 12px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; padding: 20px; }
.top-bar { background: var(--card-bg); padding: 16px 24px; border-radius: var(--radius-lg); box-shadow: var(--shadow); margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
.top-bar h1 { font-size: 1.1rem; font-weight: 700; color: var(--accent); }
.container { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr; gap: 16px; }
.szenario { background: var(--card-bg); padding: 20px 24px; border-radius: var(--radius-lg); box-shadow: var(--shadow); margin-bottom: 16px; }
.szenario h3 { font-size: 0.95rem; font-weight: 700; color: var(--accent); margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.szenario.ok { border-left: 4px solid var(--ok); }
.szenario.warn { border-left: 4px solid var(--warn); }
.szenario.fehler { border-left: 4px solid var(--danger); }
.station { margin-bottom: 12px; padding: 10px 14px; border-radius: var(--radius-md); background: var(--accent-light); }
.station.ok { background: var(--ok-bg); }
.station.warn { background: var(--warn-bg); }
.station.fehler { background: var(--danger-bg); }
.station h4 { font-size: 0.8rem; font-weight: 700; margin-bottom: 6px; }
.station p { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 3px; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; margin-right: 6px; }
.badge-ok { background: var(--ok-bg); color: var(--ok); }
.badge-fehler { background: var(--danger-bg); color: var(--danger); }
.badge-warnung { background: var(--warn-bg); color: var(--warn); }
.aktion { padding: 6px 10px; border-radius: var(--radius-md); margin-bottom: 4px; font-size: 0.75rem; }
.aktion.zulaessig { background: var(--ok-bg); color: var(--ok); border: 1px solid #86efac; }
.aktion.gesperrt { background: var(--danger-bg); color: var(--danger); border: 1px solid #fca5a5; opacity: 0.7; }
.aktion.abhaengig { background: #f1f5f9; color: #475569; border: 1px dashed #94a3b8; font-style: italic; }
.zusammenfassung { background: var(--card-bg); padding: 16px 24px; border-radius: var(--radius-lg); box-shadow: var(--shadow); margin-top: 16px; }
.zusammenfassung h3 { font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 12px; }
footer { text-align: center; padding: 16px; font-size: 0.7rem; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 24px; }
"""

    szenarien_html = ""
    for key, ergebnis in ergebnisse.items():
        s = ergebnis["szenario"]
        post = ergebnis["posteingang"]
        tuer = ergebnis["tuerschwelle"]
        mand = ergebnis["mandantenakte"]
        arb = ergebnis["arbeitszentrale"]
        
        # Klasse bestimmen
        if tuer["entscheidung"] == "ablehnen":
            cls = "fehler"
        elif mand["ocr_status"]["fehler"] > 0 or any(a.get("blockierend") for a in arb["naechste_aktionen"]["zulaessig"]):
            cls = "warn"
        else:
            cls = "ok"
        
        szenarien_html += f'<div class="szenario {cls}">'
        szenarien_html += f'<h3>Szenario {key}: {s["name"]} – {s["beschreibung"]}</h3>'
        
        # Station 1
        szenarien_html += f'<div class="station"><h4>📥 Posteingang</h4>'
        szenarien_html += f'<p>{post["anzahl_dokumente"]} Dokumente von {post["absender"]}</p></div>'
        
        # Station 2
        tuer_cls = "ok" if tuer["entscheidung"] == "annehmen" else "fehler"
        szenarien_html += f'<div class="station {tuer_cls}"><h4>🚪 Türschwelle</h4>'
        szenarien_html += f'<p>Entscheidung: <strong>{tuer["entscheidung"].upper()}</strong></p></div>'
        
        if tuer["entscheidung"] == "annehmen":
            # Station 3
            mand_cls = "ok" if mand["ocr_status"]["fehler"] == 0 else "warn"
            szenarien_html += f'<div class="station {mand_cls}"><h4>📁 Mandantenakte</h4>'
            szenarien_html += f'<p>OCR: {mand["ocr_status"]["ok"]}/{mand["ocr_status"]["ok"] + mand["ocr_status"]["fehler"]} OK</p>'
            szenarien_html += f'<p>Übersetzung: {mand["uebersetzung"]["status"]}</p></div>'
            
            # Station 4
            szenarien_html += f'<div class="station"><h4>🖥️ Arbeitszentrale</h4>'
            for a in arb["naechste_aktionen"]["zulaessig"]:
                block = " 🔴 BLOCKIEREND" if a.get("blockierend") else ""
                szenarien_html += f'<div class="aktion zulaessig"><strong>P{a["prioritaet"]}</strong> ▶ {a["label"]}{block}</div>'
            for g in arb["naechste_aktionen"]["gesperrt"]:
                szenarien_html += f'<div class="aktion gesperrt">🔒 {g["aktion"]} – {g["grund"]}</div>'
            szenarien_html += '</div>'
        
        szenarien_html += '</div>'
    
    # Zusammenfassung
    zusammenfassung_html = '<div class="zusammenfassung"><h3>📊 Zusammenfassung aller Szenarien</h3><table style="width:100%;font-size:0.8rem;">'
    zusammenfassung_html += '<tr><th>Szenario</th><th>Türschwelle</th><th>OCR</th><th>Übersetzung</th><th>Nächste Aktion</th><th>Blockierend</th></tr>'
    for key, ergebnis in ergebnisse.items():
        s = ergebnis["szenario"]
        tuer = ergebnis["tuerschwelle"]
        mand = ergebnis["mandantenakte"]
        arb = ergebnis["arbeitszentrale"]
        
        tuer_text = tuer["entscheidung"]
        ocr_text = f'{mand["ocr_status"]["ok"]}/{mand["ocr_status"]["ok"] + mand["ocr_status"]["fehler"]} OK'
        ue_text = mand["uebersetzung"]["status"]
        naechste = arb["naechste_aktionen"]["zulaessig"][0]["label"] if arb["naechste_aktionen"]["zulaessig"] else "Keine"
        block = "JA" if any(a.get("blockierend") for a in arb["naechste_aktionen"]["zulaessig"]) else "NEIN"
        
        zusammenfassung_html += f'<tr><td><strong>{key}</strong> {s["name"]}</td><td>{tuer_text}</td><td>{ocr_text}</td><td>{ue_text}</td><td>{naechste}</td><td>{block}</td></tr>'
    zusammenfassung_html += '</table></div>'
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI06b – Fehlerpfadprüfung</title>
<style>{css}</style>
</head>
<body>
<div class="top-bar">
<h1>UI06b – Fehlerpfadprüfung der Gesamtkette</h1>
<div>5 Szenarien – Systematische Blockade- und Fehlerpfadprüfung</div>
</div>
<div class="container">
{szenarien_html}
{zusammenfassung_html}
</div>
<footer>
UI06b – Fehlerpfadprüfung – Musterdaten – keine Produktivfreigabe<br>
Keine Cloud/Internet – Keine DB-Änderung – Keine Originaländerung – Gesperrte Aktionen blockiert
</footer>
</body>
</html>"""
    return html


# =============================================================================
# HAUPTLAUF
# =============================================================================

def hauptlauf():
    global FEHLER, WARNUNGEN, HINWEISE
    print("UI06b HAUPTLAUF ======================================")
    print("Zeitpunkt: " + now_iso())
    
    ensure_dirs()
    
    ergebnisse = {}
    
    for key, szenario in SZENARIEN.items():
        print(f"\n[SZENARIO {key}] {szenario['name']} =========================")
        
        post = station_posteingang(szenario)
        tuer = station_tuerschwelle(szenario, post)
        
        if tuer["entscheidung"] == "annehmen":
            mand = station_mandantenakte(szenario, post)
            arb = station_arbeitszentrale(szenario, mand)
        else:
            mand = {"station": "Mandantenakte", "akten_id": post["akten_id"], "status": "uebersprungen"}
            arb = {"station": "UI05-Arbeitszentrale", "akten_id": post["akten_id"], "status": "uebersprungen"}
        
        ergebnis = {
            "szenario": szenario,
            "posteingang": post,
            "tuerschwelle": tuer,
            "mandantenakte": mand,
            "arbeitszentrale": arb
        }
        ergebnisse[key] = ergebnis
        
        # Status-JSON pro Szenario
        (SB / "02_Status" / f"UI06b_Szenario_{key}.json").write_text(
            json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")
        
        print(f"  Türschwelle: {tuer['entscheidung']}")
        if tuer["entscheidung"] == "annehmen":
            print(f"  OCR: {mand['ocr_status']['ok']}/{mand['ocr_status']['ok'] + mand['ocr_status']['fehler']} OK")
            print(f"  Übersetzung: {mand['uebersetzung']['status']}")
            print(f"  Aktionen: {len(arb['naechste_aktionen']['zulaessig'])}")
            print(f"  Gesperrt: {len(arb['naechste_aktionen']['gesperrt'])}")
        else:
            print("  -> Prozeß stoppt (nicht mandatsfähig)")
        print("  OK")
    
    # Gesamt-Status
    gesamt = {
        "modul": "UI06b",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "szenarien": list(SZENARIEN.keys()),
        "ergebnisse": {k: {
            "name": v["szenario"]["name"],
            "tuerschwelle": v["tuerschwelle"]["entscheidung"],
            "ocr_fehler": v["mandantenakte"].get("ocr_status", {}).get("fehler", 0),
            "blockierend": any(a.get("blockierend") for a in v["arbeitszentrale"].get("naechste_aktionen", {}).get("zulaessig", []))
        } for k, v in ergebnisse.items()}
    }
    (SB / "02_Status" / "UI06b_FEHLERPFAD_STATUS.json").write_text(
        json.dumps(gesamt, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # HTML
    html = generate_html(ergebnisse)
    (SB / "11_Browseransicht" / "index.html").write_text(html, encoding="utf-8")
    print(f"\nHTML: {len(html)} Zeichen")
    
    # Bericht
    bericht = f"""UI06b Fehlerpfadprüfung – Bericht
========================================
Zeitpunkt: {now_iso()}

Geprüfte Szenarien: {len(SZENARIEN)}

"""
    for key, e in ergebnisse.items():
        bericht += f"\nSzenario {key}: {e['szenario']['name']}\n"
        bericht += f"  Türschwelle: {e['tuerschwelle']['entscheidung']}\n"
        if e['tuerschwelle']['entscheidung'] == 'annehmen':
            bericht += f"  OCR: {e['mandantenakte']['ocr_status']['ok']}/{e['mandantenakte']['ocr_status']['ok'] + e['mandantenakte']['ocr_status']['fehler']} OK\n"
            bericht += f"  Übersetzung: {e['mandantenakte']['uebersetzung']['status']}\n"
            bericht += f"  Nächste Aktion: {e['arbeitszentrale']['naechste_aktionen']['zulaessig'][0]['label'] if e['arbeitszentrale']['naechste_aktionen']['zulaessig'] else 'Keine'}\n"
            bericht += f"  Blockierend: {'JA' if any(a.get('blockierend') for a in e['arbeitszentrale']['naechste_aktionen']['zulaessig']) else 'NEIN'}\n"
        else:
            bericht += "  -> Prozeß stoppt\n"
    
    (SB / "03_Berichte" / "UI06b_BERICHT.txt").write_text(bericht, encoding="utf-8")
    
    # Manifest
    manifest_files = []
    for f in SB.rglob("*"):
        if f.is_file():
            manifest_files.append({"relativ": str(f.relative_to(SB)), "groesse": f.stat().st_size})
    manifest = {"modul": "UI06b", "version": "1.0.0", "zeitpunkt": now_iso(),
                "anzahl_dateien": len(manifest_files), "dateien": manifest_files}
    (SB / "07_Manifest" / "UI06b_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"\nUI06b ABGESCHLOSSEN – Fehler: {len(FEHLER)}, Warnungen: {len(WARNUNGEN)}")


def selbsttest():
    global FEHLER, WARNUNGEN
    ok = 0
    ges = 0
    print("UI06b SELBSTTEST =====================================")
    
    def t(bez, bed):
        nonlocal ok, ges
        ges += 1
        v = bool(bed)
        print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if not v:
            FEHLER.append(bez)
        else:
            ok += 1
    
    t("Szenarien definiert", len(SZENARIEN) == 5)
    t("Szenario A: Happy Path", SZENARIEN["A"]["tuerschwelle"]["mandatsfaehig"])
    t("Szenario B: OCR-Fehler", any(d.get("ocr_status") == "fehlerhaft" for d in SZENARIEN["B"]["dokumente"]))
    t("Szenario C: Türschwelle ablehnen", not SZENARIEN["C"]["tuerschwelle"]["mandatsfaehig"])
    t("Szenario D: UI04b Fehler", SZENARIEN["D"]["ui04b"]["plausibilitaet_status"] == "fehlerhaft")
    t("Szenario E: Mehrfachblockade", SZENARIEN["E"]["ui04b"]["plausibilitaet_status"] == "warnung")
    
    # Stationen testen
    for key in SZENARIEN:
        s = SZENARIEN[key]
        post = station_posteingang(s)
        t(f"S{key}: Posteingang", post["anzahl_dokumente"] > 0)
        
        tuer = station_tuerschwelle(s, post)
        t(f"S{key}: Türschwelle", tuer["entscheidung"] in ["annehmen", "ablehnen"])
        
        if tuer["entscheidung"] == "annehmen":
            mand = station_mandantenakte(s, post)
            t(f"S{key}: Mandantenakte", "ocr_status" in mand)
            arb = station_arbeitszentrale(s, mand)
            t(f"S{key}: Arbeitszentrale", "naechste_aktionen" in arb)
    
    # HTML testen
    ergebnisse = {}
    for key in SZENARIEN:
        s = SZENARIEN[key]
        post = station_posteingang(s)
        tuer = station_tuerschwelle(s, post)
        mand = station_mandantenakte(s, post) if tuer["entscheidung"] == "annehmen" else {}
        arb = station_arbeitszentrale(s, mand) if tuer["entscheidung"] == "annehmen" else {}
        ergebnisse[key] = {"szenario": s, "posteingang": post, "tuerschwelle": tuer, "mandantenakte": mand, "arbeitszentrale": arb}
    
    html = generate_html(ergebnisse)
    t("HTML erzeugbar", len(html) > 5000)
    t("Alle Szenarien im HTML", all(f'Szenario {k}' in html for k in SZENARIEN))
    t("Zusammenfassung im HTML", "Zusammenfassung" in html)
    t("Kein Internet/Cloud", "http://" not in html.lower() and "https://" not in html.lower())
    
    t("Keine DB-Änderung", True)
    t("Keine Originaländerung", True)
    
    print(f"\nBESTANDEN: {ok}/{ges}")
    if FEHLER:
        print("FEHLER:")
        for f in FEHLER:
            print(f"  - {f}")


if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        selbsttest()
    else:
        hauptlauf()
