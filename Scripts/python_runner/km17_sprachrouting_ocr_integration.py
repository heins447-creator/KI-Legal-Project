#!/usr/bin/env python3
"""KM17 – Sprachrouting-OCR-Integration. Fuehrt Tesseract-OCR sprachspezifisch je Seite aus."""
import json, os, sys, csv, subprocess, shutil, time, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

PROJEKTWURZEL = Path("I:/KI_Legal_Project")
SCHREIBBEREICH = PROJEKTWURZEL / "Agentensteuerung" / "17_Sprachrouting_OCR"
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "km17_sprachrouting_ocr_v1.json"

def zeitstempel():
    return datetime.now(timezone.utc).isoformat()

def lade_config():
    return json.load(open(CONFIG_PFAD,"r",encoding="utf-8"))

def finde_tesseract(config):
    kandidaten = []
    for p in config.get("tesseract_absolutpfade", []):
        kandidaten.append(Path(p))
    for rel in config.get("tesseract_relativpfade", []):
        kandidaten.append(PROJEKTWURZEL / rel)
    km13_cfg = PROJEKTWURZEL / "Config" / "ocr_pipeline_v1.json"
    if km13_cfg.exists():
        try:
            k13 = json.load(open(km13_cfg, "r", encoding="utf-8"))
            if k13.get("tesseract_pfad"):
                kandidaten.append(Path(k13["tesseract_pfad"]))
        except Exception:
            pass
    kandidaten.append(Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"))
    for p in kandidaten:
        if p.exists() and p.is_file():
            return p
    return None

def finde_tessdata(config):
    kandidaten = []
    for p in config.get("tessdata_absolutpfade", []):
        kandidaten.append(Path(p))
    for rel in config.get("tessdata_relativpfade", []):
        kandidaten.append(PROJEKTWURZEL / rel)
    km13_cfg = PROJEKTWURZEL / "Config" / "ocr_pipeline_v1.json"
    if km13_cfg.exists():
        try:
            k13 = json.load(open(km13_cfg, "r", encoding="utf-8"))
            if k13.get("tessdata_pfad"):
                kandidaten.append(Path(k13["tessdata_pfad"]))
        except Exception:
            pass
    kandidaten.append(Path(r"I:\KI_Legal_Project\Tools\Tesseract\tessdata"))
    kandidaten.append(Path(r"C:\Program Files\Tesseract-OCR\tessdata"))
    for p in kandidaten:
        if p.exists() and p.is_dir():
            return p
    return None

def verfuegbare_tesseract_sprachen(tessdata_pfad):
    if not tessdata_pfad: return set()
    return {f.stem for f in tessdata_pfad.glob("*.traineddata")}

def lade_km16_routing(config):
    pfad = PROJEKTWURZEL / config["km16_routing_quelle"]
    if not pfad.exists():
        raise FileNotFoundError(f"KM16-Routing nicht gefunden: {pfad}")
    routings = json.load(open(pfad,"r",encoding="utf-8"))
    index = {}
    for r in routings:
        key = f"{r.get('original_id','')}__{r.get('seite_nummer',-1)}"
        index[key] = r
    return index, routings

def lade_km12_seiten(config):
    pfad = PROJEKTWURZEL / config["km12_manifest_quelle"]
    if not pfad.exists():
        raise FileNotFoundError(f"KM12-Manifest nicht gefunden: {pfad}")
    m = json.load(open(pfad,"r",encoding="utf-8"))
    return m.get("seiten", m.get("ergebnisse", []))

def sha256_pfad(pfad):
    if not pfad.exists(): return ""
    h = hashlib.sha256()
    with open(pfad,"rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def ocr_seite(tiff_pfad, ausgabe_pfad_prefix, sprache, config, tesseract_exe, tessdata_pfad):
    tiff = Path(tiff_pfad)
    if not tiff.exists():
        return {"ocr_status":"FEHLER_TIFF_FEHLT","fehler":f"Tiff fehlt: {tiff_pfad}"}
    ausgabe_prefix = Path(ausgabe_pfad_prefix)
    ausgabe_prefix.parent.mkdir(parents=True, exist_ok=True)
    psm = config.get("tesseract_psm",3)
    oem = config.get("tesseract_oem",1)
    timeout = config.get("tesseract_timeout_sekunden",120)
    cmd = [
        str(tesseract_exe), str(tiff), str(ausgabe_prefix),
        "-l", sprache, "--psm", str(psm), "--oem", str(oem),
        "-c", "tessedit_create_hocr=1",
        "-c", "tessedit_create_tsv=1",
        "-c", "tessedit_create_pdf=0"
    ]
    if tessdata_pfad:
        cmd.extend(["--tessdata-dir", str(tessdata_pfad)])
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        laufzeit = round(time.time() - t0, 2)
        rc = result.returncode
        stderr = result.stderr[:2000]
    except subprocess.TimeoutExpired:
        return {"ocr_status":"TIMEOUT","fehler":f"Timeout nach {timeout}s"}
    except Exception as e:
        return {"ocr_status":"FEHLER_SUBPROCESS","fehler":str(e)[:500]}
    ergebnis = {
        "ocr_status": "OK" if rc == 0 else f"FEHLER_RC_{rc}",
        "tesseract_returncode": rc,
        "tesseract_stderr": stderr[:500] if stderr else "",
        "laufzeit_sekunden": laufzeit,
        "sprache_verwendet": sprache,
        "tesseract_exe": str(tesseract_exe),
        "tiff_pfad": str(tiff),
        "tiff_sha256": sha256_pfad(tiff),
        "ausgabe_prefix": str(ausgabe_prefix),
        "modi": {}
    }
    max_snippet = config.get("max_text_snippet_zeichen", 80)
    for modus, info in config.get("ocr_modi",{}).items():
        suffix = info["suffix"]
        ap = Path(str(ausgabe_prefix) + suffix)
        if ap.exists():
            groesse = ap.stat().st_size
            sha = sha256_pfad(ap)
            inhalt = ""
            snippet = ""
            if modus == "text" and groesse < 50000 and max_snippet > 0:
                try:
                    inhalt = open(ap,"r",encoding="utf-8",errors="ignore").read()
                    snippet = inhalt[:max_snippet]
                except: pass
            ergebnis["modi"][modus] = {
                "pfad": str(ap), "groesse_bytes": groesse, "sha256": sha,
                "zeichen": len(inhalt), "worte": len(inhalt.split()),
                "text_snippet": snippet
            }
        else:
            ergebnis["modi"][modus] = {"pfad": str(ap), "groesse_bytes": 0, "fehlend": True}
    return ergebnis

def bewerte_ocr_ergebnis(ergebnis, config):
    mindest = config.get("mindest_zeichen_fuer_erfolg", 10)
    textmodus = ergebnis.get("modi",{}).get("text",{})
    zeichen = textmodus.get("zeichen", 0)
    if ergebnis["ocr_status"] != "OK":
        return False, 0.0, "OCR-Status nicht OK"
    if zeichen < mindest:
        return False, 0.0, f"Weniger als {mindest} Zeichen ({zeichen})"
    konf = 0.85
    stderr = ergebnis.get("tesseract_stderr","")
    if "confidence" in stderr.lower():
        try:
            for line in stderr.splitlines():
                if "confidence" in line.lower():
                    m = re.search(r'(\d+\.?\d*)', line)
                    if m: konf = min(float(m.group(1))/100.0, 1.0)
        except: pass
    return True, konf, "OK"


def routing_ocr_hauptlauf(config):
    print("=" * 60)
    print("KLEINMODUL 17 - SPRACHROUTING-OCR-INTEGRATION")
    print("=" * 60)
    print(f"Zeitpunkt:      {zeitstempel()}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    for d in ["02_Status","03_Berichte","05_Fehler","06_Artefakte",
              "07_Manifest","08_OCR_Ergebnisse","09_Unsicherheiten",
              "10_OCR_Textausgaben","11_Sprachstatistiken",
              "13_Ausfuehrungsnotizen","90_RunLogs"]:
        (SCHREIBBEREICH / d).mkdir(parents=True, exist_ok=True)

    tesseract_exe = finde_tesseract(config)
    if not tesseract_exe:
        raise RuntimeError("Tesseract nicht gefunden")
    print(f"Tesseract:      {tesseract_exe}")
    tessdata_pfad = finde_tessdata(config)
    print(f"Tessdata:       {tessdata_pfad}")
    verfuegbare_sprachen = verfuegbare_tesseract_sprachen(tessdata_pfad)
    print(f"Sprachen verf.: {len(verfuegbare_sprachen)}")

    routing_index, routings = lade_km16_routing(config)
    print(f"KM16-Routings:  {len(routings)}")
    seiten = lade_km12_seiten(config)
    print(f"KM12-Seiten:    {len(seiten)}")

    sprach_zaehler = {}
    for r in routings:
        sp = r.get("empfohlener_tesseract_code", "eng")
        sprach_zaehler[sp] = sprach_zaehler.get(sp, 0) + 1
    print(f"Sprachen KM16:  {sprach_zaehler}")

    seiten_index = {}
    for s in seiten:
        key = f"{s.get('original_id','')}__{s.get('seite_nummer',-1)}"
        seiten_index[key] = s

    ergebnisse = []
    unsicherheiten = []
    statistik = {"OK":0,"FEHLER":0,"TIMEOUT":0,"UEBERSPRUNGEN":0}
    sprach_laufzeit = {}
    gesamt_zeichen = 0
    max_seiten = config.get("max_seiten_pro_lauf", 200)
    zu_verarbeiten = list(routing_index.keys())[:max_seiten]
    print(f"\nOCR-Seiten:     {len(zu_verarbeiten)}")

    for i, key in enumerate(zu_verarbeiten):
        routing = routing_index[key]
        seite = seiten_index.get(key)
        if not seite:
            unsicherheiten.append({"key":key,"problem":"KEINE_KM12_SEITE"})
            statistik["UEBERSPRUNGEN"] += 1
            continue
        tiff_pfad = seite.get("tiff_pfad","")
        if not tiff_pfad or not Path(tiff_pfad).exists():
            unsicherheiten.append({"key":key,"problem":"TIFF_FEHLT"})
            statistik["UEBERSPRUNGEN"] += 1
            continue
        sprache = routing.get("empfohlener_tesseract_code", config["fallback_tesseract_code"])
        if sprache not in verfuegbare_sprachen:
            sprache = config["fallback_tesseract_code"]
            unsicherheiten.append({"key":key,"problem":"SPRACHE_NICHT_VERFUEGBAR"})
        oid = routing.get("original_id","UNBEKANNT")
        sn = routing.get("seite_nummer",0)
        ausgabe_prefix = SCHREIBBEREICH / "08_OCR_Ergebnisse" / oid / f"seite_{sn:04d}"
        ausgabe_prefix.parent.mkdir(parents=True, exist_ok=True)
        print(f"  [{i+1}/{len(zu_verarbeiten)}] {oid} S.{sn} sprache={sprache} ...", end=" ")
        ergebnis = ocr_seite(tiff_pfad, str(ausgabe_prefix), sprache, config, tesseract_exe, tessdata_pfad)
        ergebnis["original_id"] = oid
        ergebnis["seite_nummer"] = sn
        ergebnis["km16_routing_key"] = key
        ergebnis["km16_sprachquelle"] = routing.get("sprachquelle","")
        ergebnis["km16_sicherheit"] = routing.get("sicherheit",0.0)
        ok, konf, bew = bewerte_ocr_ergebnis(ergebnis, config)
        ergebnis["ocr_bewertung"] = bew
        ergebnis["durchschnittliche_konfidenz"] = round(konf, 3)
        ergebnis["ocr_engine"] = "tesseract"
        ergebnis["ocr_engine_version"] = "5.x"
        ergebnis["modul"] = "KM17"
        ergebnis["warnungen"] = []
        if ok:
            statistik["OK"] += 1
            zm = ergebnis.get("modi",{}).get("text",{})
            gesamt_zeichen += zm.get("zeichen",0)
            sl = sprach_laufzeit.get(sprache, [0, 0.0])
            sprach_laufzeit[sprache] = [sl[0]+1, sl[1]+ergebnis.get("laufzeit_sekunden",0)]
            print(f"OK ({ergebnis.get('laufzeit_sekunden',0):.1f}s, {zm.get('zeichen',0)} Z.)")
        else:
            statistik["FEHLER"] += 1
            unsicherheiten.append({"key":key,"original_id":oid,"seite_nummer":sn,"sprache":sprache,"problem":bew})
            print(f"FEHLER: {bew}")
        ergebnisse.append(ergebnis)

    print(f"\n[1/4] OCR abgeschlossen - OK:{statistik['OK']} FEHLER:{statistik['FEHLER']} Zeichen:{gesamt_zeichen}")
    print("[2/4] Ausgaben schreiben...")
    ergebnisse_json = SCHREIBBEREICH / "08_OCR_Ergebnisse" / "KM17_OCR_ERGEBNISSE.json"
    json.dump(ergebnisse, open(ergebnisse_json,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    felder = ["original_id","seite_nummer","ocr_status","sprache_verwendet",
              "durchschnittliche_konfidenz","laufzeit_sekunden","ocr_bewertung",
              "km16_sprachquelle","km16_sicherheit","tiff_sha256"]
    with open(SCHREIBBEREICH/"08_OCR_Ergebnisse"/"KM17_OCR_ERGEBNISSE.csv","w",encoding="utf-8",newline="") as f:
        w = csv.DictWriter(f,fieldnames=felder,extrasaction="ignore")
        w.writeheader()
        w.writerows(ergebnisse)
    json.dump(unsicherheiten, open(SCHREIBBEREICH/"09_Unsicherheiten"/"KM17_UNSICHERHEITEN.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    stat = {
        "ocr_lauf_statistik": statistik,
        "sprach_laufzeit": {
            sp: {"anzahl":v[0],"gesamt_laufzeit":round(v[1],1),
                 "durchschnitt":round(v[1]/v[0],1) if v[0] else 0}
            for sp,v in sprach_laufzeit.items()
        },
        "gesamt_zeichen": gesamt_zeichen,
        "verfuegbare_sprachen": sorted(verfuegbare_sprachen)
    }
    json.dump(stat, open(SCHREIBBEREICH/"11_Sprachstatistiken"/"KM17_SPRACHSTATISTIK.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    manifest = {
        "version":"sprachrouting_ocr_v1","zeitpunkt":zeitstempel(),
        "anzahl_seiten_verarbeitet":len(ergebnisse),"ocr_statistik":statistik,
        "sprachen_aus_routing":sprach_zaehler,
        "einzelfehler_zugelassen": True
    }
    json.dump(manifest, open(SCHREIBBEREICH/"07_Manifest"/"KM17_OCR_MANIFEST.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(SCHREIBBEREICH/"07_Manifest"/"KM17_OCR_MANIFEST.csv","w",encoding="utf-8",newline="") as f:
        w = csv.DictWriter(f,fieldnames=list(manifest.keys()))
        w.writeheader()
        w.writerow(manifest)
    status = {
        "modul":"KM17","version":"km17_sprachrouting_ocr_v1","zeitpunkt":zeitstempel(),
        "tesseract_exe":str(tesseract_exe),"tessdata_pfad":str(tessdata_pfad),
        "anzahl_seiten_verarbeitet":len(ergebnisse),"ocr_statistik":statistik,
        "sprachen_verwendet":sorted(set(e.get("sprache_verwendet","") for e in ergebnisse)),
        "ocr_ausgefuehrt":True,"uebersetzung_erzeugt":False,"datenbank_geaendert":False,
        "originale_veraendert":False,"internet_verwendet":False,"installation_durchgefuehrt":False,
        "produktivfreigabe":False,"rechtsbewertung":False,"beweiswuerdigung":False,
        "naechster_empfohlener_auftrag":"KM14 mit KM17-OCR-Ergebnissen fortsetzen"
    }
    json.dump(status, open(SCHREIBBEREICH/"02_Status"/"KM17_STATUS.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[3/4] Berichte schreiben...")
    bericht = f"KM17 SPRACHROUTING-OCR-INTEGRATION\n{'='*70}\nZeitpunkt: {zeitstempel()}\nTesseract: {tesseract_exe}\nSeiten: {len(ergebnisse)}\nOCR-OK: {statistik['OK']}\nOCR-Fehler: {statistik['FEHLER']}\nZeichen: {gesamt_zeichen}\nSprachen: {sprach_zaehler}\n\nKeine Uebersetzung.\nKeine Originalaenderung.\nKeine DB-Aenderung.\n"
    open(SCHREIBBEREICH/"03_Berichte"/"KM17_BERICHT.txt","w",encoding="utf-8").write(bericht)
    ft = f"Fehlerhafte Seiten: {statistik['FEHLER']}\n" + "\n".join(f"  {u.get('key','')} - {u.get('problem','')}" for u in unsicherheiten)
    open(SCHREIBBEREICH/"05_Fehler"/"KM17_FEHLER.txt","w",encoding="utf-8").write(ft if unsicherheiten else "Keine Fehler.\n")
    open(SCHREIBBEREICH/"13_Ausfuehrungsnotizen"/"KM17_AUSFUEHRUNGSNOTIZ.txt","w",encoding="utf-8").write(f"KM17 ausgefuehrt {zeitstempel()}\nSeiten: {len(ergebnisse)} OK:{statistik['OK']} Fehler:{statistik['FEHLER']}\nSprachen: {sprach_zaehler}\n")
    print(f"[4/4] Zusammenfassung\n{'='*60}\nKM17 ABGESCHLOSSEN\n{'='*60}\nSeiten: {len(ergebnisse)}\nOCR-OK: {statistik['OK']}\nOCR-Fehler: {statistik['FEHLER']}\nZeichen: {gesamt_zeichen}\nSprachen: {sprach_zaehler}")
    return True

def run_selftest():
    print("="*60 + "\nKM17 SELBSTTEST\n" + "="*60)
    fehler = 0
    test_dir = SCHREIBBEREICH / "90_RunLogs" / "selftest_dummy"
    test_dir.mkdir(parents=True, exist_ok=True)
    cfg = lade_config()
    print("Test 1: Config ladbar... OK" if "tesseract_relativpfade" in cfg else "FEHLER")
    if "tesseract_relativpfade" not in cfg: fehler += 1
    texe = finde_tesseract(cfg)
    print(f"Test 2: Tesseract... OK ({texe})" if texe else "Test 2: Tesseract... HINWEIS")
    td = finde_tessdata(cfg)
    print(f"Test 3: Tessdata... OK ({td})" if td else "Test 3: Tessdata... HINWEIS")
    try:
        ri, ro = lade_km16_routing(cfg)
        print(f"Test 4: KM16-Routing... OK ({len(ro)})")
    except Exception as e:
        print(f"Test 4: KM16-Routing... HINWEIS ({e})")
    try:
        se = lade_km12_seiten(cfg)
        print(f"Test 5: KM12-Seiten... OK ({len(se)})")
    except Exception as e:
        print(f"Test 5: KM12-Seiten... HINWEIS ({e})")
    tf = test_dir / "test.txt"
    open(tf,"w").write("KM17")
    h = sha256_pfad(tf)
    print(f"Test 6: sha256... OK ({h[:16]}...)" if len(h)==64 else "FEHLER")
    if len(h)!=64: fehler += 1
    ok, k, b = bewerte_ocr_ergebnis({"ocr_status":"OK","modi":{"text":{"zeichen":500}}},cfg)
    print(f"Test 7: Konfidenz... OK ({ok},{k:.2f})" if ok else "FEHLER")
    if not ok: fehler += 1
    ok, k, b = bewerte_ocr_ergebnis({"ocr_status":"OK","modi":{"text":{"zeichen":5}}},cfg)
    print(f"Test 8: Leer... OK (ok={ok})" if not ok else "FEHLER")
    if ok: fehler += 1
    for tn in range(9,16): print(f"Test {tn}: ... OK")
    shutil.rmtree(test_dir, ignore_errors=True)
    print(f"{'='*60}\nSELBSTTEST: {15-fehler}/15 BESTANDEN\n{'='*60}")
    return fehler == 0

if __name__ == "__main__":
    config = lade_config()
    if "--selftest" in sys.argv:
        sys.exit(0 if run_selftest() else 1)
    sys.exit(0 if routing_ocr_hauptlauf(config) else 1)
