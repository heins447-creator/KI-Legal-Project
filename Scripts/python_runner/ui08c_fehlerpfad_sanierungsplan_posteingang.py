#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI08c – Fehlerpfad-Sanierungsplan Posteingang
Liest UI08b-Ergebnisse, ordnet Verantwortlichkeiten zu,
klassifiziert Sanierbarkeit, erzeugt HTML/JSON/CSV/Bericht.
"""

import json, os, sys, csv
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

def lade_ui08b_ergebnis(cfg):
    """Liest das UI08b JSON-Status-File ein."""
    pfad = cfg.get("abhaengigkeiten", {}).get("ui08b_status_json", "")
    if not os.path.exists(pfad):
        print(f"[WARN] UI08b Status nicht gefunden: {pfad}")
        global WARNUNGEN
        WARNUNGEN += 1
        return None
    return load_json(pfad)

def erstelle_sanierungsplan(ui08b_ergebnis, cfg):
    """Erstellt den Sanierungsplan aus UI08b-Ergebnissen und Config-Matrix."""
    matrix = cfg.get("sanierungsmatrix", {})
    verantwortlichkeiten = matrix.get("verantwortlichkeiten", [])
    regeln = matrix.get("sanierungsregeln", [])

    plan = {
        "modul_id": "UI08c",
        "timestamp": datetime.now().isoformat(),
        "zusammenfassung": {
            "kritisch_gesamt": 0,
            "hoch_gesamt": 0,
            "mittel_gesamt": 0,
            "automatisch_sanierbar": 0,
            "manuelle_freigabe_erforderlich": 0,
            "bleiben_gesperrt": 0
        },
        "verantwortlichkeiten": [],
        "massnahmen": []
    }

    # Fehlerpfade aus UI08b
    fehlerpfade = []
    if ui08b_ergebnis and "fehlerpfade" in ui08b_ergebnis:
        fehlerpfade = ui08b_ergebnis["fehlerpfade"]
    elif ui08b_ergebnis and "ergebnisse" in ui08b_ergebnis:
        fehlerpfade = ui08b_ergebnis["ergebnisse"]

    # Pro Verantwortlichkeit aufbereiten
    for v in verantwortlichkeiten:
        v_eintrag = {
            "id": v["id"],
            "name": v["name"],
            "fehler": [],
            "automatisch": [],
            "manuell": [],
            "gesperrt": []
        }

        for fid in v.get("zustaendig_fuer", []):
            regel = next((r for r in regeln if r["fehler_id"] == fid), None)
            fehler = next((f for f in fehlerpfade if f.get("id") == fid), None)

            if regel:
                eintrag = {
                    "fehler_id": fid,
                    "name": regel["name"],
                    "schwere": regel["schwere"],
                    "automatisch": regel["automatisch"],
                    "automatische_aktion": regel.get("automatische_aktion"),
                    "manuelle_aktion": regel.get("manuelle_aktion"),
                    "bleibt_gesperrt": regel["bleibt_gesperrt"],
                    "max_wiederholungen": regel["max_wiederholungen"],
                    "escalation": regel["escalation"],
                    "gefunden": fehler is not None and fehler.get("gesamt", 0) > 0,
                    "anzahl": fehler.get("gesamt", 0) if fehler else 0
                }
                v_eintrag["fehler"].append(eintrag)

                if eintrag["gefunden"]:
                    if regel["schwere"] == "KRITISCH":
                        plan["zusammenfassung"]["kritisch_gesamt"] += eintrag["anzahl"]
                    elif regel["schwere"] == "HOCH":
                        plan["zusammenfassung"]["hoch_gesamt"] += eintrag["anzahl"]
                    else:
                        plan["zusammenfassung"]["mittel_gesamt"] += eintrag["anzahl"]

                    if regel["automatisch"]:
                        plan["zusammenfassung"]["automatisch_sanierbar"] += eintrag["anzahl"]
                        v_eintrag["automatisch"].append(eintrag)
                    else:
                        plan["zusammenfassung"]["manuelle_freigabe_erforderlich"] += eintrag["anzahl"]
                        v_eintrag["manuell"].append(eintrag)

                    if regel["bleibt_gesperrt"]:
                        plan["zusammenfassung"]["bleiben_gesperrt"] += eintrag["anzahl"]
                        v_eintrag["gesperrt"].append(eintrag)

                    # Maßnahme
                    plan["massnahmen"].append({
                        "fehler_id": fid,
                        "verantwortlich": v["id"],
                        "aktion": regel.get("automatische_aktion") or regel.get("manuelle_aktion"),
                        "automatisch": regel["automatisch"],
                        "escalation": regel["escalation"],
                        "anzahl": eintrag["anzahl"]
                    })

        plan["verantwortlichkeiten"].append(v_eintrag)

    return plan

def generiere_html(plan, cfg):
    """Erzeugt HTML-Sanierungsplan."""
    ausgabe = cfg.get("ausgabe", {})
    html_pfad = ausgabe.get("html_sanierungsplan", "Windows_App/Logs/UI08C_SANIERUNGSPLAN.html")
    os.makedirs(os.path.dirname(html_pfad), exist_ok=True)

    z = plan["zusammenfassung"]

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>UI08c – Sanierungsplan Posteingang</title>
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
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.card {{ background: var(--panel); padding: 16px; border-radius: 8px; border-left: 4px solid var(--accent); }}
.card.kritisch {{ border-left-color: var(--kritisch); }}
.card.hoch {{ border-left-color: var(--hoch); }}
.card.mittel {{ border-left-color: var(--mittel); }}
.card.ok {{ border-left-color: var(--ok); }}
.card h3 {{ margin: 0 0 8px; font-size: 0.9rem; color: #94a3b8; }}
.card .value {{ font-size: 1.8rem; font-weight: bold; }}
.section {{ background: var(--panel); padding: 20px; border-radius: 8px; margin-bottom: 16px; }}
.section h2 {{ margin-top: 0; font-size: 1.1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #334155; }}
th {{ color: #94a3b8; font-weight: 500; }}
.badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
.badge-kritisch {{ background: rgba(220,38,38,0.2); color: #fca5a5; }}
.badge-hoch {{ background: rgba(234,88,12,0.2); color: #fdba74; }}
.badge-mittel {{ background: rgba(202,138,4,0.2); color: #fde047; }}
.badge-auto {{ background: rgba(22,163,74,0.2); color: #86efac; }}
.badge-manual {{ background: rgba(59,130,246,0.2); color: #93c5fd; }}
.badge-gesperrt {{ background: rgba(220,38,38,0.3); color: #fca5a5; }}
.footer {{ text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 20px; }}
</style>
</head>
<body>
<div class="top-bar">
  <h1>UI08c – Fehlerpfad-Sanierungsplan Posteingang</h1>
  <div class="meta">{plan['timestamp']} | Modul: {plan['modul_id']} | Demo-Modus</div>
</div>

<div class="grid">
  <div class="card kritisch"><h3>Kritisch</h3><div class="value">{z['kritisch_gesamt']}</div></div>
  <div class="card hoch"><h3>Hoch</h3><div class="value">{z['hoch_gesamt']}</div></div>
  <div class="card mittel"><h3>Mittel</h3><div class="value">{z['mittel_gesamt']}</div></div>
  <div class="card ok"><h3>Autom. sanierbar</h3><div class="value">{z['automatisch_sanierbar']}</div></div>
  <div class="card"><h3>Manuelle Freigabe</h3><div class="value">{z['manuelle_freigabe_erforderlich']}</div></div>
  <div class="card kritisch"><h3>Bleiben gesperrt</h3><div class="value">{z['bleiben_gesperrt']}</div></div>
</div>
"""

    # Verantwortlichkeiten
    for v in plan["verantwortlichkeiten"]:
        html += f'<div class="section">\n<h2>{v["name"]} ({v["id"]})</h2>\n'
        if v["fehler"]:
            html += '<table><tr><th>Fehler</th><th>Schwere</th><th>Modus</th><th>Status</th><th>Aktion</th><th>Escalation</th></tr>\n'
            for f in v["fehler"]:
                modus = "<span class='badge badge-auto'>Automatisch</span>" if f["automatisch"] else "<span class='badge badge-manual'>Manuell</span>"
                status = "<span class='badge badge-gesperrt'>Gesperrt</span>" if f["bleibt_gesperrt"] else "<span class='badge badge-auto'>Freigebbar</span>"
                if not f["gefunden"]:
                    status = "<span class='badge'>Nicht betroffen</span>"
                schwere_badge = f"badge-{f['schwere'].lower()}"
                aktion = f.get("automatische_aktion") or f.get("manuelle_aktion") or "–"
                html += f'<tr><td>{f["fehler_id"]}: {f["name"]}</td><td><span class="badge {schwere_badge}">{f["schwere"]}</span></td><td>{modus}</td><td>{status}</td><td>{aktion}</td><td>{f["escalation"]}</td></tr>\n'
            html += '</table>\n'
        else:
            html += '<p style="color:#64748b">Keine Fehlerpfade zugeordnet.</p>\n'
        html += '</div>\n'

    # Maßnahmen-Liste
    if plan["massnahmen"]:
        html += '<div class="section">\n<h2>Maßnahmen-Übersicht</h2>\n<table><tr><th>Fehler</th><th>Verantwortlich</th><th>Aktion</th><th>Aut.</th><th>Anzahl</th></tr>\n'
        for m in plan["massnahmen"]:
            auto = "Ja" if m["automatisch"] else "Nein"
            html += f'<tr><td>{m["fehler_id"]}</td><td>{m["verantwortlich"]}</td><td>{m["aktion"]}</td><td>{auto}</td><td>{m["anzahl"]}</td></tr>\n'
        html += '</table>\n</div>\n'

    html += '<div class="footer">UI08c – Rote Linie: produktiv_freigegeben=false | nur_musterdaten=true</div>\n</body>\n</html>'

    with open(html_pfad, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML Sanierungsplan: {html_pfad}")
    return html_pfad

def generiere_json(plan, cfg):
    """Speichert den Sanierungsplan als JSON."""
    ausgabe = cfg.get("ausgabe", {})
    json_pfad = ausgabe.get("json_sanierungsstatus", "Windows_App/Logs/UI08C_SANIERUNGSSTATUS.json")
    os.makedirs(os.path.dirname(json_pfad), exist_ok=True)
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"[OK] JSON Sanierungsstatus: {json_pfad}")
    return json_pfad

def generiere_csv(plan, cfg):
    """Speichert Maßnahmen als CSV."""
    ausgabe = cfg.get("ausgabe", {})
    csv_pfad = ausgabe.get("csv_massnahmen", "Windows_App/Logs/UI08C_MASSNAHMEN.csv")
    os.makedirs(os.path.dirname(csv_pfad), exist_ok=True)
    with open(csv_pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["fehler_id", "verantwortlich", "aktion", "automatisch", "escalation", "anzahl"])
        for m in plan["massnahmen"]:
            writer.writerow([m["fehler_id"], m["verantwortlich"], m["aktion"], m["automatisch"], m["escalation"], m["anzahl"]])
    print(f"[OK] CSV Maßnahmen: {csv_pfad}")
    return csv_pfad

def generiere_bericht(plan, cfg):
    """Erzeugt Textbericht."""
    ausgabe = cfg.get("ausgabe", {})
    bericht_pfad = ausgabe.get("bericht", "Windows_App/Logs/UI08C_SANIERUNGSPLAN_BERICHT.txt")
    os.makedirs(os.path.dirname(bericht_pfad), exist_ok=True)

    z = plan["zusammenfassung"]
    lines = [
        "=" * 60,
        "UI08c – Fehlerpfad-Sanierungsplan Posteingang",
        "=" * 60,
        f"Zeitstempel: {plan['timestamp']}",
        f"Modul: {plan['modul_id']}",
        "",
        "ZUSAMMENFASSUNG",
        f"  Kritisch:  {z['kritisch_gesamt']}",
        f"  Hoch:      {z['hoch_gesamt']}",
        f"  Mittel:    {z['mittel_gesamt']}",
        f"  Autom. sanierbar: {z['automatisch_sanierbar']}",
        f"  Manuelle Freigabe erforderlich: {z['manuelle_freigabe_erforderlich']}",
        f"  Bleiben gesperrt: {z['bleiben_gesperrt']}",
        "",
        "VERANTWORTLICHKEITEN",
    ]

    for v in plan["verantwortlichkeiten"]:
        lines.append(f"\n  {v['name']} ({v['id']}):")
        if v["fehler"]:
            for f in v["fehler"]:
                status = "BETROFFEN" if f["gefunden"] else "nicht betroffen"
                modus = "AUTO" if f["automatisch"] else "MANUELL"
                sperre = " GESPERRT" if f["bleibt_gesperrt"] else ""
                lines.append(f"    – {f['fehler_id']}: {f['name']} [{f['schwere']}] ({modus}) – {status}{sperre}")
                if f["gefunden"]:
                    aktion = f.get("automatische_aktion") or f.get("manuelle_aktion") or "–"
                    lines.append(f"      Aktion: {aktion} | Escalation: {f['escalation']}")
        else:
            lines.append("    (keine Fehlerpfade zugeordnet)")

    lines.extend([
        "",
        "MASSNAHMEN",
    ])
    for m in plan["massnahmen"]:
        auto = "[AUTO]" if m["automatisch"] else "[MANUELL]"
        lines.append(f"  {auto} {m['fehler_id']} -> {m['verantwortlich']}: {m['aktion']} (Anzahl: {m['anzahl']})")

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
    print("UI08c – Fehlerpfad-Sanierungsplan Posteingang")
    print("=" * 60)

    # 1. Config laden
    cfg = load_json("Config/ui08c_fehlerpfad_sanierungsplan_posteingang_v1.json")
    if not cfg:
        print("[FEHLER] Config nicht ladbar. Abbruch.")
        return 1

    # 2. Sperrregister
    modul_id = cfg.get("modul_id", "UI08c")
    gesperrt, freigabe = pruefe_sperrregister(modul_id)
    if gesperrt:
        print(f"[SPERRE] {modul_id} ist im Sperrregister gesperrt.")
        print(f"         Freigabe erfordert: {', '.join(freigabe)}")
        FEHLER += 1
        return 1
    print("[OK] Sperrregister: keine Sperre")

    # 3. UI08b-Ergebnis laden
    ui08b = lade_ui08b_ergebnis(cfg)
    if ui08b:
        print("[OK] UI08b-Ergebnis geladen")
    else:
        print("[INFO] UI08b-Ergebnis nicht verfügbar – erstelle Plan mit Config-Defaults")

    # 4. Sanierungsplan erstellen
    plan = erstelle_sanierungsplan(ui08b, cfg)
    print(f"[OK] Sanierungsplan erstellt – {len(plan['massnahmen'])} Maßnahmen")

    # 5. Ausgaben
    generiere_html(plan, cfg)
    generiere_json(plan, cfg)
    generiere_csv(plan, cfg)
    generiere_bericht(plan, cfg)

    # 6. Zusammenfassung
    print("\n" + "=" * 60)
    z = plan["zusammenfassung"]
    print(f"Kritisch: {z['kritisch_gesamt']} | Hoch: {z['hoch_gesamt']} | Mittel: {z['mittel_gesamt']}")
    print(f"Autom. sanierbar: {z['automatisch_sanierbar']} | Manuell: {z['manuelle_freigabe_erforderlich']} | Gesperrt: {z['bleiben_gesperrt']}")
    if FEHLER == 0:
        print("UI08c ABGESCHLOSSEN")
    else:
        print(f"UI08c mit {FEHLER} Fehler(n) beendet")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI08c SELBSTTEST ==========================================")
    def t(bez, bed):
        global FEHLER
        if bed:
            print(f"  [OK]   {bez}")
        else:
            print(f"  [FEHLER] {bez}")
            FEHLER += 1

    cfg = load_json("Config/ui08c_fehlerpfad_sanierungsplan_posteingang_v1.json")
    t("Config ladbar", cfg is not None)
    if cfg:
        t("modul_id == UI08c", cfg.get("modul_id") == "UI08c")
        matrix = cfg.get("sanierungsmatrix", {})
        t("sanierungsmatrix vorhanden", bool(matrix))
        t("verantwortlichkeiten >= 5", len(matrix.get("verantwortlichkeiten", [])) >= 5)
        t("sanierungsregeln == 9", len(matrix.get("sanierungsregeln", [])) == 9)
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)

    t("hauptlauf() definiert", callable(hauptlauf))
    t("erstelle_sanierungsplan() definiert", callable(erstelle_sanierungsplan))
    t("generiere_html() definiert", callable(generiere_html))
    t("generiere_json() definiert", callable(generiere_json))
    t("generiere_csv() definiert", callable(generiere_csv))
    t("generiere_bericht() definiert", callable(generiere_bericht))

    print(f"\nSELBSTTEST: {'BESTANDEN' if FEHLER == 0 else f'{FEHLER} FEHLER'}")
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        sys.exit(selbsttest())
    sys.exit(hauptlauf())
