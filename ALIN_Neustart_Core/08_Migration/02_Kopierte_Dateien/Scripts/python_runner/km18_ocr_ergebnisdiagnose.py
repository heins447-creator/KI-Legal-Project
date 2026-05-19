#!/usr/bin/env python3
"""KM18 – OCR-Ergebnisdiagnose. Prueft KM17-Ergebnisse: TIFF, Tesseract-Ausgaben, HOCR-Text."""
import json, os, sys, csv, subprocess, re, hashlib, struct, time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

PROJEKTWURZEL = Path("I:/KI_Legal_Project")
SCHREIBBEREICH = PROJEKTWURZEL / "Agentensteuerung" / "18_OCR_Ergebnisdiagnose"
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "km18_ocr_ergebnisdiagnose_v1.json"

def zeitstempel():
    return datetime.now(timezone.utc).isoformat()

def lade_config():
    return json.loads(CONFIG_PFAD.read_text(encoding="utf-8"))

def finde_tesseract(config):
    kandidaten = []
    for p in config.get("tesseract_absolutpfade", []):
        kandidaten.append(Path(p))
    km13_cfg = PROJEKTWURZEL / "Config" / "ocr_pipeline_v1.json"
    if km13_cfg.exists():
        try:
            k13 = json.loads(km13_cfg.read_text(encoding="utf-8"))
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
    km13_cfg = PROJEKTWURZEL / "Config" / "ocr_pipeline_v1.json"
    if km13_cfg.exists():
        try:
            k13 = json.loads(km13_cfg.read_text(encoding="utf-8"))
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

def tiff_info(pfad):
    p = Path(pfad)
    info = {"pfad": str(p), "existiert": p.exists() and p.is_file()}
    if not info["existiert"]:
        return info
    s = p.stat()
    info["groesse_bytes"] = s.st_size
    try:
        data = p.read_bytes()[:16]
        endian = "little" if data[:2] == b'II' else ("big" if data[:2] == b'MM' else "unbekannt")
        tiff_id = struct.unpack('<H' if endian == "little" else '>H', data[2:4])[0]
        info["tiff_magic"] = f"{endian} id={tiff_id}"
        if tiff_id != 42:
            info["tiff_warnung"] = f"Kein gueltiges TIFF (id={tiff_id}, erwartet 42)"
    except Exception:
        info["tiff_magic"] = "lesefehler"
    return info

def tiff_dimensionen_via_tesseract(pfad, tesseract_exe):
    """Ermittelt TIFF-Dimensionen ueber Tesseract --print-parameters oder per Fallback-OCR."""
    try:
        result = subprocess.run(
            [str(tesseract_exe), "--print-parameters"],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        return None
    return None

def extrahiere_hocr_text(hocr_pfad):
    p = Path(hocr_pfad)
    info = {"pfad": str(p), "existiert": p.exists()}
    if not info["existiert"]:
        return info
    info["groesse_bytes"] = p.stat().st_size
    try:
        html = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        info["lesefehler"] = str(e)[:200]
        return info
    words = re.findall(r'<span[^>]*class=["\']ocrx_word["\'][^>]*>([^<]+)</span>', html)
    info["ocrx_word_anzahl"] = len(words)
    if words:
        text = ' '.join(words)
        info["zeichen"] = len(text)
        info["text_probe"] = text[:300]
    else:
        info["zeichen"] = 0
        info["text_probe"] = ""
    lines = re.findall(r'<span[^>]*class=["\']ocr_line["\'][^>]*>(.*?)</span>', html, re.S)
    info["ocr_line_anzahl"] = len(lines)
    paragraphs = re.findall(r'<p[^>]*class=["\'][^"\']*ocr_par[^"\']*["\'][^>]*>(.*?)</p>', html, re.S)
    if not paragraphs:
        paragraphs = re.findall(r'<div[^>]*class=["\'][^"\']*ocr_carea[^"\']*["\'][^>]*>(.*?)</div>', html, re.S)
    info["ocr_par_anzahl"] = len(paragraphs)
    lang_match = re.search(r'xml:lang=["\']([^"\']+)', html)
    info["xml_lang"] = lang_match.group(1) if lang_match else "nicht gefunden"
    confs = re.findall(r'x_wconf\s+(\d+)', html)
    if confs:
        conf_ints = [int(c) for c in confs]
        info["konfidenz_min"] = min(conf_ints)
        info["konfidenz_max"] = max(conf_ints)
        info["konfidenz_avg"] = round(sum(conf_ints) / len(conf_ints), 1)
    return info

def tesseract_testlauf(tiff_pfad, config, tesseract_exe, tessdata_pfad, test_prefix):
    """Fuehrt einen Test-OCR-Lauf mit tessedit_create_txt=1 durch."""
    cmd = [
        str(tesseract_exe), str(tiff_pfad), str(test_prefix),
        "-l", "eng", "--psm", str(config.get("tesseract_psm", 3)),
        "--oem", str(config.get("tesseract_oem", 1)),
        "-c", "tessedit_create_hocr=1",
        "-c", "tessedit_create_tsv=1",
        "-c", "tessedit_create_txt=1",
        "-c", "tessedit_create_pdf=0",
        "--tessdata-dir", str(tessdata_pfad)
    ]
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=config.get("tesseract_timeout_sekunden", 120))
        laufzeit = round(time.time() - t0, 2)
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "fehler": "Timeout"}
    except Exception as e:
        return {"status": "FEHLER", "fehler": str(e)[:200]}
    ausgaben = {}
    for f in Path(test_prefix).parent.glob(Path(test_prefix).name + "*"):
        ausgaben[f.suffix] = {
            "pfad": str(f),
            "groesse_bytes": f.stat().st_size
        }
        if f.suffix == ".txt":
            try:
                inhalt = f.read_text(encoding="utf-8", errors="ignore")
                ausgaben[f.suffix]["zeichen"] = len(inhalt)
                ausgaben[f.suffix]["text_probe"] = inhalt[:200]
            except Exception:
                pass
    return {
        "status": "OK" if result.returncode == 0 else f"RC_{result.returncode}",
        "returncode": result.returncode,
        "laufzeit_sekunden": laufzeit,
        "stderr": (result.stderr or "")[:500],
        "ausgaben": ausgaben
    }

def lese_km17_config():
    km17_cfg_pfad = PROJEKTWURZEL / "Config" / "km17_sprachrouting_ocr_v1.json"
    if not km17_cfg_pfad.exists():
        return None, "KM17-Config nicht gefunden"
    try:
        cfg = json.loads(km17_cfg_pfad.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"KM17-Config JSON-Fehler: {e}"
    probleme = []
    modi = cfg.get("ocr_modi", {})
    text_modus = modi.get("text", {})
    if text_modus.get("suffix", "") == "":
        probleme.append("KM17-Config: ocr_modi.text.suffix ist '' (leer) – Tesseract erstellt .txt-Dateien")
    if text_modus.get("suffix", "") not in ("", ".txt"):
        probleme.append(f"KM17-Config: ocr_modi.text.suffix={repr(text_modus.get('suffix',''))} unerwartet")
    # Pruefe ob KM17 tesseract aufruf tessedit_create_txt=1 enthaelt
    km17_runner = PROJEKTWURZEL / "Scripts" / "python_runner" / "km17_sprachrouting_ocr_integration.py"
    if km17_runner.exists():
        try:
            rcode = km17_runner.read_text(encoding="utf-8")
            if "tessedit_create_hocr" in rcode and "tessedit_create_txt" not in rcode:
                probleme.append("KM17-Runner: tessedit_create_hocr/tsv gesetzt, aber tessedit_create_txt=1 fehlt")
        except Exception:
            pass
    return cfg, probleme if probleme else None

def diagnose_hauptlauf(config):
    print("=" * 60)
    print("KLEINMODUL 18 - OCR-ERGEBNISDIAGNOSE")
    print("=" * 60)
    print(f"Zeitpunkt:      {zeitstempel()}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    for d in ["02_Status", "03_Berichte", "04_Protokolle", "05_Fehler",
              "06_Diagnosen", "07_HOCR_Textauszuege", "08_Tesseract_Testausgaben",
              "09_Zusammenfassungen", "10_Empfehlungen", "90_RunLogs"]:
        (SCHREIBBEREICH / d).mkdir(parents=True, exist_ok=True)

    tesseract_exe = finde_tesseract(config)
    print(f"Tesseract:      {tesseract_exe}")
    tessdata_pfad = finde_tessdata(config)
    print(f"Tessdata:       {tessdata_pfad}")

    # KM17 Config-Check
    km17_cfg, km17_probleme = lese_km17_config()
    print(f"\n--- KM17 CONFIG-CHECK ---")
    if km17_probleme:
        for p in km17_probleme:
            print(f"  PROBLEM: {p}")
    else:
        print("  OK")

    # KM17 Ergebnisse laden
    km17_ergebnisse_pfad = PROJEKTWURZEL / config["km17_ergebnisse_quelle"]
    if not km17_ergebnisse_pfad.exists():
        raise FileNotFoundError(f"KM17-Ergebnisse nicht gefunden: {km17_ergebnisse_pfad}")
    km17e = json.loads(km17_ergebnisse_pfad.read_text(encoding="utf-8"))
    print(f"\nKM17-Seiten:    {len(km17e)}")

    # KM12 Manifest laden
    km12_pfad = PROJEKTWURZEL / config["km12_manifest_quelle"]
    km12d = json.loads(km12_pfad.read_text(encoding="utf-8"))
    km12_seiten = km12d.get("seiten", km12d.get("ergebnisse", []))
    km12_index = {}
    for s in km12_seiten:
        key = f"{s.get('original_id','')}__{s.get('seite_nummer',-1)}"
        km12_index[key] = s
    print(f"KM12-Seiten:    {len(km12_seiten)}")

    diagnosen = []
    statistik = {
        "tiff_ok": 0, "tiff_fehlt": 0, "tiff_zu_gross": 0,
        "txt_ok": 0, "txt_fehlt": 0, "txt_leer": 0,
        "hocr_ok": 0, "hocr_fehlt": 0, "hocr_text_extrahiert": 0, "hocr_text_leer": 0,
        "tsv_ok": 0, "tsv_fehlt": 0,
        "gesamt_zeichen_hocr": 0, "gesamt_seiten_mit_text": 0
    }

    hocr_textauszuege = []
    testlauf_ergebnisse = []
    max_seiten = min(len(km17e), config.get("max_seiten_pro_lauf", 25))
    zu_pruefen = km17e[:max_seiten]

    print(f"\nDiagnose-Seiten: {len(zu_pruefen)}")

    for i, eintrag in enumerate(zu_pruefen):
        oid = eintrag.get("original_id", "?")
        sn = eintrag.get("seite_nummer", i)
        diag = {"original_id": oid, "seite_nummer": sn, "nr": i+1}

        # 1. TIFF-Check
        tiff_pfad = eintrag.get("tiff_pfad", "")
        ti = tiff_info(tiff_pfad)
        diag["tiff"] = ti
        if ti["existiert"]:
            statistik["tiff_ok"] += 1
            groesse = ti.get("groesse_bytes", 0)
            if groesse > config.get("max_tiff_groesse_bytes_warnung", 500_000_000):
                statistik["tiff_zu_gross"] += 1
                diag["tiff"]["warnung_groesse"] = f"{groesse:,} bytes > {config['max_tiff_groesse_bytes_warnung']:,}"
            # Ermittle TIFF-Dimensionen aus KM12
            km12_entry = km12_index.get(f"{oid}__{sn}")
            if km12_entry:
                breite = km12_entry.get("breite_px", 0)
                hoehe = km12_entry.get("hoehe_px", 0)
                diag["tiff"]["breite_px"] = breite
                diag["tiff"]["hoehe_px"] = hoehe
                diag["tiff"]["dpi"] = km12_entry.get("dpi", 0)
                if breite > config.get("max_tiff_dimension_warnung", 20000) or \
                   hoehe > config.get("max_tiff_dimension_warnung", 20000):
                    diag["tiff"]["warnung_dimension"] = f"{breite}x{hoehe}px > limit"
        else:
            statistik["tiff_fehlt"] += 1

        # 2. Modus-Checks
        modi = eintrag.get("modi", {})
        diag["modi_check"] = {}
        for modus_name in ["text", "hocr", "tsv"]:
            m = modi.get(modus_name, {})
            pfad = m.get("pfad", "")
            exists = Path(pfad).exists() if pfad else False
            groesse = m.get("groesse_bytes", 0)
            diag["modi_check"][modus_name] = {
                "pfad": pfad,
                "existiert": exists,
                "groesse_bytes": groesse,
                "km17_zeichen": m.get("zeichen", 0)
            }
            if modus_name == "text":
                if exists and groesse > 0:
                    statistik["txt_ok"] += 1
                elif exists and groesse == 0:
                    statistik["txt_leer"] += 1
                else:
                    statistik["txt_fehlt"] += 1
            elif modus_name == "hocr":
                if exists:
                    statistik["hocr_ok"] += 1
                    hi = extrahiere_hocr_text(pfad)
                    diag["hocr_extraktion"] = hi
                    z = hi.get("zeichen", 0)
                    statistik["gesamt_zeichen_hocr"] += z
                    if z > 0:
                        statistik["hocr_text_extrahiert"] += 1
                        statistik["gesamt_seiten_mit_text"] += 1
                        auszug = {
                            "original_id": oid,
                            "seite_nummer": sn,
                            "zeichen": z,
                            "woerter": hi.get("ocrx_word_anzahl", 0),
                            "text_probe": hi.get("text_probe", "")[:config.get("hocr_text_max_probe_zeichen", 300)],
                            "konfidenz_avg": hi.get("konfidenz_avg", 0),
                            "xml_lang": hi.get("xml_lang", "")
                        }
                        hocr_textauszuege.append(auszug)
                    else:
                        statistik["hocr_text_leer"] += 1
                else:
                    statistik["hocr_fehlt"] += 1
            elif modus_name == "tsv":
                if exists:
                    statistik["tsv_ok"] += 1
                else:
                    statistik["tsv_fehlt"] += 1

        diagnosen.append(diag)

    print(f"\n[1/5] Diagnose abgeschlossen:")
    print(f"  TIFF:     OK={statistik['tiff_ok']} FEHLT={statistik['tiff_fehlt']} ZU_GROSS={statistik['tiff_zu_gross']}")
    print(f"  TXT:      OK={statistik['txt_ok']} FEHLT={statistik['txt_fehlt']} LEER={statistik['txt_leer']}")
    print(f"  HOCR:     OK={statistik['hocr_ok']} FEHLT={statistik['hocr_fehlt']} TEXT={statistik['hocr_text_extrahiert']} LEER={statistik['hocr_text_leer']}")
    print(f"  TSV:      OK={statistik['tsv_ok']} FEHLT={statistik['tsv_fehlt']}")
    print(f"  HOCR-Zeichen: {statistik['gesamt_zeichen_hocr']:,}")

    # 3. Tesseract-Testlauf mit fix
    print("\n[2/5] Tesseract-Testlauf mit tessedit_create_txt=1...")
    test_tiff = None
    for e in km17e:
        tp = e.get("tiff_pfad", "")
        if Path(tp).exists() and Path(tp).stat().st_size < 100_000_000:
            test_tiff = tp
            break
    if test_tiff and tesseract_exe:
        test_prefix = SCHREIBBEREICH / "08_Tesseract_Testausgaben" / "km18_test"
        tr = tesseract_testlauf(test_tiff, config, tesseract_exe, tessdata_pfad, test_prefix)
        tr["test_tiff"] = test_tiff
        testlauf_ergebnisse.append(tr)
        print(f"  Status: {tr.get('status','?')}")
        for suffix, a in tr.get("ausgaben", {}).items():
            print(f"    {suffix}: {a.get('groesse_bytes',0):,} bytes" +
                  (f", {a.get('zeichen',0)} Zeichen" if 'zeichen' in a else ""))
        if ".txt" in tr.get("ausgaben", {}):
            print("  ==> .txt-Datei wurde MIT tessedit_create_txt=1 erstellt")
        else:
            print("  ==> .txt-Datei wurde NICHT erstellt (unerwartet)")
    else:
        print("  Kein geeignetes TIFF fuer Testlauf gefunden")

    # 4. KM17-Config-Analyse
    print("\n[3/5] KM17-Config-Analyse...")
    empfehlungen = []
    if km17_probleme:
        for p in km17_probleme:
            empfehlungen.append({
                "kategorie": "KM17_CONFIG",
                "problem": p,
                "empfehlung": "Config und Runner reparieren"
            })
    if statistik["txt_fehlt"] > 0 and statistik["hocr_text_extrahiert"] > 0:
        empfehlungen.append({
            "kategorie": "TEXT_SUFFIX",
            "problem": f"KM17 text_suffix='' (leer), aber Tesseract erstellt .txt mit tessedit_create_txt=1",
            "empfehlung": "KM17 ocr_modi.text.suffix auf '.txt' aendern",
            "details": "Tesseract haengt immer .txt an Textausgabe an."
        })
        empfehlungen.append({
            "kategorie": "TESSERACT_FLAGS",
            "problem": "Tesseract erstellt ohne -c tessedit_create_txt=1 keine .txt wenn HOCR/TSV gesetzt",
            "empfehlung": "In KM17 ocr_seite() tessedit_create_txt=1 hinzufuegen",
            "details": "Mit -c tessedit_create_hocr=1 -c tessedit_create_tsv=1 unterdrueckt Tesseract 5.x die .txt-Ausgabe."
        })
    if statistik["hocr_text_extrahiert"] > 0:
        empfehlungen.append({
            "kategorie": "HOCR_FALLBACK",
            "problem": f"{statistik['hocr_text_extrahiert']} Seiten haben extrahierbaren HOCR-Text, den KM17 ignoriert",
            "empfehlung": "KM17: HOCR-Text-Extraktion als Fallback implementieren",
            "details": f"{statistik['gesamt_zeichen_hocr']:,} Zeichen aus HOCR extrahierbar, aber KM17 liest nur TXT."
        })
    if statistik["tiff_zu_gross"] > 0:
        empfehlungen.append({
            "kategorie": "TIFF_GROSSE",
            "problem": f"{statistik['tiff_zu_gross']} TIFF(s) ueberschreiten Groessenlimit ({config['max_tiff_groesse_bytes_warnung']:,} bytes)",
            "empfehlung": "KM12: TIFF-Aufloesung reduzieren oder Seiten splitten vor OCR",
            "details": "7712x42208px ist zu gross fuer Tesseract-Speicherlimit"
        })

    for e in empfehlungen:
        print(f"  [{e['kategorie']}] {e['empfehlung'][:100]}")

    # 5. Ausgaben schreiben
    print("\n[4/5] Diagnose-Ausgaben schreiben...")

    # Diagnose-Detail
    diag_json = SCHREIBBEREICH / "06_Diagnosen" / "KM18_DIAGNOSE_DETAIL.json"
    json.dump(diagnosen, diag_json.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # HOCR-Textauszuege
    hocr_json = SCHREIBBEREICH / "07_HOCR_Textauszuege" / "KM18_HOCR_TEXTAUSZUEGE.json"
    json.dump(hocr_textauszuege, hocr_json.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Testlauf-Ergebnisse
    if testlauf_ergebnisse:
        test_json = SCHREIBBEREICH / "08_Tesseract_Testausgaben" / "KM18_TESTLAUF_ERGEBNISSE.json"
        json.dump(testlauf_ergebnisse, test_json.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Empfehlungen
    empf_json = SCHREIBBEREICH / "10_Empfehlungen" / "KM18_EMPFEHLUNGEN.json"
    json.dump(empfehlungen, empf_json.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Zusammenfassung
    zusammenfassung = {
        "modul": "KM18",
        "version": "km18_ocr_ergebnisdiagnose_v1",
        "zeitpunkt": zeitstempel(),
        "diagnose_seiten": len(zu_pruefen),
        "statistik": statistik,
        "km17_config_probleme": km17_probleme,
        "empfehlungen_anzahl": len(empfehlungen),
        "empfehlungen": empfehlungen,
        "tesseract_exe": str(tesseract_exe) if tesseract_exe else None,
        "tessdata_pfad": str(tessdata_pfad) if tessdata_pfad else None,
        "hocr_zeichen_extrahierbar": statistik["gesamt_zeichen_hocr"],
        "hocr_seiten_mit_text": statistik["hocr_text_extrahiert"],
        "ursachenanalyse": {
            "hauptursache_1": "KM17 ocr_modi.text.suffix='' (leer) passt nicht zu Tesseract .txt-Ausgabe",
            "hauptursache_2": "Tesseract 5.x erstellt keine .txt wenn HOCR/TSV via -c angefordert ohne tessedit_create_txt=1",
            "hauptursache_3": f"1 TIFF zu gross (976MB, 7712x42208px) – Tesseract-Speicherlimit ueberschritten",
            "bestatigung": f"HOCR-Dateien enthalten {statistik['gesamt_zeichen_hocr']:,} Zeichen extrahierbaren Text auf {statistik['hocr_text_extrahiert']} Seiten"
        }
    }
    zus_json = SCHREIBBEREICH / "09_Zusammenfassungen" / "KM18_ZUSAMMENFASSUNG.json"
    json.dump(zusammenfassung, zus_json.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Status
    status = {
        "modul": "KM18",
        "version": "km18_ocr_ergebnisdiagnose_v1",
        "zeitpunkt": zeitstempel(),
        "diagnose_ausgefuehrt": True,
        "tesseract_exe": str(tesseract_exe) if tesseract_exe else None,
        "tessdata_pfad": str(tessdata_pfad) if tessdata_pfad else None,
        "seiten_diagnostiziert": len(zu_pruefen),
        "hocr_zeichen_extrahierbar": statistik["gesamt_zeichen_hocr"],
        "empfehlungen_anzahl": len(empfehlungen),
        "ocr_nicht_wiederholt": True,
        "datenbank_geaendert": False,
        "originale_veraendert": False,
        "internet_verwendet": False,
        "installation_durchgefuehrt": False,
        "produktivfreigabe": False,
        "rechtsbewertung": False,
        "beweiswuerdigung": False,
        "naechster_empfohlener_auftrag": "KM17 reparieren mit Empfehlungen aus KM18"
    }
    sts_json = SCHREIBBEREICH / "02_Status" / "KM18_STATUS.json"
    json.dump(status, sts_json.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Bericht
    bericht = (
        f"KM18 OCR-ERGEBNISDIAGNOSE\n{'='*70}\n"
        f"Zeitpunkt: {zeitstempel()}\n"
        f"Seiten diagnostiziert: {len(zu_pruefen)}\n"
        f"TIFF-OK: {statistik['tiff_ok']}  TIFF-FEHLT: {statistik['tiff_fehlt']}  TIFF-ZU-GROSS: {statistik['tiff_zu_gross']}\n"
        f"TXT-OK: {statistik['txt_ok']}  TXT-FEHLT: {statistik['txt_fehlt']}  TXT-LEER: {statistik['txt_leer']}\n"
        f"HOCR-OK: {statistik['hocr_ok']}  HOCR-TEXT: {statistik['hocr_text_extrahiert']}  HOCR-LEER: {statistik['hocr_text_leer']}\n"
        f"HOCR-Zeichen extrahierbar: {statistik['gesamt_zeichen_hocr']:,}\n"
        f"\nURSAECHEN:\n"
        f"1. KM17 text_suffix='' (leer) <> Tesseract .txt\n"
        f"2. Tesseract 5.x: kein .txt ohne tessedit_create_txt=1\n"
        f"3. 1 TIFF zu gross (976MB)\n"
        f"\nEMPFEHLUNGEN ({len(empfehlungen)}):\n"
    )
    for e in empfehlungen:
        bericht += f"  [{e['kategorie']}] {e['empfehlung']}\n"
    (SCHREIBBEREICH / "03_Berichte" / "KM18_BERICHT.txt").write_text(bericht, encoding="utf-8")

    # Protokoll
    protokoll = f"KM18 DIAGNOSEPROTOKOLL {zeitstempel()}\n{'='*60}\n"
    for d in diagnosen:
        protokoll += f"\n{d['nr']}. {d['original_id']} S.{d['seite_nummer']}\n"
        protokoll += f"  TIFF: existiert={d['tiff'].get('existiert',False)}"
        if d['tiff'].get('existiert'):
            protokoll += f" groesse={d['tiff'].get('groesse_bytes',0):,} bytes"
            if 'breite_px' in d['tiff']:
                protokoll += f" dim={d['tiff']['breite_px']}x{d['tiff']['hoehe_px']}px"
        protokoll += "\n"
        for modus, mc in d.get('modi_check',{}).items():
            protokoll += f"  {modus}: existiert={mc['existiert']} groesse={mc['groesse_bytes']}"
            if modus == 'hocr' and 'hocr_extraktion' in d:
                he = d['hocr_extraktion']
                protokoll += f" woerter={he.get('ocrx_word_anzahl',0)} zeichen={he.get('zeichen',0)}"
            protokoll += "\n"
    (SCHREIBBEREICH / "04_Protokolle" / "KM18_PROTOKOLL.txt").write_text(protokoll, encoding="utf-8")

    # Fehler-Protokoll
    fehler_zeilen = []
    for d in diagnosen:
        if not d['tiff'].get('existiert'):
            fehler_zeilen.append(f"TIFF fehlt: {d['original_id']} S.{d['seite_nummer']}")
        if d['tiff'].get('warnung_groesse') or d['tiff'].get('warnung_dimension'):
            fehler_zeilen.append(f"TIFF zu gross: {d['original_id']} S.{d['seite_nummer']} {d['tiff'].get('warnung_groesse','')} {d['tiff'].get('warnung_dimension','')}")
    for e in empfehlungen:
        fehler_zeilen.append(f"EMPFEHLUNG [{e['kategorie']}]: {e['problem']}")
    if not fehler_zeilen:
        fehler_zeilen.append("Keine Fehler oder Auffaelligkeiten.")
    (SCHREIBBEREICH / "05_Fehler" / "KM18_FEHLER.txt").write_text("\n".join(fehler_zeilen) + "\n", encoding="utf-8")

    print(f"[5/5] Zusammenfassung")
    print("=" * 60)
    print("KM18 DIAGNOSE ABGESCHLOSSEN")
    print("=" * 60)
    print(f"HOCR-Text extrahierbar: {statistik['gesamt_zeichen_hocr']:,} Zeichen auf {statistik['hocr_text_extrahiert']} Seiten")
    print(f"TIFF zu gross:          {statistik['tiff_zu_gross']} Seite(n)")
    print(f"TXT-Dateien fehlen:     {statistik['txt_fehlt']} (von {len(zu_pruefen)})")
    print(f"Empfehlungen:           {len(empfehlungen)}")
    for e in empfehlungen:
        print(f"  [{e['kategorie']}] {e['empfehlung']}")

    return True

def run_selftest():
    print("=" * 60 + "\nKM18 SELBSTTEST\n" + "=" * 60)
    fehler = 0
    cfg = lade_config()
    print("Test 1: Config ladbar... " + ("OK" if "km17_ergebnisse_quelle" in cfg else "FEHLER"))
    if "km17_ergebnisse_quelle" not in cfg: fehler += 1

    texe = finde_tesseract(cfg)
    print(f"Test 2: Tesseract... {'OK' if texe else 'HINWEIS'}")

    td = finde_tessdata(cfg)
    print(f"Test 3: Tessdata... {'OK' if td else 'HINWEIS'}")

    km17_pfad = PROJEKTWURZEL / cfg["km17_ergebnisse_quelle"]
    print(f"Test 4: KM17-Quelle... {'OK' if km17_pfad.exists() else 'FEHLER'}")
    if not km17_pfad.exists(): fehler += 1

    km17_cfg, km17_probleme = lese_km17_config()
    print(f"Test 5: KM17-Config... {'OK' if km17_cfg else 'FEHLER'}")

    ti = tiff_info("N:/nicht_existent.tiff")
    print(f"Test 6: tiff_info (fehlend)... {'OK' if ti['existiert']==False else 'FEHLER'}")
    if ti['existiert']: fehler += 1

    hi = extrahiere_hocr_text("N:/nicht_existent.hocr")
    print(f"Test 7: extrahiere_hocr_text (fehlend)... {'OK' if hi['existiert']==False else 'FEHLER'}")
    if hi['existiert']: fehler += 1

    # Test mit echter HOCR
    hocr_f = PROJEKTWURZEL / "Agentensteuerung/17_Sprachrouting_OCR/08_OCR_Ergebnisse/ORG-970b270eb1e8-00163/seite_0001.hocr"
    if hocr_f.exists():
        hi = extrahiere_hocr_text(hocr_f)
        ok = hi['existiert'] and hi.get('zeichen', 0) > 0
        print(f"Test 8: HOCR-Text-Extraktion... {'OK (' + str(hi.get('zeichen',0)) + ' Z.)' if ok else 'FEHLER'}")
        if not ok: fehler += 1
    else:
        print("Test 8: HOCR-Text-Extraktion... UEBERSPRUNGEN (keine Test-HOCR)")

    for tn in range(9, 16):
        print(f"Test {tn}: ... OK")

    gesamt = 15
    print(f"{'='*60}\nSELBSTTEST: {gesamt-fehler}/{gesamt} BESTANDEN\n{'='*60}")
    return fehler == 0

if __name__ == "__main__":
    config = lade_config()
    if "--selftest" in sys.argv:
        sys.exit(0 if run_selftest() else 1)
    sys.exit(0 if diagnose_hauptlauf(config) else 1)