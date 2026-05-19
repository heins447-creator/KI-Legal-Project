#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI12 – Kombinierter Master-Adapter
Führt UI10 (Profil-Leseadapter) und UI11 (Register-Leseadapter) zusammen.
Liefert: Profilstatus, Grundschalter, Sperrstatus, Ressourcenstatus, Toolstatus,
         Quellenstatus, Lizenzstatus, Update-Alter, Modulstatus, kritische Blockaden,
         Warnungen, zulässige nächste Schritte.

Rote Linie: produktiv_freigegeben=false, nur_musterdaten=true, echte_daten_erlaubt=false
Berührt UI03–UI07b: NEIN (nur lesend auf UI09, UI10, UI11 Ausgaben)
"""

import json
import os
import sys
from datetime import datetime

FEHLER = 0
WARNUNGEN = 0


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNUNG] Kann {path} nicht laden: {e}")
        global WARNUNGEN
        WARNUNGEN += 1
        return None


def pruefe_sperrregister(modul_id):
    sperr_pfad = "ALIN_Neustart_Core/01_Register/sperrregister.json"
    try:
        with open(sperr_pfad, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for eintrag in reg.get("eintraege", []):
            if eintrag.get("modul_id") == modul_id and eintrag.get("gesperrt", False):
                return eintrag
    except Exception as e:
        print(f"[WARNUNG] Sperrregister nicht lesbar: {e}")
        global WARNUNGEN
        WARNUNGEN += 1
    return None


def lade_ui10_adapter(cfg):
    pfad = cfg.get("eingabe_adapter", {}).get("ui10_profil_adapter", "Windows_App/Logs/UI10_PROFIL_ADAPTER.json")
    adapter = load_json(pfad)
    if adapter is None:
        print("[INFO] UI10-Adapter nicht gefunden – verwende Musterdaten.")
        return {
            "profil": {"status": "unbekannt", "felder": {}},
            "grundschalter": {},
            "konsistenz": {"regeln": []},
            "meta": {"demo_modus": True}
        }
    return adapter


def lade_ui11_adapter(cfg):
    pfad = cfg.get("eingabe_adapter", {}).get("ui11_register_adapter", "Windows_App/Logs/UI11_REGISTER_ADAPTER.json")
    adapter = load_json(pfad)
    if adapter is None:
        print("[INFO] UI11-Adapter nicht gefunden – verwende Musterdaten.")
        return {
            "register_status": {},
            "konsistenz": {"regeln": []},
            "meta": {"demo_modus": True}
        }
    return adapter


def lade_ui09_grundschalter(cfg):
    pfad = cfg.get("eingabe_adapter", {}).get("ui09_grundschalter", "Windows_App/Logs/UI09_GRUNDSCHALTER.json")
    gs = load_json(pfad)
    if gs is None:
        print("[INFO] UI09-Grundschalter nicht gefunden – verwende Musterdaten.")
        return {
            "GS01": False, "GS02": False, "GS03": False, "GS04": False,
            "GS05": False, "GS06": False, "GS07": False, "GS08": False
        }
    return gs


def lade_ui09_profilfelder(cfg):
    pfad = cfg.get("eingabe_adapter", {}).get("ui09_profilfelder", "Windows_App/Logs/UI09_PROFILFELDER.json")
    pf = load_json(pfad)
    if pf is None:
        print("[INFO] UI09-Profilfelder nicht gefunden – verwende Musterdaten.")
        return {"felder": {}}
    return pf


def wende_kombinationsregeln(ui10, ui11, grundschalter, profilfelder, regeln, grenzen):
    global WARNUNGEN
    ergebnisse = []
    blockaden = 0

    # KOMB_01: Profil-Register-Konsistenz
    felder = profilfelder.get("felder", {})
    reg_status = ui11.get("register_status", {})
    for feld_id, feld in felder.items():
        if feld.get("status") == "aktiv":
            register_ok = False
            for reg_name, reg_data in reg_status.items():
                if isinstance(reg_data, dict) and reg_data.get("eintrag_vorhanden"):
                    register_ok = True
                    break
            if not register_ok:
                ergebnisse.append({
                    "regel_id": "KOMB_01",
                    "status": "WARNUNG",
                    "nachricht": f"Profilfeld {feld_id} aktiv, aber kein passender Register-Eintrag."
                })
                WARNUNGEN += 1

    # KOMB_02: Sperrstatus dominiert Profil
    sperr = reg_status.get("sperrregister", {})
    if sperr.get("gesperrt", False):
        ergebnisse.append({
            "regel_id": "KOMB_02",
            "status": "BLOCKADE",
            "nachricht": "Sperrregister blockiert Modul – Grundschalter ignoriert."
        })
        blockaden += 1

    # KOMB_03: Lizenz-Register-Abgleich
    lizenz = reg_status.get("lizenzregister", {})
    lizenz_status = lizenz.get("status", "unbekannt")
    if lizenz_status in ["ungueltig", "abgelaufen"]:
        ergebnisse.append({
            "regel_id": "KOMB_03",
            "status": "BLOCKADE",
            "nachricht": f"Ungültige oder abgelaufene Lizenz ({lizenz_status}) blockiert abhängige Module."
        })
        blockaden += 1

    # KOMB_04: Update-Alter-Warnung
    update_reg = reg_status.get("update_register", {})
    alter_tage = update_reg.get("alter_tage", 0)
    if alter_tage > grenzen.get("update_alter_kritisch_tage", 180):
        ergebnisse.append({
            "regel_id": "KOMB_04",
            "status": "BLOCKADE",
            "nachricht": f"Modul ist seit {alter_tage} Tagen nicht aktualisiert (kritisch)."
        })
        blockaden += 1
    elif alter_tage > grenzen.get("update_alter_warnschwelle_tage", 90):
        ergebnisse.append({
            "regel_id": "KOMB_04",
            "status": "WARNUNG",
            "nachricht": f"Modul ist seit {alter_tage} Tagen nicht aktualisiert."
        })
        WARNUNGEN += 1

    # KOMB_05: Ressourcen-Tool-Konsistenz
    modul = reg_status.get("modulregister", {})
    benoetigte_res = modul.get("benoetigte_ressourcen", [])
    benoetigte_tools = modul.get("benoetigte_tools", [])
    ressourcen = reg_status.get("ressourcenregister", {})
    tools = reg_status.get("toolregister", {})
    for res in benoetigte_res:
        if not ressourcen.get(res, {}).get("aktiv", False):
            ergebnisse.append({
                "regel_id": "KOMB_05",
                "status": "WARNUNG",
                "nachricht": f"Modul benötigt Ressource '{res}', die nicht aktiv ist."
            })
            WARNUNGEN += 1
    for tool in benoetigte_tools:
        if not tools.get(tool, {}).get("aktiv", False):
            ergebnisse.append({
                "regel_id": "KOMB_05",
                "status": "WARNUNG",
                "nachricht": f"Modul benötigt Tool '{tool}', das nicht aktiv ist."
            })
            WARNUNGEN += 1

    # KOMB_06: Skill-Quellen-Konsistenz
    benoetigte_skills = modul.get("benoetigte_skills", [])
    benoetigte_quellen = modul.get("benoetigte_quellen", [])
    skills = reg_status.get("skillregister", {})
    quellen = reg_status.get("quellen_adapter_register", {})
    for skill in benoetigte_skills:
        if not skills.get(skill, {}).get("vorhanden", False):
            ergebnisse.append({
                "regel_id": "KOMB_06",
                "status": "WARNUNG",
                "nachricht": f"Modul benötigt Skill '{skill}', der nicht verfügbar ist."
            })
            WARNUNGEN += 1
    for quelle in benoetigte_quellen:
        if not quellen.get(quelle, {}).get("vorhanden", False):
            ergebnisse.append({
                "regel_id": "KOMB_06",
                "status": "WARNUNG",
                "nachricht": f"Modul benötigt Quelle '{quelle}', die nicht verfügbar ist."
            })
            WARNUNGEN += 1

    # KOMB_07: Demo-Modus-Blockade
    demo = ui10.get("meta", {}).get("demo_modus", True)
    if demo:
        for reg in ergebnisse:
            if reg["status"] in ["BLOCKADE"] and reg["regel_id"] != "KOMB_07":
                ergebnisse.append({
                    "regel_id": "KOMB_07",
                    "status": "BLOCKADE",
                    "nachricht": "Demo-Modus: Kritische oder hochriskante Schritte blockiert."
                })
                blockaden += 1
                break

    # KOMB_08: Grundschalter-Gesamtausschluss
    if not grundschalter.get("GS01", False) or not grundschalter.get("GS08", False):
        ergebnisse.append({
            "regel_id": "KOMB_08",
            "status": "BLOCKADE",
            "nachricht": "Zentraler Grundschalter (GS01 oder GS08) blockiert Systemfunktion."
        })
        blockaden += 1

    return {"regeln": ergebnisse, "blockaden": blockaden}


def bestimme_naechste_schritte(kombination, naechste_schritte_logik):
    blockaden = kombination.get("blockaden", 0)
    warnungen = sum(1 for r in kombination.get("regeln", []) if r["status"] == "WARNUNG")

    for regel in naechste_schritte_logik.get("regeln", []):
        bedingung = regel.get("bedingung", "")
        if "kritische_blockaden == 0 AND warnungen == 0" in bedingung and blockaden == 0 and warnungen == 0:
            return regel
        if "kritische_blockaden == 0 AND warnungen > 0" in bedingung and blockaden == 0 and warnungen > 0:
            return regel
        if "kritische_blockaden > 0" in bedingung and blockaden > 0:
            return regel
    return {"schritte": [], "hinweis": "Keine passende Regel gefunden."}


def erstelle_master_adapter(ui10, ui11, grundschalter, profilfelder, kombination, naechste_schritte, cfg):
    reg_status = ui11.get("register_status", {})
    adapter = {
        "meta": {
            "modul_id": "UI12",
            "name": "Kombinierter Master-Adapter",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "demo_modus": cfg.get("demo_modus", {}).get("produktiv_freigegeben", False) is False,
            "quellen": {
                "ui10": cfg.get("eingabe_adapter", {}).get("ui10_profil_adapter"),
                "ui11": cfg.get("eingabe_adapter", {}).get("ui11_register_adapter"),
                "ui09_grundschalter": cfg.get("eingabe_adapter", {}).get("ui09_grundschalter"),
                "ui09_profilfelder": cfg.get("eingabe_adapter", {}).get("ui09_profilfelder")
            }
        },
        "profilstatus": {
            "profilfelder": profilfelder.get("felder", {}),
            "grundschalter": grundschalter
        },
        "registerstatus": {
            "sperrstatus": reg_status.get("sperrregister", {}),
            "ressourcenstatus": reg_status.get("ressourcenregister", {}),
            "toolstatus": reg_status.get("toolregister", {}),
            "quellenstatus": reg_status.get("quellen_adapter_register", {}),
            "lizenzstatus": reg_status.get("lizenzregister", {}),
            "update_alter": reg_status.get("update_register", {}),
            "modulstatus": reg_status.get("modulregister", {}),
            "skillstatus": reg_status.get("skillregister", {})
        },
        "kombinationspruefung": kombination,
        "naechste_schritte": naechste_schritte,
        "zusammenfassung": {
            "kritische_blockaden": kombination.get("blockaden", 0),
            "warnungen": sum(1 for r in kombination.get("regeln", []) if r["status"] == "WARNUNG"),
            "gesamtregeln": len(kombination.get("regeln", [])),
            "system_bereit": kombination.get("blockaden", 0) == 0
        }
    }
    return adapter


def generiere_html(adapter, cfg):
    grenzen = cfg.get("grenzen", {})
    max_warn = grenzen.get("max_warnungen_anzeigen", 50)
    max_block = grenzen.get("max_blockaden_anzeigen", 20)
    max_schritte = grenzen.get("max_schritte_anzeigen", 15)

    meta = adapter.get("meta", {})
    profil = adapter.get("profilstatus", {})
    reg = adapter.get("registerstatus", {})
    kombi = adapter.get("kombinationspruefung", {})
    schritte = adapter.get("naechste_schritte", {})
    zusammenfassung = adapter.get("zusammenfassung", {})

    def badge(status, text):
        if status == "BLOCKADE":
            return f"<span class='badge badge-fehler'>{text}</span>"
        if status == "WARNUNG":
            return f"<span class='badge badge-warn'>{text}</span>"
        return f"<span class='badge badge-ok'>{text}</span>"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI12 Master-Adapter</title>
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
.info-box {{ background:#e7f3ff; border-left:4px solid var(--info); padding:12px; margin:10px 0; font-size:0.9rem; }}
.blockade-box {{ background:#f8d7da; border-left:4px solid var(--fehler); padding:12px; margin:10px 0; font-size:0.9rem; }}
.schritte-list {{ list-style:none; padding:0; }}
.schritte-list li {{ padding:6px 0; border-bottom:1px solid #f0f0f0; }}
footer {{ text-align:center; font-size:0.8rem; color:#888; margin-top:30px; }}
</style>
</head>
<body>
<div class="top-bar">
  <h1>UI12 – Kombinierter Master-Adapter</h1>
  <p style="margin:4px 0 0 0; font-size:0.85rem; color:#666;">
    Version {meta.get('version','?')} | {meta.get('zeitstempel','')} | Demo-Modus: {meta.get('demo_modus',True)}
  </p>
</div>
<div class="container">

<div class="panel">
  <h2>Zusammenfassung</h2>
  <table>
    <tr><td>System bereit</td><td>{badge('OK' if zusammenfassung.get('system_bereit') else 'BLOCKADE', 'JA' if zusammenfassung.get('system_bereit') else 'NEIN')}</td></tr>
    <tr><td>Kritische Blockaden</td><td>{badge('BLOCKADE' if zusammenfassung.get('kritische_blockaden',0)>0 else 'OK', str(zusammenfassung.get('kritische_blockaden',0)))}</td></tr>
    <tr><td>Warnungen</td><td>{badge('WARNUNG' if zusammenfassung.get('warnungen',0)>0 else 'OK', str(zusammenfassung.get('warnungen',0)))}</td></tr>
    <tr><td>Geprüfte Regeln</td><td>{zusammenfassung.get('gesamtregeln',0)}</td></tr>
  </table>
</div>

<div class="panel">
  <h2>Profilstatus (UI09)</h2>
  <table>
    <tr><th>Grundschalter</th><th>Wert</th></tr>
"""
    for gs_id, gs_wert in profil.get("grundschalter", {}).items():
        html += f"    <tr><td>{gs_id}</td><td>{badge('OK' if gs_wert else 'BLOCKADE', str(gs_wert))}</td></tr>\n"
    html += """  </table>
</div>

<div class="panel">
  <h2>Registerstatus (UI11)</h2>
  <table>
    <tr><th>Register</th><th>Status</th></tr>
"""
    for reg_name, reg_data in reg.items():
        status = reg_data.get("status", "unbekannt") if isinstance(reg_data, dict) else "unbekannt"
        html += f"    <tr><td>{reg_name}</td><td>{badge('OK' if status=='aktiv' else 'WARNUNG', status)}</td></tr>\n"
    html += """  </table>
</div>

<div class="panel">
  <h2>Kombinationsprüfung</h2>
"""
    regeln = kombi.get("regeln", [])
    blockaden_list = [r for r in regeln if r["status"] == "BLOCKADE"][:max_block]
    warnungen_list = [r for r in regeln if r["status"] == "WARNUNG"][:max_warn]

    if blockaden_list:
        html += "<div class='blockade-box'><strong>Kritische Blockaden:</strong><ul>"
        for r in blockaden_list:
            html += f"<li>[{r['regel_id']}] {r['nachricht']}</li>"
        html += "</ul></div>"
    if warnungen_list:
        html += "<div class='info-box'><strong>Warnungen:</strong><ul>"
        for r in warnungen_list:
            html += f"<li>[{r['regel_id']}] {r['nachricht']}</li>"
        html += "</ul></div>"
    if not blockaden_list and not warnungen_list:
        html += "<div class='info-box'>Keine Blockaden oder Warnungen.</div>"
    html += "</div>\n"

    html += """<div class="panel">
  <h2>Zulässige nächste Schritte</h2>
  <p style="font-size:0.9rem; color:#666; margin-bottom:10px;">""" + schritte.get("hinweis", "") + """</p>
  <ul class="schritte-list">
"""
    for schritt in schritte.get("schritte", [])[:max_schritte]:
        html += f"    <li>{schritt}</li>\n"
    html += """  </ul>
</div>

<footer>
  <p>ALIN Legal – UI12 Master-Adapter | Nur Demo/Musterdaten | Keine Produktivfreigabe</p>
</footer>
</div>
</body>
</html>"""
    return html


def generiere_json(adapter, cfg):
    pfad = cfg.get("ausgabe", {}).get("master_adapter_json", "Windows_App/Logs/UI12_MASTER_ADAPTER.json")
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(adapter, f, ensure_ascii=False, indent=2)
        print(f"[OK] Master-Adapter JSON geschrieben: {pfad}")
    except Exception as e:
        print(f"[FEHLER] JSON-Ausgabe fehlgeschlagen: {e}")
        global FEHLER
        FEHLER += 1


def generiere_konsistenzlog(kombination, cfg):
    pfad = cfg.get("ausgabe", {}).get("konsistenzlog", "Windows_App/Logs/UI12_KONSISTENZLOG.json")
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(kombination, f, ensure_ascii=False, indent=2)
        print(f"[OK] Konsistenzlog geschrieben: {pfad}")
    except Exception as e:
        print(f"[FEHLER] Konsistenzlog fehlgeschlagen: {e}")
        global FEHLER
        FEHLER += 1


def generiere_bericht(adapter, cfg):
    pfad = cfg.get("ausgabe", {}).get("bericht", "Windows_App/Logs/UI12_MASTER_ADAPTER_BERICHT.txt")
    meta = adapter.get("meta", {})
    zusammenfassung = adapter.get("zusammenfassung", {})
    kombi = adapter.get("kombinationspruefung", {})
    schritte = adapter.get("naechste_schritte", {})

    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("UI12 – KOMBINIERTER MASTER-ADAPTER BERICHT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Modul:      {meta.get('name','UI12')}\n")
            f.write(f"Version:    {meta.get('version','?')}\n")
            f.write(f"Zeitstempel: {meta.get('zeitstempel','')}\n")
            f.write(f"Demo-Modus: {meta.get('demo_modus',True)}\n\n")
            f.write("ZUSAMMENFASSUNG\n")
            f.write("-" * 40 + "\n")
            f.write(f"System bereit:         {zusammenfassung.get('system_bereit',False)}\n")
            f.write(f"Kritische Blockaden:   {zusammenfassung.get('kritische_blockaden',0)}\n")
            f.write(f"Warnungen:             {zusammenfassung.get('warnungen',0)}\n")
            f.write(f"Geprüfte Regeln:       {zusammenfassung.get('gesamtregeln',0)}\n\n")
            f.write("KOMBINATIONSPRÜFUNG\n")
            f.write("-" * 40 + "\n")
            for r in kombi.get("regeln", []):
                f.write(f"[{r['status']}] {r['regel_id']}: {r['nachricht']}\n")
            f.write("\nNÄCHSTE SCHRITTE\n")
            f.write("-" * 40 + "\n")
            f.write(f"Hinweis: {schritte.get('hinweis','')}\n")
            for s in schritte.get("schritte", []):
                f.write(f"  - {s}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("ENDE BERICHT\n")
        print(f"[OK] Bericht geschrieben: {pfad}")
    except Exception as e:
        print(f"[FEHLER] Bericht fehlgeschlagen: {e}")
        global FEHLER
        FEHLER += 1


def hauptlauf():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI12 – KOMBINIERTER MASTER-ADAPTER")
    print("=" * 60)

    cfg_pfad = "Config/ui12_master_adapter_v1.json"
    cfg = load_json(cfg_pfad)
    if cfg is None:
        print("[FEHLER] Konfiguration nicht ladbar. Abbruch.")
        FEHLER += 1
        return

    # Sperrregister prüfen
    sperr = pruefe_sperrregister("UI12")
    if sperr:
        print(f"[FEHLER] UI12 ist im Sperrregister gesperrt: {sperr.get('grund','Unbekannt')}")
        FEHLER += 1
        return
    print("[OK] Sperrregister: UI12 nicht gesperrt.")

    # Eingaben laden
    ui10 = lade_ui10_adapter(cfg)
    ui11 = lade_ui11_adapter(cfg)
    grundschalter = lade_ui09_grundschalter(cfg)
    profilfelder = lade_ui09_profilfelder(cfg)

    # Kombinationsregeln anwenden
    regeln = cfg.get("kombinationsregeln", [])
    grenzen = cfg.get("grenzen", {})
    kombination = wende_kombinationsregeln(ui10, ui11, grundschalter, profilfelder, regeln, grenzen)

    # Nächste Schritte bestimmen
    naechste_schritte = bestimme_naechste_schritte(kombination, cfg.get("naechste_schritte_logik", {}))

    # Master-Adapter erstellen
    adapter = erstelle_master_adapter(ui10, ui11, grundschalter, profilfelder, kombination, naechste_schritte, cfg)

    # Ausgaben generieren
    generiere_json(adapter, cfg)
    generiere_konsistenzlog(kombination, cfg)
    generiere_bericht(adapter, cfg)

    # HTML generieren
    html = generiere_html(adapter, cfg)
    html_pfad = cfg.get("ausgabe", {}).get("master_adapter_html", "Windows_App/Logs/UI12_MASTER_ADAPTER.html")
    try:
        os.makedirs(os.path.dirname(html_pfad), exist_ok=True)
        with open(html_pfad, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] HTML geschrieben: {html_pfad}")
    except Exception as e:
        print(f"[FEHLER] HTML-Ausgabe fehlgeschlagen: {e}")
        FEHLER += 1

    print("\n" + "=" * 60)
    print(f"UI12 Master-Adapter abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI12 MASTER-ADAPTER SELBSTTEST =====================================")

    def t(bez, bed):
        global FEHLER
        if not bed:
            print(f"[SELBSTTEST FEHLER] {bez}")
            FEHLER += 1
        else:
            print(f"[SELBSTTEST OK] {bez}")

    # Test 1: Config laden
    cfg = load_json("Config/ui12_master_adapter_v1.json")
    t("Config ladbar", cfg is not None)

    # Test 2: Kombinationsregeln vorhanden
    t("Kombinationsregeln vorhanden", len(cfg.get("kombinationsregeln", [])) > 0)

    # Test 3: Demo-Modus gesetzt
    demo = cfg.get("demo_modus", {})
    t("Demo-Modus aktiv", demo.get("produktiv_freigegeben") is False)
    t("Nur Musterdaten", demo.get("nur_musterdaten") is True)

    # Test 4: Sperrregister-Prüfung aktiv
    t("Sperrregister-Prüfung aktiv", cfg.get("sperrregister_pruefung", {}).get("aktiv") is True)

    # Test 5: Ausgabepfade definiert
    ausgabe = cfg.get("ausgabe", {})
    t("JSON-Ausgabe definiert", bool(ausgabe.get("master_adapter_json")))
    t("HTML-Ausgabe definiert", bool(ausgabe.get("master_adapter_html")))
    t("Bericht definiert", bool(ausgabe.get("bericht")))

    # Test 6: Nächste-Schritte-Logik vorhanden
    t("Nächste-Schritte-Logik vorhanden", len(cfg.get("naechste_schritte_logik", {}).get("regeln", [])) > 0)

    # Test 7: Grenzen definiert
    grenzen = cfg.get("grenzen", {})
    t("Update-Alter-Warnschwelle definiert", grenzen.get("update_alter_warnschwelle_tage", 0) > 0)
    t("Update-Alter-Kritisch definiert", grenzen.get("update_alter_kritisch_tage", 0) > 0)

    print(f"\nSELBSTTEST ENDE – Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        selbsttest()
    else:
        hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
