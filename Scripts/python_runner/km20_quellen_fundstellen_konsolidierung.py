import sys, os, json, csv, hashlib, subprocess, datetime
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
    return json.loads(Path(pfad).read_text(encoding="utf-8-sig"))

def save_json(pfad, daten):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    Path(pfad).write_text(json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8-sig")

def save_csv(pfad, zeilen, header):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(zeilen)

print("Core functions loaded")

# ============================================================
# PHASE 0: IST-AUFNAHME
# ============================================================
def ist_aufnahme(config):
    fehler = []
    warnungen = []
    ist = {}

    # KM13
    km13p = ROOT / config["quellen"]["km13_manifest"]
    if km13p.exists():
        ist["km13"] = load_json(km13p)
        ist["km13_ergebnisse"] = ist["km13"].get("ergebnisse", [])
        ist["km13_index"] = {}
        for e in ist["km13_ergebnisse"]:
            key = (e.get("original_id", ""), e.get("seite_nummer", 0))
            ist["km13_index"][key] = e
    else:
        fehler.append("KM13-Manifest fehlt")

    # KM14 Maschinenformat (per original)
    mf_dir = ROOT / config["quellen"]["km14_maschinenformat_dir"]
    ist["km14_mf"] = {}
    for mf_file in sorted(mf_dir.glob("*_maschinenformat.json")):
        d = load_json(mf_file)
        oid = d.get("original_id", mf_file.stem.replace("_maschinenformat", ""))
        ist["km14_mf"][oid] = d
    if not ist["km14_mf"]:
        warnungen.append("Keine KM14-Maschinenformat-Dateien gefunden")

    # KM14 Fundstellen (per original)
    fs_dir = ROOT / config["quellen"]["km14_fundstellen_dir"]
    ist["km14_fs"] = {}
    for fs_file in sorted(fs_dir.glob("*_fundstellen.json")):
        d = load_json(fs_file)
        oid = d.get("original_id", "")
        ist["km14_fs"][oid] = d

    # KM14 Textstruktur
    ts_dir = ROOT / config["quellen"]["km14_textstruktur_dir"]
    ist["km14_ts"] = {}
    for ts_file in sorted(ts_dir.glob("*_textstruktur.json")):
        d = load_json(ts_file)
        oid = d.get("original_id", "")
        ist["km14_ts"][oid] = d

    # KM14 Unsicherheiten
    uns_p = ROOT / config["quellen"]["km14_unsicherheiten"]
    if uns_p.exists():
        ist["km14_unsicherheiten"] = load_json(uns_p)
    else:
        ist["km14_unsicherheiten"] = {"eintraege": []}

    # KM15 Uebersetzungseinheiten (per original)
    ue_dir = ROOT / config["quellen"]["km15_uebersetzungseinheiten_dir"]
    ist["km15_ue"] = {}
    for ue_file in sorted(ue_dir.glob("*_uebersetzungseinheiten.json")):
        d = load_json(ue_file)
        oid = d.get("original_id", "")
        ist["km15_ue"][oid] = d

    # KM17 Manifest
    km17p = ROOT / config["quellen"]["km17_manifest"]
    if km17p.exists():
        ist["km17"] = load_json(km17p)
        ist["km17_index"] = {}
        for e in ist["km17"].get("ergebnisse", []):
            key = (e.get("original_id", ""), e.get("seite_nummer", 0))
            ist["km17_index"][key] = e
    else:
        warnungen.append("KM17-Manifest fehlt")

    # KM17c Manifest
    km17cp = ROOT / config["quellen"]["km17c_manifest"]
    if km17cp.exists():
        ist["km17c"] = load_json(km17cp)
        ist["km17c_index"] = {}
        for e in ist["km17c"].get("ergebnisse", []):
            ist["km17c_index"][(e.get("original_id", ""), e.get("seite_nummer", 0))] = e
    else:
        ist["km17c"] = {}
        warnungen.append("KM17c-Manifest fehlt")

    # KM19 Status
    km19p = ROOT / config["quellen"]["km19_status"]
    if km19p.exists():
        ist["km19"] = load_json(km19p)
    else:
        warnungen.append("KM19-Status fehlt")

    # KM12 Manifest
    km12p = ROOT / config["quellen"]["km12_manifest"]
    if km12p.exists():
        ist["km12"] = load_json(km12p)
        ist["km12_index"] = {}
        for e in ist["km12"].get("seiten", ist["km12"].get("ergebnisse", [])):
            if isinstance(e, dict):
                ist["km12_index"][(e.get("original_id", ""), e.get("seite_nummer", 0))] = e
    else:
        ist["km12"] = {}
        warnungen.append("KM12-Manifest fehlt")

    return ist, fehler, warnungen

# ============================================================
# PHASE 1: KONSOLIDIERUNG
# ============================================================
def konsolidieren(config, ist):
    zeilen = []
    rueckbindung = {}

    # Alle Originale und Seiten aus KM14-Maschinenformat sammeln
    for oid, mf in ist["km14_mf"].items():
        seiten = mf.get("seiten", [])
        for seite in seiten:
            sn = seite.get("seite_nummer", 0)
            sid = seite.get("seiten_id", "")
            key = (oid, sn)

            z = {
                "original_id": oid,
                "seite_nummer": sn,
                "seiten_id": sid,
                "bbox_px": seite.get("bbox_px", []),
                "ocr_status": seite.get("ocr_status", ""),
            }

            # --- OCR-Quelle bestimmen ---
            ocr_quelle = "KM13"
            if key in ist.get("km17c_index", {}):
                ocr_quelle = "KM17c (Einzelseiten-Reparatur via KM12b+KM19)"
            elif key in ist.get("km17_index", {}):
                km17e = ist["km17_index"][key]
                if km17e.get("sprache", "") not in ("eng", "deu", ""):
                    ocr_quelle = "KM17 (Sprachrouting: " + km17e.get("sprache", "?") + ")"
            z["ocr_quelle"] = ocr_quelle

            # --- TXT/HOCR/TSV-Bezug ---
            ocr_dateien = {}
            for ocr_dir_key in ["km13_ocr_dir", "km17_ocr_dir", "km17c_ocr_dir"]:
                basis = ROOT / config["quellen"][ocr_dir_key] / oid
                for dt in ["txt", "hocr", "tsv"]:
                    pfad = basis / f"seite_{sn:04d}.{dt}"
                    if pfad.exists():
                        ocr_dateien[dt] = str(pfad.relative_to(ROOT))
            z["ocr_dateien"] = ocr_dateien

            # --- KM14 Fundstellen ---
            fs_data = ist["km14_fs"].get(oid, {})
            fs_liste = fs_data.get("fundstellen", [])
            fs_seite = [f for f in fs_liste if f.get("seite_nummer") == sn]
            z["fundstellen_km14_anzahl"] = len(fs_seite)
            z["fundstellen_km14_ids"] = [f.get("fundstelle_id", "") for f in fs_seite[:10]]
            if len(fs_seite) > 10:
                z["fundstellen_km14_ids"].append("...+" + str(len(fs_seite) - 10))

            # --- KM15 Uebersetzungseinheiten ---
            ue_data = ist["km15_ue"].get(oid, {})
            ue_liste = ue_data.get("uebersetzungseinheiten", [])
            ue_seite = [u for u in ue_liste if u.get("seite_nummer") == sn]
            z["uebersetzungseinheiten_km15_anzahl"] = len(ue_seite)
            z["uebersetzungseinheiten_km15_ids"] = [u.get("uebersetzungseinheit_id", "") for u in ue_seite[:10]]
            if len(ue_seite) > 10:
                z["uebersetzungseinheiten_km15_ids"].append("...+" + str(len(ue_seite) - 10))

            # --- Koordinatenbezug (bbox) ---
            z["koordinaten_bbox_px"] = seite.get("bbox_px", [])

            # --- Unsicherheiten ---
            uns_liste = []
            # KM14 Unsicherheiten
            for u in ist.get("km14_unsicherheiten", {}).get("eintraege", []):
                if u.get("original_id") == oid and u.get("seite_nummer") == sn:
                    uns_liste.append({"quelle": "KM14", "typ": u.get("typ", ""), "beschreibung": str(u.get("beschreibung", ""))[:120]})
            # KM13 confidence
            km13e = ist.get("km13_index", {}).get(key, {})
            konf = km13e.get("durchschnittliche_konfidenz", 0)
            if konf and konf < 70:
                uns_liste.append({"quelle": "KM13", "typ": "niedrige_konfidenz", "wert": konf})
            # KM17c confidence (for repaired pages)
            for km17ce in ist.get("km17c", {}).get("ergebnisse", []):
                if km17ce.get("original_id") == oid and km17ce.get("seite_nummer") == sn:
                    k = km17ce.get("durchschnittliche_konfidenz", 0)
                    if k and k < 70:
                        uns_liste.append({"quelle": "KM17c", "typ": "niedrige_konfidenz", "wert": k})
            z["unsicherheiten"] = uns_liste
            z["unsicherheiten_anzahl"] = len(uns_liste)

            # --- Rueckbindung auf KM12/12b/17/17c/19 ---
            rb = []
            # KM12
            if key in ist.get("km12_index", {}):
                rb.append("KM12")
            # KM12b (wenn KM17c-Eintrag existiert)
            if any(ce.get("original_id") == oid for ce in ist.get("km17c", {}).get("ergebnisse", [])):
                rb.append("KM12b")
            # KM17
            if key in ist.get("km17_index", {}):
                rb.append("KM17")
            # KM17c
            if key in ist.get("km17c_index", {}):
                rb.append("KM17c")
            # KM19
            if ist.get("km19", {}).get("km17c_ok"):
                rb.append("KM19")
            # KM13 and KM14/KM15 always applicable
            rb.extend(["KM13", "KM14", "KM15"])
            z["rueckbindung_kette"] = rb
            z["rueckbindung_anzahl"] = len(set(rb))

            zeilen.append(z)

            # Rueckbindungsgraph
            graph_key = oid + "|" + str(sn)
            rueckbindung[graph_key] = {
                "original_id": oid,
                "seite_nummer": sn,
                "kette": rb,
                "module": list(set(rb))
            }

    return zeilen, rueckbindung

# ============================================================
# AUSGABEN
# ============================================================
def schreibe_alle_ausgaben(config, bereich, ist, zeilen, rueckbindung, fehler, warnungen):
    # Konsolidierung JSON + CSV
    kons_json = {"modul": "KM20", "version": config["version"],
        "zeitpunkt": now(), "anzahl_seiten": len(zeilen), "eintraege": zeilen}
    save_json(bereich / config["ausgaben"]["konsolidierung_json"], kons_json)

    csv_header = ["original_id", "seite_nummer", "seiten_id", "ocr_quelle",
        "ocr_dateien_txt", "ocr_dateien_hocr", "ocr_dateien_tsv",
        "fundstellen_km14_anzahl", "fundstellen_km14_ids",
        "uebersetzungseinheiten_km15_anzahl", "uebersetzungseinheiten_km15_ids",
        "koordinaten_bbox_px", "unsicherheiten_anzahl", "unsicherheiten_details",
        "rueckbindung_kette", "rueckbindung_anzahl"]
    csv_zeilen = []
    for z in zeilen:
        csv_zeilen.append({
            "original_id": z["original_id"],
            "seite_nummer": z["seite_nummer"],
            "seiten_id": z["seiten_id"],
            "ocr_quelle": z["ocr_quelle"],
            "ocr_dateien_txt": z["ocr_dateien"].get("txt", ""),
            "ocr_dateien_hocr": z["ocr_dateien"].get("hocr", ""),
            "ocr_dateien_tsv": z["ocr_dateien"].get("tsv", ""),
            "fundstellen_km14_anzahl": z["fundstellen_km14_anzahl"],
            "fundstellen_km14_ids": "|".join(z["fundstellen_km14_ids"]),
            "uebersetzungseinheiten_km15_anzahl": z["uebersetzungseinheiten_km15_anzahl"],
            "uebersetzungseinheiten_km15_ids": "|".join(z["uebersetzungseinheiten_km15_ids"]),
            "koordinaten_bbox_px": str(z["koordinaten_bbox_px"]),
            "unsicherheiten_anzahl": z["unsicherheiten_anzahl"],
            "unsicherheiten_details": str(z["unsicherheiten"])[:200],
            "rueckbindung_kette": " > ".join(z["rueckbindung_kette"]),
            "rueckbindung_anzahl": z["rueckbindung_anzahl"]
        })
    save_csv(bereich / config["ausgaben"]["konsolidierung_csv"], csv_zeilen, csv_header)

    # Master Index
    master = {"modul": "KM20", "version": config["version"], "zeitpunkt": now(),
        "anzahl_originale": len(ist["km14_mf"]),
        "anzahl_seiten": len(zeilen),
        "seiten_mit_ocr_ok": sum(1 for z in zeilen if z["ocr_status"] == "OK"),
        "seiten_mit_fundstellen": sum(1 for z in zeilen if z["fundstellen_km14_anzahl"] > 0),
        "seiten_mit_uebersetzungseinheiten": sum(1 for z in zeilen if z["uebersetzungseinheiten_km15_anzahl"] > 0),
        "seiten_mit_unsicherheiten": sum(1 for z in zeilen if z["unsicherheiten_anzahl"] > 0),
        "rueckbindungstiefe_max": max((z["rueckbindung_anzahl"] for z in zeilen), default=0),
        "schluessel": [z["original_id"] + "|S" + str(z["seite_nummer"]) for z in zeilen]}
    save_json(bereich / config["ausgaben"]["master_index_json"], master)
    save_csv(bereich / config["ausgaben"]["master_index_csv"],
        [{"schluessel": s} for s in master["schluessel"]], ["schluessel"])

    # Rueckbindung
    save_json(bereich / config["ausgaben"]["rueckbindung_json"], {
        "modul": "KM20", "zeitpunkt": now(), "anzahl_eintraege": len(rueckbindung),
        "rueckbindung": list(rueckbindung.values())})

    # Unsicherheiten-konsolidiert
    alle_uns = []
    for z in zeilen:
        for u in z["unsicherheiten"]:
            alle_uns.append({"original_id": z["original_id"], "seite_nummer": z["seite_nummer"],
                "quelle": u.get("quelle", ""), "typ": u.get("typ", ""),
                "beschreibung": str(u.get("beschreibung", u.get("wert", "")))[:120]})
    save_json(bereich / config["ausgaben"]["unsicherheiten_json"], {
        "modul": "KM20", "zeitpunkt": now(), "anzahl_unsicherheiten": len(alle_uns),
        "eintraege": alle_uns})

    # Status
    status = {"modul": "KM20 – Quellen- und Fundstellenkonsolidierung",
        "version": config["version"], "zeitpunkt": now(),
        "anzahl_originale": len(ist["km14_mf"]),
        "anzahl_seiten_konsolidiert": len(zeilen),
        "anzahl_fundstellen_km14": sum(z["fundstellen_km14_anzahl"] for z in zeilen),
        "anzahl_uebersetzungseinheiten_km15": sum(z["uebersetzungseinheiten_km15_anzahl"] for z in zeilen),
        "anzahl_unsicherheiten": sum(z["unsicherheiten_anzahl"] for z in zeilen),
        "rueckbindungstiefe_max": max((z["rueckbindung_anzahl"] for z in zeilen), default=0),
        "fehler_anzahl": len(fehler), "warnungen_anzahl": len(warnungen),
        "originale_veraendert": False, "datenbank_aenderungen": False,
        "uebersetzung_durchgefuehrt": False, "rechtsbewertung_durchgefuehrt": False,
        "internet_verwendet": False, "installation_durchgefuehrt": False, "produktivfreigabe": False,
        "naechster_empfohlener_auftrag": "Lokales Uebersetzungsmodell in Tools/Translation bereitstellen (Argos Translate / LibreTranslate), dann KM15-Neulauf mit aktiver Uebersetzung"}
    save_json(bereich / config["ausgaben"]["statistik_json"], status)

    # Bericht
    bericht_lines = ["=" * 60, "KM20 – QUELLEN- UND FUNDSTELLENKONSOLIDIERUNG – BERICHT",
        "=" * 60, "Zeitpunkt: " + now(), "",
        "--- Konsolidierungsergebnis ---",
        "  Originale: " + str(len(ist["km14_mf"])),
        "  Seiten: " + str(len(zeilen)),
        "  Fundstellen (KM14): " + str(sum(z["fundstellen_km14_anzahl"] for z in zeilen)),
        "  Uebersetzungseinheiten (KM15): " + str(sum(z["uebersetzungseinheiten_km15_anzahl"] for z in zeilen)),
        "  Unsicherheiten: " + str(sum(z["unsicherheiten_anzahl"] for z in zeilen)),
        "", "--- Seitenuebersicht ---"]
    for z in zeilen:
        bericht_lines.append(f"  {z['original_id']}#{z['seite_nummer']}: OCR={z['ocr_quelle'][:30]} FS={z['fundstellen_km14_anzahl']} UE={z['uebersetzungseinheiten_km15_anzahl']} UNS={z['unsicherheiten_anzahl']} RB={'>'.join(z['rueckbindung_kette'][:5])}")
    if fehler:
        bericht_lines.append("\n--- FEHLER ---")
        for f in fehler:
            bericht_lines.append("  " + f)
    if warnungen:
        bericht_lines.append("\n--- WARNUNGEN ---")
        for w in warnungen:
            bericht_lines.append("  " + w)
    bericht_lines += ["", "--- Grenzen eingehalten ---",
        "Keine Originalaenderung, keine OCR, keine Uebersetzung, keine DB-Aenderung, kein Internet.",
        "=" * 60]
    (bereich / "03_Berichte").mkdir(parents=True, exist_ok=True)
    (bereich / "03_Berichte" / "KM20_BERICHT.txt").write_text("\n".join(bericht_lines), encoding="utf-8-sig")

    # Fehlerbericht
    fl = ["KM20 FEHLERBERICHT", "=" * 40]
    if fehler:
        for f in fehler:
            fl.append("  FEHLER: " + f)
    else:
        fl.append("  Keine Fehler.")
    if warnungen:
        fl.append("\n  " + str(len(warnungen)) + " Warnungen:")
        for w in warnungen[:10]:
            fl.append("  - " + w)
    (bereich / "05_Fehler").mkdir(parents=True, exist_ok=True)
    (bereich / "05_Fehler" / "KM20_FEHLER.txt").write_text("\n".join(fl), encoding="utf-8-sig")

    return status

# ============================================================
# SELBSTTEST
# ============================================================
def selbsttest():
    print("KM20 SELBSTTEST " + "=" * 40)
    tests = 0
    fl = []
    def t(bez, bed):
        nonlocal tests
        if bed:
            tests += 1
            print("  [OK] " + bez)
        else:
            fl.append(bez)
            print("  [FEHLER] " + bez)

    config = load_json(ROOT / "Config" / "km20_quellen_fundstellen_konsolidierung_v1.json")
    t("1  Config ladbar", True)
    t("2  KM13-Manifest", (ROOT / config["quellen"]["km13_manifest"]).exists())
    t("3  KM14-Maschinenformat", (ROOT / config["quellen"]["km14_maschinenformat_dir"]).exists())
    t("4  KM14-Fundstellen", (ROOT / config["quellen"]["km14_fundstellen_dir"]).exists())
    t("5  KM15-UE-Dir", (ROOT / config["quellen"]["km15_uebersetzungseinheiten_dir"]).exists())
    t("6  KM17-Manifest", (ROOT / config["quellen"]["km17_manifest"]).exists())
    t("7  KM17c-Manifest", (ROOT / config["quellen"]["km17c_manifest"]).exists())
    t("8  KM19-Status", (ROOT / config["quellen"]["km19_status"]).exists())
    t("9  KM12-Manifest", (ROOT / config["quellen"]["km12_manifest"]).exists())
    t("10 PYTHON vorhanden", PYTHON.exists())
    t("11 ROOT vorhanden", ROOT.exists())
    t("12 now()-Funktion", isinstance(now(), str))
    t("13 sha256-Funktion", sha256_file(PYTHON) is not None)
    bereich = ROOT / config["schreibbereich"]
    bereich.mkdir(parents=True, exist_ok=True)
    t("14 Schreibbereich erstellt", bereich.exists())
    t("15 Ist-Aufnahme lauffaehig", len(ist_aufnahme(config)[0]) >= 3)

    print("\nSELBSTTEST: " + str(tests) + "/15 BESTANDEN")
    if fl:
        print("Fehler: " + str(fl))
    return tests == 15, fl

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("KM20 – QUELLEN- UND FUNDSTELLENKONSOLIDIERUNG")
    print("=" * 60)
    print("Zeitpunkt:", now())

    config = load_json(ROOT / "Config" / "km20_quellen_fundstellen_konsolidierung_v1.json")
    bereich = ROOT / config["schreibbereich"]
    bereich.mkdir(parents=True, exist_ok=True)

    print("\n[Phase 0] Ist-Aufnahme...")
    ist, fehler, warnungen = ist_aufnahme(config)
    print("  KM13 Seiten:", len(ist.get("km13_ergebnisse", [])))
    print("  KM14 Maschinenformate:", len(ist["km14_mf"]))
    print("  KM14 Fundstellen-Dateien:", len(ist["km14_fs"]))
    print("  KM15 UE-Dateien:", len(ist["km15_ue"]))
    if fehler:
        for f in fehler:
            print("  FEHLER:", f)

    print("\n[Phase 1] Konsolidierung...")
    zeilen, rueckbindung = konsolidieren(config, ist)
    print("  Seiten konsolidiert:", len(zeilen))
    print("  Rueckbindungseintraege:", len(rueckbindung))

    print("\n[Output] Ausgaben schreiben...")
    status = schreibe_alle_ausgaben(config, bereich, ist, zeilen, rueckbindung, fehler, warnungen)

    print("\n" + "=" * 60)
    print("KM20 ABGESCHLOSSEN")
    print("=" * 60)
    print("Seiten konsolidiert:", len(zeilen))
    print("Fundstellen (KM14):", sum(z["fundstellen_km14_anzahl"] for z in zeilen))
    print("UE (KM15):", sum(z["uebersetzungseinheiten_km15_anzahl"] for z in zeilen))
    print("Unsicherheiten:", sum(z["unsicherheiten_anzahl"] for z in zeilen))
    print("Rueckbindungstiefe max:", max((z["rueckbindung_anzahl"] for z in zeilen), default=0))
    print(f"\nAusgaben: {bereich}")
    print("Keine Original-/OCR-/DB-Aenderung. Keine Uebersetzung.")
    return 0

if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        ok, fl = selbsttest()
        sys.exit(0 if ok else 1)
    else:
        sys.exit(main())
