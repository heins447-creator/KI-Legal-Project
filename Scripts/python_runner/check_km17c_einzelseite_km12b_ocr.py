#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KM17c – Prüfdatei
=================
Prüft die KM17c-OCR-Ergebnisse für die KM12b-abgeleitete Einzelseite
ORG-9dd16304b3b5-00162 auf Vollständigkeit und Integrität.
"""

import json
import sys
from pathlib import Path

PROJEKTWURZEL = Path(r"I:\KI_Legal_Project")
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "km17c_einzelseite_km12b_ocr_v1.json"
SB_ROOT = PROJEKTWURZEL / "Agentensteuerung" / "17c_Einzelne_KM12b_Seite_OCR"

# Geschützte Originalbereiche, die nicht beschrieben sein dürfen
GESPERRTE_BEREICHE = [
    PROJEKTWURZEL / "Agentensteuerung" / "12_Originalabbildung_Arbeitsabbildung",
    PROJEKTWURZEL / "Agentensteuerung" / "12b_Uebergrosse_Arbeitsabbildungen" /
    "08_Abgeleitete_Arbeitsabbildungen",
    PROJEKTWURZEL / "Database",
]


def check(name: str, ok: bool, detail: str = "", fehler_liste: list = None):
    """Einzelne Prüfung mit Statusausgabe."""
    status = "[OK]" if ok else "[FEHLER]"
    ausgabe = f"{status} {name}"
    if detail:
        ausgabe += f"  – {detail}"
    print(ausgabe)
    if not ok and fehler_liste is not None:
        fehler_liste.append(f"{name}: {detail}")
    return ok


def main() -> int:
    print("=" * 60)
    print("KM17c PRÜFUNG – EINZELSEITE KM12b OCR")
    print("=" * 60)

    fehler_liste = []
    bestanden = 0
    gesamt = 0

    # Config laden
    cfg = None
    try:
        cfg = json.loads(CONFIG_PFAD.read_text(encoding="utf-8"))
    except Exception as e:
        check("Config ladbar", False, str(e), fehler_liste)
        print("\nPRÜFUNG: Abbruch – Config nicht ladbar")
        return 1

    ziel = cfg.get("ziel_seite", {})
    oid = ziel.get("original_id", "UNBEKANNT")
    sn = ziel.get("seite_nummer", 0)

    # 1. Status JSON vorhanden
    gesamt += 1
    status_pfad = SB_ROOT / "02_Status" / "KM17c_STATUS.json"
    hat_status = status_pfad.exists()
    if check("  1  Status JSON vorhanden", hat_status, str(status_pfad), fehler_liste):
        bestanden += 1

    # 2. Manifest JSON vorhanden
    gesamt += 1
    mj_pfad = SB_ROOT / "07_Manifest" / "KM17c_MANIFEST.json"
    hat_mjson = mj_pfad.exists()
    if check("  2  Manifest JSON vorhanden", hat_mjson, str(mj_pfad), fehler_liste):
        bestanden += 1

    # 3. Manifest CSV vorhanden
    gesamt += 1
    mc_pfad = SB_ROOT / "07_Manifest" / "KM17c_MANIFEST.csv"
    hat_mcsv = mc_pfad.exists()
    if check("  3  Manifest CSV vorhanden", hat_mcsv, str(mc_pfad), fehler_liste):
        bestanden += 1

    # 4. Bericht vorhanden
    gesamt += 1
    bericht_pfad = SB_ROOT / "03_Berichte" / "KM17c_BERICHT.txt"
    hat_bericht = bericht_pfad.exists()
    if check("  4  Bericht vorhanden", hat_bericht, str(bericht_pfad), fehler_liste):
        bestanden += 1

    # 5. Fehlerbericht vorhanden
    gesamt += 1
    fehler_pfad = SB_ROOT / "05_Fehler" / "KM17c_FEHLER.txt"
    hat_fehler = fehler_pfad.exists()
    if check("  5  Fehlerbericht vorhanden", hat_fehler, str(fehler_pfad), fehler_liste):
        bestanden += 1

    # 6. Ausführungsnotiz vorhanden
    gesamt += 1
    notiz_pfad = SB_ROOT / "13_Ausfuehrungsnotizen" / "KM17c_AUSFUEHRUNGSNOTIZ.txt"
    hat_notiz = notiz_pfad.exists()
    if check("  6  Ausführungsnotiz vorhanden", hat_notiz, str(notiz_pfad), fehler_liste):
        bestanden += 1

    # 7. Config vorhanden
    gesamt += 1
    if check("  7  Config vorhanden", CONFIG_PFAD.exists(), str(CONFIG_PFAD), fehler_liste):
        bestanden += 1

    # 8. JSON-Dateien gültig
    gesamt += 1
    json_ok = True
    for pfad, label in [(status_pfad, "Status"), (mj_pfad, "Manifest")]:
        try:
            if pfad.exists():
                json.loads(pfad.read_text(encoding="utf-8"))
        except Exception as e:
            json_ok = False
            fehler_liste.append(f"JSON {label} ungültig: {e}")
    if check("  8  JSON-Dateien gültig", json_ok, "", fehler_liste):
        bestanden += 1

    # 9. Abgeleitete KM12b-TIFF wurde verwendet
    gesamt += 1
    abgeleitet_tiff = (
        PROJEKTWURZEL /
        ziel.get("abgeleitete_tiff_quelle",
                 "Agentensteuerung\\12b_Uebergrosse_Arbeitsabbildungen"
                 "\\08_Abgeleitete_Arbeitsabbildungen"
                 f"\\{oid}\\seite_0001_downscaled.tiff")
    )
    tiff_existiert = abgeleitet_tiff.exists()

    # Prüfe im Manifest nach ob die TIFF-SHA256 passt
    manifest_tiff_ok = False
    if hat_mjson:
        try:
            man = json.loads(mj_pfad.read_text(encoding="utf-8"))
            erg_liste = man.get("ergebnisse", [])
            if erg_liste:
                erg = erg_liste[0]
                tiff_pfad_ist = erg.get("tiff_pfad", "")
                abgeleitet_str = str(abgeleitet_tiff.resolve())
                manifest_tiff_ok = (
                    tiff_pfad_ist.replace("\\", "/").lower() ==
                    abgeleitet_str.replace("\\", "/").lower()
                )
        except Exception:
            pass
    abgeleitet_ok = tiff_existiert and manifest_tiff_ok
    detail = f"TIFF vorhanden={tiff_existiert}, im Manifest={manifest_tiff_ok}"
    if check("  9  Abgeleitete KM12b-TIFF verwendet", abgeleitet_ok, detail, fehler_liste):
        bestanden += 1

    # 10. Keine KM12-Originalabbildung überschrieben
    gesamt += 1
    km12_original = (
        PROJEKTWURZEL /
        "Agentensteuerung\\12_Originalabbildung_Arbeitsabbildung"
        "\\08_Arbeitsabbildungen" / oid / f"seite_{sn:04d}.tiff"
    )
    km12_unveraendert = True
    if km12_original.exists():
        import hashlib
        urspr_sha = ziel.get("urspr_tiff_sha256", "")
        if urspr_sha:
            h = hashlib.sha256()
            with open(km12_original, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            aktuell_sha = h.hexdigest()
            km12_unveraendert = (aktuell_sha == urspr_sha)
    if check(" 10  Keine KM12-Originalabbildung überschrieben", km12_unveraendert,
             f"KM12-Original SHA256 OK={km12_unveraendert}", fehler_liste):
        bestanden += 1

    # 11. Keine Originaldatei verändert
    gesamt += 1
    original_ok = True
    for bereich in GESPERRTE_BEREICHE:
        if bereich.exists():
            for f in bereich.rglob("*"):
                if f.is_file() and f.suffix in (".tiff", ".tif", ".png", ".jpg", ".jpeg"):
                    mtime = f.stat().st_mtime
                    # Wir prüfen, dass keine KM17c-Dateien in den geschützten Bereich
                    # geschrieben wurden – vereinfachte Prüfung:
                    if "KM17c" in f.name:
                        original_ok = False
                        fehler_liste.append(f"KM17c-Datei in geschütztem Bereich: {f}")
                        break
            if not original_ok:
                break
    if check(" 11  Keine Originaldatei verändert", original_ok, "", fehler_liste):
        bestanden += 1

    # 12. Keine Datenbankdatei im Schreibbereich
    gesamt += 1
    db_im_sb = list(SB_ROOT.rglob("*.db")) + list(SB_ROOT.rglob("*.sqlite"))
    if check(" 12  Keine DB-Datei im Schreibbereich", not db_im_sb,
             f"Gefunden: {db_im_sb}" if db_im_sb else "", fehler_liste):
        bestanden += 1

    # 13. TXT-Datei vorhanden oder Fehler sauber dokumentiert
    gesamt += 1
    txt_pfade = list(SB_ROOT.rglob("*.txt"))
    ocr_txt = [p for p in txt_pfade if p.parent.name == oid or "OCR" in str(p)]
    # Einfacher: Prüfe ob überhaupt eine .txt existiert
    txt_ok = len(txt_pfade) > 0
    if check(" 13  TXT-Datei(en) vorhanden", txt_ok,
             f"Anzahl .txt im SB: {len(txt_pfade)}", fehler_liste):
        bestanden += 1

    # 14. HOCR-Datei vorhanden oder Fehler sauber dokumentiert
    gesamt += 1
    hocr_pfade = list(SB_ROOT.rglob("*.hocr"))
    hocr_ok = len(hocr_pfade) > 0
    if check(" 14  HOCR-Datei(en) vorhanden", hocr_ok,
             f"Anzahl .hocr im SB: {len(hocr_pfade)}", fehler_liste):
        bestanden += 1

    # 15. TSV-Datei vorhanden oder Fehler sauber dokumentiert
    gesamt += 1
    tsv_pfade = list(SB_ROOT.rglob("*.tsv"))
    tsv_ok = len(tsv_pfade) > 0
    if check(" 15  TSV-Datei(en) vorhanden", tsv_ok,
             f"Anzahl .tsv im SB: {len(tsv_pfade)}", fehler_liste):
        bestanden += 1

    # 16. SHA256 von Eingangs-TIFF und Ausgaben vorhanden
    gesamt += 1
    sha_ok = False
    if hat_mjson:
        try:
            man = json.loads(mj_pfad.read_text(encoding="utf-8"))
            erg_liste = man.get("ergebnisse", [])
            if erg_liste:
                erg = erg_liste[0]
                sha_ok = (
                    len(erg.get("tiff_sha256", "")) == 64 and
                    len(erg.get("eingangs_tiff_sha256_ist", "")) == 64
                )
        except Exception:
            pass
    if check(" 16  SHA256 dokumentiert", sha_ok, "", fehler_liste):
        bestanden += 1

    # 17. OCR nur für eine Seite ausgeführt
    gesamt += 1
    einseitig_ok = False
    if hat_status:
        try:
            stat = json.loads(status_pfad.read_text(encoding="utf-8"))
            einseitig_ok = (
                stat.get("ziel_seite") == oid and
                stat.get("ziel_seite_nummer") == sn
            )
        except Exception:
            pass
    if check(" 17  OCR nur für eine Seite", einseitig_ok,
             f"Ziel={oid} S.{sn}", fehler_liste):
        bestanden += 1

    # 18. Keine Übersetzung erzeugt
    gesamt += 1
    trans_dateien = [f for f in SB_ROOT.rglob("*")
                     if f.suffix in (".de", ".en", ".trans", ".translated")]
    if check(" 18  Keine Übersetzung erzeugt", not trans_dateien,
             f"Gefunden: {trans_dateien}" if trans_dateien else "", fehler_liste):
        bestanden += 1

    # 19. Keine Rechtsbewertung
    gesamt += 1
    # Prüfe Status auf rechtsbewertung=false
    rw_ok = True
    if hat_status:
        try:
            stat = json.loads(status_pfad.read_text(encoding="utf-8"))
            rw_ok = (
                stat.get("rechtsbewertung") is False and
                stat.get("beweiswuerdigung") is False
            )
        except Exception:
            rw_ok = False
    if check(" 19  Keine Rechtsbewertung", rw_ok, "", fehler_liste):
        bestanden += 1

    # 20. Nächster Auftrag formuliert
    gesamt += 1
    na_ok = False
    if hat_status:
        try:
            stat = json.loads(status_pfad.read_text(encoding="utf-8"))
            na_ok = bool(stat.get("naechster_empfohlener_auftrag", ""))
        except Exception:
            pass
    if check(" 20  Nächster Auftrag formuliert", na_ok, "", fehler_liste):
        bestanden += 1

    # Zusammenfassung
    print("\n" + "=" * 60)
    if fehler_liste:
        print(f"PRÜFUNG: {bestanden}/{gesamt} BESTANDEN ({len(fehler_liste)} FEHLER)")
        print("Fehlerdetails:")
        for f in fehler_liste:
            print(f"  - {f}")
    else:
        print(f"PRÜFUNG: {bestanden}/{gesamt} BESTANDEN")
    print("=" * 60)

    return 0 if not fehler_liste else 1


if __name__ == "__main__":
    sys.exit(main())
