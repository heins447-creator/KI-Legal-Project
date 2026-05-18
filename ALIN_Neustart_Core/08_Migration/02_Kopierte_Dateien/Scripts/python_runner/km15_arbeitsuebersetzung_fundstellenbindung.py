# -*- coding: utf-8 -*-
"""
KLEINMODUL 15 – ARBEITSUEBERSETZUNGSSCHICHT MIT FUNDSTELLENBINDUNG (v1)
========================================================================

Zweck:
  Technische Arbeitsuebersetzungsschicht, die auf KM14-Fundstellen aufsetzt.
  Modelliert Uebersetzungseinheiten mit vollstaendiger Rueckbindungskette.

Grenzen:
  - KEINE endgueltige juristische Uebersetzung.
  - KEINE Rechtsbewertung.
  - KEINE erfundenen Uebersetzungen echter Dokumente.
  - Agent 044 wird NICHT ersetzt (nur vorbereitet).
  - Keine Originalaenderung, keine DB-Aenderung.
  - Kein Internet, keine Cloud.

Status:
  uebersetzung_nicht_ausgefuehrt_lokales_modell_nicht_angebunden

Aufruf:
  Normal:      python km15_arbeitsuebersetzung_fundstellenbindung.py
  Selbsttest:  python km15_arbeitsuebersetzung_fundstellenbindung.py --selftest
"""

import sys
import os
import json
import csv
import datetime
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------------------------

ROOT = Path(r"I:\KI_Legal_Project")
SCHREIBBEREICH = ROOT / "Agentensteuerung" / "15_Arbeitsuebersetzung_Fundstellenbindung"
CONFIG_DIR = ROOT / "Config"

STATUS_DIR = SCHREIBBEREICH / "02_Status"
BERICHTE = SCHREIBBEREICH / "03_Berichte"
TESTS_DIR = SCHREIBBEREICH / "04_Tests"
FEHLER_DIR = SCHREIBBEREICH / "05_Fehler"
ARTEFAKTE = SCHREIBBEREICH / "06_Artefakte"
MANIFEST_DIR = SCHREIBBEREICH / "07_Manifest"
UEBERSETZUNGSEINHEITEN = SCHREIBBEREICH / "08_Uebersetzungseinheiten"
UNSICHERHEITEN = SCHREIBBEREICH / "09_Unsicherheiten"
NOTIZEN = SCHREIBBEREICH / "13_Ausfuehrungsnotizen"

CONFIG_PATH = CONFIG_DIR / "arbeitsuebersetzung_fundstellenbindung_v1.json"

LOCALES_MODEL_NICHT_ANGEBUNDEN = "uebersetzung_nicht_ausgefuehrt_lokales_modell_nicht_angebunden"
PLATZHALTER_STATUS = "platzhalter_kein_lokales_modell"

KM14_FUNDSTELLEN_DIR = ROOT / "Agentensteuerung" / "14_Maschinenformat_Fundstellenstruktur" / "09_Fundstellen"
KM14_MANIFEST_PATH = ROOT / "Agentensteuerung" / "14_Maschinenformat_Fundstellenstruktur" / "07_Manifest" / "KM14_MASCHINENFORMAT_MANIFEST.json"
KM14_STATUS_PATH = ROOT / "Agentensteuerung" / "14_Maschinenformat_Fundstellenstruktur" / "02_Status" / "KM14_STATUS.json"

EU24_SPRACHEN_MAP = {
    "bul": "bg", "hrv": "hr", "ces": "cs", "dan": "da",
    "nld": "nl", "eng": "en", "est": "et", "fin": "fi",
    "fra": "fr", "deu": "de", "ell": "el", "hun": "hu",
    "gle": "ga", "ita": "it", "lav": "lv", "lit": "lt",
    "mlt": "mt", "pol": "pl", "por": "pt", "ron": "ro",
    "slk": "sk", "slv": "sl", "spa": "es", "swe": "sv",
}

STANDARD_KONFIG = {
    "version": "arbeitsuebersetzung_fundstellenbindung_v1",
    "km14_fundstellen_dir": str(KM14_FUNDSTELLEN_DIR),
    "km14_manifest_path": str(KM14_MANIFEST_PATH),
    "km14_status_path": str(KM14_STATUS_PATH),
    "zielsprache": "deu",
    "quellsprache_auto": True,
    "max_fundstellen_pro_seite": 500,
    "max_textsegment_zeichen": 5000,
    "rohdaten_ausgabe_verboten": True,
    "lokales_modell_verfuegbar": False,
    "modell_status": LOCALES_MODEL_NICHT_ANGEBUNDEN,
    "agent_044_nicht_ersetzen": True,
    "uebersetzung_aktiv": False,
}

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------------------------

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

def verzeichnisse_anlegen():
    for d in [STATUS_DIR, BERICHTE, TESTS_DIR, FEHLER_DIR, ARTEFAKTE,
              MANIFEST_DIR, UEBERSETZUNGSEINHEITEN, UNSICHERHEITEN, NOTIZEN]:
        d.mkdir(parents=True, exist_ok=True)

def lade_konfig():
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = dict(STANDARD_KONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            pass
    return dict(STANDARD_KONFIG)

def lade_json(pfad):
    p = Path(pfad)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

def bereinige_dummy_selftest_ausgaben():
    """Entfernt Dummy-Ausgaben aus dem echten KM15-Ergebnisbereich."""
    dummy_targets = [
        UEBERSETZUNGSEINHEITEN / "ORG-TEST_uebersetzungseinheiten.json",
        STATUS_DIR / "KM15_STATUS.json",
        MANIFEST_DIR / "KM15_MANIFEST.json",
        MANIFEST_DIR / "KM15_MANIFEST.csv",
        UNSICHERHEITEN / "KM15_UNSICHERHEITEN.json",
        UNSICHERHEITEN / "KM15_UNSICHERHEITEN.csv",
        BERICHTE / "KM15_BERICHT.txt",
        FEHLER_DIR / "KM15_FEHLER.txt",
        NOTIZEN / "KM15_AUSFUEHRUNGSNOTIZ.txt",
    ]
    for p in dummy_targets:
        try:
            if p.exists() and p.is_file():
                p.unlink()
        except Exception:
            pass
    for basis in [UEBERSETZUNGSEINHEITEN, MANIFEST_DIR, UNSICHERHEITEN, STATUS_DIR, BERICHTE, FEHLER_DIR, NOTIZEN]:
        try:
            if basis.exists():
                for fp in basis.glob("*ORG-TEST*"):
                    if fp.is_file():
                        fp.unlink()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# KM14 FUNDSTELLEN LADEN
# ---------------------------------------------------------------------------

def lade_km14_fundstellen(config):
    """Laedt alle KM14-Fundstellen-Dateien."""
    fundstellen_dir = Path(config["km14_fundstellen_dir"])
    alle_fundstellen = []

    if not fundstellen_dir.exists():
        return alle_fundstellen, [f"KM14-Fundstellen-Verzeichnis nicht gefunden: {fundstellen_dir}"]

    for fp in sorted(fundstellen_dir.glob("*_fundstellen.json")):
        try:
            daten = json.loads(fp.read_text(encoding="utf-8"))
            original_id = daten.get("original_id", fp.stem.replace("_fundstellen", ""))
            fundstellen_liste = daten.get("fundstellen", [])
            alle_fundstellen.append({
                "original_id": original_id,
                "datei": fp.name,
                "pfad": str(fp),
                "anzahl_fundstellen": len(fundstellen_liste),
                "fundstellen": fundstellen_liste,
            })
        except Exception as e:
            print(f"  Warnung: Konnte {fp} nicht lesen: {e}")

    return alle_fundstellen, []

# ---------------------------------------------------------------------------
# UEBERSETZUNGSEINHEITEN BAUEN
# ---------------------------------------------------------------------------

def baue_uebersetzungseinheiten(km14_daten, config):
    """Baut Uebersetzungseinheiten aus KM14-Fundstellen."""

    uebersetzungseinheiten = []
    unsicherheiten = []
    fehler = []
    statistik = {
        "originale_verarbeitet": len(km14_daten),
        "seiten_verarbeitet": 0,
        "uebersetzungseinheiten_erzeugt": 0,
        "uebersetzungseinheiten_wort": 0,
        "uebersetzungseinheiten_seite": 0,
        "unsicherheiten_markiert": 0,
        "lokales_modell_verfuegbar": config.get("lokales_modell_verfuegbar", False),
        "uebersetzung_aktiv": config.get("uebersetzung_aktiv", False),
    }

    seiten_ids = set()
    quellsprache_hinweis = "NICHT_ERKANNT"

    for original in km14_daten:
        original_id = original["original_id"]
        fundstellen = original["fundstellen"]

        for fs in fundstellen:
            fundstelle_id = fs.get("fundstelle_id", "UNBEKANNT")
            seiten_id = fs.get("seiten_id", "")
            seite_nummer = fs.get("seite_nummer", 0)
            quellebene = fs.get("quellebene", "UNBEKANNT")
            ocr_text = fs.get("text_original_ocr", "")
            text_normalisiert = fs.get("text_normalisiert", "")
            confidence = fs.get("confidence")
            ocr_status = fs.get("ocr_status", "UNBEKANNT")
            bbox = fs.get("bbox_px", [])
            tiff_pfad = fs.get("tiff_pfad", "")
            tiff_sha256 = fs.get("tiff_sha256", "")
            maschinenformat_pfad = fs.get("maschinenformat_pfad", "")
            fs_unsicherheiten = fs.get("unsicherheitsstatus", [])

            # Sprachhinweis (OCR-Erkennung ist nur eng/osd aus KM14-Perspektive)
            quellsprache_hinweis = "NICHT_BESTIMMT"

            # Unsicherheiten sammeln
            einheit_unsicherheiten = list(fs_unsicherheiten)

            # OCR-Text kuerzen (Rohdaten-Grenze)
            ocr_text_short = ocr_text[:197] + "..." if len(ocr_text) > 200 else ocr_text
            text_norm_short = text_normalisiert[:4997] + "..." if len(text_normalisiert) > 5000 else text_normalisiert

            # Uebersetzungseinheit bauen
            einheit = {}
            einheit["uebersetzungseinheit_id"] = f"{fundstelle_id}_UE"
            einheit["original_id"] = original_id
            einheit["seiten_id"] = seiten_id
            einheit["seite_nummer"] = seite_nummer
            einheit["fundstelle_id"] = fundstelle_id
            einheit["fundstelle_ebene"] = quellebene
            einheit["ocr_text_original"] = ocr_text_short
            einheit["ocr_text_normalisiert"] = text_norm_short
            einheit["confidence_ocr"] = confidence
            einheit["ocr_status"] = ocr_status
            einheit["bbox_px"] = bbox
            einheit["quellsprache_hinweis"] = quellsprache_hinweis
            einheit["zielsprache"] = config.get("zielsprache", "deu")
            einheit["uebersetzung_text"] = None
            einheit["uebersetzungsstatus"] = LOCALES_MODEL_NICHT_ANGEBUNDEN if not config.get("lokales_modell_verfuegbar", False) else "NICHT_AUSGEFUEHRT"
            einheit["uebersetzungsmodell"] = None
            einheit["confidence_uebersetzung"] = None
            einheit["unsicherheitsstatus"] = einheit_unsicherheiten
            einheit["rueckbindung_maschinenformat"] = maschinenformat_pfad
            einheit["rueckbindung_arbeitsabbildung_tiff"] = tiff_pfad
            einheit["rueckbindung_arbeitsabbildung_sha256"] = tiff_sha256
            einheit["uebergabestatus_agent044"] = "NICHT_FREIGEGEBEN"
            einheit["erzeugt_von_modul"] = "KM15"
            einheit["zeitpunkt"] = now()

            uebersetzungseinheiten.append(einheit)
            seiten_ids.add(seiten_id)

            if quellebene == "WORT":
                statistik["uebersetzungseinheiten_wort"] += 1
            elif quellebene == "SEITE":
                statistik["uebersetzungseinheiten_seite"] += 1

            if einheit_unsicherheiten:
                statistik["unsicherheiten_markiert"] += len(einheit_unsicherheiten)
            for kategorie in einheit_unsicherheiten:
                unsicherheiten.append({
                    "original_id": original_id,
                    "seite_nummer": seite_nummer,
                    "fundstelle_id": fundstelle_id,
                    "uebersetzungseinheit_id": einheit["uebersetzungseinheit_id"],
                    "kategorie": str(kategorie),
                    "quellebene": quellebene,
                    "zeitpunkt": now(),
                    "erzeugt_von_modul": "KM15",
                })

    statistik.update({
        "seiten_verarbeitet": len(seiten_ids),
        "uebersetzungseinheiten_erzeugt": len(uebersetzungseinheiten),
        "uebersetzungseinheiten_wort": statistik["uebersetzungseinheiten_wort"],
        "uebersetzungseinheiten_seite": statistik["uebersetzungseinheiten_seite"],
    })

    return uebersetzungseinheiten, unsicherheiten, fehler, statistik

# ---------------------------------------------------------------------------
# AUSGABEN SCHREIBEN
# ---------------------------------------------------------------------------

def schreibe_ausgaben(ue_einheiten, unsicherheiten, fehler, statistik, config):
    """Schreibt alle KM15-Ausgaben."""

    zielsprache = config.get("zielsprache", "deu")
    modell_status = config.get("modell_status", LOCALES_MODEL_NICHT_ANGEBUNDEN)

    # --- Uebersetzungseinheiten JSON pro Original ---
    originale = {}
    for ue in ue_einheiten:
        oid = ue["original_id"]
        if oid not in originale:
            originale[oid] = []
        originale[oid].append(ue)

    ue_manifest = []
    for oid, einheiten in sorted(originale.items()):
        dateiname = f"{oid}_uebersetzungseinheiten.json"
        pfad = UEBERSETZUNGSEINHEITEN / dateiname
        ausgabe = {
            "original_id": oid,
            "uebersetzungseinheiten": einheiten,
            "anzahl": len(einheiten),
            "uebersetzungsstatus": modell_status,
            "zielsprache": zielsprache,
            "erzeugt_von": "KM15",
            "zeitpunkt": now(),
        }
        pfad.write_text(json.dumps(ausgabe, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        ue_manifest.append({
            "original_id": oid,
            "datei": dateiname,
            "pfad": str(pfad),
            "anzahl_einheiten": len(einheiten),
        })

    # --- Unsicherheiten JSON ---
    us_json = UNSICHERHEITEN / "KM15_UNSICHERHEITEN.json"
    us_daten = {
        "modul": "KM15",
        "zeitpunkt": now(),
        "uebersetzungsstatus": modell_status,
        "unsicherheiten_einheiten": unsicherheiten,
        "anzahl_unsicherheiten": len(unsicherheiten),
        "grund": "Platzhalter-Schicht – kein lokales Uebersetzungsmodell verfuegbar",
    }
    us_json.write_text(json.dumps(us_daten, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Unsicherheiten CSV ---
    us_csv = UNSICHERHEITEN / "KM15_UNSICHERHEITEN.csv"
    with open(us_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["fundstelle_id", "kategorie", "original_id", "seite_nummer"])
        for u in unsicherheiten:
            writer.writerow([
                u.get("fundstelle_id", ""),
                u.get("kategorie", ""),
                u.get("original_id", ""),
                u.get("seite_nummer", ""),
            ])

    # --- Status ---
    status = {
        "modul": "KM15 – Arbeitsuebersetzungsschicht mit Fundstellenbindung",
        "version": config.get("version", "v1"),
        "zeitpunkt": now(),
        "schreibbereich": str(SCHREIBBEREICH),
        "lokales_modell_verfuegbar": config.get("lokales_modell_verfuegbar", False),
        "uebersetzungsstatus": modell_status,
        "uebersetzung_aktiv": config.get("uebersetzung_aktiv", False),
        "agent_044_nicht_ersetzt": config.get("agent_044_nicht_ersetzen", True),
        "statistik": statistik,
        "grenze_uebersetzung": True,
        "grenze_rechtsbewertung": True,
        "grenze_originalaenderung": True,
        "grenze_db_aenderung": True,
        "grenze_internet": True,
        "grenze_cloud": True,
        "produktivfreigabe": False,
        "naechster_empfohlener_auftrag": (
            "Lokales Uebersetzungsmodell in Tools/Translation bereitstellen "
            "(z.B. Argos Translate oder LibreTranslate), dann KM15-Neulauf. "
            "Danach Agent 044 als Client der Uebersetzungseinheiten aktivieren."
        ),
    }
    (STATUS_DIR / "KM15_STATUS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Manifest JSON ---
    manifest = {
        "modul": "KM15",
        "zeitpunkt": now(),
        "uebersetzungseinheiten_dateien": ue_manifest,
        "anzahl_originale": statistik.get("originale_verarbeitet", 0),
        "anzahl_seiten": statistik.get("seiten_verarbeitet", 0),
        "anzahl_uebersetzungseinheiten": statistik.get("uebersetzungseinheiten_erzeugt", 0),
        "uebersetzungsstatus": modell_status,
        "zielsprache": zielsprache,
    }
    (MANIFEST_DIR / "KM15_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    # --- Manifest CSV ---
    (MANIFEST_DIR / "KM15_MANIFEST.csv").write_text(
        f"original_id,datei,anzahl_einheiten\n" +
        "\n".join(f"{m['original_id']},{m['datei']},{m['anzahl_einheiten']}" for m in ue_manifest),
        encoding="utf-8-sig", newline="\n")

    # --- Bericht ---
    bericht_zeilen = [
        "=" * 70,
        "KM15 BERICHT – ARBEITSUEBERSETZUNGSSCHICHT MIT FUNDSTELLENBINDUNG",
        "=" * 70,
        f"Zeitpunkt: {now()}",
        f"Uebersetzungsstatus: {modell_status}",
        "",
        f"Originale verarbeitet:           {statistik.get('originale_verarbeitet', 0)}",
        f"Seiten verarbeitet:              {statistik.get('seiten_verarbeitet', 0)}",
        f"Uebersetzungseinheiten erzeugt:  {statistik.get('uebersetzungseinheiten_erzeugt', 0)}",
        f"  - Wortebene:                   {statistik.get('uebersetzungseinheiten_wort', 0)}",
        f"  - Seitenebene:                 {statistik.get('uebersetzungseinheiten_seite', 0)}",
        f"Unsicherheiten markiert:         {statistik.get('unsicherheiten_markiert', 0)}",
        f"Zielsprache:                     {zielsprache}",
        "",
        "GRENZEN (eingehalten)",
        "  Keine endgueltige juristische Uebersetzung",
        "  Keine Rechtsbewertung",
        "  Keine erfundenen Uebersetzungen echter Dokumente",
        "  Agent 044 nicht ersetzt",
        "  Keine Originalaenderung",
        "  Keine Datenbankaenderung",
        "  Kein Internet",
        "  Keine Cloud",
        "",
    ]
    if not config.get("lokales_modell_verfuegbar", False):
        bericht_zeilen += [
            "PLATZHALTER-SCHICHT",
            "  Es wurde KEINE echte Uebersetzung durchgefuehrt.",
            "  Alle Uebersetzungseinheiten haben Status:",
            f"    {modell_status}",
            "",
            "  Um echte Uebersetzung zu aktivieren:",
            "  1. Lokales Uebersetzungsmodell in Tools/Translation bereitstellen",
            "  2. Config/lokales_modell_verfuegbar auf true setzen",
            "  3. KM15-Neulauf ausfuehren",
        ]
    bericht_zeilen.append("")
    (BERICHTE / "KM15_BERICHT.txt").write_text(
        "\n".join(bericht_zeilen), encoding="utf-8", newline="\n")

    # --- Fehlerbericht ---
    (FEHLER_DIR / "KM15_FEHLER.txt").write_text(
        (f"{len(fehler)} Fehler\n\n" + "\n".join(f"  {e[:200]}" for e in fehler))
        if fehler else "Keine Fehler.\n",
        encoding="utf-8", newline="\n")

    # --- Ausfuehrungsnotiz ---
    (NOTIZEN / "KM15_AUSFUEHRUNGSNOTIZ.txt").write_text(
        "\n".join([
            "KM15 AUSFUEHRUNGSNOTIZ",
            "=" * 60,
            f"Zeit: {now()}",
            f"Uebersetzungsstatus: {modell_status}",
            f"Originale: {statistik.get('originale_verarbeitet', 0)}",
            f"Seiten: {statistik.get('seiten_verarbeitet', 0)}",
            f"Einheiten: {statistik.get('uebersetzungseinheiten_erzeugt', 0)}",
            f"Lokales Modell: NICHT VERFUEGBAR",
            f"Echte Uebersetzung: NICHT DURCHGEFUEHRT",
            f"Agent 044: NICHT ERSETZT",
        ]),
        encoding="utf-8", newline="\n")

    return status

# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def run_selftest():
    """Selbsttest mit Dummy-Daten."""
    print("=" * 60)
    print("KM15 SELBSTTEST – ARBEITSUEBERSETZUNGSSCHICHT")
    print("=" * 60)

    verzeichnisse_anlegen()
    config = lade_konfig()

    tests_bestanden = 0
    tests_gesamt = 14

    try:
        # Test 1: Konfiguration
        print("\nTest 1: Konfiguration ladbar...")
        assert config is not None
        assert "version" in config
        print("  OK")
        tests_bestanden += 1

        # Test 2: Uebersetzungsstatus ist Platzhalter
        print("\nTest 2: Uebersetzungsstatus...")
        assert config.get("modell_status") == LOCALES_MODEL_NICHT_ANGEBUNDEN
        assert config.get("uebersetzung_aktiv") == False
        print("  OK: Platzhalter-Status gesetzt")
        tests_bestanden += 1

        # Test 3: Dummy-Fundstelle bauen
        print("\nTest 3: Dummy-Fundstelle...")
        dummy_fs = {
            "fundstelle_id": "ORG-TEST_S0001_FS_WORT_1",
            "original_id": "ORG-TEST",
            "seite_nummer": 1,
            "seiten_id": "ORG-TEST_S0001",
            "quellebene": "WORT",
            "text_original_ocr": "Testwort",
            "text_normalisiert": "testwort",
            "confidence": 90.0,
            "ocr_status": "OK",
            "bbox_px": [100, 200, 50, 30],
            "tiff_pfad": "/pfad/test.tiff",
            "tiff_sha256": "abc123",
            "maschinenformat_pfad": "/pfad/test_maschinenformat.json",
            "unsicherheitsstatus": [],
        }
        assert dummy_fs["quellebene"] == "WORT"
        print("  OK")
        tests_bestanden += 1

        # Test 4: Uebersetzungseinheit aus Dummy bauen
        print("\nTest 4: Uebersetzungseinheit aus Dummy...")
        dummy_original = {"original_id": "ORG-TEST", "fundstellen": [dummy_fs],
                         "datei": "test.json", "pfad": "/pfad/test.json",
                         "anzahl_fundstellen": 1}
        einheiten, uns, fehl, stat = baue_uebersetzungseinheiten([dummy_original], config)
        assert stat["uebersetzungseinheiten_erzeugt"] == 1
        ue = einheiten[0]
        assert ue["uebersetzungsstatus"] == LOCALES_MODEL_NICHT_ANGEBUNDEN
        assert ue["uebersetzung_text"] is None
        assert ue["original_id"] == "ORG-TEST"
        print(f"  OK: 1 Einheit, Status={ue['uebersetzungsstatus']}")
        tests_bestanden += 1

        # Test 5: Uebersetzungseinheit hat alle Pflichtfelder
        print("\nTest 5: Pflichtfelder...")
        pflichtfelder = [
            "uebersetzungseinheit_id", "original_id", "seiten_id",
            "fundstelle_id", "ocr_text_original", "uebersetzungsstatus",
            "zielsprache", "rueckbindung_maschinenformat", "uebergabestatus_agent044"
        ]
        for feld in pflichtfelder:
            assert feld in ue, f"Feld fehlt: {feld}"
        print(f"  OK: Alle {len(pflichtfelder)} Pflichtfelder")
        tests_bestanden += 1

        # Test 6: Keine Uebersetzung erzeugt
        print("\nTest 6: Keine erfundene Uebersetzung...")
        assert ue["uebersetzung_text"] is None
        print("  OK")
        tests_bestanden += 1

        # Test 7: Agent 044 nicht ersetzt
        print("\nTest 7: Agent 044 Uebergabestatus...")
        assert ue["uebergabestatus_agent044"] == "NICHT_FREIGEGEBEN"
        assert config.get("agent_044_nicht_ersetzen") == True
        print("  OK")
        tests_bestanden += 1

        # Test 8: Ausgaben schreibbar
        print("\nTest 8: Ausgaben schreibbar...")
        status = schreibe_ausgaben(einheiten, uns, fehl, stat, config)
        assert UEBERSETZUNGSEINHEITEN.joinpath("ORG-TEST_uebersetzungseinheiten.json").exists()
        assert STATUS_DIR.joinpath("KM15_STATUS.json").exists()
        assert MANIFEST_DIR.joinpath("KM15_MANIFEST.json").exists()
        print("  OK: Uebersetzungseinheiten, Status, Manifest geschrieben")
        tests_bestanden += 1

        # Test 9: Statistik korrekt
        print("\nTest 9: Statistik...")
        assert stat["uebersetzungseinheiten_erzeugt"] == 1
        assert stat["uebersetzungseinheiten_wort"] == 1
        assert stat["uebersetzungseinheiten_seite"] == 0
        assert stat["seiten_verarbeitet"] == 1
        print("  OK: Zaehler korrekt")
        tests_bestanden += 1

        # Test 10: Dummy-Seitenebene
        print("\nTest 10: Dummy-Seitenfundstelle...")
        dummy_seite = dict(dummy_fs)
        dummy_seite["fundstelle_id"] = "ORG-TEST_S0001_FS_SEITE"
        dummy_seite["quellebene"] = "SEITE"
        dummy_seite["text_original_ocr"] = "Ganze Seite Text"
        dummy_orig2 = {"original_id": "ORG-TEST", "fundstellen": [dummy_fs, dummy_seite],
                       "datei": "test2.json", "pfad": "/pfad/test2.json",
                       "anzahl_fundstellen": 2}
        e2, u2, f2, s2 = baue_uebersetzungseinheiten([dummy_orig2], config)
        assert s2["uebersetzungseinheiten_erzeugt"] == 2
        assert s2["uebersetzungseinheiten_wort"] == 1
        assert s2["uebersetzungseinheiten_seite"] == 1
        print("  OK: 2 Einheiten (1 Wort + 1 Seite)")
        tests_bestanden += 1

        # Test 11: Rueckbindungskette
        print("\nTest 11: Rueckbindungskette...")
        assert ue["rueckbindung_maschinenformat"] == "/pfad/test_maschinenformat.json"
        assert ue["rueckbindung_arbeitsabbildung_tiff"] == "/pfad/test.tiff"
        assert ue["rueckbindung_arbeitsabbildung_sha256"] == "abc123"
        print("  OK")
        tests_bestanden += 1

        # Test 12: Grenzen eingehalten
        print("\nTest 12: Grenzen...")
        assert status["grenze_uebersetzung"] == True
        assert status["grenze_rechtsbewertung"] == True
        assert status["grenze_originalaenderung"] == True
        assert status["grenze_db_aenderung"] == True
        assert status["grenze_internet"] == True
        assert status["grenze_cloud"] == True
        assert status["produktivfreigabe"] == False
        print("  OK: Alle Grenzen gesetzt")
        tests_bestanden += 1

        # Test 13: Unsicherheiten JSON/CSV vorhanden
        print("\nTest 13: Unsicherheiten-Ausgaben...")
        assert UNSICHERHEITEN.joinpath("KM15_UNSICHERHEITEN.json").exists()
        assert UNSICHERHEITEN.joinpath("KM15_UNSICHERHEITEN.csv").exists()
        print("  OK")
        tests_bestanden += 1

        # Test 14: Manifest CSV
        print("\nTest 14: Manifest CSV...")
        csv_content = MANIFEST_DIR.joinpath("KM15_MANIFEST.csv").read_text(encoding="utf-8")
        assert "ORG-TEST" in csv_content
        print("  OK")
        tests_bestanden += 1

    except Exception as e:
        print(f"\nFEHLER: {e}")
        traceback.print_exc()

    bereinige_dummy_selftest_ausgaben()

    print("\n" + "=" * 60)
    print(f"SELBSTTEST: {tests_bestanden}/{tests_gesamt} BESTANDEN")
    print("=" * 60)
    return tests_bestanden == tests_gesamt

# ---------------------------------------------------------------------------
# HAUPTFUNKTION
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KLEINMODUL 15 – ARBEITSUEBERSETZUNGSSCHICHT MIT FUNDSTELLENBINDUNG")
    print("=" * 60)
    print(f"Zeitpunkt:      {now()}")
    print(f"Schreibbereich: {SCHREIBBEREICH}")
    print()

    verzeichnisse_anlegen()
    config = lade_konfig()

    try:
        print("[1/4] KM14-Fundstellen laden...")
        km14_daten, fehler = lade_km14_fundstellen(config)
        print(f"      Originale mit Fundstellen: {len(km14_daten)}")
        for d in km14_daten:
            print(f"        {d['original_id']}: {d['anzahl_fundstellen']} Fundstellen")

        print("[2/4] Uebersetzungseinheiten bauen...")
        ue_einheiten, unsicherheiten, bau_fehler, statistik = baue_uebersetzungseinheiten(km14_daten, config)
        fehler.extend(bau_fehler)
        print(f"      Einheiten erzeugt:  {statistik['uebersetzungseinheiten_erzeugt']}")
        print(f"      Seiten:             {statistik['seiten_verarbeitet']}")
        print(f"      Status:             {config.get('modell_status')}")

        print("[3/4] Ausgaben schreiben...")
        status = schreibe_ausgaben(ue_einheiten, unsicherheiten, fehler, statistik, config)

        print("[4/4] Zusammenfassung...")
        print()
        print("=" * 60)
        print("KM15 ABGESCHLOSSEN")
        print("=" * 60)
        print(f"Uebersetzungsstatus:     {config.get('modell_status')}")
        print(f"Originale verarbeitet:   {statistik['originale_verarbeitet']}")
        print(f"Seiten:                  {statistik['seiten_verarbeitet']}")
        print(f"Uebersetzungseinheiten:  {statistik['uebersetzungseinheiten_erzeugt']}")
        print(f"  - Wortebene:           {statistik['uebersetzungseinheiten_wort']}")
        print(f"  - Seitenebene:         {statistik['uebersetzungseinheiten_seite']}")
        print(f"Unsicherheiten:          {statistik['unsicherheiten_markiert']}")
        print(f"Zielsprache:             {config.get('zielsprache', 'deu')}")
        print()
        print(f"Status:       {STATUS_DIR / 'KM15_STATUS.json'}")
        print(f"Bericht:      {BERICHTE / 'KM15_BERICHT.txt'}")
        print(f"Manifest:     {MANIFEST_DIR / 'KM15_MANIFEST.json'}")
        print(f"Einheiten:    {UEBERSETZUNGSEINHEITEN}")
        print()
        print("KEINE echte Uebersetzung durchgefuehrt.")
        print("Agent 044 nicht ersetzt.")
        print("Keine Rechtsbewertung erzeugt.")
        print("Keine Originalaenderung.")
        print("Keine DB-Aenderung.")

        return len(fehler) == 0

    except Exception as e:
        print(f"FEHLER: {e}")
        traceback.print_exc()
        return False

# ---------------------------------------------------------------------------
# EINSTIEG
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        if "--selftest" in sys.argv:
            success = run_selftest()
            sys.exit(0 if success else 1)
        else:
            ok = main()
            sys.exit(0 if ok else 1)
    except KeyboardInterrupt:
        print("\nABGEBROCHEN DURCH STRG+C")
        sys.exit(130)
    except Exception as exc:
        print("\nFEHLER")
        traceback.print_exc()
        sys.exit(1)
