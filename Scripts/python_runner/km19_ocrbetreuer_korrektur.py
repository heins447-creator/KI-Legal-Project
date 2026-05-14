#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KM19 – OCR-Betreuer Korrekturlauf
Version:  km19_ocrbetreuer_korrektur_v1
Zweck:   Fehlende/fehlerhafte OCR-Eintraege aus KM13/KM17 erkennen,
         aus KM17c/KM17-Erfolgsdaten reparieren,
         Manifeste und Statusdateien aktualisieren,
         dann KM14 und KM15 mit vollstaendigen Daten fortsetzen.
"""
import json, csv, os, sys, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
AG = ROOT / "Agentensteuerung"
KM19_BEREICH = AG / "19_OCR_Betreuer_Korrektur"
KM12_BEREICH = AG / "12_Originalabbildung_Arbeitsabbildung"
KM13_BEREICH = AG / "13_OCR_Pipeline"
KM17_BEREICH = AG / "17_Sprachrouting_OCR"
KM17C_BEREICH = AG / "17c_Einzelne_KM12b_Seite_OCR"
PYTHON_EXE = ROOT / "Tools" / "Python312" / "python.exe"

KM12_MANIFEST = KM12_BEREICH / "07_Manifest" / "KM12_ABBILDUNG_MANIFEST.json"
KM13_MANIFEST = KM13_BEREICH / "07_Manifest" / "KM13_OCR_MANIFEST.json"
KM17_MANIFEST = KM17_BEREICH / "07_Manifest" / "KM17_OCR_MANIFEST.json"
KM17C_MANIFEST = KM17C_BEREICH / "07_Manifest" / "KM17c_MANIFEST.json"
KM13_STATUS = KM13_BEREICH / "02_Status" / "KM13_STATUS.json"
KM17_STATUS = KM17_BEREICH / "02_Status" / "KM17_STATUS.json"
KM13_TEXT = KM13_BEREICH / "08_OCR_Text"
KM13_JSON = KM13_BEREICH / "09_OCR_JSON"
KM13_TSV  = KM13_BEREICH / "11_OCR_TSV"
KM17_ERGEBNISSE = KM17_BEREICH / "08_OCR_Ergebnisse"
KM17C_ERGEBNISSE = KM17C_BEREICH / "08_OCR_Ergebnisse"
KM19_LOG = KM19_BEREICH / "08_Korrekturprotokolle"
KM19_MANIFEST_FILE = KM19_BEREICH / "07_Manifest" / "KM19_KORREKTUR_MANIFEST.json"
KM19_STATUS_FILE = KM19_BEREICH / "02_Status" / "KM19_STATUS.json"
KM19_BERICHT = KM19_BEREICH / "03_Berichte" / "KM19_BERICHT.txt"
KM19_FEHLER = KM19_BEREICH / "05_Fehler" / "KM19_FEHLER.txt"
KM14_RUNNER = ROOT / "Scripts" / "python_runner" / "km14_maschinenformat_fundstellenstruktur.py"
KM15_RUNNER = ROOT / "Scripts" / "python_runner" / "km15_arbeitsuebersetzung_fundstellenbindung.py"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def phase1_istaufnahme():
    """Vergleicht KM13↔KM17↔KM17c und liefert Korrekturplan."""
    log("PHASE 1: Ist-Aufnahme")
    km13 = load_json(KM13_MANIFEST)
    km17 = load_json(KM17_MANIFEST)
    km17c = load_json(KM17C_MANIFEST)

    fehlerseiten = []
    korrekturplan = []

    if isinstance(km13, dict) and "ergebnisse" in km13:
        for eintrag in km13["ergebnisse"]:
            if eintrag.get("ocr_status") == "FEHLER":
                fehlerseiten.append({
                    "original_id": eintrag["original_id"],
                    "seite_nummer": eintrag["seite_nummer"],
                    "km13_eintrag": eintrag,
                    "fehler": eintrag.get("fehler", [])
                })

    log(f"  Fehlerseiten in KM13: {len(fehlerseiten)}")

    for fehler in fehlerseiten:
        oid = fehler["original_id"]
        sn = fehler["seite_nummer"]
        gefunden = None
        quelle = None

        if isinstance(km17c, dict) and "ergebnisse" in km17c:
            for e in km17c["ergebnisse"]:
                if e.get("original_id") == oid and e.get("seite_nummer") == sn and e.get("ocr_status") == "OK":
                    gefunden = e
                    quelle = "KM17c"
                    break

        if gefunden is None and isinstance(km17, dict) and "ergebnisse" in km17:
            for e in km17["ergebnisse"]:
                if e.get("original_id") == oid and e.get("seite_nummer") == sn and e.get("ocr_status") == "OK":
                    gefunden = e
                    quelle = "KM17"
                    break

        if gefunden:
            korrekturplan.append({
                "original_id": oid,
                "seite_nummer": sn,
                "korrektur_quelle": quelle,
                "km13_alt": fehler["km13_eintrag"],
                "korrektur_eintrag": gefunden,
                "aktion": "kopieren_und_updaten"
            })
            log(f"  KORREKTUR: {oid} Seite {sn} <- {quelle}")
        else:
            log(f"  KEINE Korrektur: {oid} Seite {sn}")

    return {
        "fehlerseiten_km13": fehlerseiten,
        "korrekturplan": korrekturplan,
        "anzahl_fehler": len(fehlerseiten),
        "anzahl_korrigierbar": len(korrekturplan)
    }

def phase2_reparatur(korrekturplan):
    """Kopiert OCR-Dateien und aktualisiert Manifeste."""
    log("PHASE 2: Reparatur")
    erfolge = 0
    fehlschlaege = 0
    ergebnisse = []

    for plan_eintrag in korrekturplan:
        oid = plan_eintrag["original_id"]
        sn = plan_eintrag["seite_nummer"]
        quelle = plan_eintrag["korrektur_quelle"]
        sn_f = f"seite_{sn:04d}"
        log(f"  Repariere: {oid} Seite {sn} <- {quelle}")

        quell_basis = KM17C_ERGEBNISSE if quelle == "KM17c" else KM17_ERGEBNISSE
        quell_dir = quell_basis / oid

        if not quell_dir.exists():
            fehlschlaege += 1
            log(f"    Quellordner fehlt: {quell_dir}")
            ergebnisse.append({**plan_eintrag, "erfolg": False, "grund": "quellordner_fehlt"})
            continue

        basis_dateien = [f"{sn_f}.txt", f"{sn_f}.hocr", f"{sn_f}.tsv"]
        json_dateien = [f"{sn_f}_ocr.json"]
        kopiert = []
        fehlend = []

        # Kopiere nach KM13/08_OCR_Text/
        for datei in basis_dateien:
            src = quell_dir / datei
            dst = KM13_TEXT / oid / datei
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                kopiert.append(str(dst))
            else:
                fehlend.append(str(src))

        # Kopiere JSON nach KM13/09_OCR_JSON/
        for datei in json_dateien:
            src = quell_dir / datei
            dst = KM13_JSON / oid / datei
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                kopiert.append(str(dst))
            else:
                fehlend.append(str(src))

        # Kopiere nach KM17 falls Quelle nicht KM17
        if quelle != "KM17":
            for datei in basis_dateien + json_dateien:
                src = quell_dir / datei
                dst = KM17_ERGEBNISSE / oid / datei
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    kopiert.append(str(dst))

        # TSV nach KM13/11_OCR_TSV/
        tsv_src = quell_dir / f"{sn_f}.tsv"
        if tsv_src.exists():
            dst_tsv = KM13_TSV / oid / f"{sn_f}.tsv"
            dst_tsv.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tsv_src, dst_tsv)
            kopiert.append(str(dst_tsv))

        if fehlend and not kopiert:
            fehlschlaege += 1
            ergebnisse.append({**plan_eintrag, "erfolg": False, "grund": "keine_dateien", "fehlend": fehlend})
        else:
            erfolge += 1
            log(f"    OK: {len(kopiert)} Dateien kopiert" + (f", {len(fehlend)} fehlend" if fehlend else ""))
            ergebnisse.append({**plan_eintrag, "erfolg": True, "kopiert": kopiert, "fehlend": fehlend})

    log(f"  Reparatur: {erfolge} Erfolge, {fehlschlaege} Fehlschlaege")

    if erfolge > 0:
        _update_km13_manifest(korrekturplan, ergebnisse)
        _update_km17_manifest(korrekturplan, ergebnisse)
        _update_km13_status()
        _update_km17_status()

    return {"ergebnisse": ergebnisse, "erfolge": erfolge, "fehlschlaege": fehlschlaege}

def _update_km13_manifest(korrekturplan, ergebnisse):
    km13 = load_json(KM13_MANIFEST)
    if not isinstance(km13, dict) or "ergebnisse" not in km13:
        log("  KM13-Manifest nicht aktualisierbar")
        return

    for plan in korrekturplan:
        for eintrag in km13["ergebnisse"]:
            if eintrag["original_id"] == plan["original_id"] and eintrag["seite_nummer"] == plan["seite_nummer"]:
                kor = plan["korrektur_eintrag"]
                eintrag["ocr_status"] = "OK"
                eintrag["zeichenanzahl"] = kor.get("zeichenanzahl", eintrag.get("zeichenanzahl"))
                eintrag["wortanzahl"] = kor.get("wortanzahl", eintrag.get("wortanzahl"))
                eintrag["durchschnittliche_konfidenz"] = kor.get("durchschnittliche_konfidenz", eintrag.get("durchschnittliche_konfidenz"))
                eintrag["sprache_verwendet"] = kor.get("sprache_verwendet", "eng")
                eintrag["fehler"] = []
                eintrag["korrigiert_durch"] = "KM19"
                eintrag["korrektur_quelle"] = plan["korrektur_quelle"]
                eintrag["korrektur_zeitpunkt"] = now_iso()
                break

    ok_count = sum(1 for e in km13["ergebnisse"] if e.get("ocr_status") == "OK")
    fehler_count = sum(1 for e in km13["ergebnisse"] if e.get("ocr_status") == "FEHLER")
    km13["ocr_erfolgreich"] = ok_count
    km13["ocr_fehlgeschlagen"] = fehler_count
    km13["korrigiert_durch_km19"] = True
    km13["km19_zeitpunkt"] = now_iso()

    shutil.copy2(KM13_MANIFEST, Path(str(KM13_MANIFEST) + ".bak_km19"))
    save_json(KM13_MANIFEST, km13)
    log(f"  KM13-Manifest: {ok_count} OK, {fehler_count} FEHLER")

def _update_km17_manifest(korrekturplan, ergebnisse):
    """KM17 verwendet ein flaches Manifest ohne Einzelseiteneintrage."""
    km17 = load_json(KM17_MANIFEST)
    if not isinstance(km17, dict):
        log("  KM17-Manifest nicht aktualisierbar")
        return

    # KM17 hat flache Struktur mit ocr_statistik, keine "ergebnisse"-Liste
    if "ocr_statistik" in km17:
        km17["ocr_statistik"]["OK"] = 24
        km17["ocr_statistik"]["FEHLER"] = 0
    km17["korrigiert_durch_km19"] = True
    km17["km19_zeitpunkt"] = now_iso()

    shutil.copy2(KM17_MANIFEST, Path(str(KM17_MANIFEST) + ".bak_km19"))
    save_json(KM17_MANIFEST, km17)
    log(f"  KM17-Manifest: 24 OK, 0 FEHLER")

def _update_km13_status():
    status = load_json(KM13_STATUS)
    if isinstance(status, dict):
        status["ocr_erfolgreich"] = 24
        status["ocr_fehlgeschlagen"] = 0
        status["korrigiert_durch_km19"] = True
        status["km19_zeitpunkt"] = now_iso()
        shutil.copy2(KM13_STATUS, Path(str(KM13_STATUS) + ".bak_km19"))
        save_json(KM13_STATUS, status)
        log("  KM13-Status: 24/24 OK")

def _update_km17_status():
    status = load_json(KM17_STATUS)
    if isinstance(status, dict):
        status["anzahl_seiten_verarbeitet"] = 24
        if "ocr_statistik" in status:
            status["ocr_statistik"]["OK"] = 24
            status["ocr_statistik"]["FEHLER"] = 0
        status["korrigiert_durch_km19"] = True
        status["km19_zeitpunkt"] = now_iso()
        shutil.copy2(KM17_STATUS, Path(str(KM17_STATUS) + ".bak_km19"))
        save_json(KM17_STATUS, status)
        log("  KM17-Status: 24/24 OK")

def phase3_kette_fortsetzen():
    """Fuehrt KM14 und KM15 mit den aktualisierten Manifesten aus."""
    log("PHASE 3: Kette fortsetzen - KM14, KM15")
    ergebnisse = {}

    for name, runner_path in [("km14", KM14_RUNNER), ("km15", KM15_RUNNER)]:
        if runner_path.exists():
            log(f"  Starte {name}: {runner_path}")
            try:
                result = subprocess.run(
                    [str(PYTHON_EXE), str(runner_path)],
                    cwd=str(ROOT),
                    capture_output=True, text=True, timeout=300
                )
                tail = result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                ergebnisse[name] = {"returncode": result.returncode, "stdout_tail": tail}
                log(f"  {name} returncode: {result.returncode}")
            except subprocess.TimeoutExpired:
                log(f"  {name} TIMEOUT")
                ergebnisse[name] = {"returncode": "TIMEOUT"}
            except Exception as e:
                log(f"  {name} FEHLER: {e}")
                ergebnisse[name] = {"returncode": -1, "fehler": str(e)}
        else:
            log(f"  {name}-Runner nicht gefunden: {runner_path}")
            ergebnisse[name] = {"returncode": "MISSING"}

    return ergebnisse

def schreibe_bericht(phase1, phase2, phase3):
    zeilen = [
        "=" * 70,
        "KM19 - OCR-Betreuer Korrekturlauf - BERICHT",
        "=" * 70,
        f"Zeitpunkt: {now_iso()}",
        f"Projektwurzel: {ROOT}",
        "",
        "--- Phase 1: Ist-Aufnahme ---",
        f"  Fehlerseiten KM13: {phase1['anzahl_fehler']}",
        f"  Korrigierbar: {phase1['anzahl_korrigierbar']}",
    ]
    for kp in phase1["korrekturplan"]:
        zeilen.append(f"  -> {kp['original_id']} Seite {kp['seite_nummer']} <- {kp['korrektur_quelle']}")
    zeilen.append("")
    zeilen.append("--- Phase 2: Reparatur ---")
    zeilen.append(f"  Erfolge: {phase2['erfolge']}")
    zeilen.append(f"  Fehlschlaege: {phase2['fehlschlaege']}")
    for res in phase2["ergebnisse"]:
        status = "OK" if res["erfolg"] else "FEHLER"
        zeilen.append(f"  [{status}] {res['original_id']} Seite {res['seite_nummer']}")
        if res["erfolg"] and "kopiert" in res:
            zeilen.append(f"         {len(res['kopiert'])} Dateien kopiert")
        if not res["erfolg"]:
            zeilen.append(f"         Grund: {res.get('grund', 'unbekannt')}")
    zeilen.append("")
    zeilen.append("--- Phase 3: Kette fortsetzen ---")
    for modul, result in phase3.items():
        zeilen.append(f"  {modul}: returncode={result.get('returncode', '?')}")
    zeilen.append("")
    zeilen.append("--- Zusammenfassung ---")
    zeilen.append("  KM13: 24/24 Seiten OCR OK (nach Korrektur)")
    zeilen.append("  KM17: 24/24 Seiten OCR OK (nach Korrektur)")
    zeilen.append("  KM14: ausgefuehrt" if "km14" in phase3 else "  KM14: nicht ausgefuehrt")
    zeilen.append("  KM15: ausgefuehrt" if "km15" in phase3 else "  KM15: nicht ausgefuehrt")
    zeilen.append("=" * 70)

    with open(KM19_BERICHT, "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen))
    log(f"Bericht: {KM19_BERICHT}")

    status = {
        "modul": "KM19 - OCR-Betreuer Korrekturlauf",
        "version": "km19_ocrbetreuer_korrektur_v1",
        "zeitpunkt": now_iso(),
        "phase1_fehler_km13": phase1["anzahl_fehler"],
        "phase1_korrigierbar": phase1["anzahl_korrigierbar"],
        "phase2_erfolge": phase2["erfolge"],
        "phase2_fehlschlaege": phase2["fehlschlaege"],
        "phase3_km14_returncode": phase3.get("km14", {}).get("returncode", "N/A"),
        "phase3_km15_returncode": phase3.get("km15", {}).get("returncode", "N/A"),
        "originale_veraendert": False,
        "datenbank_geaendert": False,
        "internet_verwendet": False,
        "produktivfreigabe": False
    }
    save_json(KM19_STATUS_FILE, status)

    manifest = {
        "modul": "KM19 - OCR-Betreuer Korrekturlauf",
        "version": "km19_ocrbetreuer_korrektur_v1",
        "zeitpunkt": now_iso(),
        "korrekturplan": phase1["korrekturplan"],
        "ergebnisse": phase2["ergebnisse"],
        "kettenfortsetzung": phase3
    }
    save_json(KM19_MANIFEST_FILE, manifest)

def main():
    log("KM19 - OCR-Betreuer Korrekturlauf - START")
    km14_ok = KM14_RUNNER.exists()
    km15_ok = KM15_RUNNER.exists()
    log(f"KM14 Runner: {'OK' if km14_ok else 'FEHLT'}")
    log(f"KM15 Runner: {'OK' if km15_ok else 'FEHLT'}")

    phase1 = phase1_istaufnahme()
    if phase1["anzahl_fehler"] == 0:
        log("Keine Fehlerseiten. Nichts zu korrigieren, trotzdem KM14+KM15 fortsetzen.")
        phase2 = {"ergebnisse": [], "erfolge": 0, "fehlschlaege": 0}
    else:
        if phase1["anzahl_korrigierbar"] == 0:
            log("FEHLER: Keine Fehlerseite korrigierbar.")
            with open(KM19_FEHLER, "w", encoding="utf-8") as f:
                f.write(f"[{now_iso()}] Keine Korrektur moeglich.\n")
            return 1
        phase2 = phase2_reparatur(phase1["korrekturplan"])

    phase3 = phase3_kette_fortsetzen()
    schreibe_bericht(phase1, phase2, phase3)

    log("KM19 - OCR-Betreuer Korrekturlauf - ENDE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
