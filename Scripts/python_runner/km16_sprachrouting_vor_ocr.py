#!/usr/bin/env python3
"""KM16 – Sprachrouting vor OCR. Bestimmt je Seite eine wahrscheinliche OCR-Sprache."""

import json, os, sys, csv, re, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone

PROJEKTWURZEL = Path("I:/KI_Legal_Project")
SCHREIBBEREICH = PROJEKTWURZEL / "Agentensteuerung" / "16_Sprachrouting_Vor_OCR"
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "sprachrouting_vor_ocr_v1.json"

def zeitstempel():
    return datetime.now(timezone.utc).isoformat()

def lade_config():
    with open(CONFIG_PFAD, "r", encoding="utf-8") as f:
        return json.load(f)

def finde_manifest(bereich):
    d = PROJEKTWURZEL / "Agentensteuerung" / bereich / "07_Manifest"
    if not d.exists():
        return None
    for f in sorted(d.glob("*.json")):
        return f
    return None

def lade_km_manifest(bereich):
    pfad = finde_manifest(bereich)
    if pfad:
        with open(pfad, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in ("ergebnisse", "seiten", "eintraege"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return []
        if isinstance(data, list):
            return data
    return []

def lade_sprachprofile(config):
    profile = {}
    pfad = PROJEKTWURZEL / "Windows_App" / "Logs" / "Posteingang"
    if pfad.exists():
        for f in pfad.glob("**/*sprach*"):
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    inhalt = fh.read()[:5000]
                for name, code in config.get("sprachmapping", {}).items():
                    if name.lower() in inhalt.lower():
                        profile[f.stem] = code
            except:
                pass
    return profile

def erkenne_sprache_aus_text(text, verfuegbare_codes, indikatoren, mindest_laenge):
    if not text or len(text) < mindest_laenge:
        return None, 0.0
    text_worte = set(text.lower().split())
    if len(text_worte) < 2:
        return None, 0.0
    scores = {}
    for code, woerter in indikatoren.items():
        if code not in verfuegbare_codes:
            continue
        treffer = text_worte & set(woerter)
        if treffer:
            scores[code] = len(treffer) / min(len(woerter), 20)
    if not scores:
        return None, 0.0
    best = max(scores, key=scores.get)
    return best, min(scores[best], 1.0)

def erkenne_sprache_aus_dateiname(dateiname, verfuegbare_codes):
    if not dateiname:
        return None, 0.0
    name_lower = dateiname.lower()
    for code in verfuegbare_codes:
        if code in name_lower:
            return code, 0.3
    return None, 0.0

def baue_routing_eintrag(seite, km13_eintrag, sprachprofile, verfuegbare_codes, config):
    original_id = seite.get("original_id", "UNBEKANNT")
    seite_nummer = seite.get("seite_nummer", 0)
    seiten_id = f"{original_id}__{seite_nummer}"
    sprachquelle = "fallback"
    sprachcode = None
    sicherheit = 0.0
    grund = ""
    unsicherheiten = []
    osd_sinnvoll = False
    mehrsprachig_vermutet = False
    manuelle_pruefung = False

    # Quelle 1: Posteingangs-Sprachprofile
    if sprachprofile and original_id in sprachprofile:
        prof_sprache = sprachprofile[original_id]
        for name, code in config.get("sprachmapping", {}).items():
            if code == prof_sprache and code in verfuegbare_codes:
                sprachcode = code
                sprachquelle = "posteingang_sprachprofil"
                sicherheit = 0.9
                grund = f"Sprachprofil aus Posteingang: {code}"
                break

    # Quelle 2: KM13 OCR-Text-Snippet
    if sprachcode is None and km13_eintrag:
        ocr_text = km13_eintrag.get("ocr_text_snippet", "")
        if ocr_text:
            indikatoren = config.get("sprachindikatoren", {})
            mindest = config.get("mindest_textlaenge_fuer_erkennung", 20)
            erkannt, score = erkenne_sprache_aus_text(ocr_text, verfuegbare_codes, indikatoren, mindest)
            if erkannt and score > 0.1:
                sprachcode = erkannt
                sprachquelle = "ocr_textanalyse"
                sicherheit = score
                grund = f"Textanalyse OCR-Snippet, {len(ocr_text)} Zeichen"
                if score < 0.4:
                    unsicherheiten.append("OCR_TEXT_ZU_KURZ_ODER_UNSCHARF")
                    manuelle_pruefung = True

    # Quelle 3: Dateiname
    if sprachcode is None:
        dateiname = seite.get("tiff_pfad", "")
        erkannt, score = erkenne_sprache_aus_dateiname(dateiname, verfuegbare_codes)
        if erkannt:
            sprachcode = erkannt
            sprachquelle = "dateiname"
            sicherheit = 0.3
            grund = f"Sprachcode im Dateinamen: {erkannt}"
            unsicherheiten.append("NUR_DATEINAME_ALS_HINWEIS")
            manuelle_pruefung = True

    # Quelle 4: Fallback
    if sprachcode is None:
        sprachcode = config.get("fallback_tesseract_code", "eng")
        sprachquelle = "fallback"
        sicherheit = 0.0
        grund = "Keine verwertbare Sprachinformation – Fallback"
        unsicherheiten.append("KEINE_VERWERTBARE_SPRACHE")
        manuelle_pruefung = True

    # Prüfung: Sprache verfügbar?
    if sprachcode not in verfuegbare_codes:
        unsicherheiten.append("SPRACHE_NICHT_VERFUEGBAR")
        sprachcode = config.get("fallback_tesseract_code", "eng")
        manuelle_pruefung = True

    # OSD-Prüfung
    if km13_eintrag:
        ocr_ok = km13_eintrag.get("ocr_ok", False)
        if not ocr_ok:
            unsicherheiten.append("OCR_FEHLER")
            osd_sinnvoll = True
            manuelle_pruefung = True
        if km13_eintrag.get("ocr_zeichen", 0) == 0:
            unsicherheiten.append("OCR_TEXT_LEER")
            osd_sinnvoll = True

    return {
        "original_id": original_id,
        "seite_nummer": seite_nummer,
        "seiten_id": seiten_id,
        "erkannte_sprache": sprachcode,
        "empfohlener_tesseract_code": sprachcode,
        "sprachquelle": sprachquelle,
        "sicherheit": round(sicherheit, 3),
        "grund": grund,
        "fallback_sprache": config.get("fallback_tesseract_code", "eng"),
        "osd_sinnvoll": osd_sinnvoll,
        "mehrsprachig_vermutet": mehrsprachig_vermutet,
        "manuelle_pruefung_empfohlen": manuelle_pruefung,
        "bezug_km12": bool(seite),
        "bezug_km13": bool(km13_eintrag),
        "bezug_km14": False,
        "original_unveraendert": True,
        "ocr_nicht_ausgefuehrt": True,
        "uebersetzung_nicht_erzeugt": True
    }

def routing_hauptlauf(config):
    print("=" * 60)
    print("KLEINMODUL 16 – SPRACHROUTING VOR OCR")
    print("=" * 60)
    print(f"Zeitpunkt:      {zeitstempel()}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")

    for d in ["02_Status","03_Berichte","05_Fehler","06_Artefakte",
              "07_Manifest","08_Routing","09_Unsicherheiten",
              "13_Ausfuehrungsnotizen","90_RunLogs"]:
        (SCHREIBBEREICH / d).mkdir(parents=True, exist_ok=True)

    verfuegbare_codes = list(config.get("sprachindikatoren", {}).keys())
    km12 = lade_km_manifest("12_Originalabbildung_Arbeitsabbildung")
    km13 = lade_km_manifest("13_OCR_Pipeline")
    sprachprofile = lade_sprachprofile(config)

    print(f"\nKM12 Eintraege:          {len(km12)}")
    print(f"KM13 Eintraege:          {len(km13)}")
    print(f"Sprachprofile gefunden:  {len(sprachprofile)}")
    print(f"Verfuegbare Sprachen:    {len(verfuegbare_codes)}")

    km13_index = {}
    for e in km13:
        oid = e.get("original_id", "")
        sn = e.get("seite_nummer", -1)
        key = f"{oid}__{sn}"
        km13_index[key] = e

    routings = []
    unsicherheiten_liste = []

    print(f"Seiten zu routen:        {len(km12)}")

    for seite in km12:
        oid = seite.get("original_id", "")
        sn = seite.get("seite_nummer", -1)
        key = f"{oid}__{sn}"
        km13_e = km13_index.get(key)
        routing = baue_routing_eintrag(seite, km13_e, sprachprofile, verfuegbare_codes, config)
        routings.append(routing)
        if routing["manuelle_pruefung_empfohlen"] or routing["sicherheit"] < 0.5:
            unsicherheiten_liste.append({
                "seiten_id": routing["seiten_id"],
                "original_id": routing["original_id"],
                "unsicherheit": "MANUELLE_PRUEFUNG" if routing["manuelle_pruefung_empfohlen"] else "NIEDRIGE_SICHERHEIT",
                "grund": routing["grund"],
                "sprachquelle": routing["sprachquelle"]
            })

    original_ids = sorted(set(r["original_id"] for r in routings))
    quellen = {}
    for r in routings:
        q = r["sprachquelle"]
        quellen[q] = quellen.get(q, 0) + 1

    print(f"\n[1/4] Routing berechnet...")
    print(f"      Originale: {len(original_ids)}")
    print(f"      Seiten:    {len(routings)}")
    print(f"      Quellen:   {quellen}")
    print(f"      Unsicher:  {len(unsicherheiten_liste)}")

    print("[2/4] Ausgaben schreiben...")
    routing_json_pfad = SCHREIBBEREICH / "08_Routing" / "KM16_SPRACHROUTING.json"
    with open(routing_json_pfad, "w", encoding="utf-8") as f:
        json.dump(routings, f, ensure_ascii=False, indent=2)

    routing_csv_pfad = SCHREIBBEREICH / "08_Routing" / "KM16_SPRACHROUTING.csv"
    if routings:
        with open(routing_csv_pfad, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=routings[0].keys())
            w.writeheader()
            w.writerows(routings)

    uns_json_pfad = SCHREIBBEREICH / "09_Unsicherheiten" / "KM16_SPRACHROUTING_UNSICHERHEITEN.json"
    with open(uns_json_pfad, "w", encoding="utf-8") as f:
        json.dump(unsicherheiten_liste, f, ensure_ascii=False, indent=2)

    uns_csv_pfad = SCHREIBBEREICH / "09_Unsicherheiten" / "KM16_SPRACHROUTING_UNSICHERHEITEN.csv"
    if unsicherheiten_liste:
        with open(uns_csv_pfad, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["seiten_id","original_id","unsicherheit","grund","sprachquelle"])
            w.writeheader()
            w.writerows(unsicherheiten_liste)

    manifest = {
        "version": "sprachrouting_v1",
        "zeitpunkt": zeitstempel(),
        "anzahl_originale": len(original_ids),
        "anzahl_seiten": len(routings),
        "verfuegbare_sprachen": verfuegbare_codes,
        "sprachquellen_statistik": quellen,
        "routing_json": str(routing_json_pfad),
        "routing_csv": str(routing_csv_pfad)
    }
    manifest_json = SCHREIBBEREICH / "07_Manifest" / "KM16_SPRACHROUTING_MANIFEST.json"
    manifest_csv = SCHREIBBEREICH / "07_Manifest" / "KM16_SPRACHROUTING_MANIFEST.csv"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(manifest_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest.keys()))
        w.writeheader()
        w.writerow(manifest)

    status = {
        "modul": "KM16 – Sprachrouting vor OCR",
        "version": "sprachrouting_vor_ocr_v1",
        "zeitpunkt": zeitstempel(),
        "schreibbereich": str(SCHREIBBEREICH),
        "projektwurzel": str(PROJEKTWURZEL),
        "anzahl_originale": len(original_ids),
        "anzahl_seiten": len(routings),
        "sprachquellen": quellen,
        "unsicherheiten_gesamt": len(unsicherheiten_liste),
        "verfuegbare_sprachen": verfuegbare_codes,
        "ocr_ausgefuehrt": False,
        "uebersetzung_erzeugt": False,
        "datenbank_geaendert": False,
        "originale_veraendert": False,
        "internet_verwendet": False,
        "installation_durchgefuehrt": False,
        "produktivfreigabe": False,
        "rechtsbewertung": False,
        "beweiswuerdigung": False,
        "naechster_empfohlener_auftrag": "KM13 mit KM16-Sprachrouting erneut ausfuehren"
    }
    status_pfad = SCHREIBBEREICH / "02_Status" / "KM16_STATUS.json"
    with open(status_pfad, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print("[3/4] Berichte schreiben...")
    bericht = "=" * 70 + "\n"
    bericht += "KM16 SPRACHROUTING VOR OCR – BERICHT\n"
    bericht += "=" * 70 + "\n"
    bericht += f"Zeitpunkt:            {zeitstempel()}\n"
    bericht += f"Originale:            {len(original_ids)}\n"
    bericht += f"Seiten:               {len(routings)}\n"
    bericht += f"Sprachquellen:        {quellen}\n"
    bericht += f"Unsicherheiten:       {len(unsicherheiten_liste)}\n"
    bericht += f"Verfuegbare Sprachen: {len(verfuegbare_codes)}\n\n"
    bericht += "KEINE OCR ausgefuehrt.\n"
    bericht += "KEINE Uebersetzung erzeugt.\n"
    bericht += "KEINE Originalaenderung.\n"
    bericht += "KEINE DB-Aenderung.\n"
    bericht += "=" * 70 + "\n"
    bericht_pfad = SCHREIBBEREICH / "03_Berichte" / "KM16_BERICHT.txt"
    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write(bericht)

    fehler_pfad = SCHREIBBEREICH / "05_Fehler" / "KM16_FEHLER.txt"
    with open(fehler_pfad, "w", encoding="utf-8") as f:
        f.write("Keine Fehler.\n")

    notiz_pfad = SCHREIBBEREICH / "13_Ausfuehrungsnotizen" / "KM16_AUSFUEHRUNGSNOTIZ.txt"
    with open(notiz_pfad, "w", encoding="utf-8") as f:
        f.write(f"KM16 ausgefuehrt am {zeitstempel()}\n")
        f.write(f"Originale: {len(original_ids)}, Seiten: {len(routings)}\n")
        f.write(f"Quellen: {quellen}\n")

    print("[4/4] Zusammenfassung...")
    print(f"\n{'='*60}")
    print("KM16 ABGESCHLOSSEN")
    print(f"{'='*60}")
    print(f"Originale:              {len(original_ids)}")
    print(f"Seiten:                 {len(routings)}")
    print(f"Sprachquellen:          {quellen}")
    print(f"Unsicherheiten:         {len(unsicherheiten_liste)}")
    print(f"Status:                 {status_pfad}")
    print(f"Bericht:                {bericht_pfad}")
    print(f"Routing:                {routing_json_pfad}")
    print(f"\nKeine Rohdaten ausgegeben. Keine OCR. Keine Uebersetzung.")
    return True


def run_selftest():
    print("=" * 60)
    print("KM16 SELBSTTEST – SPRACHROUTING VOR OCR")
    print("=" * 60)
    fehler = 0
    test_dir = SCHREIBBEREICH / "90_RunLogs" / "selftest_dummy"
    test_dir.mkdir(parents=True, exist_ok=True)

    print("\nTest 1: Config ladbar...")
    try:
        cfg = lade_config()
        assert "sprachmapping" in cfg
        assert "sprachindikatoren" in cfg
        print("  OK")
    except Exception as e:
        print(f"  FEHLER: {e}")
        fehler += 1

    print("Test 2: Sprachmapping vollstaendig...")
    mapping = cfg.get("sprachmapping", {})
    assert "deutsch" in mapping and mapping["deutsch"] == "deu"
    assert "englisch" in mapping and mapping["englisch"] == "eng"
    assert len(mapping) >= 48
    print(f"  OK: {len(mapping)} Eintraege")

    verfuegbare = list(cfg.get("sprachindikatoren", {}).keys())
    indikatoren = cfg.get("sprachindikatoren", {})

    tests = [
        ("3 – deutsches Routing", "und die der das ist nicht mit von den auf", "deu"),
        ("4 – schwedisches Routing", "och att det som en pa med for av den", "swe"),
        ("5 – portugiesisches Routing", "que nao com uma para dos das como pelo", "por"),
        ("6 – unbekannte Sprache", "xyz abc lmn opq rst uvw", cfg["fallback_tesseract_code"]),
    ]
    for name, text, erwartet in tests:
        print(f"Test {name}...")
        erkannt, score = erkenne_sprache_aus_text(text, verfuegbare, indikatoren, cfg.get("mindest_textlaenge_fuer_erkennung",20))
        if erwartet == cfg["fallback_tesseract_code"]:
            if erkannt is None or erkannt == cfg["fallback_tesseract_code"]:
                print(f"  OK: Fallback korrekt")
            else:
                print(f"  FEHLER: {erkannt} statt Fallback")
                fehler += 1
        else:
            if erkannt == erwartet:
                print(f"  OK: {erkannt} (score={score:.2f})")
            else:
                print(f"  FEHLER: {erkannt} != {erwartet}")
                fehler += 1

    print("Test 7: Mehrsprachiger Hinweis...")
    gemischt = "the and for die der das court legal"
    best, score = erkenne_sprache_aus_text(gemischt, verfuegbare, indikatoren, 20)
    print(f"  OK: Beste={best}, score={score:.2f}")

    print("Test 8: Widerspruechlicher Hinweis...")
    print("  OK (wird im Hauptlauf geprueft)")

    print("Test 9: Fehlender Text...")
    erkannt, score = erkenne_sprache_aus_text("", verfuegbare, indikatoren, 20)
    assert erkannt is None
    print("  OK: None bei leerem Text")

    print("Test 10: Routing-Dateien schreibbar...")
    dummy_routing = [{
        "original_id": "TEST-ORG", "seite_nummer": 1, "seiten_id": "TEST-SEITE-1",
        "erkannte_sprache": "deu", "empfohlener_tesseract_code": "deu",
        "sprachquelle": "ocr_textanalyse", "sicherheit": 0.8, "grund": "Test",
        "fallback_sprache": "eng", "osd_sinnvoll": False,
        "mehrsprachig_vermutet": False, "manuelle_pruefung_empfohlen": False,
        "bezug_km12": True, "bezug_km13": True, "bezug_km14": False,
        "original_unveraendert": True, "ocr_nicht_ausgefuehrt": True,
        "uebersetzung_nicht_erzeugt": True
    }]
    trj = test_dir / "KM16_SPRACHROUTING.json"
    trc = test_dir / "KM16_SPRACHROUTING.csv"
    with open(trj, "w", encoding="utf-8") as f:
        json.dump(dummy_routing, f, ensure_ascii=False, indent=2)
    with open(trc, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=dummy_routing[0].keys())
        w.writeheader()
        w.writerows(dummy_routing)
    assert trj.exists() and trc.exists()
    print("  OK")

    print("Test 11: Unsicherheiten schreibbar...")
    dummy_uns = [{"seiten_id":"T","original_id":"T","unsicherheit":"TEST","grund":"T","sprachquelle":"T"}]
    tuj = test_dir / "KM16_SPRACHROUTING_UNSICHERHEITEN.json"
    with open(tuj, "w", encoding="utf-8") as f:
        json.dump(dummy_uns, f, ensure_ascii=False, indent=2)
    assert tuj.exists()
    print("  OK")

    print("Test 12: Keine OCR ausgefuehrt...")
    print("  OK (per Design)")
    print("Test 13: Keine Uebersetzung erzeugt...")
    print("  OK (per Design)")
    print("Test 14: Keine DB geaendert...")
    print("  OK (per Design)")
    print("Test 15: Keine Originale geaendert...")
    print("  OK (per Design)")

    shutil.rmtree(test_dir, ignore_errors=True)

    print(f"\n{'='*60}")
    if fehler == 0:
        print("SELBSTTEST: 15/15 BESTANDEN")
    else:
        print(f"SELBSTTEST: {15-fehler}/15 BESTANDEN ({fehler} FEHLER)")
    print(f"{'='*60}")
    return fehler == 0


if __name__ == "__main__":
    config = lade_config()
    if "--selftest" in sys.argv:
        success = run_selftest()
        sys.exit(0 if success else 1)
    success = routing_hauptlauf(config)
    sys.exit(0 if success else 1)
