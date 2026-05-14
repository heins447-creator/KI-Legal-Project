import sys, json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
B = ROOT / "Agentensteuerung/21_Translation_Environment"
CONFIG = ROOT / "Config/km21_translation_env_v1.json"

def t(bez, bed, tests, fl):
    if bed: tests.append(1); print("  [OK] " + bez)
    else: fl.append(bez); print("  [FEHLER] " + bez)

def main():
    print("KM21 PRUEFUNG " + "=" * 40)
    tests, fl = [], []

    t("01 Config vorhanden", CONFIG.exists(), tests, fl)
    t("02 Status JSON", (B/"02_Status/KM21_STATUS.json").exists(), tests, fl)
    t("03 Manifest JSON", (B/"07_Manifest/KM21_MANIFEST.json").exists(), tests, fl)
    t("04 Manifest CSV", (B/"07_Manifest/KM21_MANIFEST.csv").exists(), tests, fl)
    t("05 Bericht TXT", (B/"03_Berichte/KM21_BERICHT.txt").exists(), tests, fl)
    t("06 Fehlerbericht TXT", (B/"05_Fehler/KM21_FEHLER.txt").exists(), tests, fl)
    t("07 Ausfuehrungsnotiz TXT", (B/"13_Ausfuehrungsnotizen/KM21_AUSFUEHRUNGSNOTIZ.txt").exists(), tests, fl)
    t("08 Inventar JSON", (B/"08_Inventar/KM21_TRANSLATION_INVENTAR.json").exists(), tests, fl)
    t("09 Inventar CSV", (B/"08_Inventar/KM21_TRANSLATION_INVENTAR.csv").exists(), tests, fl)
    t("10 Dummy-Test JSON", (B/"09_Test/KM21_DUMMY_TRANSLATION_TEST.json").exists(), tests, fl)
    t("11 KM15-Interface JSON", (B/"10_Schnittstelle_KM15/KM21_KM15_TRANSLATION_INTERFACE.json").exists(), tests, fl)
    t("12 KM15-Interface MD", (B/"10_Schnittstelle_KM15/KM21_KM15_TRANSLATION_INTERFACE.md").exists(), tests, fl)
    t("13 Translation-Verzeichnis", (ROOT/"Tools/Translation").exists(), tests, fl)

    try:
        status = json.loads((B/"02_Status/KM21_STATUS.json").read_text(encoding="utf-8-sig"))
        t("14 JSON gueltig", True, tests, fl)
        t("15 Status: argos-Status", "argos_translate_status" in status, tests, fl)
        t("16 Status: keine DB", "datenbank_aenderungen" not in status or not status.get("datenbank_aenderungen"), tests, fl)
        t("17 Status: keine Installation", status.get("grenzen_eingehalten", False) == True, tests, fl)
        t("18 Verfuegbarkeits-Status", isinstance(status.get("lokale_uebersetzung_verfuegbar"), bool), tests, fl)

        manifest = json.loads((B/"07_Manifest/KM21_MANIFEST.json").read_text(encoding="utf-8-sig"))
        t("19 Manifest: sprachrichtungen", len(manifest.get("sprachrichtungen", {})) == 3, tests, fl)

        test = json.loads((B/"09_Test/KM21_DUMMY_TRANSLATION_TEST.json").read_text(encoding="utf-8-sig"))
        t("20 Test: keine echten Akten", test.get("keine_echten_akten", False) == True, tests, fl)

        # Pruefe: keine DB, keine echten OCR-Inhalte, keine Installation
        db_files = list(B.rglob("*.db")) + list(B.rglob("*.duckdb")) + list(B.rglob("*.sqlite"))
        t("21 Keine DB-Dateien in KM21", len(db_files) == 0, tests, fl)

        # Naechster Auftrag formuliert
        bericht = (B/"03_Berichte/KM21_BERICHT.txt").read_text(encoding="utf-8-sig")
        t("22 Naechster Auftrag formuliert", "Auftrag" in bericht, tests, fl)

        iface = json.loads((B/"10_Schnittstelle_KM15/KM21_KM15_TRANSLATION_INTERFACE.json").read_text(encoding="utf-8-sig"))
        t("23 KM15-Freigabe dokumentiert", "km15_darf_uebersetzen" in iface.get("status", {}), tests, fl)

    except Exception as e:
        t("14-23 Inhaltlich", False, tests, fl)
        fl.append(f"Inhaltliche Pruefung: {e}")

    print(f"\nKM21 PRUEFUNG: {len(tests)}/23 BESTANDEN")
    if fl:
        for f in fl:
            print(f"  FEHLER: {f}")
    return len(tests) == 23

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
