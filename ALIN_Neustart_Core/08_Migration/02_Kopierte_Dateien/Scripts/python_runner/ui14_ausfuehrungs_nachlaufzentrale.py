#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI14 – Ausführungs- und Nachlaufzentrale UI08–UI13
Führt UI08, UI08b, UI08c, UI09, UI10, UI11, UI12, UI13 in korrekter Reihenfolge aus.
Trennt erwartbare Warnungen (Demo-Modus, fehlende Eingaben) von echten Fehlern.
Öffnet abschließend UI13 als zentrale HTML-Entscheidungsseite.

Rote Linie: produktiv_freigegeben=false, nur_musterdaten=true, echte_daten_erlaubt=false
Berührt UI03–UI07b: NEIN (führt nur UI08–UI13 aus)
"""

import json
import os
import sys
import subprocess
import webbrowser
from datetime import datetime

FEHLER = 0
WARNUNGEN = 0
SCHRITTE_LOG = []


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
        for eintrag in reg.get("eintraege", []):
            if eintrag.get("modul_id") == modul_id and eintrag.get("gesperrt", False):
                return eintrag
    except Exception:
        pass
    return None


def finde_python():
    """Findet den Projekt-Python oder fallback auf system python."""
    projekt_py = "Tools/Python312/python.exe"
    if os.path.exists(projekt_py):
        return projekt_py
    return "python"


def fuehre_schritt_aus(schritt, py_cmd):
    global FEHLER, WARNUNGEN
    modul_id = schritt["modul_id"]
    runner = schritt["runner"]
    check = schritt.get("check")
    erwartete_warnungen = schritt.get("erwartete_warnungen", [])
    
    print(f"\n{'='*60}")
    print(f"SCHRITT {schritt['schritt']}: {modul_id} – {schritt['name']}")
    print(f"{'='*60}")
    
    log_eintrag = {
        "schritt": schritt["schritt"],
        "modul_id": modul_id,
        "name": schritt["name"],
        "runner": runner,
        "status": "PENDING",
        "fehler": 0,
        "warnungen": 0,
        "hinweise": []
    }
    
    # Prüfe ob Runner existiert
    if not os.path.exists(runner):
        print(f"[FEHLER] Runner nicht gefunden: {runner}")
        FEHLER += 1
        log_eintrag["status"] = "FEHLER"
        log_eintrag["fehler"] = 1
        log_eintrag["hinweise"].append(f"Runner fehlt: {runner}")
        SCHRITTE_LOG.append(log_eintrag)
        return False
    
    # Führe Check-Datei aus (optional)
    if check and os.path.exists(check):
        print(f"[INFO] Führe Check aus: {check}")
        try:
            result = subprocess.run(
                [py_cmd, check],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print(f"[WARNUNG] Check-Datei meldet Probleme (Exitcode {result.returncode})")
                WARNUNGEN += 1
                log_eintrag["warnungen"] += 1
                log_eintrag["hinweise"].append(f"Check-Datei Exitcode {result.returncode}")
            else:
                print(f"[OK] Check-Datei bestanden.")
        except Exception as e:
            print(f"[WARNUNG] Check-Ausführung fehlgeschlagen: {e}")
            WARNUNGEN += 1
            log_eintrag["warnungen"] += 1
    
    # Führe Runner aus
    print(f"[INFO] Führe Runner aus: {runner}")
    try:
        result = subprocess.run(
            [py_cmd, runner],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Ausgabe anzeigen
        if result.stdout:
            for line in result.stdout.splitlines()[:50]:  # Max 50 Zeilen
                print(f"  {line}")
        
        # Exitcode prüfen
        if result.returncode != 0:
            # Prüfe ob es nur erwartete Warnungen sind
            stderr_lower = result.stderr.lower() if result.stderr else ""
            stdout_lower = result.stdout.lower() if result.stdout else ""
            combined = stderr_lower + stdout_lower
            
            is_expected = any(w.lower() in combined for w in erwartete_warnungen)
            
            if is_expected:
                print(f"[WARNUNG] Exitcode {result.returncode}, aber nur erwartete Warnungen.")
                WARNUNGEN += 1
                log_eintrag["warnungen"] += 1
                log_eintrag["status"] = "WARNUNG"
            else:
                print(f"[FEHLER] Runner fehlgeschlagen mit Exitcode {result.returncode}")
                FEHLER += 1
                log_eintrag["fehler"] += 1
                log_eintrag["status"] = "FEHLER"
                log_eintrag["hinweise"].append(f"Exitcode {result.returncode}")
                SCHRITTE_LOG.append(log_eintrag)
                return False
        else:
            print(f"[OK] {modul_id} erfolgreich abgeschlossen.")
            log_eintrag["status"] = "OK"
            
    except subprocess.TimeoutExpired:
        print(f"[FEHLER] Timeout nach 300 Sekunden.")
        FEHLER += 1
        log_eintrag["fehler"] += 1
        log_eintrag["status"] = "TIMEOUT"
        log_eintrag["hinweise"].append("Timeout nach 300s")
        SCHRITTE_LOG.append(log_eintrag)
        return False
    except Exception as e:
        print(f"[FEHLER] Ausführung fehlgeschlagen: {e}")
        FEHLER += 1
        log_eintrag["fehler"] += 1
        log_eintrag["status"] = "FEHLER"
        log_eintrag["hinweise"].append(str(e))
        SCHRITTE_LOG.append(log_eintrag)
        return False
    
    SCHRITTE_LOG.append(log_eintrag)
    return True


def oeffne_ui13_html(cfg):
    global WARNUNGEN
    html_pfad = cfg.get("nachlauf", {}).get("html_pfad", "Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT.html")
    abs_pfad = os.path.abspath(html_pfad)
    
    if os.path.exists(abs_pfad):
        print(f"\n[INFO] Öffne UI13-Entscheidungsseite: {abs_pfad}")
        try:
            webbrowser.open(f"file:///{abs_pfad.replace(os.sep, '/')}")
            print("[OK] Browser geöffnet.")
            return True
        except Exception as e:
            print(f"[WARNUNG] Browser konnte nicht geöffnet werden: {e}")
            WARNUNGEN += 1
            return False
    else:
        print(f"[WARNUNG] UI13-HTML nicht gefunden: {abs_pfad}")
        WARNUNGEN += 1
        return False


def generiere_bericht(cfg):
    global FEHLER, WARNUNGEN
    bericht_pfad = cfg.get("bericht", {}).get("ausgabe_pfad", "Windows_App/Logs/UI14_NACHLAUFZENTRALE_BERICHT.txt")
    zusammenfassung_pfad = cfg.get("bericht", {}).get("zusammenfassung_pfad", "Windows_App/Logs/UI14_ZUSAMMENFASSUNG.json")
    
    # Zusammenfassung JSON
    zusammenfassung = {
        "meta": {
            "modul_id": "UI14",
            "name": "Ausführungs- und Nachlaufzentrale",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "demo_modus": True
        },
        "schritte": SCHRITTE_LOG,
        "gesamt": {
            "fehler": FEHLER,
            "warnungen": WARNUNGEN,
            "schritte_gesamt": len(SCHRITTE_LOG),
            "schritte_ok": len([s for s in SCHRITTE_LOG if s["status"] == "OK"]),
            "schritte_warnung": len([s for s in SCHRITTE_LOG if s["status"] == "WARNUNG"]),
            "schritte_fehler": len([s for s in SCHRITTE_LOG if s["status"] == "FEHLER"])
        }
    }
    
    try:
        os.makedirs(os.path.dirname(zusammenfassung_pfad), exist_ok=True)
        with open(zusammenfassung_pfad, "w", encoding="utf-8") as f:
            json.dump(zusammenfassung, f, ensure_ascii=False, indent=2)
        print(f"[OK] Zusammenfassung JSON: {zusammenfassung_pfad}")
    except Exception as e:
        print(f"[FEHLER] Zusammenfassung JSON fehlgeschlagen: {e}")
        FEHLER += 1
    
    # Text-Bericht
    try:
        os.makedirs(os.path.dirname(bericht_pfad), exist_ok=True)
        with open(bericht_pfad, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("UI14 – AUSFUEHRUNGS- UND NACHLAUFZENTRALE BERICHT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Zeitstempel: {zusammenfassung['meta']['zeitstempel']}\n")
            f.write(f"Demo-Modus: {zusammenfassung['meta']['demo_modus']}\n\n")
            f.write("SCHRITTE\n")
            f.write("-" * 40 + "\n")
            for s in SCHRITTE_LOG:
                status_icon = "✓" if s["status"] == "OK" else "⚠" if s["status"] == "WARNUNG" else "✗"
                f.write(f"{status_icon} Schritt {s['schritt']}: {s['modul_id']} – {s['name']} [{s['status']}]\n")
                if s["hinweise"]:
                    for h in s["hinweise"]:
                        f.write(f"    Hinweis: {h}\n")
            f.write("\n")
            f.write("GESAMT\n")
            f.write("-" * 40 + "\n")
            f.write(f"Fehler:     {FEHLER}\n")
            f.write(f"Warnungen:  {WARNUNGEN}\n")
            f.write(f"Schritte:   {len(SCHRITTE_LOG)}\n")
            f.write(f"  OK:       {zusammenfassung['gesamt']['schritte_ok']}\n")
            f.write(f"  Warnung:  {zusammenfassung['gesamt']['schritte_warnung']}\n")
            f.write(f"  Fehler:   {zusammenfassung['gesamt']['schritte_fehler']}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("ENDE BERICHT\n")
        print(f"[OK] Bericht: {bericht_pfad}")
    except Exception as e:
        print(f"[FEHLER] Bericht fehlgeschlagen: {e}")
        FEHLER += 1


def hauptlauf():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI14 – AUSFUEHRUNGS- UND NACHLAUFZENTRALE UI08–UI13")
    print("=" * 60)
    
    cfg_pfad = "Config/ui14_ausfuehrungs_nachlaufzentrale_v1.json"
    cfg = load_json(cfg_pfad)
    if cfg is None:
        print("[FEHLER] Config nicht ladbar. Abbruch.")
        FEHLER += 1
        return
    
    # Sperrregister prüfen
    sperr = pruefe_sperrregister("UI14")
    if sperr:
        print(f"[FEHLER] UI14 ist im Sperrregister gesperrt.")
        FEHLER += 1
        return
    print("[OK] Sperrregister: UI14 nicht gesperrt.")
    
    # Python finden
    py_cmd = finde_python()
    print(f"[INFO] Verwende Python: {py_cmd}")
    
    # Schritte ausführen
    reihenfolge = cfg.get("ausfuehrungsreihenfolge", [])
    max_warn = cfg.get("fehlerbehandlung", {}).get("max_erlaubte_warnungen", 50)
    max_fehler = cfg.get("fehlerbehandlung", {}).get("max_erlaubte_fehler", 0)
    
    for schritt in reihenfolge:
        erfolg = fuehre_schritt_aus(schritt, py_cmd)
        
        # Abbruch bei zu vielen Fehlern
        if FEHLER > max_fehler and max_fehler >= 0:
            print(f"\n[FEHLER] Maximal erlaubte Fehler ({max_fehler}) überschritten. Abbruch.")
            break
        
        # Abbruch bei zu vielen Warnungen
        if WARNUNGEN > max_warn and max_warn >= 0:
            print(f"\n[WARNUNG] Maximal erlaubte Warnungen ({max_warn}) überschritten. Abbruch.")
            break
    
    # Bericht erzeugen
    generiere_bericht(cfg)
    
    # UI13 HTML öffnen
    if cfg.get("nachlauf", {}).get("automatisch_oeffnen", True):
        oeffne_ui13_html(cfg)
    
    print("\n" + "=" * 60)
    print(f"UI14 abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


def selbsttest():
    global FEHLER, WARNUNGEN
    print("UI14 SELBSTTEST =====================================")
    
    def t(bez, bed):
        global FEHLER
        if not bed:
            print(f"[SELBSTTEST FEHLER] {bez}")
            FEHLER += 1
        else:
            print(f"[SELBSTTEST OK] {bez}")
    
    # Test 1: Config laden
    cfg = load_json("Config/ui14_ausfuehrungs_nachlaufzentrale_v1.json")
    t("Config ladbar", cfg is not None)
    
    # Test 2: 8 Schritte definiert
    t("8 Schritte definiert", len(cfg.get("ausfuehrungsreihenfolge", [])) == 8)
    
    # Test 3: Reihenfolge korrekt
    schritte = cfg.get("ausfuehrungsreihenfolge", [])
    t("Schritt 1 = UI08", schritte[0]["modul_id"] == "UI08")
    t("Schritt 8 = UI13", schritte[7]["modul_id"] == "UI13")
    
    # Test 4: Demo-Modus
    demo = cfg.get("demo_modus", {})
    t("Demo-Modus aktiv", demo.get("produktiv_freigegeben") is False)
    
    # Test 5: Freeze-Grenzen
    freeze = cfg.get("freeze_grenzen", {})
    t("Freeze: beruehrt_ui03_ui07b=false", freeze.get("beruehrt_ui03_ui07b") is False)
    
    # Test 6: Nachlauf definiert
    t("Nachlauf HTML definiert", bool(cfg.get("nachlauf", {}).get("html_pfad")))
    
    # Test 7: Bericht definiert
    t("Bericht definiert", bool(cfg.get("bericht", {}).get("ausgabe_pfad")))
    
    print(f"\nSELBSTTEST ENDE – Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        selbsttest()
    else:
        hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
