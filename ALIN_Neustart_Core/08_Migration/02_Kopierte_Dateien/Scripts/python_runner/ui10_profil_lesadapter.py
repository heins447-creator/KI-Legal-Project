#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI10 – Externer Profil-Leseadapter
Liest UI09-Profil, prueft Konsistenz mit UI08/UI08b/UI08c,
stellt Adapter-JSON fuer Module ausserhalb des Freeze bereit.
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

def lade_ui09_profil(cfg):
    """Liest das UI09 zentrale Profil."""
    pfad = cfg.get("abhaengigkeiten", {}).get("ui09_zentrales_profil", "")
    if not os.path.exists(pfad):
        print(f"[WARN] UI09 Profil nicht gefunden: {pfad}")
        global WARNUNGEN
        WARNUNGEN += 1
        return None
    return load_json(pfad)

def lade_ui09_schalter(cfg):
    """Liest die UI09 Grundschalter."""
    pfad = cfg.get("abhaengigkeiten", {}).get("ui09_grundschalter", "")
    if not os.path.exists(pfad):
        print(f"[WARN] UI09 Grundschalter nicht gefunden: {pfad}")
        global WARNUNGEN
        WARNUNGEN += 1
        return None
    return load_json(pfad)

def lade_ui08_status(cfg):
    """Liest UI08 Posteingang-Status (optional)."""
    pfad = cfg.get("abhaengigkeiten", {}).get("ui08_posteingang_status", "")
    if not os.path.exists(pfad):
        return None
    return load_json(pfad)

def lade_ui08b_status(cfg):
    """Liest UI08b Fehlerpfad-Status (optional)."""
    pfad = cfg.get("abhaengigkeiten", {}).get("ui08b_fehlerpfad_status", "")
    if not os.path.exists(pfad):
        return None
    return load_json(pfad)

def lade_ui08c_status(cfg):
    """Liest UI08c Sanierungsstatus (optional)."""
    pfad = cfg.get("abhaengigkeiten", {}).get("ui08c_sanierungsstatus", "")
    if not os.path.exists(pfad):
        return None
    return load_json(pfad)

def pruefe_konsistenz(profil, schalter, ui08, ui08b, ui08c, regeln):
    """Prueft Konsistenzregeln zwischen UI09 und UI08/UI08b/UI08c."""
    fehler = []
    
    # Extrahiere relevante Werte aus UI09
    betriebsmodus = "demo"
    sicherheitsstatus = "unbekannt"
    sprache_dok = "unbekannt"
    ocr_paket = ["deu", "eng"]
    online_status = False
    
    if profil and "felder" in profil:
        for f in profil["felder"]:
            if f.get("feld_id") == "betriebsmodus":
                betriebsmodus = f.get("default", "demo")
            elif f.get("feld_id") == "sicherheitsstatus":
                sicherheitsstatus = f.get("default", "unbekannt")
            elif f.get("feld_id") == "sprache_dokument":
                sprache_dok = f.get("default", "unbekannt")
            elif f.get("feld_id") == "ressourcenpaket_ocr":
                ocr_paket = f.get("default", ["deu", "eng"])
            elif f.get("feld_id") == "online_status":
                online_status = f.get("default", False)
    
    # GS05 aus Schaltern
    gs05 = False
    if schalter and "grundschalter" in schalter:
        for s in schalter["grundschalter"]:
            if s.get("id") == "GS05":
                gs05 = s.get("default", False)
    
    for r in regeln:
        rid = r["regel_id"]
        beschreibung = r.get("beschreibung", "")
        schwere = r.get("schwere", "WARNUNG")
        
        # KONS_01: demo mode -> keine kritischen gesperrten Fehler
        if rid == "KONS_01" and betriebsmodus == "demo" and ui08b:
            kritisch_gesperrt = 0
            if "ergebnisse" in ui08b:
                for e in ui08b["ergebnisse"]:
                    if e.get("schwere") == "KRITISCH":
                        kritisch_gesperrt += e.get("gesamt", 0)
            if "fehlerpfade" in ui08b:
                for fp in ui08b["fehlerpfade"]:
                    if fp.get("schwere") == "KRITISCH":
                        kritisch_gesperrt += fp.get("gesamt", 0)
            if kritisch_gesperrt > 0:
                fehler.append({"regel": rid, "schwere": schwere, "meldung": f"Demo-Modus aber {kritisch_gesperrt} kritische gesperrte Fehler in UI08b"})
        
        # KONS_02: Sprache muss mit UI08 kompatibel sein
        if rid == "KONS_02" and ui08 and sprache_dok != "unbekannt":
            if "posteingang_uebersicht" in ui08 and "sprachprofile" in ui08["posteingang_uebersicht"]:
                verfuegbar = ui08["posteingang_uebersicht"]["sprachprofile"].get("erkannt", [])
                if sprache_dok not in verfuegbar and verfuegbar:
                    fehler.append({"regel": rid, "schwere": schwere, "meldung": f"UI09 Sprache '{sprache_dok}' nicht in UI08 verfuegbar: {verfuegbar}"})
        
        # KONS_03: sicherheitsstatus=gesperrt -> ui08c bleibt_gesperrt
        if rid == "KONS_03" and sicherheitsstatus == "gesperrt" and ui08c:
            if "zusammenfassung" in ui08c:
                if ui08c["zusammenfassung"].get("bleiben_gesperrt", 0) == 0:
                    fehler.append({"regel": rid, "schwere": schwere, "meldung": "UI09 sicherheitsstatus=gesperrt aber UI08c meldet 0 gesperrte"})
        
        # KONS_05: offline -> cache aktiv
        if rid == "KONS_05" and not online_status and not gs05:
            fehler.append({"regel": rid, "schwere": schwere, "meldung": "UI09 online_status=false aber GS05 offline_cache_aktiv=false"})
    
    return fehler

def erstelle_adapter(profil, schalter, konsistenz, bereitgestellte, cfg):
    """Erstellt das Adapter-JSON."""
    adapter = {
        "adapter_id": "UI10_PROFIL_ADAPTER",
        "timestamp": datetime.now().isoformat(),
        "quelle": "UI09",
        "profil_version": profil.get("profil_version", "unknown") if profil else "unknown",
        "betriebsmodus": "demo",
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
        "profilfelder": {},
        "grundschalter": {},
        "bereitgestellt_fuer": []
    }
    
    # Profilfelder extrahieren
    if profil and "felder" in profil:
        for f in profil["felder"]:
            adapter["profilfelder"][f["feld_id"]] = {
                "name": f.get("name"),
                "typ": f.get("typ"),
                "default": f.get("default"),
                "pflicht": f.get("pflichtfeld", False),
                "quelle": f.get("quelle"),
                "nutzer": f.get("nutzer", [])
            }
            if f.get("feld_id") == "betriebsmodus":
                adapter["betriebsmodus"] = f.get("default", "demo")
    
    # Grundschalter extrahieren
    if schalter and "grundschalter" in schalter:
        for s in schalter["grundschalter"]:
            adapter["grundschalter"][s["id"]] = {
                "name": s.get("name"),
                "default": s.get("default"),
                "aenderbar_durch": s.get("aenderbar_durch", []),
                "wirkt_auf": s.get("wirkt_auf", [])
            }
    
    # Bereitgestellte Module
    for m in bereitgestellte:
        adapter["bereitgestellt_fuer"].append({
            "modul_id": m["modul_id"],
            "nutzt_felder": m["nutzt_profilfelder"],
            "kompatibilitaet": m["kompatibilitaet"],
            "freeze_status": m["freeze_status"]
        })
    
    return adapter

def generiere_html(adapter, cfg):
    """Erzeugt HTML-Adapter-Übersicht."""
    ausgabe = cfg.get("ausgabe", {})
    html_pfad = ausgabe.get("html_adapter_uebersicht", "Windows_App/Logs/UI10_ADAPTER_UEBERSICHT.html")
    os.makedirs(os.path.dirname(html_pfad), exist_ok=True)
    
    profil = adapter.get("profilfelder", {})
    schalter = adapter.get("grundschalter", {})
    module = adapter.get("bereitgestellt_fuer", [])
    konsistenz = adapter.get("konsistenz", {})
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI10 – Profil-Leseadapter</title>
<style>
:root {{ --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0;
  --kritisch: #dc2626; --hoch: #ea580c; --mittel: #ca8a04;
  --ok: #16a34a; --accent: #3b82f6; --warn: #f59e0b; }}
body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
.top-bar {{ background: var(--panel); padding: 16px 24px; border-radius: 8px; margin-bottom: 20px; }}
.top-bar h1 {{ margin: 0; font-size: 1.3rem; }}
.top-bar .meta {{ color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.card {{ background: var(--panel); padding: 16px; border-radius: 8px; border-left: 4px solid var(--accent); }}
.card h3 {{ margin: 0 0 8px; font-size: 0.9rem; color: #94a3b8; }}
.card .value {{ font-size: 1.1rem; font-weight: 600; }}
.section {{ background: var(--panel); padding: 20px; border-radius: 8px; margin-bottom: 16px; }}
.section h2 {{ margin-top: 0; font-size: 1.1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #334155; }}
th {{ color: #94a3b8; font-weight: 500; }}
.badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
.badge-kritisch {{ background: rgba(220,38,38,0.2); color: #fca5a5; }}
.badge-hoch {{ background: rgba(234,88,12,0.2); color: #fdba74; }}
.badge-mittel {{ background: rgba(202,138,4,0.2); color: #fde047; }}
.badge-warn {{ background: rgba(245,158,11,0.2); color: #fcd34d; }}
.badge-ok {{ background: rgba(22,163,74,0.2); color: #86efac; }}
.badge-frozen {{ background: rgba(100,116,139,0.2); color: #cbd5e1; }}
.badge-active {{ background: rgba(59,130,246,0.2); color: #93c5fd; }}
.freeze-box {{ background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.3); padding: 12px; border-radius: 6px; margin-bottom: 16px; }}
.freeze-box p {{ margin: 0; color: #fca5a5; font-size: 0.9rem; }}
.footer {{ text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 20px; }}
</style>
</head>
<body>
<div class="top-bar">
  <h1>UI10 – Externer Profil-Leseadapter</h1>
  <div class="meta">Adapter: {adapter.get('adapter_id', '–')} | Quelle: UI09 v{adapter.get('profil_version', '–')} | {adapter.get('timestamp', '')}</div>
</div>

<div class="freeze-box">
  <p>⚠️ <strong>Freeze-Kompatibilität:</strong> Dieser Adapter berührt <strong>nicht</strong> die eingefrorene Strecke UI03–UI07b. Alle Module außerhalb des Freeze können das Adapter-JSON lesen.</p>
</div>

<div class="grid">
  <div class="card"><h3>Profilfelder</h3><div class="value">{len(profil)}</div></div>
  <div class="card"><h3>Grundschalter</h3><div class="value">{len(schalter)}</div></div>
  <div class="card"><h3>Bereitgestellt für</h3><div class="value">{len(module)} Module</div></div>
  <div class="card"><h3>Konsistenzfehler</h3><div class="value">{konsistenz.get('fehler', 0)}</div></div>
</div>
"""
    
    # Profilfelder
    if profil:
        html += '<div class="section">\n<h2>Profilfelder</h2>\n<table>\n<tr><th>Feld-ID</th><th>Name</th><th>Typ</th><th>Default</th><th>Pflicht</th><th>Quelle</th></tr>\n'
        for fid, fdata in profil.items():
            pflicht = "<span class='badge badge-ok'>Ja</span>" if fdata.get("pflicht") else "<span class='badge badge-frozen'>Nein</span>"
            default = json.dumps(fdata.get("default")) if fdata.get("default") is not None else "null"
            html += f'<tr><td><strong>{fid}</strong></td><td>{fdata.get("name", "–")}</td><td>{fdata.get("typ", "–")}</td><td>{default}</td><td>{pflicht}</td><td>{fdata.get("quelle", "–")}</td></tr>\n'
        html += '</table>\n</div>\n'
    
    # Grundschalter
    if schalter:
        html += '<div class="section">\n<h2>Grundschalter</h2>\n<table>\n<tr><th>ID</th><th>Name</th><th>Default</th><th>Änderbar durch</th><th>Wirkt auf</th></tr>\n'
        for sid, sdata in schalter.items():
            default = "<span class='badge badge-ok'>AN</span>" if sdata.get("default") else "<span class='badge badge-frozen'>AUS</span>"
            aenderbar = ", ".join(sdata.get("aenderbar_durch", []))
            wirkt = ", ".join(sdata.get("wirkt_auf", []))
            html += f'<tr><td><strong>{sid}</strong></td><td>{sdata.get("name", "–")}</td><td>{default}</td><td>{aenderbar}</td><td>{wirkt}</td></tr>\n'
        html += '</table>\n</div>\n'
    
    # Module
    if module:
        html += '<div class="section">\n<h2>Bereitgestellt für Module</h2>\n<table>\n<tr><th>Modul</th><th>Kompatibilität</th><th>Freeze-Status</th><th>Genutzte Felder</th></tr>\n'
        for m in module:
            if m["freeze_status"] == "eingefroren":
                freeze_badge = "<span class='badge badge-kritisch'>EINGEFROREN</span>"
                komp_badge = "<span class='badge badge-frozen'>zukünftig</span>"
            else:
                freeze_badge = "<span class='badge badge-active'>Außerhalb</span>"
                komp_badge = "<span class='badge badge-ok'>lesend</span>"
            felder = ", ".join(m.get("nutzt_felder", []))
            html += f'<tr><td><strong>{m["modul_id"]}</strong></td><td>{komp_badge}</td><td>{freeze_badge}</td><td>{felder}</td></tr>\n'
        html += '</table>\n</div>\n'
    
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
    
    html += '<div class="footer">UI10 – Rote Linie: beruehrt_UI03_UI07b=false | nur_lesend=true | neue_dateien=true</div>\n</body>\n</html>'
    
    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML Adapter-Übersicht: {html_pfad}")
    return html_pfad

def generiere_json(adapter, cfg):
    """Speichert Adapter-JSON."""
    ausgabe = cfg.get("ausgabe", {})
    json_pfad = ausgabe.get("json_adapter", "Windows_App/Logs/UI10_PROFIL_ADAPTER.json")
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(adapter, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON Adapter: {json_pfad}")
    return json_pfad

def generiere_konsistenzlog(konsistenz, cfg):
    """Speichert Konsistenz-Log."""
    ausgabe = cfg.get("ausgabe", {})
    log_pfad = ausgabe.get("konsistenz_log", "Windows_App/Logs/UI10_KONSISTENZ_LOG.json")
    os.makedirs(os.path.dirname(log_pfad), exist_ok=True)
    with open(log_pfad, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "konsistenz": konsistenz}, f, indent=2, ensure_ascii=False)
    print(f"[OK] Konsistenz-Log: {log_pfad}")
    return log_pfad

def generiere_bericht(adapter, konsistenz, cfg):
    """Erzeugt Textbericht."""
    ausgabe = cfg.get("ausgabe", {})
    bericht_pfad = ausgabe.get("bericht", "Windows_App/Logs/UI10_PROFIL_LESADAPTER_BERICHT.txt")
    os.makedirs(os.path.dirname(bericht_pfad), exist_ok=True)
    
    lines = [
        "=" * 60,
        "UI10 – Externer Profil-Leseadapter",
        "=" * 60,
        f"Adapter-ID: {adapter.get('adapter_id', '–')}",
        f"Timestamp: {adapter.get('timestamp', '–')}",
        f"Quelle: UI09 v{adapter.get('profil_version', '–')}",
        f"Betriebsmodus: {adapter.get('betriebsmodus', '–')}",
        "",
        "FREEZE-KOMPATIBILITAET",
        "  beruehrt_ui03_ui07b: False",
        "  nur_lesend: True",
        "  neue_dateien: True",
        "",
        f"PROFILFELDER ({len(adapter.get('profilfelder', {}))} Stueck)",
    ]
    
    for fid, fdata in adapter.get("profilfelder", {}).items():
        lines.append(f"  {fid}: {fdata.get('name', '–')} (Typ: {fdata.get('typ', '–')}, Default: {json.dumps(fdata.get('default'))})")
    
    lines.extend([
        "",
        f"GRUNDSCHALTER ({len(adapter.get('grundschalter', {}))} Stueck)",
    ])
    
    for sid, sdata in adapter.get("grundschalter", {}).items():
        status = "AN" if sdata.get("default") else "AUS"
        lines.append(f"  {sid}: {sdata.get('name', '–')} [{status}]")
    
    lines.extend([
        "",
        f"BEREITGESTELLT FUER ({len(adapter.get('bereitgestellt_fuer', []))} Module)",
    ])
    
    for m in adapter.get("bereitgestellt_fuer", []):
        freeze = "[EINGEFROREN]" if m["freeze_status"] == "eingefroren" else "[AUSserhalb]"
        felder = ", ".join(m.get("nutzt_felder", []))
        lines.append(f"  {m['modul_id']} {freeze} -> {felder}")
    
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
    print("UI10 – Externer Profil-Leseadapter")
    print("=" * 60)
    
    # 1. Config laden
    cfg = load_json("Config/ui10_profil_lesadapter_v1.json")
    if not cfg:
        print("[FEHLER] Config nicht ladbar. Abbruch.")
        return 1
    
    # 2. Sperrregister
    modul_id = cfg.get("modul_id", "UI10")
    gesperrt, freigabe = pruefe_sperrregister(modul_id)
    if gesperrt:
        print(f"[SPERRE] {modul_id} ist im Sperrregister gesperrt.")
        print(f"         Freigabe erfordert: {', '.join(freigabe)}")
        FEHLER += 1
        return 1
    print("[OK] Sperrregister: keine Sperre")
    
    # 3. UI09 laden
    profil = lade_ui09_profil(cfg)
    schalter = lade_ui09_schalter(cfg)
    
    if profil:
        print(f"[OK] UI09 Profil geladen: {profil.get('profil_id', '–')}")
    if schalter:
        print(f"[OK] UI09 Grundschalter geladen: {len(schalter.get('grundschalter', []))} Schalter")
    
    # 4. UI08/UI08b/UI08c laden (optional)
    ui08 = lade_ui08_status(cfg)
    ui08b = lade_ui08b_status(cfg)
    ui08c = lade_ui08c_status(cfg)
    
    if ui08:
        print("[OK] UI08 Status geladen")
    if ui08b:
        print("[OK] UI08b Fehlerpfad-Status geladen")
    if ui08c:
        print("[OK] UI08c Sanierungsstatus geladen")
    
    # 5. Konsistenz prüfen
    regeln = cfg.get("konsistenzregeln", [])
    konsistenz = pruefe_konsistenz(profil, schalter, ui08, ui08b, ui08c, regeln)
    if konsistenz:
        print(f"[WARN] {len(konsistenz)} Konsistenzfehler gefunden")
        for kf in konsistenz:
            print(f"       [{kf['schwere']}] {kf['regel']}: {kf['meldung']}")
    else:
        print("[OK] Alle Konsistenzregeln bestanden")
    
    # 6. Adapter erstellen
    bereitgestellte = cfg.get("bereitgestellte_module", [])
    adapter = erstelle_adapter(profil, schalter, konsistenz, bereitgestellte, cfg)
    print(f"[OK] Adapter erstellt für {len(bereitgestellte)} Module")
    
    # 7. Ausgaben
    generiere_json(adapter, cfg)
    generiere_html(adapter, cfg)
    generiere_konsistenzlog(konsistenz, cfg)
    generiere_bericht(adapter, konsistenz, cfg)
    
    # 8. Zusammenfassung
    print("\n" + "=" * 60)
    print(f"Profilfelder: {len(adapter['profilfelder'])} | Grundschalter: {len(adapter['grundschalter'])} | Module: {len(adapter['bereitgestellt_fuer'])}")
    print(f"Konsistenzfehler: {len(konsistenz)}")
    if FEHLER == 0:
        print("UI10 ABGESCHLOSSEN")
    else:
        print(f"UI10 mit {FEHLER} Fehler(n) beendet")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI10 SELBSTTEST ==========================================")
    def t(bez, bed):
        global FEHLER
        if bed:
            print(f"  [OK]   {bez}")
        else:
            print(f"  [FEHLER] {bez}")
            FEHLER += 1
    
    cfg = load_json("Config/ui10_profil_lesadapter_v1.json")
    t("Config ladbar", cfg is not None)
    if cfg:
        t("modul_id == UI10", cfg.get("modul_id") == "UI10")
        t("adapter_konfiguration vorhanden", bool(cfg.get("adapter_konfiguration")))
        t("freeze_kompatibilitaet.beruehrt_ui03_ui07b == false",
          cfg.get("adapter_konfiguration", {}).get("freeze_kompatibilitaet", {}).get("beruehrt_ui03_ui07b") is False)
        t("konsistenzregeln >= 3", len(cfg.get("konsistenzregeln", [])) >= 3)
        t("bereitgestellte_module >= 5", len(cfg.get("bereitgestellte_module", [])) >= 5)
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)
    
    t("hauptlauf() definiert", callable(hauptlauf))
    t("lade_ui09_profil() definiert", callable(lade_ui09_profil))
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
