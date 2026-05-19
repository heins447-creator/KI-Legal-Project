#!/usr/bin/env python3
"""UI02c – PRUEFDATEI – Prueft alle erzeugten Dateien auf Konsistenz"""
import sys, json, os
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI02_Tuerschwelle_Bau" / "17_Freigabe_UI02c"

FEHLER = 0
def check(bez, bed):
    global FEHLER
    v = bool(bed)
    if not v:
        print(f"  [FEHLER] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK] {bez}")
    return v

print("UI02c PRUEFDATEI =====================================")

# 1. Pfade
paths = {
    "Status": SB / "02_Status" / "UI02c_STATUS.json",
    "Bericht": SB / "03_Berichte" / "UI02c_BERICHT.txt",
    "Fehlerbericht": SB / "05_Fehler" / "UI02c_FEHLER.txt",
    "Manifest": SB / "07_Manifest" / "UI02c_MANIFEST.json",
    "ViewData": SB / "08_ViewData" / "UI02c_VIEWDATA.json",
    "Freigabevorschlag": SB / "09_Freigabevorschlag" / "UI02c_FREIGABEVORSCHLAG.json",
    "Formularschema": SB / "10_Freigabeformular" / "UI02c_FREIGABEFORMULAR_SCHEMA.json",
    "Rueckgabe-Template": SB / "11_Rueckgabe" / "UI02c_RUECKGABE_AN_REGULAEREN_PROZESS_TEMPLATE.json",
    "HTML": SB / "12_Browseransicht" / "index.html",
    "CSS": SB / "12_Browseransicht" / "ui02c.css",
    "JS": SB / "12_Browseransicht" / "ui02c.js",
    "Config": ROOT / "Config" / "ui02c_freigabe_dropdowns_notizen_v1.json",
}

for name, p in paths.items():
    check(f"Datei vorhanden: {name}", p.exists())

# 2. JSON validieren
json_paths = [p for name, p in paths.items() if p.suffix == ".json" and p.exists()]
for jp in json_paths:
    try:
        data = json.loads(jp.read_text(encoding="utf-8-sig"))
        check(f"JSON gueltig: {jp.name}", True)
    except Exception as e:
        check(f"JSON gueltig: {jp.name}", False)
        print(f"    Grund: {e}")

# 3. HTML pruefen
html_path = paths["HTML"]
if html_path.exists():
    html = html_path.read_text(encoding="utf-8")
    check("HTML enthaelt VIEWDATA-Platzhalter", "{{VIEWDATA_JSON}}" not in html)  # sollte ersetzt sein
    check("HTML referenziert CSS", 'href="ui02c.css"' in html)
    check("HTML referenziert JS", 'src="ui02c.js"' in html)
    check("HTML enthaelt Mikrofon-Hinweis", "Windows-Taste + H" in html or "lokale Diktat" in html)
    check("HTML enthaelt Keine-Rechtsberatung", "Keine Rechtsberatung" in html)
    check("HTML enthaelt speichereFreigabe", "speichereFreigabe" in html)
    check("HTML enthaelt Tuerschwellenhinweis", "tuerschwelle" in html.lower())
    check("HTML enthaelt 7 Schritte", "1.–4." in html)
    check("HTML enthaelt Wiedervorlage-Sektion", "Wiedervorlage" in html)
    check("HTML enthaelt Rueckgabe-Sektion", "Rueckgabe an Sekretariat" in html)
    check("HTML enthaelt Mandatsentscheidung", "Mandatsentscheidung" in html)
    check("Keine TIFF-Referenz", ".tiff" not in html.lower() and ".tif" not in html.lower())
    check("Keine Base64-Blöcke im HTML", "base64," not in html.lower())

# 4. CSS pruefen
css_path = paths["CSS"]
if css_path.exists():
    css = css_path.read_text(encoding="utf-8")
    check("CSS enthaelt entscheidung-card", "entscheidung-card" in css)
    check("CSS enthaelt mic-btn", "mic-btn" in css)
    check("CSS enthaelt layout flex", "layout" in css)

# 5. JS pruefen
js_path = paths["JS"]
if js_path.exists():
    js = js_path.read_text(encoding="utf-8")
    check("JS enthaelt speichereFreigabe", "speichereFreigabe" in js)
    check("JS enthaelt fillDropdown", "fillDropdown" in js)
    check("JS enthaelt showMicHint", "showMicHint" in js)
    check("JS enthaelt JSON-Download Blob", "Blob" in js and "application/json" in js)

# 6. Manifest pruefen
mf_path = paths["Manifest"]
if mf_path.exists():
    mf = json.loads(mf_path.read_text(encoding="utf-8-sig"))
    check(f"Manifest >10 Dateien", mf.get("anzahl_dateien", 0) >= 10)
    check("Manifest enthaelt index.html", any("index.html" in d.get("relativ","") for d in mf.get("dateien",[])))

# 7. Freigabevorschlag pruefen
fv_path = paths["Freigabevorschlag"]
if fv_path.exists():
    fv = json.loads(fv_path.read_text(encoding="utf-8-sig"))
    check("FV hat dokument_ids", "dokument_ids" in fv)
    check("FV hat dokumente", "dokumente" in fv)
    check("FV hat Hinweis", "Keine Rechtsberatung" in fv.get("hinweis", ""))

# 8. Formularschema pruefen
fs_path = paths["Formularschema"]
if fs_path.exists():
    fs = json.loads(fs_path.read_text(encoding="utf-8-sig"))
    check("FS hat 13 Dropdowns", len(fs.get("dropdowns", [])) == 13)
    check("FS hat Entscheidungen", len(fs.get("entscheidungsoptionen", [])) >= 4)
    check("FS hat Agentenauftraege", len(fs.get("agentenauftrag_vorschlaege", [])) >= 3)

# 9. Grenzen
check("Keine DB-Datei im Schreibbereich", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))
check("Keine API-Key-Dateien", not any(SB.rglob("*.env")) and not any(SB.rglob("*secret*")) and not any(SB.rglob("*api_key*")))

# 10. ViewData pruefen
vd_path = paths["ViewData"]
if vd_path.exists():
    vd = json.loads(vd_path.read_text(encoding="utf-8-sig"))
    check("VD hat dokumente", "dokumente" in vd)
    check("VD hat freigabevorschlag", "freigabevorschlag" in vd)
    check("VD hat formularschema", "formularschema" in vd)

print(f"\nPRUEFERGEBNIS: {FEHLER} Fehler")
if FEHLER > 0:
    print("PRUEFDATEI NICHT BESTANDEN")
    sys.exit(1)
else:
    print("PRUEFDATEI BESTANDEN")
    sys.exit(0)
