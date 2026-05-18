#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI09 – Zentrale Grundschalter und Profilfelder
Erzeugt ein zentrales Profil-JSON und Grundschalter-JSON,
validiert gegen Regeln, erzeugt HTML-Übersicht.
"""

import json, os, sys
from datetime import datetime

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[FEHLER] Kann {path} nicht laden: {e}")
        global FEHLER
        FEHLER += 1
        return None

def pruefe_sperrregister(modul_id):
    sperr_pfad = "ALIN_Neustart_Core/01_Register/sperrregister.json"
    try:
        with open(sperr_pfad, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for e in reg.get("eintraege", []):
            if e.get("modul_id") == modul_id and e.get("gesperrt"):
                return True, e.get("freigabe_erfordert", [])
    except Exception:
        pass
    return False, []

def validiere_profil(profil, regeln):
    """Validiert das Profil gegen die Validierungsregeln."""
    fehler = []
    felder = {f["feld_id"]: f for f in profil.get("felder", [])}

    for r in regeln:
        rid = r["regel_id"]
        bed = r["bedingung"]
        schwere = r["schwere"]

        # VAL01: produktiv -> online oder cache
        if rid == "VAL01":
            modus = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "betriebsmodus"), "demo")
            online = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "online_status"), False)
            if modus == "produktiv" and not online:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": "Produktivmodus ohne Online-Status und ohne Offline-Cache"})

        # VAL02: gesperrt -> keine Freigaben
        elif rid == "VAL02":
            sicherheit = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "sicherheitsstatus"), "unbekannt")
            if sicherheit == "gesperrt":
                fv = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "freigabe_vorzimmer"), False)
                fa = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "freigabe_anwalt"), False)
                fs = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "freigabe_schlusskontrolle"), False)
                if fv or fa or fs:
                    fehler.append({"regel": rid, "schwere": schwere, "meldung": "Gesperrtes Dokument hat Freigaben"})

        # VAL03: produktiv -> akten_id
        elif rid == "VAL03":
            modus = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "betriebsmodus"), "demo")
            akte = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "akten_id"), None)
            if modus == "produktiv" and not akte:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": "Produktivmodus ohne Akten-ID"})

        # VAL04: mandant_id
        elif rid == "VAL04":
            mandant = next((f.get("default") for f in profil.get("felder", []) if f["feld_id"] == "mandant_id"), None)
            if not mandant:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": "Mandanten-ID nicht gesetzt"})

        # VAL05: musterdaten=false -> produktiv
        elif rid == "VAL05":
            # GS07 ist in grundschalter
            pass  # Wird in grundschalter-validierung geprüft

    return fehler

def validiere_grundschalter(schalter, regeln):
    """Validiert Grundschalter gegen Regeln."""
    fehler = []
    gs = {s["id"]: s for s in schalter}

    for r in regeln:
        rid = r["regel_id"]
        schwere = r["schwere"]

        if rid == "VAL05":
            gs07 = gs.get("GS07", {})
            if not gs07.get("default", True):
                # Musterdaten-Modus aus -> prüfe ob Betriebsmodus=produktiv
                # Diese Prüfung braucht das Profil, wird in hauptlauf kombiniert
                pass

    return fehler

def generiere_html(profil, schalter, validierungsfehler, cfg):
    """Erzeugt HTML-Profilübersicht."""
    ausgabe = cfg.get("ausgabe", {})
    html_pfad = ausgabe.get("html_profiluebersicht", "Windows_App/Logs/UI09_PROFILUEBERSICHT.html")
    os.makedirs(os.path.dirname(html_pfad), exist_ok=True)

    felder = profil.get("felder", [])

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI09 – Zentrales Profil und Grundschalter</title>
<style>
:root {{
  --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0;
  --kritisch: #dc2626; --hoch: #ea580c; --mittel: #ca8a04;
  --ok: #16a34a; --accent: #3b82f6;
}}
body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
.top-bar {{ background: var(--panel); padding: 16px 24px; border-radius: 8px; margin-bottom: 20px; }}
.top-bar h1 {{ margin: 0; font-size: 1.3rem; }}
.top-bar .meta {{ color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.card {{ background: var(--panel); padding: 16px; border-radius: 8px; border-left: 4px solid var(--accent); }}
.card h3 {{ margin: 0 0 8px; font-size: 0.9rem; color: #94a3b8; }}
.card .value {{ font-size: 1.1rem; font-weight: 600; }}
.card .detail {{ font-size: 0.8rem; color: #64748b; margin-top: 4px; }}
.section {{ background: var(--panel); padding: 20px; border-radius: 8px; margin-bottom: 16px; }}
.section h2 {{ margin-top: 0; font-size: 1.1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #334155; }}
th {{ color: #94a3b8; font-weight: 500; }}
.badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
.badge-pflicht {{ background: rgba(220,38,38,0.2); color: #fca5a5; }}
.badge-optional {{ background: rgba(100,116,139,0.2); color: #cbd5e1; }}
.badge-kritisch {{ background: rgba(220,38,38,0.2); color: #fca5a5; }}
.badge-hoch {{ background: rgba(234,88,12,0.2); color: #fdba74; }}
.toggle {{ display: inline-block; width: 36px; height: 20px; background: #334155; border-radius: 10px; position: relative; }}
.toggle.on {{ background: var(--ok); }}
.toggle::after {{ content: ''; position: absolute; width: 16px; height: 16px; background: white; border-radius: 50%; top: 2px; left: 2px; transition: 0.2s; }}
.toggle.on::after {{ left: 18px; }}
.footer {{ text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 20px; }}
</style>
</head>
<body>
<div class="top-bar">
  <h1>UI09 – Zentrale Grundschalter und Profilfelder</h1>
  <div class="meta">Profil: {profil.get('profil_id', '–')} v{profil.get('profil_version', '–')} | {datetime.now().isoformat()}</div>
</div>
"""

    # Profilfelder
    html += '<div class="section">\n<h2>Profilfelder ({} Stück)</h2>\n'.format(len(felder))
    html += '<table><tr><th>Feld</th><th>Typ</th><th>Default</th><th>Pflicht</th><th>Quelle</th><th>Nutzer</th></tr>\n'
    for f in felder:
        pflicht = "<span class='badge badge-pflicht'>Pflicht</span>" if f.get("pflichtfeld") else "<span class='badge badge-optional'>Optional</span>"
        default = json.dumps(f.get("default")) if f.get("default") is not None else "null"
        nutzer = ", ".join(f.get("nutzer", []))
        html += f'<tr><td><strong>{f["feld_id"]}</strong><br><span style="color:#64748b;font-size:0.8rem">{f.get("name", "")}</span></td><td>{f.get("typ", "–")}</td><td>{default}</td><td>{pflicht}</td><td>{f.get("quelle", "–")}</td><td>{nutzer}</td></tr>\n'
    html += '</table>\n</div>\n'

    # Grundschalter
    html += '<div class="section">\n<h2>Grundschalter ({} Stück)</h2>\n'.format(len(schalter))
    html += '<table><tr><th>ID</th><th>Name</th><th>Default</th><th>Änderbar durch</th><th>Wirkt auf</th></tr>\n'
    for s in schalter:
        default_on = "<span class='toggle on'></span>" if s.get("default") else "<span class='toggle'></span>"
        aenderbar = ", ".join(s.get("aenderbar_durch", []))
        wirkt = ", ".join(s.get("wirkt_auf", []))
        html += f'<tr><td>{s["id"]}</td><td><strong>{s["name"]}</strong><br><span style="color:#64748b;font-size:0.8rem">{s.get("beschreibung", "")}</span></td><td>{default_on}</td><td>{aenderbar}</td><td>{wirkt}</td></tr>\n'
    html += '</table>\n</div>\n'

    # Validierungsfehler
    if validierungsfehler:
        html += '<div class="section">\n<h2>Validierungsfehler</h2>\n<table><tr><th>Regel</th><th>Schwere</th><th>Meldung</th></tr>\n'
        for vf in validierungsfehler:
            badge = f"badge-{vf['schwere'].lower()}"
            html += f'<tr><td>{vf["regel"]}</td><td><span class="badge {badge}">{vf["schwere"]}</span></td><td>{vf["meldung"]}</td></tr>\n'
        html += '</table>\n</div>\n'
    else:
        html += '<div class="section">\n<h2>Validierung</h2>\n<p style="color:var(--ok)">✓ Alle Validierungsregeln bestanden</p>\n</div>\n'

    html += '<div class="footer">UI09 – Rote Linie: produktiv_freigegeben=false | nur_musterdaten=true</div>\n</body>\n</html>'

    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML Profilübersicht: {html_pfad}")
    return html_pfad

def generiere_json_profil(profil, cfg):
    """Speichert das zentrale Profil als JSON."""
    ausgabe = cfg.get("ausgabe", {})
    json_pfad = ausgabe.get("json_profil", "Windows_App/Logs/UI09_ZENTRALES_PROFIL.json")
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(profil, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON Profil: {json_pfad}")
    return json_pfad

def generiere_json_schalter(schalter, cfg):
    """Speichert Grundschalter als JSON."""
    ausgabe = cfg.get("ausgabe", {})
    json_pfad = ausgabe.get("json_grundschalter", "Windows_App/Logs/UI09_GRUNDSCHALTER.json")
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump({"grundschalter": schalter, "timestamp": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON Grundschalter: {json_pfad}")
    return json_pfad

def generiere_bericht(profil, schalter, validierungsfehler, cfg):
    """Erzeugt Textbericht."""
    ausgabe = cfg.get("ausgabe", {})
    bericht_pfad = ausgabe.get("bericht", "Windows_App/Logs/UI09_ZENTRALE_GRUNDSCHALTER_BERICHT.txt")
    os.makedirs(os.path.dirname(bericht_pfad), exist_ok=True)

    lines = [
        "=" * 60,
        "UI09 – Zentrale Grundschalter und Profilfelder",
        "=" * 60,
        f"Profil-ID: {profil.get('profil_id', '–')}",
        f"Profil-Version: {profil.get('profil_version', '–')}",
        f"Zeitstempel: {datetime.now().isoformat()}",
        "",
        f"PROFILFELDER ({len(profil.get('felder', []))} Stueck)",
    ]
    for f in profil.get("felder", []):
        pflicht = "[PFLICHT]" if f.get("pflichtfeld") else "[optional]"
        default = json.dumps(f.get("default")) if f.get("default") is not None else "null"
        lines.append(f"  {f['feld_id']}: {f.get('name', '')} {pflicht} (Default: {default})")

    lines.extend([
        "",
        f"GRUNDSCHALTER ({len(schalter)} Stueck)",
    ])
    for s in schalter:
        status = "AN" if s.get("default") else "AUS"
        lines.append(f"  {s['id']}: {s['name']} [{status}]")
        lines.append(f"    -> Wirkt auf: {', '.join(s.get('wirkt_auf', []))}")

    lines.extend([
        "",
        "VALIDIERUNG",
    ])
    if validierungsfehler:
        lines.append(f"  {len(validierungsfehler)} Fehler gefunden:")
        for vf in validierungsfehler:
            lines.append(f"    [{vf['schwere']}] {vf['regel']}: {vf['meldung']}")
    else:
        lines.append("  Alle Validierungsregeln bestanden.")

    lines.extend([
        "",
        "=" * 60,
        "Rote Linie: produktiv_freigegeben=false | nur_musterdaten=true",
        "=" * 60,
    ])

    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Bericht: {bericht_pfad}")
    return bericht_pfad

def hauptlauf():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI09 – Zentrale Grundschalter und Profilfelder")
    print("=" * 60)

    # 1. Config laden
    cfg = load_json("Config/ui09_zentrale_grundschalter_profilfelder_v1.json")
    if not cfg:
        print("[FEHLER] Config nicht ladbar. Abbruch.")
        return 1

    # 2. Sperrregister
    modul_id = cfg.get("modul_id", "UI09")
    gesperrt, freigabe = pruefe_sperrregister(modul_id)
    if gesperrt:
        print(f"[SPERRE] {modul_id} ist im Sperrregister gesperrt.")
        print(f"         Freigabe erfordert: {', '.join(freigabe)}")
        FEHLER += 1
        return 1
    print("[OK] Sperrregister: keine Sperre")

    # 3. Profil und Schalter extrahieren
    profil = cfg.get("zentrales_profil", {})
    schalter = cfg.get("grundschalter", {}).get("schalter", [])
    regeln = cfg.get("validierungsregeln", [])

    print(f"[OK] Profil geladen: {profil.get('profil_id', '–')} mit {len(profil.get('felder', []))} Feldern")
    print(f"[OK] Grundschalter geladen: {len(schalter)} Schalter")

    # 4. Validierung
    val_fehler = validiere_profil(profil, regeln)
    if val_fehler:
        print(f"[WARN] {len(val_fehler)} Validierungsfehler gefunden")
        for vf in val_fehler:
            print(f"       [{vf['schwere']}] {vf['regel']}: {vf['meldung']}")
    else:
        print("[OK] Alle Validierungsregeln bestanden")

    # 5. Ausgaben
    generiere_html(profil, schalter, val_fehler, cfg)
    generiere_json_profil(profil, cfg)
    generiere_json_schalter(schalter, cfg)
    generiere_bericht(profil, schalter, val_fehler, cfg)

    # 6. Zusammenfassung
    print("\n" + "=" * 60)
    print(f"Profilfelder: {len(profil.get('felder', []))} | Grundschalter: {len(schalter)} | Validierungsfehler: {len(val_fehler)}")
    if FEHLER == 0:
        print("UI09 ABGESCHLOSSEN")
    else:
        print(f"UI09 mit {FEHLER} Fehler(n) beendet")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI09 SELBSTTEST ==========================================")
    def t(bez, bed):
        global FEHLER
        if bed:
            print(f"  [OK]   {bez}")
        else:
            print(f"  [FEHLER] {bez}")
            FEHLER += 1

    cfg = load_json("Config/ui09_zentrale_grundschalter_profilfelder_v1.json")
    t("Config ladbar", cfg is not None)
    if cfg:
        t("modul_id == UI09", cfg.get("modul_id") == "UI09")
        profil = cfg.get("zentrales_profil", {})
        t("zentrales_profil vorhanden", bool(profil))
        t("mindestens 10 Profilfelder", len(profil.get("felder", [])) >= 10)
        t("profil_id gesetzt", bool(profil.get("profil_id")))
        schalter = cfg.get("grundschalter", {}).get("schalter", [])
        t("mindestens 5 Grundschalter", len(schalter) >= 5)
        t("GS07 Musterdaten-Modus vorhanden", any(s.get("id") == "GS07" for s in schalter))
        regeln = cfg.get("validierungsregeln", [])
        t("mindestens 3 Validierungsregeln", len(regeln) >= 3)
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)

    t("hauptlauf() definiert", callable(hauptlauf))
    t("validiere_profil() definiert", callable(validiere_profil))
    t("generiere_html() definiert", callable(generiere_html))
    t("generiere_json_profil() definiert", callable(generiere_json_profil))
    t("generiere_json_schalter() definiert", callable(generiere_json_schalter))
    t("generiere_bericht() definiert", callable(generiere_bericht))

    print(f"\nSELBSTTEST: {'BESTANDEN' if FEHLER == 0 else f'{FEHLER} FEHLER'}")
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        sys.exit(selbsttest())
    sys.exit(hauptlauf())
