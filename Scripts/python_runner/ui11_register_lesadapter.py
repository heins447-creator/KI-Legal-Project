#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI11 – Register-Leseadapter
Liest alle 8 zentralen Register, prueft Konsistenz,
stellt Adapter-JSON fuer Module ausserhalb des Freeze bereit.
"""

import json, os, sys
from datetime import datetime, timedelta

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

def lade_register(name, cfg):
    """Laedt ein Register aus der Config-Pfadangabe."""
    pfad = cfg.get("abhaengigkeiten", {}).get(name, "")
    if not pfad:
        return None
    if not os.path.exists(pfad):
        print(f"[WARN] Register nicht gefunden: {pfad}")
        global WARNUNGEN
        WARNUNGEN += 1
        return None
    return load_json(pfad)

def analysiere_register(register_name, daten):
    """Erstellt eine Zusammenfassung eines Registers."""
    if not daten:
        return {"name": register_name, "eintraege": 0, "warnungen": 0, "gesperrt": 0, "status": "nicht_gefunden"}
    
    eintraege = daten.get("eintraege", [])
    warnungen = 0
    gesperrt = 0
    
    for e in eintraege:
        if "warnungen" in e and e["warnungen"]:
            warnungen += len(e["warnungen"])
        if e.get("gesperrt"):
            gesperrt += 1
    
    return {
        "name": register_name,
        "eintraege": len(eintraege),
        "warnungen": warnungen,
        "gesperrt": gesperrt,
        "status": "ok"
    }

def pruefe_konsistenz(register_daten, regeln):
    """Prueft Konsistenzregeln zwischen Registern."""
    fehler = []
    
    sperr = register_daten.get("sperrregister", {})
    modul = register_daten.get("modulregister", {})
    tool = register_daten.get("toolregister", {})
    lizenz = register_daten.get("lizenzregister", {})
    ressourcen = register_daten.get("ressourcenregister", {})
    update = register_daten.get("update_register", {})
    quellen = register_daten.get("quellen_adapter_register", {})
    
    for r in regeln:
        rid = r["regel_id"]
        schwere = r.get("schwere", "WARNUNG")
        
        # REG_KONS_01: Gesperrte Module existieren im Modulregister
        if rid == "REG_KONS_01" and sperr and modul:
            sperr_ids = {e.get("modul_id") for e in sperr.get("eintraege", []) if e.get("gesperrt")}
            modul_ids = {e.get("modul_id") for e in modul.get("eintraege", [])}
            fehlend = sperr_ids - modul_ids
            if fehlend:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": f"Gesperrte Module nicht im Modulregister: {', '.join(fehlend)}"})
        
        # REG_KONS_02: Tools haben Lizenzen
        if rid == "REG_KONS_02" and tool and lizenz:
            tool_namen = {e.get("tool_id", e.get("name", "")) for e in tool.get("eintraege", [])}
            lizenz_namen = {e.get("tool_id", e.get("name", "")) for e in lizenz.get("eintraege", [])}
            fehlend = tool_namen - lizenz_namen
            if fehlend and "" not in fehlend:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": f"Tools ohne Lizenz: {', '.join(fehlend)}"})
        
        # REG_KONS_03: Modul-Ressourcen existieren
        if rid == "REG_KONS_03" and modul and ressourcen:
            ressourcen_ids = {e.get("ressourcen_id", e.get("id", "")) for e in ressourcen.get("eintraege", [])}
            fehlende_ressourcen = []
            for m in modul.get("eintraege", []):
                for res in m.get("benoetigte_ressourcen", []):
                    if res not in ressourcen_ids:
                        fehlende_ressourcen.append(f"{m.get('modul_id', '?')}.{res}")
            if fehlende_ressourcen:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": f"Fehlende Ressourcen: {', '.join(fehlende_ressourcen[:5])}"})
        
        # REG_KONS_04: Update-Register nicht aelter als 90 Tage
        if rid == "REG_KONS_04" and update:
            cutoff = datetime.now() - timedelta(days=90)
            alte = 0
            for e in update.get("eintraege", []):
                letzte = e.get("letzte_pruefung", "")
                if letzte:
                    try:
                        if datetime.fromisoformat(letzte.replace("Z", "+00:00")) < cutoff:
                            alte += 1
                    except Exception:
                        pass
            if alte > 0:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": f"{alte} Update-Eintraege aelter als 90 Tage"})
        
        # REG_KONS_05: Quellen-Adapter hat EU-Eintrag
        if rid == "REG_KONS_05" and quellen:
            eu_eintraege = [e for e in quellen.get("eintraege", []) if "EU" in e.get("region", "") or "europa" in e.get("region", "").lower()]
            if not eu_eintraege:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": "Kein EU-Quelleneintrag im Quellen-Adapter-Register"})
    
    return fehler

def erstelle_adapter(register_daten, analysen, konsistenz, cfg):
    """Erstellt das Adapter-JSON."""
    adapter = {
        "adapter_id": "UI11_REGISTER_ADAPTER",
        "timestamp": datetime.now().isoformat(),
        "quelle": "ALIN_Neustart_Core/01_Register",
        "register_anzahl": 8,
        "freeze_kompatibilitaet": {
            "beruehrt_ui03_ui07b": False,
            "nur_lesend": True,
            "neue_dateien": True
        },
        "konsistenz": {
            "geprueft": True,
            "fehler": len(konsistenz),
            "details": konsistenz
        },
        "register_zusammenfassung": {},
        "register_daten": {}
    }
    
    for name, analyse in analysen.items():
        adapter["register_zusammenfassung"][name] = analyse
        if register_daten.get(name):
            adapter["register_daten"][name] = {
                "schema_version": register_daten[name].get("schema_version", "unknown"),
                "register_id": register_daten[name].get("register_id", "unknown"),
                "eintraege_anzahl": analyse["eintraege"]
            }
    
    return adapter

def generiere_html(adapter, cfg):
    """Erzeugt HTML-Register-Übersicht."""
    ausgabe = cfg.get("ausgabe", {})
    html_pfad = ausgabe.get("html_register_uebersicht", "Windows_App/Logs/UI11_REGISTER_UEBERSICHT.html")
    os.makedirs(os.path.dirname(html_pfad), exist_ok=True)
    
    zusammenfassung = adapter.get("register_zusammenfassung", {})
    konsistenz = adapter.get("konsistenz", {})
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI11 – Register-Leseadapter</title>
<style>
:root {{ --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0;
  --kritisch: #dc2626; --hoch: #ea580c; --mittel: #ca8a04;
  --ok: #16a34a; --accent: #3b82f6; --warn: #f59e0b; }}
body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
.top-bar {{ background: var(--panel); padding: 16px 24px; border-radius: 8px; margin-bottom: 20px; }}
.top-bar h1 {{ margin: 0; font-size: 1.3rem; }}
.top-bar .meta {{ color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.card {{ background: var(--panel); padding: 16px; border-radius: 8px; border-left: 4px solid var(--accent); }}
.card.ok {{ border-left-color: var(--ok); }}
.card.warn {{ border-left-color: var(--warn); }}
.card.error {{ border-left-color: var(--kritisch); }}
.card h3 {{ margin: 0 0 8px; font-size: 0.9rem; color: #94a3b8; }}
.card .value {{ font-size: 1.8rem; font-weight: bold; }}
.card .detail {{ font-size: 0.8rem; color: #64748b; margin-top: 4px; }}
.section {{ background: var(--panel); padding: 20px; border-radius: 8px; margin-bottom: 16px; }}
.section h2 {{ margin-top: 0; font-size: 1.1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #334155; }}
th {{ color: #94a3b8; font-weight: 500; }}
.badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
.badge-ok {{ background: rgba(22,163,74,0.2); color: #86efac; }}
.badge-warn {{ background: rgba(245,158,11,0.2); color: #fcd34d; }}
.badge-kritisch {{ background: rgba(220,38,38,0.2); color: #fca5a5; }}
.freeze-box {{ background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.3); padding: 12px; border-radius: 6px; margin-bottom: 16px; }}
.freeze-box p {{ margin: 0; color: #fca5a5; font-size: 0.9rem; }}
.footer {{ text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 20px; }}
</style>
</head>
<body>
<div class="top-bar">
  <h1>UI11 – Register-Leseadapter</h1>
  <div class="meta">Adapter: {adapter.get('adapter_id', '–')} | {adapter.get('timestamp', '')} | {adapter.get('register_anzahl', 0)} Register</div>
</div>

<div class="freeze-box">
  <p>⚠️ <strong>Freeze-Kompatibilität:</strong> Dieser Adapter berührt <strong>nicht</strong> die eingefrorene Strecke UI03–UI07b. Alle Module außerhalb des Freeze können das Adapter-JSON lesen.</p>
</div>

<div class="grid">
"""
    
    for name, data in zusammenfassung.items():
        status_class = "ok" if data["status"] == "ok" else "error"
        warn_text = f"{data['warnungen']} Warnungen" if data['warnungen'] else "Keine Warnungen"
        sperr_text = f"{data['gesperrt']} gesperrt" if data['gesperrt'] else ""
        html += f'<div class="card {status_class}"><h3>{name}</h3><div class="value">{data["eintraege"]}</div><div class="detail">{warn_text} {sperr_text}</div></div>\n'
    
    html += '</div>\n'
    
    # Konsistenz
    html += '<div class="section">\n<h2>Konsistenzprüfung</h2>\n'
    if konsistenz.get("fehler", 0) > 0:
        html += f'<p>{konsistenz.get("fehler", 0)} Fehler gefunden:</p>\n<table>\n<tr><th>Regel</th><th>Schwere</th><th>Meldung</th></tr>\n'
        for kf in konsistenz.get("details", []):
            badge = f"badge-{kf['schwere'].lower()}" if kf['schwere'].lower() in ['kritisch', 'hoch', 'mittel', 'warnung'] else "badge-warn"
            html += f'<tr><td>{kf["regel"]}</td><td><span class="badge {badge}">{kf["schwere"]}</span></td><td>{kf["meldung"]}</td></tr>\n'
        html += '</table>\n'
    else:
        html += '<p style="color:var(--ok)">✓ Alle Konsistenzregeln bestanden</p>\n'
    html += '</div>\n'
    
    # Register-Details
    html += '<div class="section">\n<h2>Register-Details</h2>\n<table>\n<tr><th>Register</th><th>Eintraege</th><th>Warnungen</th><th>Gesperrt</th><th>Status</th></tr>\n'
    for name, data in zusammenfassung.items():
        status_badge = "<span class='badge badge-ok'>OK</span>" if data["status"] == "ok" else "<span class='badge badge-warn'>Nicht gefunden</span>"
        html += f'<tr><td><strong>{name}</strong></td><td>{data["eintraege"]}</td><td>{data["warnungen"]}</td><td>{data["gesperrt"]}</td><td>{status_badge}</td></tr>\n'
    html += '</table>\n</div>\n'
    
    html += '<div class="footer">UI11 – Rote Linie: beruehrt_UI03_UI07b=false | nur_lesend=true | neue_dateien=true</div>\n</body>\n</html>'
    
    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML Register-Übersicht: {html_pfad}")
    return html_pfad

def generiere_json(adapter, cfg):
    """Speichert Adapter-JSON."""
    ausgabe = cfg.get("ausgabe", {})
    json_pfad = ausgabe.get("json_adapter", "Windows_App/Logs/UI11_REGISTER_ADAPTER.json")
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(adapter, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON Adapter: {json_pfad}")
    return json_pfad

def generiere_konsistenzlog(konsistenz, cfg):
    """Speichert Konsistenz-Log."""
    ausgabe = cfg.get("ausgabe", {})
    log_pfad = ausgabe.get("konsistenz_log", "Windows_App/Logs/UI11_KONSISTENZ_LOG.json")
    os.makedirs(os.path.dirname(log_pfad), exist_ok=True)
    with open(log_pfad, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "konsistenz": konsistenz}, f, indent=2, ensure_ascii=False)
    print(f"[OK] Konsistenz-Log: {log_pfad}")
    return log_pfad

def generiere_bericht(adapter, konsistenz, cfg):
    """Erzeugt Textbericht."""
    ausgabe = cfg.get("ausgabe", {})
    bericht_pfad = ausgabe.get("bericht", "Windows_App/Logs/UI11_REGISTER_LESADAPTER_BERICHT.txt")
    os.makedirs(os.path.dirname(bericht_pfad), exist_ok=True)
    
    lines = [
        "=" * 60,
        "UI11 – Register-Leseadapter",
        "=" * 60,
        f"Adapter-ID: {adapter.get('adapter_id', '–')}",
        f"Timestamp: {adapter.get('timestamp', '–')}",
        f"Register-Anzahl: {adapter.get('register_anzahl', 0)}",
        "",
        "FREEZE-KOMPATIBILITAET",
        "  beruehrt_ui03_ui07b: False",
        "  nur_lesend: True",
        "  neue_dateien: True",
        "",
        "REGISTER-ZUSAMMENFASSUNG",
    ]
    
    for name, data in adapter.get("register_zusammenfassung", {}).items():
        status = "OK" if data["status"] == "ok" else "NICHT GEFUNDEN"
        lines.append(f"  {name}: {data['eintraege']} Eintraege, {data['warnungen']} Warnungen, {data['gesperrt']} gesperrt [{status}]")
    
    lines.extend([
        "",
        "KONSISTENZPRUEFUNG",
        f"  Fehler: {len(konsistenz)}",
    ])
    
    if konsistenz:
        for kf in konsistenz:
            lines.append(f"  [{kf['schwere']}] {kf['regel']}: {kf['meldung']}")
    else:
        lines.append("  Alle Regeln bestanden.")
    
    lines.extend([
        "",
        "=" * 60,
        "Rote Linie: beruehrt_UI03_UI07b=false | nur_lesend=true | neue_dateien=true",
        "=" * 60,
    ])
    
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Bericht: {bericht_pfad}")
    return bericht_pfad

def hauptlauf():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI11 – Register-Leseadapter")
    print("=" * 60)
    
    # 1. Config laden
    cfg = load_json("Config/ui11_register_lesadapter_v1.json")
    if not cfg:
        print("[FEHLER] Config nicht ladbar. Abbruch.")
        return 1
    
    # 2. Sperrregister
    modul_id = cfg.get("modul_id", "UI11")
    gesperrt, freigabe = pruefe_sperrregister(modul_id)
    if gesperrt:
        print(f"[SPERRE] {modul_id} ist im Sperrregister gesperrt.")
        print(f"         Freigabe erfordert: {', '.join(freigabe)}")
        FEHLER += 1
        return 1
    print("[OK] Sperrregister: keine Sperre")
    
    # 3. Alle Register laden
    register_namen = [
        "sperrregister", "ressourcenregister", "skillregister", "toolregister",
        "quellen_adapter_register", "lizenzregister", "update_register", "modulregister"
    ]
    
    register_daten = {}
    analysen = {}
    
    for name in register_namen:
        daten = lade_register(name, cfg)
        register_daten[name] = daten
        analysen[name] = analysiere_register(name, daten)
        if daten:
            print(f"[OK] {name}: {analysen[name]['eintraege']} Eintraege, {analysen[name]['warnungen']} Warnungen, {analysen[name]['gesperrt']} gesperrt")
        else:
            print(f"[WARN] {name}: nicht gefunden")
    
    # 4. Konsistenz prüfen
    regeln = cfg.get("konsistenzregeln", [])
    konsistenz = pruefe_konsistenz(register_daten, regeln)
    if konsistenz:
        print(f"[WARN] {len(konsistenz)} Konsistenzfehler gefunden")
        for kf in konsistenz:
            print(f"       [{kf['schwere']}] {kf['regel']}: {kf['meldung']}")
    else:
        print("[OK] Alle Konsistenzregeln bestanden")
    
    # 5. Adapter erstellen
    adapter = erstelle_adapter(register_daten, analysen, konsistenz, cfg)
    print(f"[OK] Adapter erstellt fuer {len(register_namen)} Register")
    
    # 6. Ausgaben
    generiere_json(adapter, cfg)
    generiere_html(adapter, cfg)
    generiere_konsistenzlog(konsistenz, cfg)
    generiere_bericht(adapter, konsistenz, cfg)
    
    # 7. Zusammenfassung
    print("\n" + "=" * 60)
    total_eintraege = sum(a["eintraege"] for a in analysen.values())
    total_warnungen = sum(a["warnungen"] for a in analysen.values())
    print(f"Register: {len(register_namen)} | Eintraege: {total_eintraege} | Warnungen: {total_warnungen} | Konsistenzfehler: {len(konsistenz)}")
    if FEHLER == 0:
        print("UI11 ABGESCHLOSSEN")
    else:
        print(f"UI11 mit {FEHLER} Fehler(n) beendet")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI11 SELBSTTEST ==========================================")
    def t(bez, bed):
        global FEHLER
        if bed:
            print(f"  [OK]   {bez}")
        else:
            print(f"  [FEHLER] {bez}")
            FEHLER += 1
    
    cfg = load_json("Config/ui11_register_lesadapter_v1.json")
    t("Config ladbar", cfg is not None)
    if cfg:
        t("modul_id == UI11", cfg.get("modul_id") == "UI11")
        t("8 Register in abhaengigkeiten", len(cfg.get("abhaengigkeiten", {})) >= 8)
        t("konsistenzregeln >= 3", len(cfg.get("konsistenzregeln", [])) >= 3)
        t("freeze.beruehrt_ui03_ui07b == false",
          cfg.get("adapter_konfiguration", {}).get("freeze_kompatibilitaet", {}).get("beruehrt_ui03_ui07b") is False)
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)
    
    t("hauptlauf() definiert", callable(hauptlauf))
    t("lade_register() definiert", callable(lade_register))
    t("analysiere_register() definiert", callable(analysiere_register))
    t("pruefe_konsistenz() definiert", callable(pruefe_konsistenz))
    t("erstelle_adapter() definiert", callable(erstelle_adapter))
    t("generiere_html() definiert", callable(generiere_html))
    t("generiere_json() definiert", callable(generiere_json))
    
    print(f"\nSELBSTTEST: {'BESTANDEN' if FEHLER == 0 else f'{FEHLER} FEHLER'}")
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        sys.exit(selbsttest())
    sys.exit(hauptlauf())
