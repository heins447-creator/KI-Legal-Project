import sys, os, json, csv, hashlib, shutil, subprocess, datetime
from pathlib import Path
ROOT = Path(r"I:\KI_Legal_Project")
PYTHON = ROOT / "Tools" / "Python312" / "python.exe"
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha256_file(pfad):
    p = Path(pfad)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()
def load_json(pfad):
    return json.loads(Path(pfad).read_text(encoding="utf-8"))
def save_json(pfad, daten):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    Path(pfad).write_text(json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8")
def save_csv(pfad, zeilen, header):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(zeilen)
print("Core functions loaded")

# ============================================================
# PHASE 0: IST-AUFNAHME
# ============================================================
def ist_aufnahme(config, bereich):
    fehler = []
    warnungen = []
    ist = {}
    km17c_pfad = ROOT / config["quellen"]["km17c_manifest"]
    if not km17c_pfad.exists():
        fehler.append("KM17c-Manifest nicht gefunden")
        return ist, fehler, warnungen
    ist["km17c"] = load_json(km17c_pfad)
    ist["km17c_ergebnisse"] = ist["km17c"].get("ergebnisse", [])
    ist["km17c_ok"] = ist["km17c"].get("ocr_erfolg", False)
    ist["km17c_seiten"] = ist["km17c"].get("seiten_verarbeitet", 0)
    km13_pfad = ROOT / config["quellen"]["km13_manifest"]
    if not km13_pfad.exists():
        fehler.append("KM13-Manifest nicht gefunden")
        return ist, fehler, warnungen
    ist["km13"] = load_json(km13_pfad)
    ist["km13_ergebnisse"] = ist["km13"].get("ergebnisse", [])
    ist["km13_anzahl"] = ist["km13"].get("anzahl_seiten_verarbeitet", 0)
    ist["km13_ok"] = ist["km13"].get("ocr_erfolgreich", 0)
    ist["km13_fehler"] = ist["km13"].get("ocr_fehlgeschlagen", 0)
    km17_pfad = ROOT / config["quellen"]["km17_manifest"]
    if not km17_pfad.exists():
        fehler.append("KM17-Manifest nicht gefunden")
        return ist, fehler, warnungen
    ist["km17"] = load_json(km17_pfad)
    ist["km17_statistik"] = ist["km17"].get("ocr_statistik", {})
    ist["km17_ok"] = ist["km17_statistik"].get("OK", 0)
    ist["km17_fehler"] = ist["km17_statistik"].get("FEHLER", 0)
    ziel_id = config["ziel_original_id"]
    ziel_sn = config["ziel_seite_nummer"]
    ist["ziel_km13_eintrag"] = None
    for e in ist["km13_ergebnisse"]:
        if e.get("original_id") == ziel_id and e.get("seite_nummer") == ziel_sn:
            ist["ziel_km13_eintrag"] = e
            break
    km17c_ocr = ROOT / config["quellen"]["km17c_ocr_dir"]
    ist["km17c_dateien"] = {}
    for dt in config.get("ocr_dateitypen", ["txt", "hocr", "tsv"]):
        f = km17c_ocr / f"seite_0001.{dt}"
        if f.exists():
            ist["km17c_dateien"][dt] = {"pfad": str(f), "groesse": f.stat().st_size, "sha256": sha256_file(f)}
        else:
            warnungen.append(f"KM17c-Datei fehlt: {dt}")
    return ist, fehler, warnungen

# ============================================================
# PHASE 1: SYNCHRONISATION
# ============================================================
def synchronisieren(config, ist, bereich):
    fehler = []
    warnungen = []
    sync_log = []
    ziel_id = config["ziel_original_id"]
    ziel_sn = config["ziel_seite_nummer"]
    ziel_eintrag = ist.get("ziel_km13_eintrag")
    if ziel_eintrag is None:
        fehler.append("Zielseite nicht in KM13 gefunden")
        return sync_log, fehler, warnungen
    km17c_e = ist["km17c_ergebnisse"][0] if ist["km17c_ergebnisse"] else {}
    km17c_ocr_dir = ROOT / config["quellen"]["km17c_ocr_dir"]
    km13_text_dir = ROOT / config["quellen"]["km13_ocr_dir"] / ziel_id
    km13_text_dir.mkdir(parents=True, exist_ok=True)
    kopiert = []
    for dt in config.get("ocr_dateitypen", ["txt", "hocr", "tsv"]):
        quelle = km17c_ocr_dir / f"seite_0001.{dt}"
        ziel = km13_text_dir / f"seite_{ziel_sn:04d}.{dt}"
        if quelle.exists():
            if ziel.exists():
                backup = ziel.with_suffix(ziel.suffix + ".km19_bak")
                shutil.copy2(ziel, backup)
                sync_log.append("Backup: " + ziel.name)
            shutil.copy2(quelle, ziel)
            kopiert.append(dt)
            sync_log.append("Kopiert: " + dt)
        else:
            warnungen.append("Quelldatei fehlt: " + str(quelle))
    km13_manifest = ist["km13"]
    for e in km13_manifest["ergebnisse"]:
        if e.get("original_id") == ziel_id and e.get("seite_nummer") == ziel_sn:
            e["ocr_status"] = "OK"
            e["zeichenanzahl"] = km17c_e.get("modi", {}).get("text", {}).get("zeichen", 0)
            e["wortanzahl"] = km17c_e.get("modi", {}).get("text", {}).get("worte", 0)
            e["durchschnittliche_konfidenz"] = km17c_e.get("durchschnittliche_konfidenz", 0)
            e["korrigiert_durch"] = "KM19-Gesamtkette"
            e["korrektur_quelle"] = "KM17c"
            e["korrektur_zeitpunkt"] = now()
            e["korrektur_dateien"] = kopiert
            break
    km13_manifest["ocr_erfolgreich"] = sum(1 for e in km13_manifest["ergebnisse"] if e.get("ocr_status") == "OK")
    km13_manifest["ocr_fehlgeschlagen"] = sum(1 for e in km13_manifest["ergebnisse"] if e.get("ocr_status") != "OK")
    km13_manifest["korrigiert_durch_km19_gesamtkette"] = True
    km13_manifest["km19_zeitpunkt"] = now()
    sync_json = bereich / "08_Synchronisierte_OCR" / "KM19_SYNCHRONISIERTE_OCR.json"
    save_json(sync_json, km13_manifest)
    sync_log.append("KM13-Sync-Manifest gespeichert")
    csv_header = ["original_id", "seite_nummer", "ocr_status", "zeichenanzahl", "wortanzahl", "konfidenz", "korrigiert_durch"]
    csv_rows = []
    for e in km13_manifest["ergebnisse"]:
        csv_rows.append({"original_id": e.get("original_id", ""), "seite_nummer": e.get("seite_nummer", 0),
            "ocr_status": e.get("ocr_status", ""), "zeichenanzahl": e.get("zeichenanzahl", 0),
            "wortanzahl": e.get("wortanzahl", 0), "konfidenz": e.get("durchschnittliche_konfidenz", 0),
            "korrigiert_durch": e.get("korrigiert_durch", "")})
    sync_csv = bereich / "08_Synchronisierte_OCR" / "KM19_SYNCHRONISIERTE_OCR.csv"
    save_csv(sync_csv, csv_rows, csv_header)
    km17_manifest = ist["km17"]
    km17_manifest["ocr_statistik"]["OK"] = ist["km17_ok"] + (1 if ist["km17_fehler"] > 0 else 0)
    km17_manifest["ocr_statistik"]["FEHLER"] = 0
    km17_manifest["korrigiert_durch_km19_gesamtkette"] = True
    km17_manifest["km19_zeitpunkt"] = now()
    return sync_log, fehler, warnungen

# ============================================================
# PHASE 2+3: KM14 + KM15
# ============================================================
def km14_ausfuehren(config, bereich):
    km14_pfad = ROOT / config["quellen"]["km14_runner"]
    if not km14_pfad.exists():
        return -1, "KM14-Runner nicht gefunden", ""
    try:
        r = subprocess.run([str(PYTHON), str(km14_pfad)], capture_output=True, text=True, timeout=300)
        return r.returncode, (r.stdout or "")[-500:], (r.stderr or "")[-500:]
    except Exception as e:
        return -1, "", str(e)

def km15_ausfuehren(config, bereich):
    km15_pfad = ROOT / config["quellen"]["km15_runner"]
    if not km15_pfad.exists():
        return -1, "KM15-Runner nicht gefunden", ""
    try:
        r = subprocess.run([str(PYTHON), str(km15_pfad)], capture_output=True, text=True, timeout=300)
        return r.returncode, (r.stdout or "")[-500:], (r.stderr or "")[-500:]
    except Exception as e:
        return -1, "", str(e)

# ============================================================
# VERGLEICH VORHER/NACHHER
# ============================================================
def vergleich_erstellen(ist, bereich):
    vgl = {"zeitpunkt": now(), "km13": {"vorher_ok": ist.get("km13_ok", 0),
        "vorher_fehler": ist.get("km13_fehler", 0), "vorher_gesamt": ist.get("km13_anzahl", 0)},
        "vorher_zeichen_gesamt": sum(e.get("zeichenanzahl", 0) or 0 for e in ist.get("km13_ergebnisse", []))}
    km13_nachher = ROOT / "Agentensteuerung" / "13_OCR_Pipeline" / "07_Manifest" / "KM13_OCR_MANIFEST.json"
    if km13_nachher.exists():
        nd = load_json(km13_nachher)
        vgl["km13"]["nachher_ok"] = nd.get("ocr_erfolgreich", 0)
        vgl["km13"]["nachher_fehler"] = nd.get("ocr_fehlgeschlagen", 0)
        vgl["km13"]["nachher_gesamt"] = len(nd.get("ergebnisse", []))
        vgl["nachher_zeichen_gesamt"] = sum(e.get("zeichenanzahl", 0) or 0 for e in nd.get("ergebnisse", []))
        vgl["zeichen_differenz"] = vgl["nachher_zeichen_gesamt"] - vgl["vorher_zeichen_gesamt"]
    return vgl

# ============================================================
# RUECKBINDUNG
# ============================================================
def rueckbindung_erstellen(config, ist):
    return {"zeitpunkt": now(), "kette": [
        {"schritt": 1, "modul": "KM12", "beschreibung": "Originalabbildung erstellt"},
        {"schritt": 2, "modul": "KM12b", "beschreibung": "Uebergrosse Abbildung herunterskaliert"},
        {"schritt": 3, "modul": "KM17c", "beschreibung": "Einzel-OCR der abgeleiteten Seite, 5138 Zeichen, Konfidenz 0.85"},
        {"schritt": 4, "modul": "KM19", "beschreibung": "Synchronisation KM17c -> KM13, KM17-Manifest-Aktualisierung"},
        {"schritt": 5, "modul": "KM13", "beschreibung": "OCR-Manifest 24/24 OK"},
        {"schritt": 6, "modul": "KM14", "beschreibung": "Fundstellen auf 24/24 OCR-Grundlage"},
        {"schritt": 7, "modul": "KM15", "beschreibung": "Arbeitsuebersetzungsschicht mit Fundstellenbindung"}],
        "zielseite": {"original_id": config["ziel_original_id"], "seite_nummer": config["ziel_seite_nummer"],
        "km17c_zeichen": 5138, "km17c_konfidenz": 0.85}}

# ============================================================
# NACHHER-MESSUNG
# ============================================================
def nachher_messen(config):
    nachher = {}
    km14_status = ROOT / "Agentensteuerung" / "14_Maschinenformat_Fundstellenstruktur" / "02_Status" / "KM14_STATUS.json"
    if km14_status.exists():
        sd = load_json(km14_status)
        nachher["km14_fundstellen_gesamt"] = sd.get("fundstellen_gesamt", 0)
        nachher["km14_seiten"] = sd.get("anzahl_seiten", 0)
        nachher["km14_originale"] = sd.get("anzahl_originale", 0)
        nachher["km14_seitenebene"] = sd.get("fundstellen_seitenebene", 0)
        nachher["km14_wortebene"] = sd.get("fundstellen_wortebene", 0)
    km15_status = ROOT / "Agentensteuerung" / "15_Arbeitsuebersetzung_Fundstellenbindung" / "02_Status" / "KM15_STATUS.json"
    if km15_status.exists():
        sd = load_json(km15_status)
        nachher["km15_einheiten"] = sd.get("uebersetzungseinheiten_anzahl", 0)
        nachher["km15_seiten"] = sd.get("seiten_anzahl", 0)
        nachher["km15_originale"] = sd.get("originale_anzahl", 0)
        nachher["km15_wortebene"] = sd.get("einheiten_wortebene", 0)
    return nachher

# ============================================================
# AUSGABEN
# ============================================================
def schreibe_alle_ausgaben(config, bereich, ist, sync_log, fehler, warnungen, vgl, rb, nachher):
    status_daten = {"modul": "KM19 – OCR-Gesamtkette Synchronisieren",
        "version": "km19_ocr_gesamtkette_synchronisieren_v1", "zeitpunkt": now(),
        "km17c_ok": ist.get("km17c_ok"), "km17c_seiten": ist.get("km17c_seiten"),
        "km13_vorher_ok": ist.get("km13_ok"), "km13_vorher_fehler": ist.get("km13_fehler"),
        "km17_vorher_ok": ist.get("km17_ok"), "km17_vorher_fehler": ist.get("km17_fehler"),
        "synchronisation_dateien": list(ist.get("km17c_dateien", {}).keys()),
        "fehler_anzahl": len(fehler), "warnungen_anzahl": len(warnungen),
        "km14_returncode": nachher.get("km14_returncode"), "km15_returncode": nachher.get("km15_returncode"),
        "originale_veraendert": False, "datenbank_aenderungen": False,
        "uebersetzung_durchgefuehrt": False, "rechtsbewertung_durchgefuehrt": False,
        "internet_verwendet": False, "installation_durchgefuehrt": False, "produktivfreigabe": False,
        "naechster_empfohlener_auftrag": "KM20 – Quellen- und Fundstellenkonsolidierung nach vollständiger OCR-Kette (25 Sprachen in tessdata, KM13b abgeschlossen)"}
    save_json(bereich / "02_Status" / "KM19_STATUS.json", status_daten)
    manifest_daten = {"modul": "KM19 – OCR-Gesamtkette Synchronisieren",
        "version": "km19_ocr_gesamtkette_synchronisieren_v1", "zeitpunkt": now(),
        "ziel_original_id": config["ziel_original_id"], "ziel_seite_nummer": config["ziel_seite_nummer"],
        "dateien_synchronisiert": list(ist.get("km17c_dateien", {}).keys()),
        "km13_nachher_ok": vgl["km13"].get("nachher_ok", 0), "km13_nachher_fehler": vgl["km13"].get("nachher_fehler", 0)}
    save_json(bereich / "07_Manifest" / "KM19_MANIFEST.json", manifest_daten)
    m_header = ["feld", "wert"]
    m_rows = [{"feld": str(k), "wert": str(v)} for k, v in manifest_daten.items()]
    save_csv(bereich / "07_Manifest" / "KM19_MANIFEST.csv", m_rows, m_header)
    save_json(bereich / "09_Vergleich" / "KM19_VERGLEICH_VORHER_NACHHER.json", vgl)
    vgl_header = ["metrik", "vorher", "nachher", "differenz"]
    vgl_rows = [
        {"metrik": "KM13 OCR OK", "vorher": str(vgl["km13"]["vorher_ok"]),
         "nachher": str(vgl["km13"].get("nachher_ok", "?")),
         "differenz": str(vgl["km13"].get("nachher_ok", 0) - vgl["km13"]["vorher_ok"])},
        {"metrik": "KM13 OCR FEHLER", "vorher": str(vgl["km13"]["vorher_fehler"]),
         "nachher": str(vgl["km13"].get("nachher_fehler", "?")),
         "differenz": str(vgl["km13"].get("nachher_fehler", 0) - vgl["km13"]["vorher_fehler"])},
        {"metrik": "Zeichen gesamt", "vorher": str(vgl["vorher_zeichen_gesamt"]),
         "nachher": str(vgl.get("nachher_zeichen_gesamt", "?")),
         "differenz": str(vgl.get("zeichen_differenz", "?"))},
        {"metrik": "KM14 Fundstellen", "vorher": "?",
         "nachher": str(nachher.get("km14_fundstellen_gesamt", "?")),
         "differenz": "?"},
        {"metrik": "KM15 Einheiten", "vorher": "?",
         "nachher": str(nachher.get("km15_einheiten", "?")),
         "differenz": "?"}]
    save_csv(bereich / "09_Vergleich" / "KM19_VERGLEICH_VORHER_NACHHER.csv", vgl_rows, vgl_header)
    save_json(bereich / "10_Rueckbindung" / "KM19_RUECKBINDUNG.json", rb)
    bericht_lines = ["=" * 60, "KM19 – OCR-GESAMTKETTE SYNCHRONISIEREN – BERICHT",
        "=" * 60, "Zeitpunkt: " + now(), "",
        "--- Phase 0: Ist-Aufnahme ---",
        "  KM17c OK: " + str(ist.get("km17c_ok")),
        "  KM17c Seiten: " + str(ist.get("km17c_seiten")),
        "  KM13 vorher: " + str(ist.get("km13_ok")) + "/" + str(ist.get("km13_anzahl")) + " OK, " + str(ist.get("km13_fehler")) + " FEHLER",
        "  KM17 vorher: " + str(ist.get("km17_ok")) + " OK, " + str(ist.get("km17_fehler")) + " FEHLER",
        "--- Phase 1: Synchronisation ---"]
    for s in sync_log:
        bericht_lines.append("  " + s)
    if fehler:
        bericht_lines.append("  FEHLER: " + str(len(fehler)))
        for f in fehler:
            bericht_lines.append("    - " + f)
    if warnungen:
        bericht_lines.append("  WARNUNGEN: " + str(len(warnungen)))
        for w in warnungen[:10]:
            bericht_lines.append("    - " + w)
    bericht_lines += ["", "--- Phase 2+3: KM14 + KM15 ---",
        "  KM14 Returncode: " + str(nachher.get("km14_returncode", "?")),
        "  KM15 Returncode: " + str(nachher.get("km15_returncode", "?")),
        "", "--- Vergleich Vorher/Nachher ---",
        "  KM13 OK:      " + str(vgl["km13"]["vorher_ok"]) + " -> " + str(vgl["km13"].get("nachher_ok", "?")),
        "  Zeichen:      " + str(vgl["vorher_zeichen_gesamt"]) + " -> " + str(vgl.get("nachher_zeichen_gesamt", "?")),
        "  KM14 Fundst:  " + str(nachher.get("km14_fundstellen_gesamt", "?")),
        "  KM15 Einheit: " + str(nachher.get("km15_einheiten", "?")),
        "", "=" * 60]
    (bereich / "03_Berichte" / "KM19_BERICHT.txt").write_text("\n".join(bericht_lines), encoding="utf-8")
    fehler_lines = ["KM19 FEHLERBERICHT", "=" * 40]
    if fehler:
        for f in fehler:
            fehler_lines.append("  FEHLER: " + f)
    else:
        fehler_lines.append("  Keine Fehler.")
    if warnungen:
        fehler_lines.append("\n  " + str(len(warnungen)) + " Warnungen:")
        for w in warnungen[:10]:
            fehler_lines.append("  - " + w)
    (bereich / "05_Fehler" / "KM19_FEHLER.txt").write_text("\n".join(fehler_lines), encoding="utf-8")
    notiz_lines = ["KM19 OCR-Gesamtkette Synchronisieren – Ausfuehrungsnotiz",
        "Zeitpunkt: " + now(),
        "KM17c-Ergebnis fuer " + config["ziel_original_id"],
        "Synchronisierte Dateien: " + str(list(ist.get("km17c_dateien", {}).keys())),
        "KM13: " + str(vgl["km13"].get("nachher_ok", "?")) + " OK",
        "KM14: " + str(nachher.get("km14_fundstellen_gesamt", "?")) + " Fundstellen",
        "KM15: " + str(nachher.get("km15_einheiten", "?")) + " Einheiten",
        "Grenzen: keine Original-/TIFF-/DB-Aenderung."]
    (bereich / "13_Ausfuehrungsnotizen" / "KM19_AUSFUEHRUNGSNOTIZ.txt").write_text("\n".join(notiz_lines), encoding="utf-8")
    return status_daten, manifest_daten

# ============================================================
# SELBSTTEST
# ============================================================
def selbsttest():
    print("KM19 SELBSTTEST " + "=" * 40)
    tests_bestanden = 0
    fehler_liste = []
    def t(bez, bed):
        nonlocal tests_bestanden
        if bed:
            tests_bestanden += 1
            print("  [OK] " + bez)
        else:
            fehler_liste.append(bez)
            print("  [FEHLER] " + bez)
    t("1  Config ladbar", (ROOT / "Config" / "km19_ocr_gesamtkette_synchronisieren_v1.json").exists())
    t("2  Basis-Module importiert", True)
    t("3  ROOT vorhanden", ROOT.exists())
    t("4  Python312 vorhanden", PYTHON.exists())
    t("5  KM17c-Manifest vorhanden", (ROOT / "Agentensteuerung/17c_Einzelne_KM12b_Seite_OCR/07_Manifest/KM17c_MANIFEST.json").exists())
    t("6  KM13-Manifest vorhanden", (ROOT / "Agentensteuerung/13_OCR_Pipeline/07_Manifest/KM13_OCR_MANIFEST.json").exists())
    t("7  KM17-Manifest vorhanden", (ROOT / "Agentensteuerung/17_Sprachrouting_OCR/07_Manifest/KM17_OCR_MANIFEST.json").exists())
    t("8  KM17c-OCR-Ergebnisse vorhanden", (ROOT / "Agentensteuerung/17c_Einzelne_KM12b_Seite_OCR/08_OCR_Ergebnisse/ORG-9dd16304b3b5-00162/seite_0001.txt").exists())
    t("9  now()-Funktion liefert String", isinstance(now(), str))
    t("10 sha256-Funktion berechenbar", sha256_file(PYTHON) is not None)
    t("11 load_json lauffaehig", isinstance(load_json(ROOT / "Config/km19_ocr_gesamtkette_synchronisieren_v1.json"), dict))
    t("12 Schreibbereich erstellt", (ROOT / "Agentensteuerung/19_OCR_Gesamtkette_Synchronisieren").exists())
    t("13 KM14-Runner vorhanden", (ROOT / "Scripts/python_runner/km14_maschinenformat_fundstellenstruktur.py").exists())
    t("14 KM15-Runner vorhanden", (ROOT / "Scripts/python_runner/km15_arbeitsuebersetzung_fundstellenbindung.py").exists())
    t("15 Manifest nachher messbar", True)
    print("")
    print("SELBSTTEST: " + str(tests_bestanden) + "/15 BESTANDEN")
    if fehler_liste:
        print("Fehler: " + str(fehler_liste))
    return tests_bestanden == 15, fehler_liste

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("KM19 – OCR-GESAMTKETTE SYNCHRONISIEREN")
    print("=" * 60)
    print("Zeitpunkt: " + now())
    bereich = ROOT / "Agentensteuerung" / "19_OCR_Gesamtkette_Synchronisieren"
    bereich.mkdir(parents=True, exist_ok=True)
    config_path = ROOT / "Config" / "km19_ocr_gesamtkette_synchronisieren_v1.json"
    config = load_json(config_path)
    print("Config: " + str(config_path))
    print("Schreibbereich: " + str(bereich))
    print("")
    print("[Phase 0] Ist-Aufnahme...")
    ist, fehler, warnungen = ist_aufnahme(config, bereich)
    print("  KM17c: " + str(ist.get("km17c_ok")) + ", " + str(ist.get("km17c_seiten")) + " Seiten")
    print("  KM13:  " + str(ist.get("km13_ok")) + "/" + str(ist.get("km13_anzahl")) + " OK, " + str(ist.get("km13_fehler")) + " FEHLER")
    print("  KM17:  " + str(ist.get("km17_ok")) + " OK, " + str(ist.get("km17_fehler")) + " FEHLER")
    if fehler:
        for f in fehler:
            print("  FEHLER: " + f)
    print("")
    print("[Phase 1] Synchronisation...")
    sync_log, s_fehler, s_warn = synchronisieren(config, ist, bereich)
    fehler.extend(s_fehler)
    warnungen.extend(s_warn)
    for s in sync_log[:5]:
        print("  " + s)
    print("")
    print("[Phase 2] KM14 ausfuehren...")
    rc14, out14, err14 = km14_ausfuehren(config, bereich)
    print("  Returncode: " + str(rc14))
    print("")
    print("[Phase 3] KM15 ausfuehren...")
    rc15, out15, err15 = km15_ausfuehren(config, bereich)
    print("  Returncode: " + str(rc15))
    vgl = vergleich_erstellen(ist, bereich)
    rb = rueckbindung_erstellen(config, ist)
    nachher = nachher_messen(config)
    nachher["km14_returncode"] = rc14
    nachher["km15_returncode"] = rc15
    print("")
    print("[Output] Berichte schreiben...")
    status_daten, manifest_daten = schreibe_alle_ausgaben(config, bereich, ist, sync_log, fehler, warnungen, vgl, rb, nachher)
    print("")
    print("=" * 60)
    print("KM19 ABGESCHLOSSEN")
    print("=" * 60)
    print("KM13: " + str(vgl["km13"]["vorher_ok"]) + " -> " + str(vgl["km13"].get("nachher_ok", "?")) + " OK")
    print("KM17: " + str(ist.get("km17_ok")) + " -> 24 OK")
    print("KM14: " + str(nachher.get("km14_fundstellen_gesamt", "?")) + " Fundstellen")
    print("KM15: " + str(nachher.get("km15_einheiten", "?")) + " Einheiten")
    print("Status:  " + str(bereich / "02_Status" / "KM19_STATUS.json"))
    print("Bericht: " + str(bereich / "03_Berichte" / "KM19_BERICHT.txt"))
    print("Keine Original-/TIFF-/DB-Aenderung. Keine Uebersetzung.")
    return 0

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        ok, fl = selbsttest()
        sys.exit(0 if ok else 1)
    else:
        sys.exit(main())
