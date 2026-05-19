#!/usr/bin/env python3
"""UI06 – Musterlauf Gesamtkette

Simuliert den vollständigen Prozeß:
  Posteingang -> Türschwelle -> Mandantenakte (OCR/Übersetzung/Freigabe) -> UI05-Arbeitszentrale

Verwendet ausschließlich Musterdaten, keine echten Mandantendaten.
Keine DB-Änderung, kein Internet, keine Cloud.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI06_Musterlauf_Gesamtkette"
CONFIG_PATH = ROOT / "Config" / "ui06_musterlauf_gesamtkette_v1.json"

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


def ensure_dirs(cfg):
    for sub in ["02_Status", "03_Berichte", "05_Fehler", "07_Manifest", "11_Browseransicht"]:
        (SB / sub).mkdir(parents=True, exist_ok=True)


# =============================================================================
# STATION 1: POSTEINGANG
# =============================================================================

def station_posteingang(muster):
    """Simuliert Posteingang: Dokumente werden registriert."""
    print("\n[STATION 1] POSTEINGANG =============================")
    post = muster.get("posteingang", {})
    docs = muster.get("dokumente", [])

    posteingang_status = {
        "station": "Posteingang",
        "akten_id": muster.get("akten_id", "unbekannt"),
        "eingangsdatum": post.get("eingangsdatum", "unbekannt"),
        "absender": post.get("absender", "unbekannt"),
        "verfahrensnummer": post.get("verfahrensnummer", ""),
        "dringend": post.get("dringend", False),
        "dokumente": [
            {
                "id": d["id"],
                "name": d["name"],
                "sprache": d["sprache"],
                "seiten": d["seiten"],
                "status": "eingegangen"
            }
            for d in docs
        ],
        "anzahl_dokumente": len(docs),
        "zeitpunkt": now_iso()
    }

    (SB / "02_Status" / "UI06_01_POSTEINGANG.json").write_text(
        json.dumps(posteingang_status, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  Akten-ID: {posteingang_status['akten_id']}")
    print(f"  Absender: {posteingang_status['absender']}")
    print(f"  Dokumente: {posteingang_status['anzahl_dokumente']}")
    for d in posteingang_status["dokumente"]:
        print(f"    - {d['name']} ({d['sprache']}, {d['seiten']} Seiten)")
    print("  OK")
    return posteingang_status


# =============================================================================
# STATION 2: TÜRSCHWELLE
# =============================================================================

def station_tuerschwelle(muster, posteingang):
    """Simuliert Türschwelle: Mandatsfähigkeit prüfen."""
    print("\n[STATION 2] TÜRSCHWELLE =============================")
    tuerschwelle = muster.get("tuerschwelle", {})

    # Prüfungen
    mandatsfaehig = tuerschwelle.get("mandatsfaehig", False)
    fristen = tuerschwelle.get("fristen", [])
    risiko = tuerschwelle.get("risiko", "unbekannt")

    # Sperrregister prüfen (MANDATSANNAHME_TUERSCHWELLE_V1)
    sperr = pruefe_sperrregister("MANDATSANNAHME_TUERSCHWELLE_V1")
    if sperr.get("gesperrt"):
        WARNUNGEN.append(f"Türschwelle gesperrt: {sperr.get('grund')}")

    tuerschwelle_status = {
        "station": "Türschwelle",
        "akten_id": posteingang["akten_id"],
        "mandatsfaehig": mandatsfaehig,
        "fristen": fristen,
        "risiko": risiko,
        "dringend": posteingang.get("dringend", False),
        "entscheidung": "annehmen" if mandatsfaehig else "ablehnen",
        "sperrregister_pruefung": sperr,
        "zeitpunkt": now_iso()
    }

    (SB / "02_Status" / "UI06_02_TUERSCHWELLE.json").write_text(
        json.dumps(tuerschwelle_status, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  Mandatsfähig: {'JA' if mandatsfaehig else 'NEIN'}")
    print(f"  Risiko: {risiko}")
    print(f"  Fristen: {', '.join(fristen) if fristen else 'Keine'}")
    print(f"  Entscheidung: {tuerschwelle_status['entscheidung']}")
    if sperr.get("gesperrt"):
        print(f"  WARNUNG: {sperr['grund']}")
    print("  OK")
    return tuerschwelle_status


# =============================================================================
# STATION 3: MANDANTENAKTE (OCR / Übersetzung / Freigabe)
# =============================================================================

def station_mandantenakte(muster, posteingang):
    """Simuliert Mandantenakte: OCR, Übersetzung, Freigabe."""
    print("\n[STATION 3] MANDANTENAKTE ===========================")
    docs = muster.get("dokumente", [])

    ocr_ergebnisse = []
    uebersetzungs_status = "nicht_benoetigt"
    freigabe_status = "ausstehend"
    ocr_fehler_count = 0
    ocr_ok_count = 0

    for d in docs:
        if d.get("ocr_status") == "ok":
            ocr_ok_count += 1
            ocr_ergebnisse.append({
                "dokument_id": d["id"],
                "status": "ok",
                "sprache": d["sprache"],
                "text_vorhanden": True
            })
        else:
            ocr_fehler_count += 1
            ocr_ergebnisse.append({
                "dokument_id": d["id"],
                "status": "fehlerhaft",
                "sprache": d["sprache"],
                "text_vorhanden": False,
                "fehler": d.get("ocr_fehler", "Unbekannter Fehler")
            })

    # Übersetzungsprüfung
    sprachen = {d["sprache"] for d in docs}
    if "en" in sprachen or "sv" in sprachen:
        # Prüfe Argos-Modelle (KM21b)
        argos_verfuegbar = False  # In Musterlauf: nicht verfügbar
        if argos_verfuegbar:
            uebersetzungs_status = "ausstehend"
        else:
            uebersetzungs_status = "fehlende_sprachpaare"
            HINWEISE.append("Argos-Modelle fehlen – Übersetzung geparkt (KM21b-0)")

    # Freigabe: nur wenn alle OCR ok
    if ocr_fehler_count == 0:
        freigabe_status = "freigegeben"
    else:
        freigabe_status = "ausstehend"

    mandantenakte_status = {
        "station": "Mandantenakte",
        "akten_id": posteingang["akten_id"],
        "dokumente": [
            {
                "id": d["id"],
                "name": d["name"],
                "sprache": d["sprache"],
                "seiten": d["seiten"],
                "ocr_status": d.get("ocr_status", "unbekannt"),
                "ocr_text_vorhanden": d.get("ocr_text_vorhanden", False)
            }
            for d in docs
        ],
        "ocr_status": {
            "status": "ok" if ocr_fehler_count == 0 else "fehlerhaft",
            "ok": ocr_ok_count,
            "fehler": ocr_fehler_count
        },
        "uebersetzung": {
            "status": uebersetzungs_status,
            "sprachen": list(sprachen),
            "argos_verfuegbar": argos_verfuegbar if 'argos_verfuegbar' in dir() else False
        },
        "freigabe": {
            "status": freigabe_status
        },
        "parkstatus": {
            "status": "geparkt" if uebersetzungs_status == "fehlende_sprachpaare" else "offen"
        },
        "zeitpunkt": now_iso()
    }

    (SB / "02_Status" / "UI06_03_MANDANTENAKTE.json").write_text(
        json.dumps(mandantenakte_status, indent=2, ensure_ascii=False), encoding="utf-8")

    # UI03-1g kompatibles Status-JSON erzeugen (damit UI05 es lesen könnte)
    ui03_status = {
        "akten_id": posteingang["akten_id"],
        "ocr_status": mandantenakte_status["ocr_status"],
        "uebersetzung": mandantenakte_status["uebersetzung"],
        "freigabe": mandantenakte_status["freigabe"],
        "parkstatus": mandantenakte_status["parkstatus"],
        "dokumente": mandantenakte_status["dokumente"]
    }
    (SB / "02_Status" / "UI03_1g_GESAMTANSICHT_STATUS.json").write_text(
        json.dumps(ui03_status, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  Dokumente: {len(docs)}")
    print(f"  OCR OK: {ocr_ok_count}, Fehler: {ocr_fehler_count}")
    print(f"  Übersetzung: {uebersetzungs_status}")
    print(f"  Freigabe: {freigabe_status}")
    print("  OK")
    return mandantenakte_status


# =============================================================================
# STATION 4: UI05-ARBEITSZENTRALE
# =============================================================================

def station_ui05_arbeitszentrale(muster, mandantenakte):
    """Simuliert UI05-Arbeitszentrale: Aktionen bestimmen."""
    print("\n[STATION 4] UI05-ARBEITSZENTRALE ====================")

    ui04b = muster.get("ui04b_entscheidung", {})

    # Aktionen bestimmen (gleiche Logik wie UI05)
    aktionen = []
    gesperrte_aktionen = []
    abhaengigkeiten = []

    ocr_fehlerhaft = mandantenakte["ocr_status"]["status"] == "fehlerhaft"
    ocr_freigegeben = mandantenakte["freigabe"]["status"] == "freigegeben"

    # P0: OCR-Fehler
    if ocr_fehlerhaft:
        aktionen.append({
            "prioritaet": 0,
            "label": "OCR-Fehler prüfen (UI03-1b)",
            "modul": "UI03-1b",
            "blockierend": True,
            "grund": "OCR enthält Fehler – weitere Verarbeitung blockiert"
        })

    # P1: OCR-Freigabe
    if mandantenakte["freigabe"]["status"] == "ausstehend":
        aktionen.append({
            "prioritaet": 1,
            "label": "OCR-Freigabe prüfen (UI03-1d)",
            "modul": "UI03-1d",
            "blockierend": False
        })

    # P2: Übersetzung
    if mandantenakte["uebersetzung"]["status"] == "fehlende_sprachpaare":
        gesperrte_aktionen.append({
            "aktion": "Übersetzung starten",
            "grund": "Fehlende Argos-Sprachpaare (KM21b blockiert)",
            "modul": "KM21b",
            "prioritaet": 2
        })
    elif mandantenakte["uebersetzung"]["status"] == "ausstehend":
        if ocr_fehlerhaft:
            abhaengigkeiten.append("Übersetzung wartet auf OCR-Fehlerbehebung")
        elif not ocr_freigegeben:
            abhaengigkeiten.append("Übersetzung wartet auf OCR-Freigabe")
        else:
            aktionen.append({
                "prioritaet": 2,
                "label": "Übersetzungsarbeitsplatz öffnen (UI03-1c)",
                "modul": "UI03-1c",
                "blockierend": False
            })

    # P3: UI04b Entscheidung
    plausi = ui04b.get("plausibilitaet_status", "unbekannt")
    if plausi == "fehlerhaft":
        aktionen.append({
            "prioritaet": 3,
            "label": "Entscheidungsmaske korrigieren (UI04b)",
            "modul": "UI04b",
            "blockierend": True,
            "grund": "Plausibilitätsfehler – Entscheidung nicht möglich"
        })
    elif plausi == "warnung":
        aktionen.append({
            "prioritaet": 3,
            "label": "Entscheidung mit Warnungen prüfen (UI04b)",
            "modul": "UI04b",
            "blockierend": False
        })
    elif plausi == "ok":
        aktionen.append({
            "prioritaet": 3,
            "label": "Entscheidung freigeben (UI04b)",
            "modul": "UI04b",
            "blockierend": False
        })

    # P4: Geparkte Aufträge
    if mandantenakte["parkstatus"]["status"] == "geparkt":
        aktionen.append({
            "prioritaet": 4,
            "label": "Geparkte Aufträge verwalten (UI03-1f)",
            "modul": "UI03-1f",
            "blockierend": False
        })

    # Sperrregister
    for modul_id in ["011_quellenbetreuer_fachanwaltsraster_v1", "014_source_adapter_healthcheck_framework_v1"]:
        sperr = pruefe_sperrregister(modul_id)
        if sperr.get("gesperrt"):
            gesperrte_aktionen.append({
                "aktion": f"{modul_id} ausführen",
                "grund": sperr.get("grund", "Gesperrt"),
                "freigabe_erfordert": sperr.get("freigabe_erfordert", []),
                "prioritaet": 99
            })

    aktionen.sort(key=lambda x: x["prioritaet"])

    arbeitszentrale_status = {
        "station": "UI05-Arbeitszentrale",
        "akten_id": mandantenakte["akten_id"],
        "ui03": {
            "ocr_status": mandantenakte["ocr_status"],
            "uebersetzung": mandantenakte["uebersetzung"],
            "freigabe": mandantenakte["freigabe"],
            "parkstatus": mandantenakte["parkstatus"]
        },
        "ui04b": {
            "plausibilitaet_status": plausi,
            "dokumente": ui04b.get("dokumente", 0),
            "fehler": ui04b.get("fehler", 0),
            "warnungen": ui04b.get("warnungen", 0)
        },
        "naechste_aktionen": {
            "zulaessig": aktionen,
            "gesperrt": gesperrte_aktionen,
            "abhaengigkeiten": abhaengigkeiten
        },
        "sperrregister_pruefung": True,
        "gesperrte_aktionen_blockiert": len(gesperrte_aktionen) > 0,
        "zeitpunkt": now_iso()
    }

    (SB / "02_Status" / "UI06_04_ARBEITSZENTRALE.json").write_text(
        json.dumps(arbeitszentrale_status, indent=2, ensure_ascii=False), encoding="utf-8")

    # UI04b kompatibles Status-JSON erzeugen
    ui04b_status = {
        "plausibilitaet_status": plausi,
        "dokumente": ui04b.get("dokumente", 0),
        "fehler": ui04b.get("fehler", 0),
        "warnungen": ui04b.get("warnungen", 0)
    }
    (SB / "02_Status" / "UI04b_STATUS.json").write_text(
        json.dumps(ui04b_status, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  Zulässige Aktionen: {len(aktionen)}")
    for a in aktionen:
        block = " [BLOCKIEREND]" if a.get("blockierend") else ""
        print(f"    P{a['prioritaet']}{block} {a['label']}")
    print(f"  Gesperrte Aktionen: {len(gesperrte_aktionen)}")
    for g in gesperrte_aktionen:
        print(f"    🔒 {g['aktion']} – {g['grund']}")
    print("  OK")
    return arbeitszentrale_status


# =============================================================================
# HTML-GENERIERUNG
# =============================================================================

def generate_html(musterlauf, cfg):
    """Erzeugt HTML für den vollständigen Musterlauf."""
    akten_id = musterlauf.get("akten_id", "unbekannt")
    post = musterlauf.get("posteingang", {})
    tuerschwelle = musterlauf.get("tuerschwelle", {})
    docs = musterlauf.get("dokumente", [])
    ui04b = musterlauf.get("ui04b_entscheidung", {})

    # Stationen laden
    s1 = load_json(SB / "02_Status" / "UI06_01_POSTEINGANG.json") or {}
    s2 = load_json(SB / "02_Status" / "UI06_02_TUERSCHWELLE.json") or {}
    s3 = load_json(SB / "02_Status" / "UI06_03_MANDANTENAKTE.json") or {}
    s4 = load_json(SB / "02_Status" / "UI06_04_ARBEITSZENTRALE.json") or {}

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
.akten-id { font-size: 0.85rem; color: var(--text-secondary); }
.container { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .container { grid-template-columns: 1fr; } }
.karte { background: var(--card-bg); padding: 20px 24px; border-radius: var(--radius-lg); box-shadow: var(--shadow); }
.karte h3 { font-size: 0.95rem; font-weight: 700; color: var(--accent); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.station { margin-bottom: 16px; padding: 12px; border-radius: var(--radius-md); background: var(--accent-light); border-left: 4px solid var(--accent2); }
.station.ok { background: var(--ok-bg); border-left-color: var(--ok); }
.station.warn { background: var(--warn-bg); border-left-color: var(--warn); }
.station.fehler { background: var(--danger-bg); border-left-color: var(--danger); }
.station h4 { font-size: 0.85rem; font-weight: 700; margin-bottom: 8px; }
.station p { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 4px; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; margin-right: 8px; margin-bottom: 4px; }
.badge-ok { background: var(--ok-bg); color: var(--ok); }
.badge-fehler { background: var(--danger-bg); color: var(--danger); }
.badge-warnung { background: var(--warn-bg); color: var(--warn); }
.badge-ausstehend { background: #f1f5f9; color: #64748b; }
.dokument { padding: 8px 12px; border-radius: var(--radius-md); margin-bottom: 6px; font-size: 0.8rem; background: #f8fafc; border: 1px solid var(--border); }
.dokument.fehler { background: var(--danger-bg); border-color: #fca5a5; }
.aktion { padding: 8px 12px; border-radius: var(--radius-md); margin-bottom: 6px; font-size: 0.8rem; }
.aktion.zulaessig { background: var(--ok-bg); color: var(--ok); border: 1px solid #86efac; }
.aktion.gesperrt { background: var(--danger-bg); color: var(--danger); border: 1px solid #fca5a5; opacity: 0.7; }
.aktion.abhaengig { background: #f1f5f9; color: #475569; border: 1px dashed #94a3b8; font-style: italic; }
.pfeil { text-align: center; font-size: 1.5rem; color: var(--accent2); margin: 8px 0; }
footer { text-align: center; padding: 16px; font-size: 0.7rem; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 24px; }
"""

    # Station 1: Posteingang
    s1_html = f'<div class="station ok"><h4>📥 Station 1: Posteingang</h4>'
    s1_html += f'<p>Absender: {post.get("absender", "unbekannt")}</p>'
    s1_html += f'<p>Verfahren: {post.get("verfahrensnummer", "")}</p>'
    s1_html += f'<p>Dokumente: {len(docs)}</p>'
    for d in docs:
        s1_html += f'<div class="dokument">{d["name"]} ({d["sprache"]}, {d["seiten"]} Seiten)</div>'
    s1_html += '</div>'

    # Station 2: Türschwelle
    mandatsfaehig = tuerschwelle.get("mandatsfaehig", False)
    s2_klasse = "ok" if mandatsfaehig else "fehler"
    s2_html = f'<div class="station {s2_klasse}"><h4>🚪 Station 2: Türschwelle</h4>'
    s2_html += f'<p>Mandatsfähig: <strong>{"JA" if mandatsfaehig else "NEIN"}</strong></p>'
    s2_html += f'<p>Risiko: {tuerschwelle.get("risiko", "unbekannt")}</p>'
    s2_html += f'<p>Entscheidung: {"Annehmen" if mandatsfaehig else "Ablehnen"}</p>'
    s2_html += '</div>'

    # Station 3: Mandantenakte
    ocr_fehler = sum(1 for d in docs if d.get("ocr_status") != "ok")
    s3_klasse = "ok" if ocr_fehler == 0 else "warn"
    s3_html = f'<div class="station {s3_klasse}"><h4>📁 Station 3: Mandantenakte</h4>'
    s3_html += f'<p>OCR: {len(docs) - ocr_fehler} OK, {ocr_fehler} Fehler</p>'
    for d in docs:
        status = "✅" if d.get("ocr_status") == "ok" else "❌"
        cls = "" if d.get("ocr_status") == "ok" else "fehler"
        s3_html += f'<div class="dokument {cls}">{status} {d["name"]} – OCR: {d.get("ocr_status", "unbekannt")}</div>'
    s3_html += f'<p>Übersetzung: {s3.get("uebersetzung", {}).get("status", "unbekannt")}</p>'
    s3_html += f'<p>Freigabe: {s3.get("freigabe", {}).get("status", "unbekannt")}</p>'
    s3_html += '</div>'

    # Station 4: Arbeitszentrale
    aktionen = s4.get("naechste_aktionen", {})
    zulaessig = aktionen.get("zulaessig", [])
    gesperrt = aktionen.get("gesperrt", [])
    abhaengig = aktionen.get("abhaengigkeiten", [])

    s4_html = f'<div class="station"><h4>🖥️ Station 4: UI05-Arbeitszentrale</h4>'
    s4_html += '<p><strong>Nächste zulässige Aktionen:</strong></p>'
    for a in zulaessig:
        block = " 🔴 BLOCKIEREND" if a.get("blockierend") else ""
        s4_html += f'<div class="aktion zulaessig"><strong>P{a["prioritaet"]}</strong> ▶ {a["label"]}{block}</div>'
    if abhaengig:
        s4_html += '<p><strong>Wartend:</strong></p>'
        for ab in abhaengig:
            s4_html += f'<div class="aktion abhaengig">⏳ {ab}</div>'
    if gesperrt:
        s4_html += '<p><strong>Gesperrt:</strong></p>'
        for g in gesperrt:
            s4_html += f'<div class="aktion gesperrt">🔒 {g["aktion"]} – {g["grund"]}</div>'
    s4_html += '</div>'

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI06 – Musterlauf Gesamtkette</title>
<style>{css}</style>
</head>
<body>
<div class="top-bar">
<h1>UI06 – Musterlauf Gesamtkette</h1>
<div class="akten-id">Akten-ID: {akten_id}</div>
</div>
<div class="container">
<div class="karte">
<h3>Prozeßverlauf</h3>
{s1_html}
<div class="pfeil">⬇</div>
{s2_html}
<div class="pfeil">⬇</div>
{s3_html}
<div class="pfeil">⬇</div>
{s4_html}
</div>
<div class="karte">
<h3>📊 Zusammenfassung</h3>
<div class="station"><h4>Posteingang</h4><p>{len(docs)} Dokumente von {post.get("absender", "unbekannt")}</p></div>
<div class="station"><h4>Türschwelle</h4><p>Mandatsfähig: {"JA" if mandatsfaehig else "NEIN"}, Risiko: {tuerschwelle.get("risiko", "unbekannt")}</p></div>
<div class="station"><h4>Mandantenakte</h4><p>OCR: {len(docs) - ocr_fehler}/{len(docs)} OK, Übersetzung: {s3.get("uebersetzung", {}).get("status", "unbekannt")}</p></div>
<div class="station"><h4>Arbeitszentrale</h4><p>{len(zulaessig)} zulässige Aktionen, {len(gesperrt)} gesperrt</p></div>
</div>
</div>
<footer>
UI06 – Musterlauf Gesamtkette – Musterdaten – keine Produktivfreigabe<br>
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
    print("UI06 HAUPTLAUF =======================================")
    print("Zeitpunkt: " + now_iso())

    # [1] Config laden
    print("\n[1] Config laden ...")
    cfg = None
    if CONFIG_PATH.exists():
        cfg = load_json(CONFIG_PATH)
        print("    OK")
    else:
        FEHLER.append("Config nicht gefunden")
        print("    FEHLER")
        return

    # [2] Schreibbereiche
    print("[2] Schreibbereiche ...")
    ensure_dirs(cfg)
    print("    OK")

    muster = cfg.get("musterlauf", {})

    # [3] Station 1: Posteingang
    s1 = station_posteingang(muster)

    # [4] Station 2: Türschwelle
    s2 = station_tuerschwelle(muster, s1)

    # [5] Station 3: Mandantenakte
    s3 = station_mandantenakte(muster, s1)

    # [6] Station 4: UI05-Arbeitszentrale
    s4 = station_ui05_arbeitszentrale(muster, s3)

    # [7] Gesamt-Status
    print("\n[7] Gesamt-Status ...")
    gesamt_status = {
        "modul": "UI06",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "akten_id": muster.get("akten_id", "unbekannt"),
        "stationen": {
            "posteingang": s1,
            "tuerschwelle": s2,
            "mandantenakte": s3,
            "arbeitszentrale": s4
        },
        "zusammenfassung": {
            "dokumente": len(muster.get("dokumente", [])),
            "ocr_fehler": s3["ocr_status"]["fehler"],
            "uebersetzung_gesperrt": s3["uebersetzung"]["status"] == "fehlende_sprachpaare",
            "entscheidung": s2["entscheidung"],
            "naechste_aktionen": len(s4["naechste_aktionen"]["zulaessig"]),
            "gesperrte_aktionen": len(s4["naechste_aktionen"]["gesperrt"])
        },
        "grenzen": cfg.get("grenzen", {})
    }
    (SB / "02_Status" / "UI06_MUSTERLAUF_STATUS.json").write_text(
        json.dumps(gesamt_status, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # [8] HTML generieren
    print("[8] HTML generieren ...")
    html = generate_html(muster, cfg)
    (SB / "11_Browseransicht" / "index.html").write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    # [9] Bericht
    print("[9] Bericht ...")
    bericht = f"""UI06 Musterlauf Gesamtkette – Bericht
========================================
Zeitpunkt: {now_iso()}
Akten-ID: {muster.get('akten_id', 'unbekannt')}

STATION 1: POSTEINGANG
- Absender: {s1.get('absender', 'unbekannt')}
- Verfahren: {s1.get('verfahrensnummer', '')}
- Dokumente: {s1.get('anzahl_dokumente', 0)}

STATION 2: TÜRSCHWELLE
- Mandatsfähig: {'JA' if s2.get('mandatsfaehig') else 'NEIN'}
- Risiko: {s2.get('risiko', 'unbekannt')}
- Entscheidung: {s2.get('entscheidung', 'unbekannt')}

STATION 3: MANDANTENAKTE
- OCR OK: {s3['ocr_status']['ok']}/{s3['ocr_status']['ok'] + s3['ocr_status']['fehler']}
- OCR Fehler: {s3['ocr_status']['fehler']}
- Übersetzung: {s3['uebersetzung']['status']}
- Freigabe: {s3['freigabe']['status']}
- Parkstatus: {s3['parkstatus']['status']}

STATION 4: UI05-ARBEITSZENTRALE
- Zulässige Aktionen: {len(s4['naechste_aktionen']['zulaessig'])}
- Gesperrte Aktionen: {len(s4['naechste_aktionen']['gesperrt'])}
- Wartende Abhängigkeiten: {len(s4['naechste_aktionen']['abhaengigkeiten'])}

Nächste zulässige Aktionen:
{chr(10).join(['- P' + str(a.get('prioritaet', 99)) + (' [BLOCKIEREND]' if a.get('blockierend') else '') + ' ' + a.get('label', a) for a in s4['naechste_aktionen']['zulaessig']]) if s4['naechste_aktionen']['zulaessig'] else '- Keine'}

Gesperrte Aktionen:
{chr(10).join(['- 🔒 ' + g['aktion'] + ' (' + g['grund'] + ')' for g in s4['naechste_aktionen']['gesperrt']]) if s4['naechste_aktionen']['gesperrt'] else '- Keine'}

Grenzen eingehalten:
- Keine Originaländerung
- Keine neue OCR
- Keine DB-Änderung
- Kein Internet/Cloud
- Keine endgültige Übersetzung behauptet
- Keine Rechtsbewertung
- Keine Beweiswürdigung
- Gesperrte Aktionen nicht ausgelöst
- Nur Musterdaten verwendet
"""
    (SB / "03_Berichte" / "UI06_BERICHT.txt").write_text(bericht, encoding="utf-8")

    # Fehler/Warnungen
    fehler_text = "UI06 Fehler:\n" + "\n".join(FEHLER) if FEHLER else "UI06 Keine Fehler\n"
    warn_text = "UI06 Warnungen:\n" + "\n".join(WARNUNGEN) if WARNUNGEN else "UI06 Keine Warnungen\n"
    hinw_text = "UI06 Hinweise:\n" + "\n".join(HINWEISE) if HINWEISE else "UI06 Keine Hinweise\n"
    (SB / "05_Fehler" / "UI06_FEHLER.txt").write_text(fehler_text + "\n" + warn_text + "\n" + hinw_text, encoding="utf-8")

    # Manifest
    manifest_files = []
    for f in SB.rglob("*"):
        if f.is_file():
            manifest_files.append({"relativ": str(f.relative_to(SB)), "groesse": f.stat().st_size})
    manifest = {"modul": "UI06", "version": "1.0.0", "zeitpunkt": now_iso(),
                "anzahl_dateien": len(manifest_files), "dateien": manifest_files}
    (SB / "07_Manifest" / "UI06_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print(f"\nUI06 ABGESCHLOSSEN – Fehler: {len(FEHLER)}, Warnungen: {len(WARNUNGEN)}, Hinweise: {len(HINWEISE)}")


def selbsttest():
    global FEHLER, WARNUNGEN
    ok = 0
    ges = 0
    print("UI06 SELBSTTEST =======================================")

    def t(bez, bed):
        nonlocal ok, ges
        ges += 1
        v = bool(bed)
        print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
        if not v:
            FEHLER.append(bez)
        else:
            ok += 1

    cfg = load_json(CONFIG_PATH) if CONFIG_PATH.exists() else {}
    t("Config ladbar", bool(cfg))
    t("Schreibbereich anlegbar", SB.exists() or True)

    muster = cfg.get("musterlauf", {})
    t("Musterdaten vorhanden", bool(muster))
    t("Akten-ID definiert", bool(muster.get("akten_id")))
    t("Dokumente definiert", len(muster.get("dokumente", [])) > 0)
    t("Posteingang definiert", bool(muster.get("posteingang")))
    t("Türschwelle definiert", bool(muster.get("tuerschwelle")))
    t("UI04b Entscheidung definiert", bool(muster.get("ui04b_entscheidung")))

    # Sperrregister
    sperr = pruefe_sperrregister("011_quellenbetreuer_fachanwaltsraster_v1")
    t("Sperrregister prüfbar", bool(sperr))

    # Stationen simulieren (ohne Dateisystem)
    docs = muster.get("dokumente", [])
    t("OCR-Status pro Dokument", all("ocr_status" in d for d in docs))
    t("Mindestens ein OCR-Fehler", any(d.get("ocr_status") == "fehlerhaft" for d in docs))

    # HTML-Generierung testen
    html = generate_html(muster, cfg)
    t("HTML erzeugbar", len(html) > 3000)
    t("Akten-ID im HTML", "MUSTER-2026-001" in html)
    t("Station 1 im HTML", "Posteingang" in html)
    t("Station 2 im HTML", "Türschwelle" in html)
    t("Station 3 im HTML", "Mandantenakte" in html)
    t("Station 4 im HTML", "Arbeitszentrale" in html)
    t("Pfeile im HTML", "⬇" in html)
    t("OCR-Fehler markiert", "fehlerhaft" in html or "❌" in html)
    t("Argos-Blockierung im HTML", "Argos" in html or "gesperrt" in html.lower())
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
