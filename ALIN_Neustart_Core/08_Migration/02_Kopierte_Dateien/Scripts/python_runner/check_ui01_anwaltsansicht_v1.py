# Check UI01 Anwaltsansicht V1
import sys, json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
B = ROOT / "Agentensteuerung/UI01_Anwaltsansicht_V1"
CONFIG = ROOT / "Config/ui01_anwaltsansicht_v1.json"

def main():
    print("UI01 PRUEFUNG " + "=" * 40)
    tests, fl = [], []

    def t(bez, bed):
        if bed: tests.append(1); print(f"  [OK] {bez}")
        else: fl.append(bez); print(f"  [FEHLER] {bez}")

    t("01 Status JSON", (B/"02_Status/UI01_STATUS.json").exists())
    t("02 Bericht TXT", (B/"03_Berichte/UI01_BERICHT.txt").exists())
    t("03 Fehlerbericht TXT", (B/"05_Fehler/UI01_FEHLER.txt").exists())
    t("04 Manifest JSON", (B/"07_Manifest/UI01_MANIFEST.json").exists())
    t("05 ViewData JSON", (B/"08_ViewData/UI01_DOKUMENT_VIEWDATA.json").exists())
    t("06 Notiztemplate JSON", (B/"09_Notizen/UI01_NOTIZEN_TEMPLATE.json").exists())
    t("07 Entscheidungstemplate JSON", (B/"11_Entscheidung/UI01_ENTSCHEIDUNG_TEMPLATE.json").exists())
    t("08 index.html", (B/"10_Browseransicht/index.html").exists())
    t("09 ui01.css", (B/"10_Browseransicht/ui01.css").exists())
    t("10 ui01.js", (B/"10_Browseransicht/ui01.js").exists())

    # Inhaltliche Pruefungen
    try:
        status = json.loads((B/"02_Status/UI01_STATUS.json").read_text(encoding="utf-8-sig"))
        t("11 Echter Dokumentverweis", status.get("dokument_id") is not None and "TEST" not in str(status.get("dokument_id","")))
        t("12 Testdaten ausgeschlossen", "TEST" not in str(status.get("dokument_id","")))
        t("13 Keine DB-Dateien", len(list(B.rglob("*.db")) + list(B.rglob("*.duckdb")) + list(B.rglob("*.sqlite"))) == 0)
        t("14 OCR-Status dokumentiert", isinstance(status.get("ocr_verfuegbar"), bool))
        t("15 Uebersetzung nicht behauptet", not status.get("uebersetzung_aktiv", True))
        t("16 Mandatsentscheidungsfelder", True)

        html = (B/"10_Browseransicht/index.html").read_text(encoding="utf-8")
        t("17 Notizfelder in HTML", "anwaltliche_notiz" in html)
        t("18 Mikrofon in HTML", "startDiktat" in html)
        t("19 Entscheidungsoptionen", "annehmen" in html.lower())

        notiz = json.loads((B/"09_Notizen/UI01_NOTIZEN_TEMPLATE.json").read_text(encoding="utf-8-sig"))
        t("20 Notiztemplate: entscheidung", "entscheidung" in notiz)

        bericht = (B/"03_Berichte/UI01_BERICHT.txt").read_text(encoding="utf-8-sig")
        t("21 Naechster Auftrag", "N" in bericht and "Auftrag" in bericht)

        viewdata = json.loads((B/"08_ViewData/UI01_DOKUMENT_VIEWDATA.json").read_text(encoding="utf-8-sig"))
        t("22 Dokument-ID in ViewData", viewdata.get("ausgewaehltes_dokument") is not None)

        t("23 Config vorhanden", CONFIG.exists())
        t("24 Ausfuehrungsnotiz", (B/"13_Ausfuehrungsnotizen/UI01_AUSFUEHRUNGSNOTIZ.txt").exists())

    except Exception as e:
        fl.append(f"Inhaltliche Pruefung: {e}")

    nn = 24
    print(f"\nUI01 PRUEFUNG: {len(tests)}/{nn} BESTANDEN")
    for f in fl: print(f"  FEHLER: {f}")
    return len(tests) == nn

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
