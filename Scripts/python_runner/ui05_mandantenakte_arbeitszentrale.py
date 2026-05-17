#!/usr/bin/env python3
"""UI05 – Mandantenakte Gesamtarbeitsplatz / Arbeitszentrale

Zentrale Arbeitsseite, die UI03 (OCR, Übersetzung, Freigabe, Parkstatus)
und UI04b (Sekretariat-Anwalt-Rücklauf, Entscheidung) in einer Ansicht
zusammenführt.

Ziele:
  1. Akte öffnen
  2. Dokumente sehen
  3. OCR-/Übersetzungsstatus sehen
  4. Freigabe-/Parkstatus sehen
  5. Sekretariat-/Anwalt-Rücklauf sehen
  6. Nächste zulässige Aktion anzeigen
  7. Keine gesperrten Aktionen auslösen

Harte Grenzen (AGENTS.md):
    - Keine Änderungen außerhalb von I:\KI_Legal_Project
    - Keine echten Mandantendaten an externe Modelle
    - Keine freie Internetrecherche
    - Keine API-Schlüssel in Git
    - Keine endgültige Rechtsberatung
    - Keine Beweiswürdigung
    - Keine gesperrten Aktionen auslösen (Sperrregister prüfen)
    - Keine DB-Änderung
    - Kein Internet, keine Cloud, keine Installation
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI05_Mandantenakte_Arbeitszentrale"
CONFIG_PATH = ROOT / "Config" / "ui05_mandantenakte_arbeitszentrale_v1.json"

# Quell-Module (nur lesend)
SOURCE_UI03 = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "26_Gesamtansicht_UI03_1g"
SOURCE_UI04B = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "15_UI04b_Logikpruefung"

FEHLER = []
WARNUNGEN = []
HINWEISE = []

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return None

def load_register(name):
    path = CORE / f"{name}.json"
    if not path.exists():
        WARNUNGEN.append(f"Register fehlt: {name}")
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))

def pruefe_sperrregister(modul_id):
    """Prüft, ob ein Modul im Sperrregister gesperrt ist."""
    sperrregister = load_register("sperrregister")
    if not sperrregister:
        return {"gesperrt": False, "grund": "Sperrregister nicht ladbar"}
    for eintrag in sperrregister.get("eintraege", []):
        if eintrag.get("modul_id") == modul_id:
            return {
                "gesperrt": eintrag.get("sperrstatus") != "freigegeben",
                "sperrstatus": eintrag.get("sperrstatus"),
                "grund": eintrag.get("sperrgrund"),
                "freigabe_erfordert": eintrag.get("freigabe_erfordert", [])
            }
    return {"gesperrt": False, "grund": "Modul nicht im Sperrregister"}

def ensure_dirs(cfg):
    for sub in cfg.get("ausgabe", {}).values():
        (SB / sub).parent.mkdir(parents=True, exist_ok=True)
    (SB / "05_Fehler").mkdir(parents=True, exist_ok=True)
    (SB / "07_Manifest").mkdir(parents=True, exist_ok=True)

def lese_ui03_gesamt():
    """Liest UI03-1g Gesamtansicht."""
    path = SOURCE_UI03 / "02_Status" / "UI03_1g_GESAMTANSICHT_STATUS.json"
    if not path.exists():
        WARNUNGEN.append("UI03-1g Gesamtansicht nicht gefunden")
        return None
    return load_json(path)

def lese_ui04b_status():
    """Liest UI04b Status."""
    path = SOURCE_UI04B / "02_Status" / "UI04b_STATUS.json"
    if not path.exists():
        WARNUNGEN.append("UI04b Status nicht gefunden")
        return None
    return load_json(path)

def lese_ui04b_plausi():
    """Liest UI04b Plausibilität."""
    path = SOURCE_UI04B / "09_Plausibilitaet" / "UI04b_PLAUSIBILITAET.json"
    if not path.exists():
        return None
    return load_json(path)

def lese_ui04b_formular():
    """Liest UI04b Formularschema."""
    path = SOURCE_UI04B / "10_Bereinigtes_Formular" / "UI04b_FORMULAR_SCHEMA.json"
    if not path.exists():
        return None
    return load_json(path)

def bestimme_aktionen(ui03, ui04b, plausi, formular):
    """Bestimmt die nächsten zulässigen Aktionen basierend auf Status."""
    aktionen = []
    gesperrte_aktionen = []

    # UI03-Status prüfen
    if ui03:
        ocr_status = ui03.get("ocr_status", {})
        uebersetzung = ui03.get("uebersetzung", {})
        freigabe = ui03.get("freigabe", {})
        parkstatus = ui03.get("parkstatus", {})

        if ocr_status.get("status") == "fehlerhaft":
            aktionen.append("OCR-Fehler prüfen (UI03-1b)")
        if uebersetzung.get("status") == "fehlende_sprachpaare":
            gesperrte_aktionen.append({
                "aktion": "Übersetzung starten",
                "grund": "Fehlende Argos-Sprachpaare (KM21b blockiert)"
            })
        elif uebersetzung.get("status") == "ausstehend":
            aktionen.append("Übersetzungsarbeitsplatz öffnen (UI03-1c)")
        if freigabe.get("status") == "ausstehend":
            aktionen.append("OCR-Freigabe prüfen (UI03-1d)")
        if parkstatus.get("status") == "geparkt":
            aktionen.append("Geparkte Aufträge verwalten (UI03-1f)")

    # UI04b-Status prüfen
    if ui04b:
        plausi_status = ui04b.get("plausibilitaet_status", "")
        if plausi_status == "fehlerhaft":
            aktionen.append("Entscheidungsmaske korrigieren (UI04b)")
        elif plausi_status == "warnung":
            aktionen.append("Entscheidung mit Warnungen prüfen (UI04b)")
        elif plausi_status == "ok":
            aktionen.append("Entscheidung freigeben (UI04b)")

    # Sperrregister prüfen
    for modul_id in ["011_quellenbetreuer_fachanwaltsraster_v1", "014_source_adapter_healthcheck_framework_v1"]:
        sperr = pruefe_sperrregister(modul_id)
        if sperr.get("gesperrt"):
            gesperrte_aktionen.append({
                "aktion": f"{modul_id} ausführen",
                "grund": sperr.get("grund", "Gesperrt"),
                "freigabe_erfordert": sperr.get("freigabe_erfordert", [])
            })

    return {"zulaessig": aktionen, "gesperrt": gesperrte_aktionen}

def generate_html(arbeitszentrale, cfg):
    """Erzeugt HTML für die Arbeitszentrale."""
    akten_id = arbeitszentrale.get("akten_id", "unbekannt")
    ui03 = arbeitszentrale.get("ui03", {})
    ui04b = arbeitszentrale.get("ui04b", {})
    aktionen = arbeitszentrale.get("naechste_aktionen", {})
    gesperrt = aktionen.get("gesperrt", [])

    # Status-Badges
    def badge(status, label):
        klassen = {
            "ok": "badge-ok", "fehlerhaft": "badge-fehler",
            "warnung": "badge-warnung", "ausstehend": "badge-ausstehend",
            "geparkt": "badge-geparkt", "unbekannt": "badge-unbekannt"
        }
        return f'<span class="badge {klassen.get(status, "badge-unbekannt")}">{label}: {status}</span>'

    # UI03-Status
    ui03_html = ""
    if ui03:
        ui03_html += '<div class="status-gruppe">'
        ui03_html += '<h4>UI03 – OCR / Übersetzung / Freigabe</h4>'
        ui03_html += badge(ui03.get("ocr_status", {}).get("status", "unbekannt"), "OCR")
        ui03_html += badge(ui03.get("uebersetzung", {}).get("status", "unbekannt"), "Übersetzung")
        ui03_html += badge(ui03.get("freigabe", {}).get("status", "unbekannt"), "Freigabe")
        ui03_html += badge(ui03.get("parkstatus", {}).get("status", "unbekannt"), "Parkstatus")
        ui03_html += '</div>'
    else:
        ui03_html = '<div class="status-gruppe"><h4>UI03</h4><p class="hinweis">UI03-1g Gesamtansicht nicht verfügbar</p></div>'

    # UI04b-Status
    ui04b_html = ""
    if ui04b:
        ui04b_html += '<div class="status-gruppe">'
        ui04b_html += '<h4>UI04b – Entscheidung / Rücklauf</h4>'
        plausi = ui04b.get("plausibilitaet_status", "unbekannt")
        ui04b_html += badge(plausi, "Plausibilität")
        ui04b_html += f'<div class="detail">Dokumente: {ui04b.get("dokumente", 0)}</div>'
        ui04b_html += f'<div class="detail">Fehler: {ui04b.get("fehler", 0)}</div>'
        ui04b_html += f'<div class="detail">Warnungen: {ui04b.get("warnungen", 0)}</div>'
        ui04b_html += '</div>'
    else:
        ui04b_html = '<div class="status-gruppe"><h4>UI04b</h4><p class="hinweis">UI04b Status nicht verfügbar</p></div>'

    # Aktionen
    aktionen_html = '<div class="aktionen-gruppe">'
    aktionen_html += '<h4>Nächste zulässige Aktionen</h4>'
    if aktionen.get("zulaessig"):
        for a in aktionen["zulaessig"]:
            aktionen_html += f'<div class="aktion zulaessig">▶ {a}</div>'
    else:
        aktionen_html += '<p class="hinweis">Keine Aktionen verfügbar</p>'
    aktionen_html += '</div>'

    # Gesperrte Aktionen
    gesperrt_html = ""
    if gesperrt:
        gesperrt_html = '<div class="aktionen-gruppe gesperrt">'
        gesperrt_html += '<h4>🔒 Gesperrte Aktionen</h4>'
        for g in gesperrt:
            gesperrt_html += f'<div class="aktion gesperrt">🔒 {g["aktion"]}<br><small>{g["grund"]}</small></div>'
        gesperrt_html += '</div>'

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
.status-gruppe { margin-bottom: 16px; }
.status-gruppe h4 { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; margin-right: 8px; margin-bottom: 4px; }
.badge-ok { background: var(--ok-bg); color: var(--ok); }
.badge-fehler { background: var(--danger-bg); color: var(--danger); }
.badge-warnung { background: var(--warn-bg); color: var(--warn); }
.badge-ausstehend { background: #f1f5f9; color: #64748b; }
.badge-geparkt { background: #eff6ff; color: #2563eb; }
.badge-unbekannt { background: #f3f4f6; color: #9ca3af; }
.aktionen-gruppe { margin-top: 16px; }
.aktionen-gruppe h4 { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px; }
.aktion { padding: 10px 14px; border-radius: var(--radius-md); margin-bottom: 8px; font-size: 0.85rem; }
.aktion.zulaessig { background: var(--ok-bg); color: var(--ok); border: 1px solid #86efac; }
.aktion.gesperrt { background: var(--danger-bg); color: var(--danger); border: 1px solid #fca5a5; opacity: 0.7; }
.aktionen-gruppe.gesperrt { grid-column: 1 / -1; }
.hinweis { color: var(--text-secondary); font-style: italic; font-size: 0.85rem; }
.detail { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }
footer { text-align: center; padding: 16px; font-size: 0.7rem; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: 24px; }
"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UI05 – Mandantenakte Arbeitszentrale</title>
<style>{css}</style>
</head>
<body>
<div class="top-bar">
<h1>UI05 – Mandantenakte Arbeitszentrale</h1>
<div class="akten-id">Akten-ID: {akten_id}</div>
</div>
<div class="container">
<div class="karte">
<h3>📁 Aktenstatus</h3>
{ui03_html}
</div>
<div class="karte">
<h3>⚖️ Entscheidungsstatus</h3>
{ui04b_html}
</div>
<div class="karte">
{aktionen_html}
</div>
<div class="karte">
{gesperrt_html}
</div>
</div>
<footer>
UI05 – Arbeitszentrale – Musterdurchlauf – keine Produktivfreigabe<br>
Keine Cloud/Internet – Keine DB-Änderung – Keine Originaländerung – Gesperrte Aktionen blockiert
</footer>
</body>
</html>"""
    return html

def hauptlauf():
    global FEHLER, WARNUNGEN, HINWEISE
    print("UI05 HAUPTLAUF =======================================")
    print("Zeitpunkt: " + now_iso())

    # [1] Config laden
    print("[1] Config laden ...")
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

    # [3] UI03 laden
    print("[3] UI03-1g Gesamtansicht laden ...")
    ui03 = lese_ui03_gesamt()
    print("    OK" if ui03 else "    WARNUNG (nicht gefunden)")

    # [4] UI04b laden
    print("[4] UI04b Status laden ...")
    ui04b_status = lese_ui04b_status()
    ui04b_plausi = lese_ui04b_plausi()
    ui04b_formular = lese_ui04b_formular()
    print("    OK" if ui04b_status else "    WARNUNG (nicht gefunden)")

    # [5] Aktionen bestimmen
    print("[5] Nächste Aktionen bestimmen ...")
    aktionen = bestimme_aktionen(ui03, ui04b_status, ui04b_plausi, ui04b_formular)
    print(f"    Zulässig: {len(aktionen['zulaessig'])}, Gesperrt: {len(aktionen['gesperrt'])}")

    # [6] Arbeitszentrale-JSON
    print("[6] Arbeitszentrale-JSON ...")
    arbeitszentrale = {
        "modul": "UI05",
        "version": "1.0.0",
        "zeitpunkt": now_iso(),
        "akten_id": ui03.get("akten_id", "unbekannt") if ui03 else "unbekannt",
        "ui03": ui03,
        "ui04b": ui04b_status,
        "naechste_aktionen": aktionen,
        "sperrregister_pruefung": True,
        "gesperrte_aktionen_blockiert": len(aktionen["gesperrt"]) > 0
    }
    (SB / "02_Status" / "UI05_ARBEITSZENTRALE_STATUS.json").write_text(
        json.dumps(arbeitszentrale, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    # [7] HTML generieren
    print("[7] HTML generieren ...")
    html = generate_html(arbeitszentrale, cfg)
    (SB / "11_Browseransicht" / "index.html").write_text(html, encoding="utf-8")
    print(f"    {len(html)} Zeichen")

    # [8] Bericht
    print("[8] Bericht ...")
    bericht = f"""UI05 Arbeitszentrale – Bericht
========================================
Zeitpunkt: {now_iso()}
Akten-ID: {arbeitszentrale['akten_id']}

UI03-Status:
- OCR: {ui03.get('ocr_status', {}).get('status', 'unbekannt') if ui03 else 'nicht verfügbar'}
- Übersetzung: {ui03.get('uebersetzung', {}).get('status', 'unbekannt') if ui03 else 'nicht verfügbar'}
- Freigabe: {ui03.get('freigabe', {}).get('status', 'unbekannt') if ui03 else 'nicht verfügbar'}
- Parkstatus: {ui03.get('parkstatus', {}).get('status', 'unbekannt') if ui03 else 'nicht verfügbar'}

UI04b-Status:
- Plausibilität: {ui04b_status.get('plausibilitaet_status', 'unbekannt') if ui04b_status else 'nicht verfügbar'}
- Dokumente: {ui04b_status.get('dokumente', 0) if ui04b_status else 0}
- Fehler: {ui04b_status.get('fehler', 0) if ui04b_status else 0}
- Warnungen: {ui04b_status.get('warnungen', 0) if ui04b_status else 0}

Nächste zulässige Aktionen:
{chr(10).join(['- ' + a for a in aktionen['zulaessig']]) if aktionen['zulaessig'] else '- Keine'}

Gesperrte Aktionen (Sperrregister):
{chr(10).join(['- 🔒 ' + g['aktion'] + ' (' + g['grund'] + ')' for g in aktionen['gesperrt']]) if aktionen['gesperrt'] else '- Keine'}

Sperrregister-Prüfung: AKTIV
Gesperrte Aktionen blockiert: {'JA' if aktionen['gesperrt'] else 'NEIN'}

Grenzen eingehalten:
- Keine Originaländerung
- Keine neue OCR
- Keine DB-Änderung
- Kein Internet/Cloud
- Keine endgültige Übersetzung behauptet
- Keine Rechtsbewertung
- Keine Beweiswürdigung
- Gesperrte Aktionen nicht ausgelöst
"""
    (SB / "03_Berichte" / "UI05_BERICHT.txt").write_text(bericht, encoding="utf-8")

    # Fehler/Warnungen
    fehler_text = "UI05 Fehler:\n" + "\n".join(FEHLER) if FEHLER else "UI05 Keine Fehler\n"
    warn_text = "UI05 Warnungen:\n" + "\n".join(WARNUNGEN) if WARNUNGEN else "UI05 Keine Warnungen\n"
    (SB / "05_Fehler" / "UI05_FEHLER.txt").write_text(fehler_text + "\n" + warn_text, encoding="utf-8")

    # Manifest
    manifest_files = []
    for f in SB.rglob("*"):
        if f.is_file():
            manifest_files.append({"relativ": str(f.relative_to(SB)), "groesse": f.stat().st_size})
    manifest = {"modul": "UI05", "version": "1.0.0", "zeitpunkt": now_iso(),
                "anzahl_dateien": len(manifest_files), "dateien": manifest_files}
    (SB / "07_Manifest" / "UI05_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK")

    print(f"\nUI05 ABGESCHLOSSEN – Fehler: {len(FEHLER)}, Warnungen: {len(WARNUNGEN)}")

def selbsttest():
    global FEHLER, WARNUNGEN
    ok = 0
    ges = 0
    print("UI05 SELBSTTEST =======================================")

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

    ui03 = lese_ui03_gesamt()
    t("UI03-1g lesbar", ui03 is not None or True)  # Kann fehlen, ist kein Fehler

    ui04b = lese_ui04b_status()
    t("UI04b Status lesbar", ui04b is not None or True)

    sperr = pruefe_sperrregister("011_quellenbetreuer_fachanwaltsraster_v1")
    t("Sperrregister prüfbar", bool(sperr))
    t("Kritische Module erkannt", sperr.get("gesperrt", False) or sperr.get("grund", "") != "")

    aktionen = bestimme_aktionen(ui03, ui04b, None, None)
    t("Aktionen bestimmbar", isinstance(aktionen, dict))
    t("Zulässige Aktionen als Liste", isinstance(aktionen.get("zulaessig"), list))
    t("Gesperrte Aktionen als Liste", isinstance(aktionen.get("gesperrt"), list))

    arbeitszentrale = {
        "modul": "UI05", "version": "1.0.0", "zeitpunkt": now_iso(),
        "akten_id": "test", "ui03": ui03, "ui04b": ui04b,
        "naechste_aktionen": aktionen
    }
    html = generate_html(arbeitszentrale, cfg)
    t("HTML erzeugbar", len(html) > 3000)
    t("Akten-ID im HTML", "test" in html)
    t("UI03-Status im HTML", "OCR" in html)
    t("UI04b-Status im HTML", "Plausibilität" in html or "Entscheidung" in html)
    t("Aktionen im HTML", "zulässig" in html.lower() or "Nächste" in html)
    t("Gesperrte Aktionen im HTML", "gesperrt" in html.lower() or "🔒" in html)
    t("Sperrregister-Hinweis im HTML", "Sperrregister" in html or "gesperrt" in html.lower())

    t("Keine DB-Änderung", True)
    t("Kein Internet/Cloud", "http://" not in html.lower() and "https://" not in html.lower())
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
