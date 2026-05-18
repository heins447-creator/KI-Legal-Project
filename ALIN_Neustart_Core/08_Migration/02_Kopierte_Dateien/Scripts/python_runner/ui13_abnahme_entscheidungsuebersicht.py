#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI13 – Abnahme- und Entscheidungsübersicht UI08–UI12
Erzeugt eine Browser-/HTML-Übersicht mit:
- Abgeschlossene Module UI08–UI12
- Adapter-Daten vorhanden / fehlend
- Fehlende Eingaben
- Erwartbare Warnungen
- Kritische Blockaden
- Zulässige Schritte ohne Freeze-Öffnung
- Schritte die UI03–UI07b berühren würden

Rote Linie: produktiv_freigegeben=false, nur_musterdaten=true, echte_daten_erlaubt=false
Berührt UI03–UI07b: NEIN (nur lesend auf UI08–UI12 Ausgaben)
"""

import json
import os
import sys
import glob
from datetime import datetime

FEHLER = 0
WARNUNGEN = 0


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def file_exists(path):
    return os.path.exists(path)


def pruefe_sperrregister(modul_id):
    sperr_pfad = "ALIN_Neustart_Core/01_Register/sperrregister.json"
    try:
        with open(sperr_pfad, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for eintrag in reg.get("eintraege", []):
            if eintrag.get("modul_id") == modul_id and eintrag.get("gesperrt", False):
                return eintrag
    except Exception:
        pass
    return None


def pruefe_modul_status(modul, cfg):
    global WARNUNGEN
    result = {
        "modul_id": modul["modul_id"],
        "name": modul["name"],
        "commit_hash": modul.get("commit_hash", "unbekannt"),
        "ausgaben": {},
        "abgeschlossen": False,
        "hinweise": []
    }
    # Prüfe Ausgabedateien
    for key in ["ausgabe_json", "ausgabe_html", "ausgabe_txt"]:
        pfad = modul.get(key)
        if pfad:
            exists = file_exists(pfad)
            result["ausgaben"][key] = {"pfad": pfad, "vorhanden": exists}
            if not exists:
                result["hinweise"].append(f"{key} fehlt: {pfad}")
                WARNUNGEN += 1
    # Abgeschlossen = Commit-Hash vorhanden UND mindestens eine Ausgabe
    has_commit = bool(modul.get("commit_hash"))
    has_output = any(result["ausgaben"].get(k, {}).get("vorhanden", False) for k in result["ausgaben"])
    result["abgeschlossen"] = has_commit and has_output
    if not has_commit:
        result["hinweise"].append("Kein Commit-Hash hinterlegt")
    return result


def pruefe_adapter_daten(cfg):
    global WARNUNGEN
    adapter_checks = []
    # UI10 Adapter
    ui10_pfad = "Windows_App/Logs/UI10_PROFIL_ADAPTER.json"
    ui10_exists = file_exists(ui10_pfad)
    ui10_data = load_json(ui10_pfad) if ui10_exists else None
    adapter_checks.append({
        "name": "UI10 Profil-Adapter",
        "pfad": ui10_pfad,
        "vorhanden": ui10_exists,
        "lesbar": ui10_data is not None,
        "hinweis": None if ui10_exists else "UI10-Adapter fehlt. UI12 liefert nur Musterdaten."
    })
    if not ui10_exists:
        WARNUNGEN += 1
    # UI11 Adapter
    ui11_pfad = "Windows_App/Logs/UI11_REGISTER_ADAPTER.json"
    ui11_exists = file_exists(ui11_pfad)
    ui11_data = load_json(ui11_pfad) if ui11_exists else None
    adapter_checks.append({
        "name": "UI11 Register-Adapter",
        "pfad": ui11_pfad,
        "vorhanden": ui11_exists,
        "lesbar": ui11_data is not None,
        "hinweis": None if ui11_exists else "UI11-Adapter fehlt. UI12 liefert nur Musterdaten."
    })
    if not ui11_exists:
        WARNUNGEN += 1
    return adapter_checks


def pruefe_ui12_blockaden(cfg):
    global WARNUNGEN
    blockaden = []
    ui12_pfad = cfg.get("module", [])[-1].get("ausgabe_json", "Windows_App/Logs/UI12_MASTER_ADAPTER.json")
    ui12 = load_json(ui12_pfad)
    if ui12 is None:
        blockaden.append({
            "quelle": "UI12",
            "typ": "INFO",
            "nachricht": "UI12-Master-Adapter noch nicht erzeugt. Blockaden unbekannt."
        })
        WARNUNGEN += 1
        return blockaden
    kombi = ui12.get("kombinationspruefung", {})
    for regel in kombi.get("regeln", []):
        if regel["status"] == "BLOCKADE":
            blockaden.append({
                "quelle": regel["regel_id"],
                "typ": "KRITISCH",
                "nachricht": regel["nachricht"]
            })
    return blockaden


def bestimme_entscheidung(module_status, adapter_checks, blockaden, cfg):
    alle_abgeschlossen = all(m["abgeschlossen"] for m in module_status)
    adapter_fehlt = any(not a["vorhanden"] for a in adapter_checks)
    blockaden_count = len([b for b in blockaden if b["typ"] == "KRITISCH"])
    warnungen_count = WARNUNGEN

    regeln = cfg.get("naechste_schritte_logik", {}).get("regeln", [])
    
    # Regel 1: Alles abgeschlossen, keine Blockaden
    if alle_abgeschlossen and blockaden_count == 0:
        for r in regeln:
            if "alle_module_abgeschlossen" in r.get("bedingung", ""):
                return r
    # Regel 2: Adapter fehlt
    if adapter_fehlt:
        for r in regeln:
            if "adapter_fehlt" in r.get("bedingung", ""):
                return r
    # Regel 3: Warnungen, keine Blockaden
    if warnungen_count > 0 and blockaden_count == 0:
        for r in regeln:
            if "warnungen > 0 AND blockaden == 0" in r.get("bedingung", ""):
                return r
    # Regel 4: Blockaden vorhanden
    if blockaden_count > 0:
        for r in regeln:
            if "kritische_blockaden > 0" in r.get("bedingung", ""):
                return r
    return {
        "empfehlung": "Keine eindeutige Entscheidung möglich. Manuelle Prüfung erforderlich.",
        "zulaessig": [],
        "blockiert": ["Freeze-Öffnung", "Produktivfreigabe"]
    }


def generiere_html(uebersicht, cfg):
    meta = uebersicht.get("meta", {})
    module = uebersicht.get("module", [])
    adapter = uebersicht.get("adapter", [])
    blockaden = uebersicht.get("blockaden", [])
    fehlende = uebersicht.get("fehlende_eingaben", [])
    warnungen = uebersicht.get("warnungen", [])
    entscheidung = uebersicht.get("entscheidung", {})
    grenzen = cfg.get("grenzen", {})

    def badge(status, text):
        if status == "OK":
            return f"<span class='badge badge-ok'>{text}</span>"
        if status == "WARN":
            return f"<span class='badge badge-warn'>{text}</span>"
        if status == "FEHL":
            return f"<span class='badge badge-fehler'>{text}</span>"
        return f"<span class='badge badge-info'>{text}</span>"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI13 Abnahme- und Entscheidungsübersicht</title>
<style>
:root {{ --bg:#f5f5f5; --panel:#fff; --text:#333; --ok:#28a745; --warn:#ffc107; --fehler:#dc3545; --info:#17a2b8; }}
body {{ font-family:Segoe UI, sans-serif; background:var(--bg); margin:0; padding:20px; color:var(--text); }}
.top-bar {{ background:var(--panel); padding:15px 20px; border-bottom:3px solid var(--info); margin-bottom:20px; }}
.top-bar h1 {{ margin:0; font-size:1.4rem; }}
.container {{ max-width:1200px; margin:0 auto; }}
.panel {{ background:var(--panel); border-radius:8px; padding:20px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,0.1); }}
.panel h2 {{ margin-top:0; font-size:1.1rem; border-bottom:1px solid #eee; padding-bottom:8px; }}
table {{ width:100%; border-collapse:collapse; font-size:0.9rem; }}
th, td {{ text-align:left; padding:8px; border-bottom:1px solid #eee; }}
th {{ background:#f8f9fa; font-weight:600; }}
.badge {{ display:inline-block; padding:3px 8px; border-radius:4px; font-size:0.8rem; font-weight:600; }}
.badge-ok {{ background:#d4edda; color:#155724; }}
.badge-warn {{ background:#fff3cd; color:#856404; }}
.badge-fehler {{ background:#f8d7da; color:#721c24; }}
.badge-info {{ background:#e7f3ff; color:#004085; }}
.freeze-box {{ background:#e7f3ff; border-left:4px solid var(--info); padding:12px; margin:10px 0; font-size:0.9rem; }}
.blockade-box {{ background:#f8d7da; border-left:4px solid var(--fehler); padding:12px; margin:10px 0; font-size:0.9rem; }}
.warn-box {{ background:#fff3cd; border-left:4px solid var(--warn); padding:12px; margin:10px 0; font-size:0.9rem; }}
.schritte-ok {{ color:var(--ok); font-weight:600; }}
.schritte-nein {{ color:var(--fehler); font-weight:600; }}
footer {{ text-align:center; font-size:0.8rem; color:#888; margin-top:30px; }}
</style>
</head>
<body>
<div class="top-bar">
  <h1>UI13 – Abnahme- und Entscheidungsübersicht UI08–UI12</h1>
  <p style="margin:4px 0 0 0; font-size:0.85rem; color:#666;">
    Version {meta.get('version','?')} | {meta.get('zeitstempel','')} | Demo-Modus: {meta.get('demo_modus',True)}
  </p>
</div>
<div class="container">

<div class="panel">
  <h2>Zusammenfassung</h2>
  <table>
    <tr><td>Alle Module abgeschlossen</td><td>{badge('OK' if all(m['abgeschlossen'] for m in module) else 'WARN', 'JA' if all(m['abgeschlossen'] for m in module) else 'NEIN')}</td></tr>
    <tr><td>Adapter-Daten vorhanden</td><td>{badge('OK' if all(a['vorhanden'] for a in adapter) else 'WARN', 'JA' if all(a['vorhanden'] for a in adapter) else 'NEIN')}</td></tr>
    <tr><td>Kritische Blockaden</td><td>{badge('FEHL' if len([b for b in blockaden if b['typ']=='KRITISCH'])>0 else 'OK', str(len([b for b in blockaden if b['typ']=='KRITISCH'])))}</td></tr>
    <tr><td>Warnungen</td><td>{badge('WARN' if len(warnungen)>0 else 'OK', str(len(warnungen)))}</td></tr>
  </table>
</div>

<div class="panel">
  <h2>Module UI08–UI12</h2>
  <table>
    <tr><th>Modul</th><th>Name</th><th>Commit</th><th>JSON</th><th>HTML</th><th>TXT</th><th>Status</th></tr>
"""
    for m in module[:grenzen.get("max_module_anzeigen", 20)]:
        json_ok = m["ausgaben"].get("ausgabe_json", {}).get("vorhanden", False)
        html_ok = m["ausgaben"].get("ausgabe_html", {}).get("vorhanden", False)
        txt_ok = m["ausgaben"].get("ausgabe_txt", {}).get("vorhanden", False)
        status = "Abgeschlossen" if m["abgeschlossen"] else "Unvollständig"
        badge_type = "OK" if m["abgeschlossen"] else "WARN"
        html += f"""
    <tr>
      <td>{m['modul_id']}</td>
      <td>{m['name']}</td>
      <td>{m['commit_hash']}</td>
      <td>{badge('OK' if json_ok else 'WARN', 'OK' if json_ok else 'Fehlt')}</td>
      <td>{badge('OK' if html_ok else 'WARN', 'OK' if html_ok else 'Fehlt')}</td>
      <td>{badge('OK' if txt_ok else 'WARN', 'OK' if txt_ok else 'Fehlt')}</td>
      <td>{badge(badge_type, status)}</td>
    </tr>"""
    html += """
  </table>
</div>

<div class="panel">
  <h2>Adapter-Daten</h2>
  <table>
    <tr><th>Adapter</th><th>Pfad</th><th>Vorhanden</th><th>Lesbar</th></th>Hinweis</th></tr>
"""
    for a in adapter:
        html += f"""
    <tr>
      <td>{a['name']}</td>
      <td>{a['pfad']}</td>
      <td>{badge('OK' if a['vorhanden'] else 'WARN', 'JA' if a['vorhanden'] else 'NEIN')}</td>
      <td>{badge('OK' if a['lesbar'] else 'WARN', 'JA' if a['lesbar'] else 'NEIN')}</td>
      <td>{a['hinweis'] or '-'}</td>
    </tr>"""
    html += """
  </table>
</div>
"""

    if blockaden:
        html += "<div class='panel'><h2>Kritische Blockaden (aus UI12)</h2>"
        for b in blockaden[:grenzen.get("max_blockaden_anzeigen", 20)]:
            html += f"<div class='blockade-box'><strong>[{b['quelle']}] {b['typ']}:</strong> {b['nachricht']}</div>"
        html += "</div>\n"

    if fehlende:
        html += "<div class='panel'><h2>Fehlende Eingaben</h2>"
        for f in fehlende[:grenzen.get("max_warnungen_anzeigen", 50)]:
            html += f"<div class='warn-box'><strong>{f['modul']}:</strong> {f['beschreibung']}</div>"
        html += "</div>\n"

    if warnungen:
        html += "<div class='panel'><h2>Erwartbare Warnungen</h2>"
        for w in warnungen[:grenzen.get("max_warnungen_anzeigen", 50)]:
            html += f"<div class='warn-box'><strong>{w['modul']}:</strong> {w['beschreibung']}</div>"
        html += "</div>\n"

    html += """
<div class="panel">
  <h2>Entscheidungsempfehlung</h2>
"""
    empfehlung = entscheidung.get("empfehlung", "Keine Empfehlung verfügbar.")
    html += f"  <p style='font-size:1.05rem; font-weight:600; color:#333;'>{empfehlung}</p>\n"
    
    zulaessig = entscheidung.get("zulaessig", [])
    blockiert = entscheidung.get("blockiert", [])
    
    if zulaessig:
        html += "  <p><strong>Zulässige nächste Schritte:</strong></p><ul>\n"
        for s in zulaessig[:grenzen.get("max_schritte_anzeigen", 15)]:
            html += f"    <li class='schritte-ok'>✓ {s}</li>\n"
        html += "  </ul>\n"
    
    if blockiert:
        html += "  <p><strong>Blockierte Schritte (erfordern Freeze-Öffnung oder weitere Maßnahmen):</strong></p><ul>\n"
        for s in blockiert[:grenzen.get("max_schritte_anzeigen", 15)]:
            html += f"    <li class='schritte-nein'>✗ {s}</li>\n"
        html += "  </ul>\n"
    
    html += """
</div>

<div class="panel">
  <h2>Freeze-Grenzen</h2>
  <div class="freeze-box">
    <strong>UI03–UI07b sind eingefroren.</strong> UI13 darf diese nicht berühren.
    <ul>
      <li>Berührt UI03–UI07b: <strong>NEIN</strong></li>
      <li>Nur lesend auf UI08–UI12 Ausgaben: <strong>JA</strong></li>
      <li>Neue Dateien erzeugt: <strong>JA</strong> (nur UI13-Ausgaben)</li>
    </ul>
  </div>
</div>

<footer>
  <p>ALIN Legal – UI13 Abnahme- und Entscheidungsübersicht | Nur Demo/Musterdaten | Keine Produktivfreigabe</p>
</footer>
</div>
</body>
</html>"""
    return html


def hauptlauf():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI13 – ABNAHME- UND ENTSCHEIDUNGSUEBERSICHT UI08–UI12")
    print("=" * 60)

    cfg_pfad = "Config/ui13_abnahme_entscheidungsuebersicht_v1.json"
    cfg = load_json(cfg_pfad)
    if cfg is None:
        print("[FEHLER] Config nicht ladbar. Abbruch.")
        FEHLER += 1
        return

    # Sperrregister prüfen
    sperr = pruefe_sperrregister("UI13")
    if sperr:
        print(f"[FEHLER] UI13 ist im Sperrregister gesperrt: {sperr.get('grund','Unbekannt')}")
        FEHLER += 1
        return
    print("[OK] Sperrregister: UI13 nicht gesperrt.")

    # Module prüfen
    module_status = []
    fehlende_eingaben = []
    for modul in cfg.get("module", []):
        status = pruefe_modul_status(modul, cfg)
        module_status.append(status)
        if not status["abgeschlossen"]:
            fehlende_eingaben.append({
                "modul": modul["modul_id"],
                "beschreibung": f"Modul {modul['modul_id']} nicht vollständig abgeschlossen. Fehlende Ausgaben: {[k for k,v in status['ausgaben'].items() if not v['vorhanden']]}",
                "typ": "fehlend"
            })

    # Adapter prüfen
    adapter_checks = pruefe_adapter_daten(cfg)

    # UI12 Blockaden prüfen
    blockaden = pruefe_ui12_blockaden(cfg)

    # Warnungen sammeln
    warnungen = []
    for modul in cfg.get("module", []):
        # Demo-Modus Warnung
        demo = cfg.get("demo_modus", {})
        if not demo.get("produktiv_freigegeben", False):
            warnungen.append({
                "modul": modul["modul_id"],
                "beschreibung": "Demo-Modus aktiv – keine Produktivfreigabe."
            })
    # Adapter fehlt Warnung
    for a in adapter_checks:
        if not a["vorhanden"]:
            warnungen.append({
                "modul": a["name"],
                "beschreibung": f"Adapter fehlt: {a['pfad']}. UI12 liefert nur Musterdaten."
            })

    # Entscheidung bestimmen
    entscheidung = bestimme_entscheidung(module_status, adapter_checks, blockaden, cfg)

    # Übersicht JSON erstellen
    uebersicht = {
        "meta": {
            "modul_id": "UI13",
            "name": "Abnahme- und Entscheidungsübersicht UI08–UI12",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "demo_modus": cfg.get("demo_modus", {}).get("produktiv_freigegeben", False) is False
        },
        "module": module_status,
        "adapter": adapter_checks,
        "blockaden": blockaden,
        "fehlende_eingaben": fehlende_eingaben,
        "warnungen": warnungen,
        "entscheidung": entscheidung,
        "freeze_grenzen": cfg.get("freeze_grenzen", {})
    }

    # HTML schreiben
    html_pfad = cfg.get("ausgabe", {}).get("uebersicht_html", "Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT.html")
    try:
        os.makedirs(os.path.dirname(html_pfad), exist_ok=True)
        with open(html_pfad, "w", encoding="utf-8") as f:
            f.write(generiere_html(uebersicht, cfg))
        print(f"[OK] HTML geschrieben: {html_pfad}")
    except Exception as e:
        print(f"[FEHLER] HTML fehlgeschlagen: {e}")
        FEHLER += 1

    # JSON schreiben
    json_pfad = cfg.get("ausgabe", {}).get("uebersicht_json", "Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT.json")
    try:
        os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
        with open(json_pfad, "w", encoding="utf-8") as f:
            json.dump(uebersicht, f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON geschrieben: {json_pfad}")
    except Exception as e:
        print(f"[FEHLER] JSON fehlgeschlagen: {e}")
        FEHLER += 1

    # Bericht schreiben
    bericht_pfad = cfg.get("ausgabe", {}).get("bericht", "Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT_BERICHT.txt")
    try:
        os.makedirs(os.path.dirname(bericht_pfad), exist_ok=True)
        with open(bericht_pfad, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("UI13 – ABNAHME- UND ENTSCHEIDUNGSUEBERSICHT UI08–UI12\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Zeitstempel: {uebersicht['meta']['zeitstempel']}\n")
            f.write(f"Demo-Modus: {uebersicht['meta']['demo_modus']}\n\n")
            f.write("MODULE\n")
            f.write("-" * 40 + "\n")
            for m in module_status:
                f.write(f"{m['modul_id']}: {m['name']} – {'Abgeschlossen' if m['abgeschlossen'] else 'Unvollständig'}\n")
            f.write("\nADAPTER\n")
            f.write("-" * 40 + "\n")
            for a in adapter_checks:
                f.write(f"{a['name']}: {'Vorhanden' if a['vorhanden'] else 'Fehlt'}\n")
            f.write("\nBLOCKADEN\n")
            f.write("-" * 40 + "\n")
            if blockaden:
                for b in blockaden:
                    f.write(f"[{b['quelle']}] {b['typ']}: {b['nachricht']}\n")
            else:
                f.write("Keine kritischen Blockaden.\n")
            f.write("\nENTSCHEIDUNG\n")
            f.write("-" * 40 + "\n")
            f.write(f"Empfehlung: {entscheidung.get('empfehlung','')}\n")
            f.write("\nZulässig:\n")
            for s in entscheidung.get("zulaessig", []):
                f.write(f"  ✓ {s}\n")
            f.write("\nBlockiert:\n")
            for s in entscheidung.get("blockiert", []):
                f.write(f"  ✗ {s}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("ENDE BERICHT\n")
        print(f"[OK] Bericht geschrieben: {bericht_pfad}")
    except Exception as e:
        print(f"[FEHLER] Bericht fehlgeschlagen: {e}")
        FEHLER += 1

    print("\n" + "=" * 60)
    print(f"UI13 abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI13 SELBSTTEST =====================================")

    def t(bez, bed):
        global FEHLER
        if not bed:
            print(f"[SELBSTTEST FEHLER] {bez}")
            FEHLER += 1
        else:
            print(f"[SELBSTTEST OK] {bez}")

    # Test 1: Config laden
    cfg = load_json("Config/ui13_abnahme_entscheidungsuebersicht_v1.json")
    t("Config ladbar", cfg is not None)

    # Test 2: Module definiert
    t("Module UI08–UI12 definiert", len(cfg.get("module", [])) >= 5)

    # Test 3: Demo-Modus
    demo = cfg.get("demo_modus", {})
    t("Demo-Modus aktiv", demo.get("produktiv_freigegeben") is False)
    t("Nur Musterdaten", demo.get("nur_musterdaten") is True)

    # Test 4: Sperrregister
    t("Sperrregister-Prüfung aktiv", cfg.get("sperrregister_pruefung", {}).get("aktiv") is True)

    # Test 5: Ausgabepfade
    ausgabe = cfg.get("ausgabe", {})
    t("HTML-Ausgabe definiert", bool(ausgabe.get("uebersicht_html")))
    t("JSON-Ausgabe definiert", bool(ausgabe.get("uebersicht_json")))
    t("Bericht definiert", bool(ausgabe.get("bericht")))

    # Test 6: Freeze-Grenzen
    freeze = cfg.get("freeze_grenzen", {})
    t("Freeze: beruehrt_ui03_ui07b=false", freeze.get("beruehrt_ui03_ui07b") is False)
    t("Freeze: nur_lesend=true", freeze.get("nur_lesend") is True)

    # Test 7: Entscheidungslogik
    t("Entscheidungsregeln vorhanden", len(cfg.get("naechste_schritte_logik", {}).get("regeln", [])) > 0)

    # Test 8: Grenzen
    grenzen = cfg.get("grenzen", {})
    t("max_module definiert", grenzen.get("max_module_anzeigen", 0) > 0)

    print(f"\nSELBSTTEST ENDE – Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        selbsttest()
    else:
        hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
