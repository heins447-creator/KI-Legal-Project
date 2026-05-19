import sys, json, csv, datetime
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
BEREICH = ROOT / "Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung"
SRC = BEREICH / "08_Konsolidierung/KM20_KONSOLIDIERUNG.json"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

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

TEST_IDS = {"ORG-TEST-KM14"}

def main():
    print("KM20b – TESTDUMMY-AUSSCHLUSS " + "=" * 40)
    src = load_json(SRC)
    alle = src["eintraege"]
    real = [z for z in alle if z["original_id"] not in TEST_IDS]
    test = [z for z in alle if z["original_id"] in TEST_IDS]
    print(f"Echte Seiten: {len(real)} (von {len(alle)})")
    print(f"Testdaten: {len(test)}")

    if test:
        save_json(BEREICH / "08_Konsolidierung/KM20_TESTDATEN.json", {
            "modul": "KM20", "beschreibung": "Testdaten – nicht produktiv",
            "anzahl_testseiten": len(test), "eintraege": test})
        print("+ Testdaten separiert: KM20_TESTDATEN.json")

    # Produktive Konsolidierung ueberschreiben
    save_json(SRC, {"modul": src["modul"], "version": src["version"],
        "zeitpunkt": src["zeitpunkt"], "anzahl_seiten": len(real), "eintraege": real})

    # Master-Index
    master = {"modul": "KM20", "version": src["version"], "zeitpunkt": now(),
        "anzahl_originale": 3, "anzahl_seiten": len(real),
        "seiten_mit_ocr_ok": sum(1 for z in real if z["ocr_status"] == "OK"),
        "seiten_mit_fundstellen": sum(1 for z in real if z["fundstellen_km14_anzahl"] > 0),
        "seiten_mit_uebersetzungseinheiten": sum(1 for z in real if z["uebersetzungseinheiten_km15_anzahl"] > 0),
        "seiten_mit_unsicherheiten": sum(1 for z in real if z["unsicherheiten_anzahl"] > 0),
        "rueckbindungstiefe_max": max((z["rueckbindung_anzahl"] for z in real), default=0),
        "schluessel": [z["original_id"] + "|S" + str(z["seite_nummer"]) for z in real]}
    save_json(BEREICH / "07_Manifest/KM20_MASTER_INDEX.json", master)
    save_csv(BEREICH / "07_Manifest/KM20_MASTER_INDEX.csv",
        [{"schluessel": s} for s in master["schluessel"]], ["schluessel"])

    # Rueckbindung
    rb = {}
    for z in real:
        k = z["original_id"] + "|" + str(z["seite_nummer"])
        rb[k] = {"original_id": z["original_id"], "seite_nummer": z["seite_nummer"],
            "kette": z["rueckbindung_kette"], "module": list(set(z["rueckbindung_kette"]))}
    save_json(BEREICH / "10_Rueckbindung/KM20_RUECKBINDUNG.json", {
        "modul": "KM20", "zeitpunkt": now(), "anzahl_eintraege": len(rb),
        "rueckbindung": list(rb.values())})

    # Unsicherheiten
    alle_uns = []
    for z in real:
        for u in z["unsicherheiten"]:
            alle_uns.append({"original_id": z["original_id"], "seite_nummer": z["seite_nummer"],
                "quelle": u.get("quelle", ""), "typ": u.get("typ", ""),
                "beschreibung": str(u.get("beschreibung", u.get("wert", "")))[:120]})
    save_json(BEREICH / "09_Unsicherheiten/KM20_UNSICHERHEITEN.json", {
        "modul": "KM20", "zeitpunkt": now(), "anzahl_unsicherheiten": len(alle_uns),
        "eintraege": alle_uns})

    # Status
    fs = sum(z["fundstellen_km14_anzahl"] for z in real)
    ue = sum(z["uebersetzungseinheiten_km15_anzahl"] for z in real)
    uns = sum(z["unsicherheiten_anzahl"] for z in real)
    status = {"modul": "KM20", "version": src["version"], "zeitpunkt": now(),
        "anzahl_originale": 3, "anzahl_seiten_konsolidiert": len(real),
        "anzahl_fundstellen_km14": fs, "anzahl_uebersetzungseinheiten_km15": ue,
        "anzahl_unsicherheiten": uns,
        "rueckbindungstiefe_max": max((z["rueckbindung_anzahl"] for z in real), default=0),
        "testdaten_ausgeschlossen": len(test),
        "fehler_anzahl": 0, "warnungen_anzahl": 0,
        "originale_veraendert": False, "datenbank_aenderungen": False,
        "uebersetzung_durchgefuehrt": False, "rechtsbewertung_durchgefuehrt": False,
        "internet_verwendet": False, "installation_durchgefuehrt": False, "produktivfreigabe": False}
    save_json(BEREICH / "02_Status/KM20_STATUS.json", status)

    # Bericht
    bericht = ["KM20b – QUELLEN- UND FUNDSTELLENKONSOLIDIERUNG – PRODUKTIVBEREINIGT",
        "=" * 60, "Zeitpunkt: " + now(), "",
        f"Echte Originale: 3",
        f"Echte Seiten: {len(real)}",
        f"Fundstellen (KM14): {fs}",
        f"Uebersetzungseinheiten (KM15): {ue}",
        f"Unsicherheiten: {uns}",
        f"Testdaten ausgeschlossen: {len(test)} Seite(n) (ORG-TEST-KM14, 0 Fundstellen)",
        "", "--- Grenzen: Keine Original-/OCR-/DB-Aenderung ---",
        "Naechster Schritt: Uebersetzungsmodell in Tools/Translation"]
    (BEREICH / "03_Berichte").mkdir(parents=True, exist_ok=True)
    (BEREICH / "03_Berichte/KM20_PRODUKTIV_BERICHT.txt").write_text("\n".join(bericht), encoding="utf-8-sig")

    print(f"\nKM20b ERGEBNIS:")
    print(f"  Produktiv: {len(real)} Seiten, {fs} FS, {ue} UE, {uns} Unsicherheiten")
    print(f"  Ausgeschlossen: {len(test)} Testseite(n)")
    print(f"  Originale: 3 (echt)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
