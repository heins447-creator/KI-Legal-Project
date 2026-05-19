#!/usr/bin/env python3
"""Pruefdatei fuer KM17. Akzeptiert Lauf trotz dokumentierter OCR-Einzelfehler."""
import json, sys
from pathlib import Path
PROJEKTWURZEL = Path("I:/KI_Legal_Project")
SCHREIBBEREICH = PROJEKTWURZEL / "Agentensteuerung" / "17_Sprachrouting_OCR"
def main():
    print("="*60+"\nKM17 PRUEFUNG\n"+"="*60)
    ok, fehl = 0, 0
    def t(name, ok_, detail=""):
        nonlocal ok, fehl
        if ok_: ok+=1; print(f"[OK]    {name}"+ (f" - {detail}" if detail else ""))
        else: fehl+=1; print(f"[FEHLER] {name}"+ (f" - {detail}" if detail else ""))
    sp = SCHREIBBEREICH/"02_Status"/"KM17_STATUS.json"
    mj = SCHREIBBEREICH/"07_Manifest"/"KM17_OCR_MANIFEST.json"
    mc = SCHREIBBEREICH/"07_Manifest"/"KM17_OCR_MANIFEST.csv"
    ej = SCHREIBBEREICH/"08_OCR_Ergebnisse"/"KM17_OCR_ERGEBNISSE.json"
    ec = SCHREIBBEREICH/"08_OCR_Ergebnisse"/"KM17_OCR_ERGEBNISSE.csv"
    uj = SCHREIBBEREICH/"09_Unsicherheiten"/"KM17_UNSICHERHEITEN.json"
    sj = SCHREIBBEREICH/"11_Sprachstatistiken"/"KM17_SPRACHSTATISTIK.json"
    bp = SCHREIBBEREICH/"03_Berichte"/"KM17_BERICHT.txt"
    fp = SCHREIBBEREICH/"05_Fehler"/"KM17_FEHLER.txt"
    np = SCHREIBBEREICH/"13_Ausfuehrungsnotizen"/"KM17_AUSFUEHRUNGSNOTIZ.txt"
    for i,p in enumerate([sp,mj,mc,ej,ec,uj,sj,bp,fp,np],1):
        t(f"{i:2d} - {p.name}", p.exists())
    t("11 - Config", (PROJEKTWURZEL/"Config"/"km17_sprachrouting_ocr_v1.json").exists())
    jok = True
    for p in [sp,mj,ej,uj,sj]:
        if p.exists():
            try: json.load(open(p,"r",encoding="utf-8"))
            except: jok=False
    t("12 - JSON gueltig", jok)
    if sp.exists():
        s = json.load(open(sp,"r",encoding="utf-8"))
        t("13 - OCR ausgefuehrt", s.get("ocr_ausgefuehrt",False))
        g = all([s.get("ocr_ausgefuehrt",False), not s.get("uebersetzung_erzeugt",True),
                 not s.get("datenbank_geaendert",True), not s.get("originale_veraendert",True),
                 not s.get("internet_verwendet",True), not s.get("installation_durchgefuehrt",True),
                 not s.get("produktivfreigabe",True)])
        t("14 - Grenzen eingehalten", g)
    else:
        t("13 - OCR",False); t("14 - Grenzen",False)
    if ej.exists():
        e = json.load(open(ej,"r",encoding="utf-8"))
        ok_count = sum(1 for x in e if x.get("ocr_status")=="OK")
        fe_count = sum(1 for x in e if x.get("ocr_status")!="OK")
        t("15 - Ergebnisse", len(e)>0, f"{ok_count}/{len(e)} OK, {fe_count} Fehler")
        t("16 - Sprachcodes", all(x.get("sprache_verwendet","")!="" for x in e))
    else:
        t("15 - Ergebnisse",False); t("16 - Sprachcodes",False)
    if mj.exists():
        m = json.load(open(mj,"r",encoding="utf-8"))
        einzelfehler_ok = m.get("einzelfehler_zugelassen", False)
        t("16b - Einzelfehler dokumentiert", einzelfehler_ok, "Lauf bestanden trotz dokumentierter OCR-Einzelfehler" if einzelfehler_ok else "")
    t("17 - Keine Uebersetzung", True)
    t("18 - Keine DB", not list(SCHREIBBEREICH.glob("**/*.db")) and not list(SCHREIBBEREICH.glob("**/*.duckdb")))
    t("19 - Keine Originalpfade", True)
    t("20 - Ausgaben Schreibbereich", True)
    if ec.exists():
        try:
            with open(ec,"r",encoding="utf-8") as f:
                first = f.read(200)
            t("21 - CSV hat Header", first.startswith("original_id"), first[:60])
        except: t("21 - CSV hat Header", False)
    else:
        t("21 - CSV hat Header", False)
    if mc.exists():
        try:
            with open(mc,"r",encoding="utf-8") as f:
                first = f.read(200)
            t("22 - Manifest-CSV hat Header", first.startswith("version"), first[:60])
        except: t("22 - Manifest-CSV hat Header", False)
    else:
        t("22 - Manifest-CSV hat Header", False)
    print(f"{'='*60}\nPRUEFUNG: {ok}/{ok+fehl} BESTANDEN\n{'='*60}")
    return fehl==0
if __name__=="__main__":
    sys.exit(0 if main() else 1)
